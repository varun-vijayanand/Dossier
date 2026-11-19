# Dossier: Technical Design Document

*Version 1.0 draft · Companion to the PRD · Requirement IDs (FR-x.x) refer to the PRD*

## 1. Purpose and Scope

This document describes how Dossier is built: components, data model, interfaces, the agent workflow, and how it is deployed and operated. It is the reference for implementation. Product intent and acceptance criteria live in the PRD, test methods in the Evaluation and Test Plan, and controls in the Security and System Card.

## 2. Architecture Overview

```
Analyst (browser)
      |
  Streamlit console
      |  HTTPS + JWT
  FastAPI service  -------------------------+
      |                                     |
  Agent worker (LangGraph)            Postgres + pgvector
      |        |                      (data, checkpoints,
      |        +--> LLM provider       audit log, vectors)
      |             (Claude via API)        ^
      |  MCP (streamable HTTP)              |
  MCP server  ------------------------------+
  (tools, resources, masking, RBAC)

All services --> Langfuse (traces, cost, eval scores)
```

### Components

| Component | Responsibility | Technology | Scaling note |
| --- | --- | --- | --- |
| Console | Alert queue, evidence view, review actions, governance view | Streamlit | Single replica |
| API service | Auth, alert and run endpoints, review decisions, audit queries | FastAPI, Pydantic | Scale to zero when idle |
| Agent worker | Runs the LangGraph workflow, calls the LLM and MCP tools | Python, LangGraph | One run per alert; concurrency capped |
| MCP server | Only path from the agent to bank data and retrieval; masking, role checks, call logging | MCP Python SDK | Stateless, scale to zero |
| Database | Operational data, vectors, graph checkpoints, audit log | Postgres with pgvector | Hosted free tier for demo |
| Observability | Traces, token cost, latency, eval scores | Langfuse | Hosted or compose-local |

## 3. Key Design Decisions

| ID | Decision | Alternatives considered | Rationale |
| --- | --- | --- | --- |
| D1 | Agent reaches data only through an MCP server | Direct SQL tools inside the agent | One audited, role-checked boundary; the same tools work from any MCP client |
| D2 | LangGraph state machine with a human interrupt | Free-form tool-calling loop | Deterministic routing, bounded retries, resumable runs, inspectable state |
| D3 | Statistics and aggregations computed in SQL or Python | Letting the model compute | Numbers must be exact; the model reasons and writes |
| D4 | Separate grounding verification step | Trusting the draft | Catches unsupported claims before a human sees them |
| D5 | One Postgres with pgvector | Postgres plus a separate vector database | Fewer services to run and pay for; sufficient for a small corpus |
| D6 | Tiered models: Haiku 5.5 for triage, query building, and verification; Sonnet 5.5 for assessment and drafting | One model for everything | Cost and latency control without hurting the steps that need quality |
| D7 | Evidence IDs on every returned record | Free-text citations | Machine-checkable grounding |
| D8 | Masking applied in the MCP layer | Masking in the UI | Sensitive values never reach prompts or traces |
| D9 | Ground-truth labels excluded from all tool outputs | Label access for convenience | Prevents evaluation leakage |
| D10 | Azure Container Apps with scale to zero | Always-on VM or AWS service | Near-zero idle cost for a demo |

## 4. Data Model

All tables live in one Postgres database. Key columns and constraints are shown; add indexes on foreign keys and on (account\_id, timestamp) for transactions.

```sql
create table customers (
  customer_id text primary key,
  name_masked text, customer_type text check (customer_type in ('individual','entity')),
  nationality text, residence_country text, occupation_or_industry text,
  expected_monthly_turnover numeric, risk_rating text, pep_flag boolean,
  onboarded_on date
);
create table accounts (
  account_id text primary key, customer_id text references customers,
  bank_id text, account_type text, currency text, opened_on date, status text
);
create table transactions (
  txn_id text primary key, ts timestamptz not null,
  from_account text references accounts, to_account text references accounts,
  amount numeric not null, currency text, payment_format text, channel text,
  counterparty_country text, memo text,
  is_laundering boolean  -- label: never returned by any tool
);
create table alerts (
  alert_id text primary key, account_id text references accounts,
  created_at timestamptz, priority text, status text,
  ground_truth text  -- evaluation only, never returned by any tool
);
create table rule_hits (
  hit_id text primary key, alert_id text references alerts,
  rule_id text, rule_name text, window_start timestamptz, window_end timestamptz,
  details jsonb
);
create table cases (
  case_id text primary key, alert_ids text[], assignee text,
  disposition text, status text, created_at timestamptz, updated_at timestamptz
);
create table narratives (
  narrative_id uuid primary key, case_id text references cases, version int,
  body jsonb not null, model_id text, prompt_version text, tool_versions jsonb,
  created_at timestamptz, approved_by text, approved_at timestamptz,
  unique (case_id, version)
);
create table typology_chunks (
  chunk_id text primary key, source text, jurisdiction text, typology_tag text,
  section_title text, published_on date, content text, embedding vector(1024)
);
create table audit_log (
  event_id uuid primary key, ts timestamptz default now(), actor text, actor_role text,
  action text, resource text, input_hash text, output_hash text, trace_id text
);
```

- The audit log is append-only: the application role has insert and select rights only.
- The embedding dimension depends on the chosen embedding model; set it from configuration.
- LangGraph checkpoint tables are created by the checkpointer library in the same database.

## 5. MCP Server

### Transport and identity

- Streamable HTTP for deployment, stdio for local development and desktop-client testing.
- The API service passes a signed token containing the caller's role and a trace ID. The server validates it, applies role-based masking, and logs the call.
- The server is read-only except for `save_case_draft`, which can only create a draft record.

### Common response envelope

```json
{
  "data": {},
  "evidence_ids": ["txn:T1042", "kyc:C77"],
  "truncated": false,
  "next_cursor": null,
  "as_of": "2026-11-12T10:00:00Z"
}
```

### Tool contracts

| Tool | Input | Output (in `data`) | Limits |
| --- | --- | --- | --- |
| list\_alerts | status?, priority?, limit, cursor | Alert summaries | limit at most 100 |
| get\_alert | alert\_id | Alert, rule hits, account reference | n/a |
| get\_customer\_kyc | customer\_id | Masked profile, risk rating, PEP flag, expected turnover | Fields masked by role |
| get\_transactions | account\_id, start, end, direction?, min\_amount?, limit, cursor | Transactions with evidence IDs | limit at most 200 per page |
| get\_behavior\_stats | account\_id, window\_days | Volume, velocity, baseline deviation, counterparty counts, balance retention | Computed in SQL |
| get\_counterparty\_network | account\_id, hops (1 or 2), window\_days | Nodes and edges with amounts | At most 100 nodes |
| get\_prior\_cases | customer\_id | Earlier alerts and dispositions | At most 20 |
| search\_typologies | query, jurisdiction?, top\_k | Ranked chunks with chunk IDs and source | top\_k at most 10 |
| save\_case\_draft | case\_id, narrative\_json, recommendation | Draft ID and status | Creates a draft only |

### Resources and prompts

- Resources: typology cards, data dictionary, report templates (India STR primary, FinCEN SAR secondary), investigation playbook.
- Prompt: a reusable "investigate this alert" prompt so any MCP client can follow the same procedure.

### Error contract

```json
{ "error": { "code": "LIMIT_EXCEEDED", "message": "...", "retryable": false } }
```

Codes: `INVALID_ARGUMENT`, `NOT_FOUND`, `FORBIDDEN`, `LIMIT_EXCEEDED`, `UPSTREAM_UNAVAILABLE` (retryable). The agent retries only retryable errors, with exponential backoff, and routes persistent failures to the human gate with a flagged partial result.

### Masking by role

| Field | Analyst | Investigator | Governance |
| --- | --- | --- | --- |
| Customer name | Masked | Visible | Masked |
| Account numbers | Last 4 digits | Full | Last 4 digits |
| Free-text memos | Passed as delimited data | Passed as delimited data | Passed as delimited data |

LLM prompts and traces always use the masked form, whatever the viewer's role.

## 6. RAG Pipeline

1. **Ingest.** Parse PDFs and pages to text with headings preserved. Record source URL, licence note, and fetch date in a sources file.
2. **Chunk.** Split by section, target a few hundred tokens with modest overlap, and keep the section title as metadata.
3. **Tag.** Add jurisdiction and typology tags (for example structuring, layering, mule accounts, trade-based laundering).
4. **Embed and store.** Embed with the configured model into `typology_chunks`.
5. **Retrieve.** Hybrid search: vector similarity plus Postgres full-text, merged, with jurisdiction filters (India first, then global).
6. **Rerank.** Rerank the top 20 to a final 5 with a cross-encoder or a Haiku-based reranker.
7. **Return.** Each result carries a chunk ID, source, and section title for citation.

**Query construction.** A Haiku step converts the structured signals (for example "many small deposits just under threshold across 3 days, then rapid outbound transfers") into 2 or 3 retrieval queries rather than passing raw transaction text.

**Empty-result rule.** If the best reranked score falls below a tuned threshold, the tool returns no results and the narrative states that no matching typology was found.

## 7. Agent Design

### Model assignment

| Step | Model | Reason |
| --- | --- | --- |
| Triage, query building, verification | Haiku 5.5 | High volume, structured tasks |
| Risk assessment, narrative drafting | Sonnet 5.5 | Reasoning and writing quality |
| Evaluation judge | A different model from the generator, such as Opus 5.5 or GPT-6 Sol | Reduces self-preference bias |

All model calls go through one interface that records model ID, prompt version, token counts, and cost.

### State

```python
class InvestigationState(TypedDict):
    alert_id: str
    role: str
    alert: dict | None
    kyc: dict | None
    transactions: list[dict]
    stats: dict | None
    network: dict | None
    prior_cases: list[dict]
    signals: list[dict]
    typology_hits: list[dict]
    triage: dict | None          # priority, needs_deep_review, reasons
    assessment: dict | None      # risk, recommendation, reasons with evidence IDs
    narrative: dict | None       # validated against NarrativeSchema
    verification: dict | None    # passed, failures
    retries: int
    limits: dict                 # tool_calls, tokens, deadline
    decision: dict | None        # analyst action and feedback
```

### Nodes

| Node | Does | Failure handling |
| --- | --- | --- |
| intake | `get_alert`, load rule hits | Not found ends the run with an error |
| triage | Haiku classifies priority and whether deep review is needed | Uncertain results go to deep review |
| gather\_evidence | KYC, transactions, prior cases, network via MCP | Retryable errors backoff; persistent failure flags partial evidence |
| compute\_signals | `get_behavior_stats` plus rule hits into a signal list | None expected; deterministic |
| match\_typology | Haiku builds queries; `search_typologies`; rerank | Empty result recorded as no match |
| assess\_risk | Sonnet outputs risk level, recommendation, and reasons with evidence IDs | Schema violation triggers one retry |
| draft\_narrative | Sonnet writes the structured narrative | Schema violation triggers one retry |
| verify\_grounding | Rule checks plus a Haiku support check (Section 9) | Failures return to drafting with specifics, at most 2 times |
| human\_review | Graph interrupts and waits for a decision | State persists until the decision arrives |
| finalize | `save_case_draft`, update status, write audit event | Retried; failure surfaces to the analyst |

### Routing

- intake leads to triage.
- triage routes low-risk alerts straight to human\_review with a short closure rationale, and others to gather\_evidence.
- gather\_evidence leads through compute\_signals, match\_typology, assess\_risk, and draft\_narrative to verify\_grounding.
- verify\_grounding routes failures back to draft\_narrative (bounded) and successes to human\_review.
- human\_review routes approve to finalize, redraft to draft\_narrative with the analyst's feedback in state, and reject to end.

### Limits

Hard caps per run: 25 tool calls, a token budget, and a 120-second deadline. When a cap is hit, the run stops and hands a flagged partial result to the human gate.

### Checkpointing and interrupts

A Postgres checkpointer persists state after every node. The review gate uses a LangGraph interrupt, so a run can wait for days and resume with the analyst's decision. The thread ID equals the alert ID, so reopening an alert resumes the same run.

## 8. Narrative Schema

```python
class Claim(BaseModel):
    text: str
    evidence_ids: list[str] = Field(min_length=1)

class NarrativeSchema(BaseModel):
    case_summary: str
    subject: dict                       # masked identifiers, type, risk rating
    period_reviewed: tuple[date, date]
    activity: list[Claim]               # chronological
    indicators: list[Claim]             # red flags, each with a typology chunk if applicable
    typology_assessment: dict           # matched typology or "no match", confidence, chunk_ids
    mitigating_factors: list[Claim]
    recommended_disposition: Literal["close", "monitor", "escalate", "file"]
    disposition_reason: str
    limitations: list[str]
    evidence_index: list[str]
```

The model returns this as structured output. Amounts, dates, and counts are inserted into text from tool results by the drafting prompt's templates and then checked, not computed by the model.

## 9. Grounding Verifier

1. **Schema check.** Valid against `NarrativeSchema`.
2. **Citation check.** Every claim has at least one evidence ID, and every ID exists in this run's evidence.
3. **Number and date check.** Extract numbers and dates from each claim and match them against the cited records, allowing rounding and currency formatting rules.
4. **Support check.** A Haiku call receives each claim with its cited records and answers supported, partly supported, or unsupported, with a short reason.
5. **Decision.** Any failure returns specific feedback to drafting. After 2 failed retries the draft goes to the analyst flagged as unverified, with the failures listed.

## 10. Service API

| Endpoint | Purpose |
| --- | --- |
| GET /alerts | Queue with filters |
| GET /alerts/{id} | Alert detail and evidence summary |
| POST /alerts/{id}/investigate | Start or resume a run |
| GET /runs/{id} | Status, current node, trace link |
| POST /runs/{id}/decision | Approve, edit, redraft, or reject, with comments |
| GET /cases/{id}/narrative | Current and previous versions with diffs |
| GET /audit | Audit events (governance role) |
| GET /health, GET /metrics | Liveness and operational metrics |

Authentication uses JWT with analyst, investigator, and governance roles. Every route checks the role, validates request bodies with Pydantic, and applies rate limits.

## 11. Configuration, Secrets, and Environments

- Environments: local (docker compose), staging (optional), demo (Azure).
- Configuration through environment variables loaded into a typed settings object: model IDs, thresholds, limits, embedding dimension, database URL.
- Secrets (API keys, database credentials, signing keys) come from the cloud secret store in Azure and from an untracked `.env` locally. Never commit them, and add secret scanning to CI.
- Prompts live in versioned files, and the prompt version is stored with every narrative.

## 12. Deployment and CI/CD

**Topology (demo).** Four Azure Container Apps (console, API, agent worker, MCP server) with scale to zero, a hosted Postgres with pgvector, and Langfuse hosted or run alongside. Images are stored in GitHub Container Registry.

**Pipeline stages (GitHub Actions)**

1. Lint and type check (ruff, mypy)
2. Unit tests
3. MCP contract tests (schemas, limits, masking, no ground-truth leakage)
4. Retrieval tests
5. Evaluation gate on the gold set, with thresholds from the Evaluation Plan
6. Secret and dependency scanning
7. Build and push images
8. Deploy to the demo environment on merge to main

## 13. Resilience and Error Handling

- Timeouts and retries with exponential backoff on model calls and MCP calls, retrying only retryable errors.
- Idempotent finalize step, so a retry cannot create duplicate drafts.
- Persistent checkpoints so restarts do not lose runs.
- Cold-start tolerance: scale-to-zero services may take a few seconds to wake, so the console shows run status instead of timing out.
- Provider fallback is optional: the model interface can route to a second provider, but the primary path is not silently swapped, because that would change evaluated behavior.

## 14. Performance and Cost Budget

Planning figures per alert, to be replaced with measured values:

| Step | Model | Approx. input / output tokens |
| --- | --- | --- |
| Triage and query building | Haiku 5.5 | 5K / 0.5K |
| Verification | Haiku 5.5 | 6K / 0.5K |
| Assessment and drafting | Sonnet 5.5 | 25K / 2.5K |

At list prices checked in November 2026 this is roughly $0.08 to $0.09 per alert before retries. Targets: median end-to-end under 30 seconds, p95 under 90 seconds. Keep evidence packs well under Haiku's 100K-token price step, use prompt caching for the fixed system prompt and typology context, and use batch mode for evaluation runs.

## 15. Engineering Standards

- Python 3.11 or later, fully typed, Pydantic models at every boundary.
- Tests at every layer: unit, contract, integration, and evaluation.
- Conventional commits, short-lived branches, pull requests with CI required.
- Architecture decisions recorded as short ADRs in `docs/decisions/`.
- Logging is structured JSON with trace IDs and never contains unmasked PII.
- Reproducible environments through a lock file and pinned container base images.

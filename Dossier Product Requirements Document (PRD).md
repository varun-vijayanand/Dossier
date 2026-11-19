# Dossier: Product Requirements Document (PRD)

*Version 1.0 draft · Status: for build · Companion docs: Technical Design, Evaluation and Test Plan, Security and System Card, Delivery Plan*

## 1. Summary

Dossier is an AI investigation assistant for anti-money-laundering (AML) transaction-monitoring alerts. For each alert it gathers evidence from bank data through an MCP server, matches the activity to known laundering typologies using retrieval-augmented generation (RAG), and drafts a cited, India-STR-style investigation narrative. A human analyst reviews every outcome. Nothing is closed, escalated, or filed without approval.

Dossier is a portfolio project built on synthetic and public data. It demonstrates production-minded GenAI engineering in a regulated domain: agent orchestration, tool protocols, grounded generation, evaluation, observability, and security.

## 2. Background and Problem

Transaction-monitoring systems raise far more alerts than investigators can work, and most alerts are false positives. Every investigation repeats the same steps: read the alert, pull the customer profile, scan transactions, check counterparties, compare against typologies, and write a narrative. This is slow, inconsistent between analysts, and difficult to audit.

First-generation LLM tools help with writing but create new risks: invented facts, unexplained conclusions, and no record of how a conclusion was reached. In a regulated setting, a fluent but ungrounded narrative is worse than no narrative.

**Opportunity.** Use an agent for the mechanical evidence gathering and first-draft writing, and make every statement traceable to a source record, so the analyst spends time on judgment instead of assembly.

## 3. Objectives and Success Metrics

### Product objectives

| ID | Objective |
| --- | --- |
| O1 | Give analysts a complete, cited evidence pack and draft narrative for each alert |
| O2 | Keep humans in control: no disposition or filing without explicit approval |
| O3 | Make every claim verifiable and every action auditable |
| O4 | Quantify quality, cost, and latency so claims about the system are evidence-based |

### Success metrics and initial targets

Targets are starting points and will be adjusted after the first baseline run. Whatever the final numbers are, they will be reported honestly with the baselines.

| Metric | Target | Measured by |
| --- | --- | --- |
| Recall on true-suspicious alerts | At least 0.90 | Gold set (Evaluation Plan) |
| False-positive handling | Report share of false positives correctly proposed for closure | Gold set |
| Faithfulness (claims supported by cited evidence) | At least 0.90 | Grounding check plus LLM judge |
| Citation precision | At least 0.95 | Automated evidence-ID check |
| Unsupported numbers or dates in accepted drafts | Zero | Rule-based matching against tool outputs |
| Median processing time per alert | Under 30 seconds | Langfuse traces |
| Cost per alert | Stated and tracked | Langfuse cost data |
| Analyst effort proxy | Time for you to review 10 alerts manually versus with Dossier | Timed self-study, reported with caveats |

## 4. Users and Personas

**Asha, Level 1 analyst.** Works a queue of 40 or more alerts a day. Needs to decide quickly whether an alert needs deeper review. Wants the facts in one place, with a clear reason for any recommendation.

**Rohan, Level 2 investigator / MLRO delegate.** Handles escalated cases and signs off on filings. Needs a defensible narrative, mitigating factors alongside red flags, and the ability to edit or reject.

**Meera, AI governance reviewer.** Audits how the system behaves. Needs traces, evaluation results, and an audit log that reconstructs any decision.

## 5. Scope

### In scope (MVP)

- Synthetic alert generation from public and synthetic data
- Read-only MCP server for alerts, KYC, transactions, behavior statistics, counterparty networks, prior cases, and typology search
- RAG over typology and regulatory documents with citations
- LangGraph investigation workflow with a human review gate
- Structured narrative in an India STR-style template (FinCEN SAR as secondary template)
- Analyst console (Streamlit) backed by a FastAPI service
- Evaluation harness, baselines, bias and prompt-injection tests
- Langfuse observability, audit log, PII masking, role-based access
- Containerized deployment on Azure Container Apps with CI/CD

### Out of scope

- Real customer data and any real regulatory submission
- Training a transaction-monitoring detection model (covered by Project 2)
- Document forensics and KYC document checks (covered by Project 3)
- Multi-tenant production hardening, SSO, and formal regulatory certification
- Fully autonomous alert closure

### Stretch

- Alert score from the Project 2 graph model as an extra tool
- Counterparty network visualization in the console
- Second dataset (Project 0 data) behind the same schema
- Analyst feedback loop that adds corrections to the gold set
- React front end

## 6. Primary User Journey

1. Asha opens the alert queue, sorted by priority, with Dossier's preliminary recommendation shown for each alert.
2. She opens an alert. Dossier has already run, or runs on demand, and shows a summary, the key transactions on a timeline, the customer profile, behavior statistics, matched typologies, and a draft narrative.
3. Every sentence in the narrative has clickable citations that open the underlying transaction, KYC item, or typology passage.
4. Asha chooses: approve the recommendation, edit the draft, request a redraft with feedback, or reject.
5. Low-risk alerts show a short proposed-closure rationale. She still approves or overrides it.
6. Escalated cases go to Rohan, who edits the narrative and approves the draft as ready for filing. The system never submits it anywhere.
7. Meera can open the audit view for any case and see every tool call, model call, and human action.

## 7. Functional Requirements

Priority uses MoSCoW: **M**ust, **S**hould, **C**ould.

### 7.1 Alert intake and queue

| ID | Requirement | Priority | Acceptance criteria |
| --- | --- | --- | --- |
| FR-1.1 | Generate alerts from transaction data using at least 6 explainable rules, with deliberately noisy rules to create false positives | M | Rule hits stored per alert; gold set contains both true and false positives |
| FR-1.2 | Display an alert queue with priority, status, rule hits, and Dossier's recommendation | M | Queue filters by status and priority; loads within 2 seconds for 500 alerts |
| FR-1.3 | Alert statuses: new, in review, escalated, closed, draft ready | M | Status transitions are logged |

### 7.2 Investigation

| ID | Requirement | Priority | Acceptance criteria |
| --- | --- | --- | --- |
| FR-2.1 | Agent retrieves alert, KYC, transactions, prior cases, behavior statistics, and counterparty network only through MCP tools | M | No direct database access from the agent; verified by contract test |
| FR-2.2 | Agent computes statistics (velocity, totals, baseline deviation, balance retention) in code, not in the model | M | Numbers in narrative match tool output exactly |
| FR-2.3 | Agent retrieves typology guidance via RAG and cites passage IDs | M | Each typology claim has a valid passage ID or the narrative states no match was found |
| FR-2.4 | Agent triages alerts and routes low-risk alerts to a short closure rationale | M | Triage decision and reasons recorded in state and trace |
| FR-2.5 | Agent stays within limits on tool calls, tokens, and wall-clock time per run | M | Limit breach ends the run gracefully with a flagged partial result |
| FR-2.6 | Counterparty network analysis up to 2 hops | S | Fan-in, fan-out, and cycle patterns detected on gold cases |
| FR-2.7 | Optional alert score from Project 2 model | C | Score and top features shown as supplementary evidence |

### 7.3 Narrative generation

| ID | Requirement | Priority | Acceptance criteria |
| --- | --- | --- | --- |
| FR-3.1 | Produce a structured narrative validated against a schema: summary, subject, period, activity, indicators, typology assessment, mitigating factors, disposition, limitations, evidence index | M | Schema validation passes or the run fails visibly |
| FR-3.2 | Every factual sentence cites at least one evidence ID | M | Verifier rejects uncited sentences |
| FR-3.3 | Grounding verifier checks that cited records support each claim and returns failures to drafting, with at most 2 retries | M | Unsupported claim rate measured in evals |
| FR-3.4 | Include mitigating factors and limitations, not only red flags | M | Rubric item scored in evals |
| FR-3.5 | Render the narrative into an India STR-style template, with a FinCEN SAR template as secondary | M | Both templates render from the same JSON |
| FR-3.6 | Mark every output as DRAFT until approved | M | Template watermark and status field |

### 7.4 Human review

| ID | Requirement | Priority | Acceptance criteria |
| --- | --- | --- | --- |
| FR-4.1 | Graph pauses at a review gate with a persistent checkpoint and resumes on the analyst's decision | M | A run paused for 24 hours resumes correctly |
| FR-4.2 | Analyst can approve, edit inline, request redraft with feedback, or reject | M | Each action is logged with user and timestamp |
| FR-4.3 | No disposition is applied and no narrative is marked ready without approval | M | Verified by integration test |
| FR-4.4 | Edited narratives are saved as new versions with a diff against the model draft | S | Version history visible in console |

### 7.5 Audit and governance

| ID | Requirement | Priority | Acceptance criteria |
| --- | --- | --- | --- |
| FR-5.1 | Append-only audit log of user actions, tool calls, and model calls with input and output hashes and trace IDs | M | Any case reconstructable from the log |
| FR-5.2 | Governance view showing audit events and latest evaluation summary | S | Filterable by case, user, and date |
| FR-5.3 | Every narrative stores model ID, prompt version, and tool versions | M | Fields present on every narrative record |

### 7.6 Evaluation and operations

| ID | Requirement | Priority | Acceptance criteria |
| --- | --- | --- | --- |
| FR-6.1 | Evaluation harness runs the gold set and reports all metrics | M | One command produces a report |
| FR-6.2 | CI fails when key metrics fall below thresholds | M | Gate configured and demonstrated |
| FR-6.3 | Baselines: rules only, single-prompt LLM, and the full agent | M | Side-by-side table in the eval report |
| FR-6.4 | Bias test using counterfactual swaps of demographic attributes | M | No disposition change on matched pairs, or differences are reported |
| FR-6.5 | Prompt-injection suite using hostile text in memos and documents | M | Injected instructions are not followed |
| FR-6.6 | Langfuse tracing with cost and latency per node | M | Trace exists for every run |

## 8. Non-Functional Requirements

| Area | Requirement |
| --- | --- |
| Performance | Median end-to-end investigation under 30 seconds; p95 under 90 seconds; console pages load in under 2 seconds |
| Reliability | Runs survive service restarts through persistent checkpoints; tool failures are retried with backoff and surfaced when they persist |
| Security | Role-based access, PII masking by default, secrets outside the repo, no ground-truth labels exposed to the agent |
| Privacy | Synthetic and public data only; masked identifiers in prompts and traces |
| Cost | Cost per alert is tracked; the whole demo should stay within a small monthly budget by using scale-to-zero hosting and a cheaper model for triage |
| Observability | Traces, metrics, and logs for every run; alerts when cost or grounding failures exceed thresholds |
| Maintainability | Typed Python, tests at every layer, versioned prompts, documented decisions |
| Portability | Model access sits behind one interface so the provider can be swapped |
| Accessibility and usability | Console works on a laptop screen, with keyboard-friendly review actions |

## 9. Data Requirements

- **Transactions and labels:** public IBM synthetic AML dataset, used as the MVP source. Labels are kept out of every tool output.
- **KYC and customers:** generated synthetically with rules that make some customers consistent with their activity and others not.
- **Typology corpus:** public FATF, FIU-IND, FinCEN, and RBI guidance plus your own typology cards. Keep a sources list with URLs and licences.
- **Gold set:** 30 to 50 hand-reviewed alerts with expected disposition, expected typology, and key evidence.
- **Second dataset (stretch):** Project 0 data loaded behind the same schema.
- **Retention:** traces and drafts are demo data; document the retention approach a real deployment would need.

## 10. Assumptions and Dependencies

- Access to a Claude API key and budget for evaluation runs.
- The IBM dataset remains publicly available with its current licence terms.
- Free or low-cost tiers are sufficient for hosting the database, tracing, and containers.
- Synthetic data is good enough to demonstrate the workflow, with limits stated clearly.
- A second model family (GPT-6 Sol or Luna) is accessible for the comparison arm.

## 11. Risks and Open Questions

| Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- |
| Model invents facts or numbers | Medium | High | Evidence-ID rule, verifier, numeric matching, eval gate |
| Synthetic data looks too clean | High | Medium | Noisy rules, hand-built edge cases, honest limitations section |
| Prompt injection through memo or document text | Medium | High | Untrusted-data handling, delimiters, adversarial tests |
| Scope creep | High | Medium | MVP and stretch split; cut stretch first |
| Weak or noisy dataset labels | Medium | Medium | Manual review of the gold set and a label-quality note |
| Cost overruns during evaluation | Medium | Low | Haiku for bulk runs, batch mode, caching, cost alerts |
| Regulatory format details are misunderstood | Medium | Medium | Base the template on public FIU-IND guidance and label it as illustrative, not a filing format |

**Open questions**

1. Which public STR field layout will serve as the template reference, and how closely should the demo mirror it?
2. Which free-tier Postgres host with pgvector will be used for the deployed demo?
3. How many gold-set alerts can you review by hand before the eval results become the bottleneck?

## 12. Release Criteria (MVP)

- All Must requirements pass their acceptance criteria.
- Evaluation report is published with baselines and thresholds met or the gaps explained.
- Prompt-injection and bias suites pass in CI.
- Audit log reconstructs a sample case end to end.
- Deployed demo or recorded walkthrough is available.
- README, architecture diagram, and System Card are complete.

## 13. Glossary

- **AML**: anti-money laundering.
- **Alert**: a flag raised by a monitoring rule for review.
- **STR / SAR**: suspicious transaction report (India) and suspicious activity report (US).
- **FIU-IND**: India's Financial Intelligence Unit.
- **KYC**: know your customer.
- **Typology**: a recognized pattern of money laundering.
- **MCP**: Model Context Protocol, a standard way to expose tools and data to language models.
- **RAG**: retrieval-augmented generation.
- **Grounding**: tying each generated claim to a source record.
- **MLRO**: money laundering reporting officer.

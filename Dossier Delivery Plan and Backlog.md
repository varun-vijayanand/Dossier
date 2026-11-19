# Dossier: Delivery Plan and Backlog

*Version 1.0 draft · Companion to the PRD, Technical Design, Evaluation Plan, and Security and System Card*

## 1. Purpose

This plan turns the PRD into work you can schedule: epics, stories with acceptance criteria, milestones, working agreements, and the portfolio deliverables that make the project usable in interviews.

## 2. Estimates and Pace (Read First)

Estimates below are in **focused days**, meaning a full day of uninterrupted work, assuming you use an AI coding assistant for boilerplate and tests. They total about **33 focused days**.

| Your pace | Rough calendar time |
| --- | --- |
| Full time | 7 to 8 weeks |
| About 20 hours a week | 12 to 14 weeks |
| About 10 hours a week | 6 to 7 months |

The earlier four-week outline in the Project Definition document is the aggressive case, with a thinner scope and full-time effort. Treat this plan as the realistic baseline, and cut scope using the order in Section 6 instead of cutting quality controls.

## 3. Epics, Stories, and Acceptance Criteria

### E1. Data and alerts (3.5 days)

| Story | Acceptance criteria | Est. |
| --- | --- | --- |
| S1.1 Load IBM AML data into Postgres with the schema from the Technical Design | Tables created by migration; row counts verified; labels stored in a separate column | 1 |
| S1.2 Generate synthetic KYC for all customers | Reproducible with a seed; includes profiles consistent and inconsistent with activity | 0.5 |
| S1.3 Rule engine with 6 or more rules | Each rule has unit tests; alerts and rule hits written; some noisy rules produce false positives | 1 |
| S1.4 Draft the gold set of 40 alerts with expected outcomes | Dev and test split defined; labeling notes recorded; 10 re-reviewed after a gap | 1 |

### E2. MCP server (4.5 days)

| Story | Acceptance criteria | Est. |
| --- | --- | --- |
| S2.1 Scaffold server, auth, response envelope, error contract | Runs over stdio and HTTP; invalid token rejected | 0.5 |
| S2.2 Alert, KYC, transaction, and prior-case tools | Limits and pagination enforced; evidence IDs on every record | 1 |
| S2.3 Behavior statistics and counterparty network tools | Statistics computed in SQL; 2-hop network capped at 100 nodes | 1 |
| S2.4 Masking and role-based access | Contract tests prove role differences; unmasked identifiers never appear in analyst responses | 1 |
| S2.5 Audit logging and contract test suite | Every call logged; test confirms no label fields in any output | 0.5 |
| S2.6 Connect from an MCP-compatible desktop client | Demonstrate an alert investigation by hand through the tools | 0.5 |

### E3. RAG (3.5 days)

| Story | Acceptance criteria | Est. |
| --- | --- | --- |
| S3.1 Collect corpus and sources file | At least 15 documents or cards with URLs and licence notes | 0.5 |
| S3.2 Ingest and chunk with metadata | Section-aware chunks with jurisdiction and typology tags | 0.5 |
| S3.3 Embeddings and hybrid search | Search returns chunk IDs and sources; India filter works | 1 |
| S3.4 Reranking and empty-result rule | No-match questions return nothing | 0.5 |
| S3.5 Retrieval question set and metrics | 40 questions; Hit@5 and MRR reported | 0.5 |
| S3.6 Expose search as an MCP tool | Tool passes contract tests | 0.5 |

### E4. Agent (6.5 days)

| Story | Acceptance criteria | Est. |
| --- | --- | --- |
| S4.1 Graph skeleton, state, Postgres checkpointer | Run survives a restart | 0.5 |
| S4.2 Triage node | Low-risk alerts route to a closure rationale | 0.5 |
| S4.3 Evidence and signals nodes | Evidence collected only via MCP; limits enforced | 1 |
| S4.4 Typology matching node | Queries built from signals; citations returned | 0.5 |
| S4.5 Assessment and drafting with the narrative schema | Schema-valid output with evidence IDs | 1.5 |
| S4.6 Grounding verifier | Catches seeded unsupported claims; bounded retries | 1.5 |
| S4.7 Human review interrupt and resume | Pause, restart services, resume with a decision | 0.5 |
| S4.8 Error handling and run limits | Forced limit yields a flagged partial result | 0.5 |

### E5. Evaluation and observability (5 days)

| Story | Acceptance criteria | Est. |
| --- | --- | --- |
| S5.1 Langfuse tracing with cost and latency | Trace for every run with spans per node | 0.5 |
| S5.2 Harness and baselines B0 and B1 | One command produces a metrics table | 1 |
| S5.3 Judge, rubric, and calibration | Agreement with your own scores reported | 1 |
| S5.4 Bias counterfactual suite | Flip rate reported with trace review notes | 0.75 |
| S5.5 Prompt-injection and robustness suites | All injection cases pass; failures become regressions | 0.75 |
| S5.6 CI gates and nightly run | Seeded regression fails the build | 1 |

### E6. API and console (4 days)

| Story | Acceptance criteria | Est. |
| --- | --- | --- |
| S6.1 FastAPI endpoints with Pydantic models | OpenAPI docs; role checks on every route | 1 |
| S6.2 JWT auth and roles | Role matrix tested | 0.5 |
| S6.3 Streamlit alert queue and workspace | Evidence timeline, profile, typology matches, narrative with clickable citations | 1.5 |
| S6.4 Review panel and narrative versions | Approve, edit, redraft, reject; diff against model draft | 0.5 |
| S6.5 Governance view | Audit events and latest evaluation summary | 0.5 |

### E7. Deployment and CI/CD (3 days)

| Story | Acceptance criteria | Est. |
| --- | --- | --- |
| S7.1 Dockerfiles and compose for the full local stack | One command starts everything | 1 |
| S7.2 GitHub Actions pipeline | Lint, type check, tests, eval gate, build, scan | 1 |
| S7.3 Azure Container Apps deployment with secrets and budget alerts | Demo reachable; scale to zero confirmed; spend alert set | 1 |

### E8. Documentation and portfolio (3 days)

| Story | Acceptance criteria | Est. |
| --- | --- | --- |
| S8.1 README with architecture diagram and quick start | A new reader can run the stack from the README | 1 |
| S8.2 Evaluation report with baselines | Follows the report template in the Evaluation Plan | 0.5 |
| S8.3 Complete the System Card with measured results | All placeholders filled | 0.5 |
| S8.4 Demo video (3 to 5 minutes) and write-up | Script in Section 8 | 1 |

## 4. Milestones

| Milestone | Cumulative focused days | Exit criteria |
| --- | --- | --- |
| M1. Data and tools ready | About 8 | E1 and E2 complete; you can investigate an alert by hand through the MCP tools in a desktop client |
| M2. Agent produces grounded drafts | About 18 | E3 and E4 complete; the agent drafts and verifies narratives on the dev split |
| M3. Quality proven | About 23 | E5 complete; baselines and agent compared on the test split; safety suites pass |
| M4. Product usable | About 27 | E6 complete; analyst can run the review loop in the console |
| M5. Shipped | About 33 | E7 and E8 complete; demo deployed or recorded; documents final |

At each milestone, update the PRD's risk table, the evaluation numbers, and a short changelog entry.

## 5. Working Agreements

### Definition of Ready (a story can start when)

- It has acceptance criteria and a size estimate.
- Its dependencies are done or stubbed.
- You know how it will be tested.

### Definition of Done (a story is done when)

- Acceptance criteria pass, with tests that fail without the change.
- CI is green, including lint and type checks.
- Prompts, models, and corpus versions are recorded where relevant.
- Documentation is updated, including any new decision recorded as a short ADR.
- No unmasked identifiers or secrets appear in code, logs, or traces.

### Repository conventions

- Trunk-based development with short branches and pull requests, even when working alone, so CI and history stay clean.
- Conventional commit messages.
- One issue per story, labeled by epic and milestone, in a simple project board with columns for backlog, in progress, in review, and done.
- A weekly 20-minute review: update estimates, burn-down, risks, and the cut list.

## 6. Scope Control

**Cut order if time runs short** (cut from the top first):

1. React front end and any UI polish beyond the review loop
2. Optional AWS deployment run
3. Second dataset (Project 0 data)
4. Counterparty network visualization
5. Project 2 alert-score tool and the fine-tuned model comparison arm (A6)
6. Second-model-family comparison arm (A5)
7. Staging environment

**Never cut:** the grounding verifier, the human review gate, the evaluation harness with baselines, the injection suite, masking and role checks, and the audit log. These are what make the project credible.

## 7. Delivery Risks

| Risk | Early signal | Response |
| --- | --- | --- |
| Scope creep | Stories added without removing others | Apply the cut order; every addition needs a swap |
| LLM behavior is inconsistent | Consistency metric below target on dev split | Tighten prompts and schemas, lower temperature, add examples, add verifier checks |
| Evaluation takes too long | Gold set labeling slips | Freeze at 30 alerts with a stated limitation rather than skipping labeling |
| Costs creep up | Cost per alert above plan | Use Haiku and caching, shrink evidence packs, run evaluations in batch mode |
| Hosting surprises | Unexpected cloud charges | Budget alerts on day one, scale to zero, tear down experiments |
| Perfectionism | Polishing UI before evals exist | Hold the milestone order: quality proof before polish |

## 8. Portfolio Deliverables

### README outline

1. One-paragraph pitch and a short demo GIF
2. The problem and the approach in five sentences
3. Architecture diagram and a one-paragraph flow
4. Key results table (from the evaluation report, with sample sizes)
5. Quick start (one command with compose) and configuration
6. MCP tool reference
7. Evaluation, safety, and observability summary
8. Limitations (synthetic data, small gold set, template is illustrative)
9. Roadmap and links to the PRD, Technical Design, Evaluation Plan, and System Card

### Demo script (about 4 minutes)

| Time | Show |
| --- | --- |
| 0:00 | The problem: an alert queue and why investigations are slow |
| 0:30 | Open a suspicious alert: evidence timeline, profile, and matched typology with citations |
| 1:30 | Click citations through to source records; point out mitigating factors and limitations |
| 2:00 | Request a redraft with feedback, then approve; show the review gate and audit trail |
| 2:45 | Open Langfuse: trace, cost, and latency for the run |
| 3:15 | Show the evaluation table with baselines and the injection test catching a hostile memo |
| 3:45 | The same MCP tools used from a desktop client, then close with limits and next steps |

### Resume bullets (fill brackets only with measured results)

- Built **Dossier**, an agentic AML alert-investigation assistant using LangGraph, an MCP tool server, and RAG over typology guidance, producing cited India STR-style narratives with mandatory human approval.
- Designed a claim-level grounding verifier and evaluation harness (faithfulness \[x\], citation precision \[y\], recall \[z\] on \[n\] held-out alerts) with rules-only and single-prompt baselines.
- Implemented prompt-injection, bias counterfactual, and robustness suites in CI, plus PII masking, role-based access, and an append-only audit log.
- Instrumented cost and latency with Langfuse (\[a\] per alert, \[b\] median seconds), and deployed containers to Azure Container Apps with GitHub Actions CI/CD.

### Two-minute interview pitch (outline)

1. **Problem:** alert volume and slow, inconsistent investigations.
2. **Design choice:** an agent with a verifier and a human gate, because ungrounded fluency is dangerous in this domain.
3. **How you proved it:** baselines, a frozen test split, and honest confidence intervals.
4. **What went wrong and how you fixed it:** pick one real failure from your traces.
5. **What you would do next:** real-data validation, analyst feedback loop, and Project 2 model integration.

## 9. Decision Log Template

Keep a short entry for each significant decision in `docs/decisions/`:

- Date and title
- Context and options considered
- Decision and why
- Consequences and how it will be revisited

Seed it with the ten decisions in the Technical Design (D1 to D10).

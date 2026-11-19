# Dossier: Security, Compliance, and System Card

*Version 1.0 draft · Companion to the PRD, Technical Design, and Evaluation Plan*

## 1. Purpose and Scope

Dossier handles banking-style data and produces text that influences investigative decisions, so security and governance are product features, not extras. This document covers the threat model, controls, human-oversight rules, compliance alignment, and the System Card that describes the system's intended use, limits, and measured behavior.

The project uses synthetic and public data only. The controls are designed as if the data were real so the design is credible and the habits carry over.

## 2. Data Classification and Handling

| Class | Examples | Handling |
| --- | --- | --- |
| Restricted | Unmasked customer names, full account numbers, ground-truth labels | Role-limited, never sent to the model or written to traces; labels never leave the evaluation harness |
| Internal | Transactions, rule hits, behavior statistics, draft narratives | Accessible by role; logged on access; masked identifiers in prompts and traces |
| Public | Typology documents, schemas, templates | Freely accessible within the system |

Rules: collect and expose only what a step needs (minimization), mask by default, and keep identifiers out of logs.

## 3. Threat Model

| Threat | Example | Impact | Controls |
| --- | --- | --- | --- |
| Prompt injection through data | A memo, name field, or document passage that tells the agent to close an alert or call a tool | Wrong disposition, unauthorized action, leaked context | Treat all free text as data; clear delimiters; instruction-like text flagged; the agent cannot change tool permissions; write tool limited to drafts; adversarial test suite in CI |
| Hallucinated facts in narratives | Invented amounts, dates, or typology claims | Misleading filing draft | Evidence-ID rule, grounding verifier, numeric matching, human review |
| Over-trust by analysts (automation bias) | Analyst approves without reading | Poor decisions | Show reasoning, mitigating factors, and limitations; require explicit approval; display verification status and confidence |
| Sensitive data exposure | Unmasked PII in prompts, traces, or logs | Privacy breach | Masking in the MCP layer; log scrubbing; trace redaction; role-based reveal |
| Evaluation leakage | Agent sees ground-truth labels | Inflated results | Labels excluded from every tool; contract test; separate evaluation store |
| Unauthorized access | Stolen token or misconfigured route | Data access, tampering | JWT with short expiry, role checks on every route and tool, rate limits |
| Tampering with records | Altering audit entries or approved narratives | Loss of accountability | Append-only audit log, hashed inputs and outputs, versioned narratives |
| Supply-chain compromise | Malicious package or container image | Code execution | Pinned versions, lock files, dependency scanning, minimal base images, secret scanning |
| Secret leakage | API keys committed or logged | Account abuse, cost | Secret store, `.env` untracked, scanning in CI, key rotation |
| Cost abuse or runaway loops | Repeated runs, large evidence, retry storms | Unexpected bills | Per-run limits, rate limits, cost alerts, bounded retries |
| Tipping off | Subject learns a report is being considered | Compromised investigation | Console warnings, narrative template notice, no customer-facing outputs |
| Biased outcomes | Different treatment based on name or nationality | Unfair decisions | Counterfactual bias suite, review of flips, documentation of legitimate risk factors |

## 4. Control Specifications

### 4.1 Roles and permissions

| Action | Analyst | Investigator | Governance | Admin |
| --- | --- | --- | --- | --- |
| View alert queue and masked evidence | Yes | Yes | Yes | Yes |
| Run an investigation | Yes | Yes | No | Yes |
| Approve, edit, or reject a recommendation | Yes (own queue) | Yes | No | No |
| Mark a narrative ready for filing | No | Yes | No | No |
| View unmasked identifiers | No | Yes | No | No |
| View audit log and evaluation results | No | No | Yes | Yes |
| Change configuration or thresholds | No | No | No | Yes |

Separation of duties: governance reviewers can read but never change cases, and in a real deployment the person who marks a narrative ready for filing should differ from its last editor.

### 4.2 Authentication and sessions

- JWT access tokens with short expiry, signed with a key from the secret store.
- The agent and MCP server act with a service identity plus the calling user's role and trace ID, so tool access follows the human's permissions.
- Token validation at the API and again at the MCP server.

### 4.3 PII masking

- Masking happens in the MCP layer before any data reaches the model.
- Names are replaced with stable pseudonyms within a case, and account numbers are shortened to the last 4 digits for non-investigator roles.
- Traces and logs store masked values only.
- A unit test scans prompts and traces from the gold set for patterns that look like unmasked identifiers.

### 4.4 Audit logging

- Log every user action, MCP tool call, and model call with actor, role, resource, trace ID, and hashes of inputs and outputs.
- The application's database role can insert and read audit records but not update or delete them.
- A sample case must be fully reconstructable from the log (an acceptance test).

### 4.5 Prompt-injection defense (layered)

1. **Separation.** Untrusted text is wrapped in explicit data delimiters, and system prompts state that content inside them is data and must never be followed as instructions.
2. **Least privilege.** The agent can only call read tools plus a draft-saving tool. It has no ability to submit, delete, or change permissions.
3. **Tool-argument validation.** The MCP server validates every argument and rejects out-of-range requests, so injected text cannot widen a query.
4. **Output checks.** The verifier flags narrative text that repeats instruction-like phrases from data.
5. **Human gate.** No disposition applies without approval.
6. **Testing.** An adversarial suite runs in CI, and each new finding becomes a regression case.

### 4.6 Secrets and configuration

- Secrets live in the cloud secret store in deployment and an untracked `.env` locally.
- CI runs secret scanning, and a leaked key is rotated immediately.
- Separate keys for development, evaluation, and demo, each with a spending cap.

### 4.7 Network and runtime

- Only the console and API are publicly reachable. The MCP server and database accept traffic only from the application services where the hosting platform allows it.
- Containers run as non-root with minimal base images.
- TLS everywhere, and no credentials in URLs.

### 4.8 Retention and deletion (documented design)

For the demo, data is synthetic. For a real deployment the design would set retention periods for traces, drafts, and audit logs in line with record-keeping obligations, with deletion procedures for data that is no longer required. Document the intended periods in the README as a design note.

## 5. Human Oversight Rules

- Nothing is closed, escalated, filed, or marked ready without an explicit human action recorded in the audit log.
- The system never submits a report to any authority. Output is always a draft labeled DRAFT.
- Narratives must show mitigating factors and limitations alongside red flags.
- Verification status is shown plainly. A draft that failed grounding checks is labeled unverified, with the failures listed.
- Analysts can always override, edit, or reject, and their edits are versioned with a diff against the model draft.
- The console reminds users not to disclose a suspicion report to the subject.

## 6. Compliance Alignment

Dossier is a portfolio system and not a regulated product, so the aim is alignment with widely recognized expectations rather than certification. Verify the current versions of any framework before citing it in public materials.

| Area | Expectation | How Dossier addresses it |
| --- | --- | --- |
| AML process | Documented, consistent investigation steps with records that support reporting decisions | Standard graph workflow, versioned narratives, audit trail |
| Human accountability | A responsible person decides on reporting | Approval gates and role separation |
| Explainability | Reasons for a recommendation can be traced | Evidence-ID citations, reasons stored with each recommendation |
| Model risk management | Documented purpose, validation, monitoring, change control | System Card, evaluation plan, versioned prompts and models |
| AI risk practice | Govern, map, measure, and manage AI risks | Threat model, evaluation suites, monitoring |
| LLM application security | Protection against known LLM risks such as injection and sensitive data disclosure | Layered defenses and adversarial testing |
| Privacy | Data minimization and purpose limitation | Masking, role-based reveal, synthetic data, retention design note |

Useful references to check and cite accurately: India's PMLA and the PML Rules, RBI's KYC and AML directions, FIU-IND guidance, India's Digital Personal Data Protection Act 2023, the OWASP Top 10 for LLM Applications, the NIST AI Risk Management Framework, and supervisory model-risk guidance such as the US SR 11-7.

## 7. Security Release Checklist

- [ ] Contract tests confirm role-based masking and no ground-truth fields in any tool output
- [ ] Injection suite passes in CI
- [ ] Secret scanning and dependency scanning pass with no critical findings
- [ ] Audit log append-only behavior verified by a test that attempts an update
- [ ] Role matrix tested for each route and tool
- [ ] Prompts and traces from the gold set contain no unmasked identifiers
- [ ] Spending caps and cost alerts configured
- [ ] System Card completed with measured results

## 8. Incident Response (Mini-Runbook)

| Event | First response | Follow-up |
| --- | --- | --- |
| Injection suspected in production data | Disable the affected run, preserve the trace, quarantine the source record | Add a regression case, tighten delimiters or validation |
| Unmasked data found in logs or traces | Stop log shipping, purge the affected entries, rotate related keys | Fix the masking gap and add a scanning test |
| Cost spike | Pause the agent worker, review traces for loops or oversized evidence | Lower limits, add alerts, review retry logic |
| Hallucination reaches an approved narrative | Mark the narrative as corrected, link the review | Add the failure to the evaluation set |
| Leaked secret | Revoke and rotate immediately | Review access logs and add scanning coverage |

# System Card: Dossier

## A. Overview

- **Name:** Dossier
- **Version:** v1.0 (update with each release)
- **Type:** Agentic AI assistant for AML alert investigation, built on a large language model, an MCP tool server, and retrieval over public typology guidance
- **Status:** Portfolio and demonstration system on synthetic and public data

## B. Intended Use

- **Primary use:** help an AML analyst investigate a transaction-monitoring alert by gathering evidence, matching typologies, and drafting a cited narrative for human review.
- **Intended users:** analysts, investigators, and governance reviewers acting within a defined review process.
- **Out of scope:** automated closure or filing, use on real customer data without a separate risk review, legal advice, and any decision about customers made without human review.

## C. System Description

- **Models:** Claude Haiku 5.5 for triage, query building, and verification; Claude Sonnet 5.5 for assessment and drafting. A second model family is used for comparison, and a different model serves as evaluation judge.
- **Inputs:** an alert ID and the evidence retrieved through MCP tools; public typology passages from the retrieval index.
- **Outputs:** a structured, cited narrative in an India STR-style template (FinCEN SAR as secondary), a recommended disposition, and an evidence index.
- **Controls:** read-only tools, grounding verification, human approval gates, role-based masking, audit logging, and cost and run limits.

## D. Performance

Fill this section from the latest evaluation report and update it with every release.

| Metric | Rules only | Single prompt | Dossier (reference config) |
| --- | --- | --- | --- |
| Recall on suspicious alerts | *tbd* | *tbd* | *tbd* |
| False-positive closure rate | *tbd* | *tbd* | *tbd* |
| Faithfulness | n/a | *tbd* | *tbd* |
| Citation precision | n/a | *tbd* | *tbd* |
| Unsupported numbers | n/a | *tbd* | *tbd* |
| Median latency and cost per alert | n/a | *tbd* | *tbd* |

State the test split size, confidence intervals, model versions, and run date beside the table.

## E. Limitations and Known Failure Modes

- Results come from synthetic data and may not predict performance on real transaction patterns.
- The gold set is small and labeled by one person.
- The system can miss unusual typologies not covered by the retrieval corpus, and can over-flag legitimate activity that resembles known patterns.
- Narrative quality depends on the completeness of the evidence returned by the tools. Missing KYC or sparse history lowers reliability, and the narrative must say so.
- Judge-based metrics carry the biases of the judge model.
- Behavior can change when model providers update model versions.
- The India STR template is illustrative and is not an official filing format.

## F. Risks and Mitigations

See the threat model in Section 3. The main residual risks are automation bias, subtle hallucination that passes verification, and bias that the test suite does not capture. Mitigations are human review, claim-level citations, and continued evaluation.

## G. Human Oversight

Every disposition and narrative requires approval from a human reviewer, recorded with user, role, and time. The system cannot submit anything externally.

## H. Monitoring and Change Management

- Langfuse traces, cost, and latency are monitored, along with grounding-failure rate and analyst override rate.
- Model IDs, prompt versions, corpus versions, and thresholds are versioned and stored with each narrative.
- Any change to a model, prompt, or retrieval corpus requires a fresh evaluation run before release, and the change log records the before and after metrics.

## I. Feedback and Contact

List the repository issue tracker and a contact address here so reviewers can report problems.

<!--
Sync Impact Report
Version change: N/A (initial adoption) -> 1.0.0
Modified principles:
- [PRINCIPLE_1_NAME] -> I. Code Quality by Design
- [PRINCIPLE_2_NAME] -> II. Testing Is Non-Negotiable
- [PRINCIPLE_3_NAME] -> III. Consistent User Experience
- [PRINCIPLE_4_NAME] -> IV. Performance Budgets as Requirements
- [PRINCIPLE_5_NAME] -> V. Maintainability and Simplicity
Added sections:
- Engineering Standards
- Delivery Workflow & Quality Gates
Removed sections:
- None
Templates requiring updates:
- ✅ updated: .specify/templates/plan-template.md
- ✅ updated: .specify/templates/spec-template.md
- ✅ updated: .specify/templates/tasks-template.md
- ⚠ pending: .specify/templates/commands/*.md (directory not present)
Follow-up TODOs:
- None
-->

# gw2bot Constitution

## Core Principles

### I. Code Quality by Design
All production code MUST be readable, modular, and reviewable. Every change MUST
include clear naming, focused functions, and bounded module responsibilities.
Pull requests MUST pass formatting, linting, and static analysis checks before
merge. Code that increases accidental complexity without measurable value MUST be
rejected or simplified before approval.

Rationale: High quality code lowers defect rates, reduces maintenance cost, and
keeps delivery speed sustainable as the project grows.

### II. Testing Is Non-Negotiable
Every behavior change MUST be covered by automated tests. Bug fixes MUST include
a regression test that fails before the fix and passes after it. New features
MUST include unit tests and at least one integration or end-to-end validation of
the primary user path. No pull request may be merged with failing tests.

Rationale: Required automated tests protect core behavior, enable safe refactors,
and prevent repeated regressions.

### III. Consistent User Experience
User-facing behavior MUST be consistent across flows, including terminology,
error messages, interaction patterns, and visual hierarchy. Any intentional UX
deviation MUST be documented in the specification and approved during review.
Accessibility and clarity MUST be considered part of correctness for all user
facing changes.

Rationale: Consistency improves learnability and trust, and reduces support load
from avoidable user confusion.

### IV. Performance Budgets as Requirements
Each feature specification MUST define measurable performance targets for the
primary user interactions or system pathways it affects. Implementations MUST
demonstrate that changes do not violate stated latency, throughput, or resource
bounds. If budgets are exceeded, mitigation work MUST be planned before release.

Rationale: Treating performance as a requirement avoids late-stage surprises and
protects user experience at scale.

### V. Maintainability and Simplicity
Design and implementation decisions MUST prefer the simplest approach that meets
documented requirements. New abstractions MUST be justified by concrete reuse,
testability, or operational benefit. Dead code, duplicate logic, and obsolete
paths MUST be removed as part of ongoing maintenance.

Rationale: Simpler systems are easier to reason about, test, and evolve.

## Engineering Standards

- The canonical workflow is specification -> plan -> tasks -> implementation,
  with constitution checks at each stage.
- Definitions of done MUST include code review, automated tests, and updated
  documentation when behavior changes.
- Public interfaces MUST document expected inputs, outputs, and error behavior.
- Non-trivial changes MUST include rollback or mitigation notes in planning.

## Delivery Workflow & Quality Gates

- Plan documents MUST list constitution gates and explicit pass criteria.
- Specifications MUST include testable acceptance scenarios, UX consistency
  expectations, and measurable performance outcomes.
- Task lists MUST include dedicated tasks for testing, UX validation, and
  performance validation.
- Pull request review MUST verify compliance with all principles before merge.

## Governance

This constitution supersedes conflicting project conventions. Amendments require
documented rationale, explicit impact analysis, and approval in the same review
path used for project standards changes.

Versioning policy for this constitution follows semantic versioning:
- MAJOR: Backward-incompatible governance changes or principle removal/redefinition.
- MINOR: New principle or materially expanded governance requirements.
- PATCH: Clarifications, wording improvements, and non-semantic refinements.

Compliance review expectations:
- Every feature plan MUST include a constitution check before implementation.
- Every pull request review MUST confirm quality, testing, UX consistency, and
  performance requirements were satisfied.
- Violations MUST be tracked with an owner and remediation timeline before merge,
  unless formally waived with documented justification.

**Version**: 1.0.0 | **Ratified**: 2026-03-30 | **Last Amended**: 2026-03-30
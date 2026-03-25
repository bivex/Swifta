# Domain and Business Goals

## Problem Statement

The business needs a maintainable way to parse Swift source outside the compiler so it can power static analysis, structural inspection, cataloging, and future integrations with external tools.

## Business Goals

1. Parse Swift code in a repeatable and automatable way.
2. Expose a stable structural model that downstream tools can trust.
3. Keep parsing logic isolated from delivery concerns so the system can evolve from CLI to service or plugin without rewriting business logic.
4. Make grammar and contract versioning explicit.
5. Start as a simple monolith that is easy to understand, test, and onboard onto.

## Stakeholders

* business/product owners who need reliable source intelligence
* parser engineers who maintain grammar integration
* tool integrators who consume parse reports
* operations and CI maintainers who run parsing at scale

## In Scope

* lexical and syntactic parsing of Swift source files
* structural extraction of key declarations
* project-level orchestration across many files
* diagnostics, versioning, and operational metadata
* clear contracts and boundaries for future extensions

## Out of Scope for v1

* full semantic analysis
* type inference
* build graph resolution
* distributed deployment
* persistence beyond process-local execution

## Domain Model

### Core Entity

`ParsingJob`

This aggregate root represents one parsing execution over one or more source units. Its invariants are:

* a job must contain at least one source unit
* source unit identifiers must be unique within a job
* a job can only complete after every source unit has an outcome

### Supporting Entity

`SourceUnit`

Represents one Swift file known by its stable identifier and source code payload.

### Value Objects

* `SourceUnitId`: stable logical identity of a source file inside the job
* `GrammarVersion`: identifies the parser grammar contract
* `SyntaxDiagnostic`: immutable parse issue with location and severity
* `StructuralElement`: immutable extracted declaration or import
* `ParseStatistics`: immutable counters and elapsed time
* `ParseOutcome`: immutable result for one source unit

### Domain Events

* `ParsingJobStarted`
* `SourceUnitParsed`
* `SourceUnitParsingFailed`
* `ParsingJobCompleted`

### Reactions to Domain Events

Current reactions are intentionally simple:

* publish structured logs
* expose lifecycle metadata to the application result
* keep extension points ready for metrics, tracing, persistence, or notifications

## Bounded Contexts

### Parsing Orchestration

Responsible for job lifecycle, invariants, and use cases.

### Syntax Parsing

Responsible for turning source text into a parse tree and syntax diagnostics through an infrastructure adapter.

### Structural Extraction

Responsible for mapping parser output into the system's stable structural model.

### Delivery

Responsible for exposing results through CLI or future APIs without leaking infrastructure details back inward.


# Requirements

## Functional Requirements

1. The system must parse a single `.swift` file.
2. The system must parse a directory recursively and ignore non-Swift files.
3. The system must return a versioned parse report for each source unit.
4. The system must aggregate file-level outcomes into one parsing job result.
5. The system must capture syntax diagnostics with message, severity, line, and column.
6. The system must continue parsing other files when one file fails.
7. The system must extract a stable structural model containing at least imports, types, functions, variables, and extensions.
8. The system must keep external dependencies behind explicit interfaces.
9. The system must expose grammar version and report schema version as part of the result contract.
10. The system must make parser limitations visible rather than silently pretending compiler-level correctness.

## Non-Functional Requirements

### Maintainability

* keep domain and application layers independent from ANTLR, filesystem, and CLI code
* keep modules small and single-purpose
* use explicit contracts and constructor injection

### Testability

* cover domain rules with unit tests
* test adapters at boundary level
* keep use cases runnable with test doubles

### Operability

* emit structured lifecycle logs
* make errors explicit and machine-readable
* support deterministic CLI execution in CI

### Resilience

* isolate file failures from the rest of the job
* distinguish business validation failures from technical failures
* keep boundary validation explicit

### Security

* do not execute parsed source
* avoid hidden network calls during normal parsing
* keep configuration externalized

### Extensibility

* allow new adapters without changing stable domain code
* allow richer structural extraction behind the same use-case contract
* keep schema and grammar versions explicit for backward-compatible evolution

## Quality Attributes

The system prioritizes clarity, correctness, and evolvability over premature optimization. Performance optimization is allowed only after measurement and must preserve architectural boundaries.


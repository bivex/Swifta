# Architecture

## Chosen Shape

The system uses a DDD-inspired layered monolith with hexagonal boundaries.

## Layers

### Domain

Contains:

* entities and value objects
* invariants
* ports
* domain events

The domain does not know about ANTLR, filesystem paths, CLI arguments, JSON serializers, or logging backends.

### Application

Contains:

* use cases
* request and response DTOs
* orchestration logic

The application layer coordinates work through ports and publishes domain events.

### Infrastructure

Contains:

* ANTLR grammar integration
* parser generation scripts
* filesystem adapters
* logging adapters

Infrastructure implements ports instead of defining the domain shape.

### Presentation

Contains:

* CLI entry points
* response rendering
* exit-code policy

## Aggregates and Responsibilities

### ParsingJob Aggregate

Owns:

* the list of source units in the job
* file-level parse outcomes
* completion rules

Does not own:

* filesystem traversal
* parser engine lifecycle
* JSON rendering

## Error Model

The contract distinguishes:

* business validation errors, such as an empty source set
* technical failures, such as unreadable files or parser runtime failures
* syntax diagnostics, which are parser findings and not process crashes

## Why a Monolith

The workload is cohesive, the domain is still forming, and the team benefits more from simplicity and low operational overhead than from distributed decomposition. Bounded contexts are still explicit so the system can split later if a real need appears.


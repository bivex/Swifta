# Glossary and Ubiquitous Language

## Terms

`Parsing Job`
: One execution that processes one or more source units and produces aggregated outcomes.

`Source Unit`
: One Swift source file treated as an addressable input.

`Parse Outcome`
: The immutable result of parsing one source unit.

`Structural Model`
: The normalized representation of source structure that the rest of the system consumes.

`Structural Element`
: One extracted item in the structural model, such as an import, class, struct, enum, protocol, extension, function, or variable.

`Syntax Diagnostic`
: A parser-reported issue with location, severity, and message.

`Grammar Version`
: The version label of the grammar contract used to parse a source unit.

`Report Schema Version`
: The version label of the JSON/application contract exposed to consumers.

`Port`
: An inward-facing interface owned by the domain or application layer.

`Adapter`
: An outward-facing implementation of a port that talks to a concrete technology.

`Boundary Validation`
: Validation performed when data enters or leaves the system.

## Naming Rules

* Use `ParsingJob`, not `TaskManager`.
* Use `SourceUnit`, not `FileData`.
* Use `StructuralElement`, not `NodeInfo`.
* Use `SwiftSyntaxParser`, not `ParserHelper`.
* Use `ParseReport`, not `ResultBlob`.


# System Boundaries and Interaction Contexts

## System Boundary

Swifta owns the flow from Swift source input to versioned parse report output.

Inside the system boundary:

* parsing job orchestration
* parser invocation through ports
* structural extraction
* diagnostics normalization
* result contract assembly

Outside the system boundary:

* IDEs
* CI pipelines
* future external analysis systems
* storage systems
* dashboards and monitoring backends

## Interaction Contexts

### 1. Source Discovery Context

Input adapters discover `.swift` files from a filesystem path and supply `SourceUnit` data to the application layer.

### 2. Parsing Context

The application layer asks the `SwiftSyntaxParser` port to parse one `SourceUnit`.

### 3. Structural Extraction Context

The ANTLR adapter maps raw parse trees into the domain structural model.

### 4. Delivery Context

The presentation layer serializes application DTOs as JSON for CLI consumers.

## Dependency Direction

Dependencies are one-directional:

* presentation -> application
* infrastructure -> application/domain ports
* application -> domain
* domain -> nothing outside itself


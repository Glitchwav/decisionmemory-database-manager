# Triad Method Plan: Hybrid Daemonless Database

## 1. /co (The Concept Engineer)
**Objective**: Translate intent into Concept Spec. Define Problem Space.

**Context (Snowball Synthesis)**: 
The user previously requested extreme binary minimization for `db-cli` (~450KB). Now, they need a LanceDB + SurrealDB hybrid. LanceDB brings in Apache Arrow and Polars traits, which are massive dependencies. Therefore, the "daemonless" requirement remains, but "zero-dependency" is waived for the `lancedb` crate out of necessity. It must run instantly, strictly on-demand, linking Vector (Cold) to Graph (Topology).

**Nouns (Entities)**:
- `RecordId`: A deterministic, typed identifier sharing exact space across Graph and Cold storage.
- `GraphNode`: The metadata and topology stored in SurrealDB.
- `ColdVector`: The raw text, chunks, and `f32` embedding arrays stored in LanceDB.
- `HybridContext`: The unified output returned to the agent (Vector Text + Graph Relationships).

**Verbs (Operations)**:
- `ingest`: Natively compute embeddings, write vector to LanceDB, write topology to SurrealDB.
- `semantic_search`: Query LanceDB by vector distance to yield `RecordId`, then join via SurrealDB.
- `graph_walk`: Query SurrealDB for `RecordId` connections, then fetch Cold contents from LanceDB.

## 2. /og (The Ontology Guardian)
**Objective**: Audit Co's spec against System Rules and Rust Persona.

**Audit Results against "Systems Engineer" Persona**:
- **Rule 1 (Reject Stringly-typed logic)**: *PASS*. Co specified `RecordId` and typed entities. Enforced: `RecordId` must be a struct wrapping `String` to prevent arbitrary string passing. Operations must return a `Result<HybridContext, ErrorEnum>`.
- **Rule 2 (Integration & Wiring)**: *PASS*. LanceDB and SurrealDB logic must NOT bleed into `main.rs`. We require a flat module structure: `storage::lance` and `storage::surreal`. `main.rs` only coordinates.
- **Rule 3 (Dependencies)**: *WARNING*. LanceDB will explode binary size. We must accept this, as it is the cost of isolated local vector search. SurrealDB should STILL be accessed via raw `TcpStream` HTTP to save binary size, rather than using the massive `surrealdb` Rust SDK.

**Verdict**: APPROVED. Passing to Bu.

## 3. /bu (The Strict Builder)
**Objective**: Build via Toolchain. Enforce Systems Engineer Persona.

**Execution Plan**:
1. Initialize `lancedb-hybrid` Cargo workspace.
2. Define the unified Skeleton in `src/main.rs`.
3. Use strict types (`RecordId`, `HybridContext`).
4. Keep the HTTP `TcpStream` manual client for SurrealDB.
5. Stub LanceDB ingestion methods using `todo!()` macros.

 # GraphManager & ContextManager – N3/Turtle Support Plan

 > **Version:** 2025-05-18  > **Status:** Draft for internal review

 This document outlines the proposed changes to the core `GraphManager` (and related
 context processing) to support Notation‑3 (N3/Turtle) artifacts as a first‑class data layer
 alongside the existing N‑Quads serialization. The goal is to allow TTL/N3 vocabulary,
 shapes, and rules files to be parsed, persisted, diffed, and stored with provenance,
 without surface‑level workarounds.

 ---

 ## 1 · Background

 Currently, `GraphManager` and `ContextProcessor.normalize()` emit and consume canonical
 JSON‑LD data in N‑Quads format only. All persistence, patch diffing, and provenance wrapping
 operate on N‑Quads strings. However, our Linked‑Open‑Data architecture (Layers 1/2)
 uses Turtle (N3) files for ontologies (`.ttl`), SHACL shapes (`.ttl`), rules (`.ttl`),
 and optional logic (`.n3`). To fully embrace this data‑driven model, we need to support
 TTL/N3 files directly.

 ## 2 · Goals

 1. **Load** TTL/N3 files into `GraphManager` (in‑memory or rdflib backend) via Turtle parsing.
 2. **Serialize** graphs back to Turtle/N3 when persisting named graphs or patches.
 3. **Round‑trip diff**: compute patch deltas between two Turtle graphs.
 4. **Preserve provenance, signing, and the existing patch model** over Turtle triples.
 5. **Maintain backward compatibility**: N-Quads remains default for JSON-LD normalization.
 6. **Ensure signing and verification workflows** remain intact for TTL/N3 content by leveraging
    the canonical JSON-LD → N-Quads pipeline.
 7. **Extend `ContextProcessor`** (and document loader) so HTTP/local Turtle contexts
    can yield JSON-LD `@context` without manual conversion.

 ## 3 · Scope

 Affected modules:

 - `cogitarelink/core/graph.py` – methods in `GraphManager` and backends.
 - `cogitarelink/core/context.py` – in `ContextProcessor` & document loader for TTL contexts.
 - Tests: new unit tests for TTL round‑trip and diffing.
 - Docs: update `docs/architecture.md` or add a new section on Turtle support.

 Changes to reasoning/sandbox or EYE integration are _out of scope_ for this plan.

 ## 4 · Proposed Design

 ### 4.1 GraphManager API Enhancements

 - Detect format by file extension (`.ttl`, `.n3`, `.turtle`) or an explicit `format` parameter.
 - Add `ingest_turtle(data: str, graph_id: str|None = None)` helper:
   ```python
   self._backend.parse(data, format="turtle", graph_id=graph_id)
   ```
 - Add `serialize(format: Literal["nquads","turtle"]=...)` to emit Turtle when requested.
 - Extend backends (`InMemoryGraph`, `RDFLibGraph`) to handle `parse(data, format, graph_id)`
   and `serialize(format)`.

 ### 4.2 ContextProcessor Improvements

 - Extend `_try_dereference()` in `get_document_loader()` to accept local or HTTP Turtle
   documents (`.ttl`/`.turtle`) and derive namespace maps as JSON‑LD contexts.
 - Optionally introduce `ContextProcessor.normalize_turtle()` to canonicalize JSON‑LD context
   loaded from TTL sources.

 ### 4.3 Backend Implementation Sketch

 ```python
 # in RDFLibGraph (backend)
 def parse(self, data: str, format: str = "nquads", graph_id: str|None = None):
     target = self.ds if graph_id is None else self.ds.graph(graph_id)
     target.parse(data=data, format=format)

 def serialize(self, destination: str|None = None, format: str = "nquads") -> str:
     return self.ds.serialize(destination=destination, format=format)
 ```

 ## 5 · Tasks

 | Step | Task                                                              |
 | ---- | ----------------------------------------------------------------- |
 | 1    | Extend `GraphBackend` protocol with generic `parse(data,format,graph_id)`. |
 | 2    | Implement `parse(...,format="turtle")` in backends.              |
 | 3    | Add `serialize(format)` method to backends.                        |
 | 4    | Update `GraphManager` to expose `ingest_turtle()` and `serialize()`. |
 | 5    | Enhance `ContextProcessor` / document loader for TTL contexts.     |
 | 6    | Write unit tests in `tests/test_graphmanager_turtle.py`.          |
 | 7    | Update docs (`docs/architecture.md` or new `docs/graph_manager.md`). |

 ## 6 · Testing

 - **Round‑trip test:** parse a sample TTL file, serialize back to Turtle,
   and parse again; graphs must be isomorphic.
 - **Diff test:** ingest two TTL graphs with a change and assert the patch contains only
   the delta Turtle triples.
  - **Context loading test:** simulate HTTP GET of a `.ttl` URL and verify derived JSON‑LD context.
  - **Signing test:** ingest a sample TTL graph, normalize to canonical N‑Quads, generate and verify
   a signature, and ensure the signature remains valid after TTL round-trip.

 ## 7 · Backward Compatibility

 - Default behavior of `normalize()` remains N‑Quads for JSON‑LD.
 - Existing `ingest_nquads()` and `normalize()` paths are unchanged.
 - TTL support is opt‑in via new methods or file extension detection.

 ## 8 · Next Steps

 1. Finalize API signatures in a follow‑up PR.
 2. Implement and iterate on tests.
 3. Document and demo TTL-based shape/rule ingestion for a sample domain.
 4. Add demo and tests for end-to-end signing/verification of TTL-based graph imports.

 *End of document.*
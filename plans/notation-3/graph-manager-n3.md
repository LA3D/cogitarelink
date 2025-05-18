# GraphManager & ContextManager – N3/Turtle Support Plan

> **Version:** 2025-05-19 (Revised)  > **Status:** Draft for internal review

This document outlines the proposed changes to support Notation‑3 (N3/Turtle) artifacts within the existing JSON-LD-centric architecture. The plan treats N3/Turtle as an interchange format within a standards-based semantic framework, preserving the core architectural patterns of Cogitarelink while adding support for TTL/N3 vocabulary, shapes, and rules files.

---

## 1 · Background

Cogitarelink's core architecture is built around JSON-LD 1.1, with the Context layer serving as the primary driver of the system. The `GraphManager` and `ContextProcessor.normalize()` currently emit and consume canonical JSON‑LD data in N‑Quads format. However, our Linked‑Open‑Data architecture uses Turtle (N3) files for ontologies (`.ttl`), SHACL shapes (`.ttl`), rules (`.ttl`), and optional logic (`.n3`). To better integrate these formats while preserving the existing architecture, we need to enhance our import/export capabilities for TTL/N3 files.

### 1.1 · Standards-Based Integration Approach

Rather than creating custom vocabulary terms or ad-hoc integration patterns, we will leverage established W3C standards to describe and organize N3 rule artifacts:

- **rdf:Dataset**: Used as an umbrella container for all named graphs, following the JSON-LD 1.1 pattern for graph collections.
- **PROF Vocabulary**: The W3C Profiles Vocabulary (http://www.w3.org/ns/dx/prof/) provides terms for describing resource profiles and their artifacts.
- **log: Vocabulary**: The SWAP log namespace (http://www.w3.org/2000/10/swap/log#) provides terms for describing N3 documents and their semantics.
- **Dublin Core Terms**: Used for basic relationships like conformance and format specification.

This standards-based approach creates a clear, consistent pattern for tools and agents to discover and use N3 rule resources within the JSON-LD context.

### 1.2 · High-Level Structure

```
rdf:Dataset
└── prof:Profile               # describes the logic profile
    └── prof:hasArtifact       # points at one or more rule artifacts (N3 files)
        └── log:Document       # each artifact is an N3 rule file
            └── log:semantics  # (optional) blank-node formula
```

Agents' discovery path:  
rdf:Dataset → dct:conformsTo → prof:Profile → prof:hasArtifact → fetch artifact (typed log:Document or text/n3) → run the rules.

## 2 · Goals

1. **Load** TTL/N3 files into `GraphManager` as named graphs via Turtle parsing.
2. **Serialize** graphs back to Turtle/N3 when needed for export or viewing.
3. **Maintain JSON-LD centrality** by treating Turtle as an interchange format, not a parallel processing path.
4. **Organize rule artifacts** using W3C PROF vocabulary and log: namespace for clear semantic organization.
5. **Create a consistent discovery path** for both tools and LLM agents to find and use rule resources.
6. **Preserve provenance, signing, and validation workflows** by continuing to use the canonical JSON-LD → N-Quads pipeline.
7. **Extend `ContextProcessor`** to better handle Turtle contexts and N3 rule documents.

## 3 · Scope

Affected modules:

- `cogitarelink/core/graph.py` – methods in `GraphManager` and backends for Turtle import/export.
- `cogitarelink/core/context.py` – enhancements to document loader for TTL contexts and N3 rule files.
- `cogitarelink/vocab/registry.py` – extend `VocabEntry` to include PROF profiles and artifacts.
- `cogitarelink/reason/sandbox.py` – enhance with rule discovery and integration path.
- Tests: new unit tests for TTL import/export and rule discovery.
- Docs: update architecture documentation to explain the PROF-based rule organization.

## 4 · Proposed Design

### 4.1 JSON-LD 1.1 Structure Example

```json
{
  "@context": {
    "rdf":   "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "prof":  "http://www.w3.org/ns/dx/prof/",
    "log":   "http://www.w3.org/2000/10/swap/log#",
    "dct":   "http://purl.org/dc/terms/",

    "conformsTo": { "@id": "dct:conformsTo", "@type": "@id" },
    "hasArtifact": {
      "@id": "prof:hasArtifact",
      "@type": "@id",
      "@container": "@set"          // always treat as a set
    },
    "isProfileOf": { "@id": "prof:isProfileOf", "@type": "@id" },
    "format": "dct:format",
    "title":  { "@id": "dct:title", "@container": "@language" },
    "profile": "prof:Profile",
    "ResourceDescriptor": "prof:ResourceDescriptor",
    "Document": "log:Document",
    "semantics": { "@id": "log:semantics", "@type": "@id" }
  },

  "@type": "rdf:Dataset",

  "@graph": {
    "InferenceProfile": {
      "@id": "http://example.org/profile/inference",
      "@type": "profile",
      "title": { "en": "N3 Inference Profile" },
      "isProfileOf": "http://www.w3.org/TeamSubmission/n3/",
      "hasArtifact": [
        "http://example.org/rules/rules.n3"
      ]
    },

    "RuleArtifact": {
      "@id": "http://example.org/rules/rules.n3",
      "@type": [ "ResourceDescriptor", "Document" ],
      "format": "text/n3",
      "conformsTo": "http://www.w3.org/TeamSubmission/n3/",
      "semantics": "_:formula1"
    },

    "KnowledgeGraph": {
      "@id": "http://example.org/graph/kg1",
      "@type": "dcat:Dataset",
      "conformsTo": "http://example.org/profile/inference"
    }
  }
}
```

### 4.2 GraphManager API Enhancements

- Add `parse(data, format, graph_id)` method to both backend implementations.
- Add a `serialize(format)` method to export data in different formats.
- Add helper method `ingest_turtle(ttl, graph_id)` that calls `parse()`:
  ```python
  def ingest_turtle(self, data: str, graph_id: str | None = None):
      self._backend.parse(data, format="turtle", graph_id=graph_id)
  ```
- Add helper method for N3 rules:
  ```python
  def ingest_n3(self, data: str, graph_id: str | None = None):
      self._backend.parse(data, format="n3", graph_id=graph_id)
  ```
- Detect format by file extension (`.ttl`, `.n3`, `.turtle`) or an explicit `format` parameter.

### 4.3 VocabEntry Enhancements with PROF Integration

- Extend `VocabEntry` model to include PROF profiles and artifacts:
  ```python
  class VocabEntry(BaseModel):
      # existing fields...
      profiles: List[PROFProfile] = Field(default_factory=list)
      
  class PROFProfile(BaseModel):
      id: str  # Profile IRI
      title: Dict[str, str] = Field(default_factory=dict)  # Language-keyed titles
      is_profile_of: str = "http://www.w3.org/TeamSubmission/n3/"
      artifacts: List[PROFArtifact] = Field(default_factory=list)
      
  class PROFArtifact(BaseModel):
      id: str  # Artifact IRI
      format: str = "text/n3"  # MIME type
      role: Literal["rules", "shapes", "ontology"] = "rules"
      local_path: Optional[str] = None  # Local file path if available
  ```
- Provide helper methods for artifact discovery:
  ```python
  def get_rule_artifacts(self) -> List[PROFArtifact]:
      """Return all rule artifacts across all profiles."""
      result = []
      for profile in self.profiles:
          result.extend([a for a in profile.artifacts 
                         if a.role == "rules"])
      return result
  
  def get_profile_by_id(self, profile_id: str) -> Optional[PROFProfile]:
      """Get a specific profile by its ID."""
      for profile in self.profiles:
          if profile.id == profile_id:
              return profile
      return None
  ```

### 4.4 ContextProcessor Improvements

- Enhance `_try_dereference()` to handle both Turtle contexts and N3 rule documents:
  ```python
  def _try_dereference(url: str) -> Dict[str, Any] | None:
      """Return a pyld-style remote-doc dict if dereference succeeds."""
      try:
          r = _http_get(url)
      except Exception as e:
          log.debug(f"network fetch failed for {url}: {e}")
          return None
  
      ctype = r.headers.get("content-type", "").split(";")[0].strip()
      body  = r.text
  
      # Handle N3 documents specifically
      if ctype == "text/n3" or url.endswith(".n3"):
          # Store in graph manager as a rule artifact
          graph_id = url
          GraphManager().ingest_n3(body, graph_id)
          
          # Create a JSON-LD wrapper that identifies this as a log:Document
          doc = {
              "@context": {
                  "log": "http://www.w3.org/2000/10/swap/log#",
                  "dct": "http://purl.org/dc/terms/"
              },
              "@id": url,
              "@type": "log:Document",
              "dct:format": "text/n3"
          }
          return _wrap_json_doc(json.dumps(doc), url)
      
      # Existing handlers for JSON-LD and Turtle
      if ctype in ("application/ld+json", "application/json"):
          try:
              json.loads(body)  # sanity check
              return _wrap_json_doc(body, url)
          except json.JSONDecodeError:
              pass  # keep inspecting
  
      if ctype in ("text/turtle", "application/x-turtle"):
          from rdflib import Graph
          g = Graph().parse(data=body, format="turtle")
          ctx = {"@context": {p: str(iri) for p, iri in g.namespaces()}}
          return _wrap_json_doc(json.dumps(ctx), url)
  
      # HTML with Link header handling remains the same
      # ...
  ```

### 4.5 Rule Discovery Helper

Create a dedicated helper for discovering N3 rule artifacts using the PROF pattern:

```python
def discover_rule_artifacts(dataset_id: str) -> List[str]:
    """
    Discover N3 rule artifacts for a dataset using PROF pattern.
    
    Returns a list of artifact IRIs that can be loaded.
    
    Discovery path:
    dataset → dct:conformsTo → prof:Profile → prof:hasArtifact
    """
    graph = GraphManager()
    
    # Find conformsTo links
    profile_links = graph.query(
        subj=dataset_id, 
        pred="http://purl.org/dc/terms/conformsTo"
    )
    
    artifacts = []
    for _, _, profile_id in profile_links:
        # For each profile, find its artifacts
        artifact_links = graph.query(
            subj=profile_id,
            pred="http://www.w3.org/ns/dx/prof/hasArtifact"
        )
        
        for _, _, artifact_id in artifact_links:
            # Check if this is a log:Document
            types = [o for _, _, o in graph.query(
                subj=artifact_id,
                pred="http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
            )]
            
            if ("http://www.w3.org/2000/10/swap/log#Document" in types or
                artifact_id.endswith(".n3")):
                artifacts.append(artifact_id)
    
    return artifacts
```

### 4.6 Reasoning Integration

Enhance the `reason_over()` function to automatically discover rule artifacts:

```python
def reason_over(*, 
                jsonld: str,
                shapes_turtle: str | None = None,
                query: str | None = None,
                n3_rules: str | None = None,
                dataset_id: str | None = None
               ) -> Tuple[str, str]:
    """
    • If explicit `n3_rules` → use those directly
    • If `dataset_id` → discover rules via PROF profile
    • If `shapes_turtle` → run SHACL rules (iterate rules)
    • If `query` → run SPARQL CONSTRUCT
    • Returns (patch_jsonld, nl_summary)
    """
    data = _to_graph(jsonld)
    patch = Graph()
    
    # First, try explicit N3 rules
    if n3_rules:
        # Run N3 rules via EYE reasoner or other engine
        # ... implementation details ...
        summary = f"Applied explicit N3 rules, derived {len(patch)} triples"
    
    # Second, try PROF discovery if dataset_id provided
    elif dataset_id:
        rule_artifacts = discover_rule_artifacts(dataset_id)
        if rule_artifacts:
            # Fetch and apply each discovered rule artifact
            for artifact_id in rule_artifacts:
                # Load artifact content (may be cached from document loader)
                # ... implementation details ...
                # Apply rules
                # ... implementation details ...
            summary = f"Applied {len(rule_artifacts)} discovered rule artifacts, derived {len(patch)} triples"
        elif shapes_turtle:
            # Fall back to SHACL
            # ... existing SHACL implementation ...
        elif query:
            # Fall back to SPARQL CONSTRUCT
            # ... existing SPARQL implementation ...
        else:
            summary = "no-op"
    
    # Existing SHACL and SPARQL paths
    elif shapes_turtle:
        # ... existing SHACL implementation ...
    elif query:
        # ... existing SPARQL implementation ...
    else:
        summary = "no-op"
    
    prov_patch = wrap_patch_with_prov(patch)
    return prov_patch.serialize(format="json-ld"), summary
```

### 4.7 Backend Implementation

```python
# in GraphBackend protocol
def parse(self, data: str, format: str, graph_id: str | None = None): ...
def serialize(self, format: str = "nquads") -> str: ...

# in RDFLibGraph (backend)
def parse(self, data: str, format: str = "nquads", graph_id: str | None = None):
    target = self.ds if graph_id is None else self.ds.graph(URIRef(graph_id))
    target.parse(data=data, format=format)

def serialize(self, format: str = "nquads") -> str:
    return self.ds.serialize(format=format)

# in InMemoryGraph (backend)
def parse(self, data: str, format: str = "nquads", graph_id: str | None = None):
    if format == "nquads":
        return self.add_nquads(data, graph_id)
    elif format in ("turtle", "n3"):
        # Use rdflib to parse then convert to our internal format
        g = Graph()
        g.parse(data=data, format=format)
        self.add_nquads(g.serialize(format="nquads"), graph_id)
    else:
        raise ValueError(f"Unsupported format: {format}")
```

## 5 · Tasks

| Step | Task                                                              |
| ---- | ----------------------------------------------------------------- |
| 1    | Extend `GraphBackend` protocol with `parse()` and `serialize()` methods. |
| 2    | Implement these methods in both backends.                          |
| 3    | Add `ingest_turtle()` and `ingest_n3()` helpers to `GraphManager`. |
| 4    | Extend `VocabEntry` with PROF profile and artifact model.          |
| 5    | Enhance `ContextProcessor` document loader to handle N3 rule files. |
| 6    | Implement rule discovery helper using PROF pattern.                |
| 7    | Enhance `reason_over()` to use discovered rule artifacts.          |
| 8    | Write unit tests for N3 import/export and rule discovery.          |
| 9    | Update documentation to explain the PROF-based rule organization.  |

## 6 · Testing

- **Import test:** Parse N3 and Turtle files into named graphs and verify triples are loaded correctly.
- **Export test:** Serialize a graph to Turtle/N3 and verify the output format.
- **PROF discovery test:** Create a test dataset with PROF profile and verify the rule discovery path.
- **Automatic reasoning test:** Verify that `reason_over()` can automatically discover and apply rules.
- **Round-trip test:** Import N3, export back to N3, and verify semantic equivalence.
- **Context derivation test:** Load a Turtle ontology and verify it produces a usable JSON-LD context.
- **Integration test:** Verify the full pipeline from JSON-LD + N3 rules to inferred triples with provenance.

## 7 · Backward Compatibility

- JSON-LD remains the primary format for the system architecture.
- The Context layer continues to drive the system as before.
- N3/Turtle support is purely additive, with no changes to existing flows.
- Existing entity processing pipeline remains intact.
- All provenance and verification mechanisms continue to work as before.
- Using standard W3C vocabularies ensures compatibility with existing semantic web tooling.

## 8 · Benefits of the PROF-Based Approach

- **Organizational Clarity**: Everything lives inside a single rdf:Dataset; named graphs can still be stored by GraphManager under the same dataset ID.
- **Standards-Based**: Uses only established W3C vocabularies and patterns.
- **Simple Discovery Path**: Agents follow one well-defined property path: dataset → conformsTo → profile → hasArtifact.
- **JSON-LD Native**: Advanced containers keep the document compact, deterministic, and easy to transform.
- **Semantic Clarity**: Clear typing with log:Document and format specification.
- **Extensible**: The PROF pattern can easily accommodate different rule profiles (inference, validation, etc.).
- **Interoperable**: Works with existing semantic web tools that understand these vocabularies.

## 9 · Next Steps

1. Implement the GraphBackend enhancements for Turtle/N3 parsing.
2. Create the PROF profile and artifact model in VocabEntry.
3. Implement the rule discovery mechanism.
4. Enhance `reason_over()` to use discovered rules.
5. Create tests and documentation for the new capabilities.
6. Develop example rule profiles and artifacts.
7. Create agent guidance for navigating the PROF-based rule organization.

*End of document.*
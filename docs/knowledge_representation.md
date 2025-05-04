# Knowledge Representation Guidelines

This guide explains how to author and organize the domain knowledge artifacts for CogitareLink. It covers:
- JSON-LD Contexts (Layer 0)
- Ontologies & Vocabularies (Layer 1)
- SHACL Validation Shapes (Layer 2a)
- SHACL Derivation Rules (Layer 2b)
- Verifiability & Signatures
- Provenance
- Temporal Modeling

---

## 1 Layer 0: JSON-LD Contexts

Purpose: map short terms → IRIs, enable the LLM to assemble data with minimal prompt overhead.

Guidelines:
- Keep `@context` < 2 KB so it fits in LLM prompts and caches efficiently.
- Declare only the classes and properties the agent will reference.
- Use `@protected: true` on critical terms to prevent unintentional redefinition.
- If deriving from a Turtle ontology, use `composer.context_from_ttl()` to generate the context.
- All context loading, expansion, compaction, and normalization should be performed via `ContextProcessor` (and its document loader). Avoid manually merging contexts in application code.

Example `context.jsonld`:
```json
{
  "@context": {
    "ex":    "http://example.org/ns#",
    "time":  "http://www.w3.org/2006/time#",
    "hasShape": {"@id":"ex:hasShape","@type":"@id","@protected":true}
  }
}
```

---

## 2 Layer 1: Ontologies & Vocabularies

Define your domain schema (classes, properties) with RDFS/OWL in Turtle (`ontology.ttl`) or JSON-LD.

Guidelines:
- Keep class hierarchies shallow; deep inheritance adds token cost without much benefit.
- Express domain relationships as RDFS subproperties rather than embedding business logic.
- Include `owl:versionInfo` to track versions (e.g. "2025-05").
- Publish as both Turtle and JSON-LD if consumers need one format or the other.

Example `ontology.ttl`:
```turtle
@prefix ex:   <http://example.org/ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl:  <http://www.w3.org/2002/07/owl#> .

ex:Meeting a owl:Class ;
  rdfs:label "Meeting" .

ex:hasStart a owl:DatatypeProperty ;
  rdfs:domain ex:Meeting ;
  rdfs:range  xsd:dateTime .
```

---

## 3 Layer 2: SHACL Shapes & Rules

### 3a Validation Shapes

Use a single NodeShape file (`shapes.ttl`) to express constraints that *must* hold.
  
Note: Store this file under `data/<your-domain>/shapes.ttl` (Layer 2) and load it via the `reason_over` tool; avoid embedding SHACL Turtle snippets directly in application code.

Guidelines:
- One `sh:NodeShape` per operation (e.g. `MeetingShape` targets `ex:Meeting`).
- Use `sh:property` blocks to validate datatypes, cardinalities, patterns.
- Provide human-readable messages with `sh:message` and appropriate `sh:severity`.

Example `shapes.ttl`:
```turtle
@prefix sh:  <http://www.w3.org/ns/shacl#> .
@prefix ex:  <http://example.org/ns#> .

ex:MeetingShape a sh:NodeShape ;
  sh:targetClass ex:Meeting ;
  sh:property [
    sh:path      ex:hasStart ;
    sh:datatype  xsd:dateTime ;
    sh:minCount  1 ;
    sh:maxCount  1 ;
    sh:message   "Every Meeting must have exactly one start time." ;
  ] .
```

### 3b Derivation Rules

Use `sh:SPARQLRule` or `sh:JSRule` in `rules.ttl` to infer new triples.
  
Note: Store derivation rules in `data/<your-domain>/rules.ttl` (Layer 2) so the kernel and LLM can fetch them on demand; avoid inlining these Turtle strings in Python.

Guidelines:
- Prefix inferred triples with a domain namespace to avoid polluting generic vocab.
- Keep SPARQL CONSTRUCT templates concise; LLMs can generate ad-hoc queries at runtime.
- For complex calculations, embed JavaScript via `sh:JSRule`.

Example `rules.ttl`:
```turtle
@prefix sh:  <http://www.w3.org/ns/shacl#> .
@prefix ex:  <http://example.org/ns#> .

ex:OverlappingMeetingRule a sh:SPARQLRule ;
  sh:construct """
    CONSTRUCT {
      ?m1 ex:overlapsWith ?m2 .
    }
    WHERE {
      ?m1 a ex:Meeting ; ex:hasStart ?s1 ; ex:hasEnd ?e1 .
      ?m2 a ex:Meeting ; ex:hasStart ?s2 ; ex:hasEnd ?e2 .
      FILTER(?m1 != ?m2 && ?s1 < ?e2 && ?s2 < ?e1)
    }
  """ .
```

For duration calculations, a JS rule:
```turtle
ex:DurationRule a sh:JSRule ;
  sh:js """
    function generate(node) {
      const s = new Date(node['ex:hasStart']);
      const e = new Date(node['ex:hasEnd']);
      return [{
        subject: node['@id'],
        predicate: 'ex:durationMinutes',
        object: { '@value': (e - s)/60000, '@type': 'xsd:decimal' }
      }];
    }
  """ .
```

---

## 4 Verifiability & Signatures

To ensure integrity of context, ontology, shapes, and rules:
- Sign artifacts using JSON-LD Signatures or JWS (e.g. Ed25519).
- Include signature documents alongside originals (`*.signed.jsonld`).
- Ingest signatures at startup and verify before use.

Example workflow:
```bash
jsonld-sign --key private.pem --input shapes.ttl --format turtle \
  --output shapes.signed.ttl
jsonld-verify --key public.pem --input shapes.signed.ttl
```

---

## 5 Provenance

All inferred triples are automatically wrapped with PROV metadata via `wrap_patch_with_prov()`:
- Each patch gets a new `prov:Activity` blank node.
- Every triple added carries `prov:wasGeneratedBy` linking to the activity.
- Agents can cite activities when explaining derived facts.

To query provenance:
```sparql
SELECT ?s ?p ?o ?act ?time WHERE {
  GRAPH <patch> { ?s ?p ?o . ?s prov:wasGeneratedBy ?act }
  ?act prov:startedAtTime ?time .
}
```

---

## 6 Temporal Modeling

Use the W3C OWL-Time vocabulary to represent time:
- `time:Instant` with `time:inXSDDateTime` for points.
- `time:Interval` with `time:hasBeginning` / `time:hasEnd`.

Shape constraints:
```turtle
ex:IntervalShape a sh:NodeShape ;
  sh:targetClass time:Interval ;
  sh:property [ sh:path time:hasBeginning; sh:nodeKind sh:IRI ];
  sh:property [ sh:path time:hasEnd;       sh:nodeKind sh:IRI ];
  sh:rule [ a sh:JSRule ; sh:js """
    function validate(node) {
      let b = new Date(node['time:hasBeginning']);
      let e = new Date(node['time:hasEnd']);
      if (b >= e) throw 'Interval must start before it ends.';
      return [];
    }
  """ ] .
```

---

## 7 File Layout & Cross-Linking

```
data/yourdomain/
  context.jsonld    ← Layer 0
  ontology.ttl      ← Layer 1
  shapes.ttl        ← Layer 2a (validation)
  rules.ttl         ← Layer 2b (derivation)
  data.jsonld       ← Layer 3 (instances)
```

- Link from data → shapes via `ex:hasShape`.
- Shapes import ontology with `owl:imports <ontology.ttl>`.
- Context terms align to ontology IRIs.

Follow these guidelines to maintain a minimal Python kernel and push all domain logic into data artifacts.
  
## 8 Optional SHACL & DASH Extensions
  
### 8.1 SHACL `sh:shapesGraph`
  
Spec (SHACL Core): the property [sh:shapesGraph](https://www.w3.org/TR/shacl/#shaclShapesGraphDefinition) links a data or graph resource to external shapes graphs.
Agents can fetch and apply these shapes automatically without LLM-generated IRIs.
  
Example:
```turtle
<urn:example:calendar> a ex:Calendar ;
    sh:shapesGraph <urn:shapes:calendar-shapes.ttl> .
```
  
### 8.2 DASH Data Shapes Extensions
  
DASH (https://datashapes.org/dash) provides reusable SHACL extensions:
  
#### 8.2.1 UI & Linking Hints
- `dash:applicableToClass`: soft association of a shape to a class (hint for candidate shapes).
- `dash:shape`: assert that a resource conforms to a given shape (non-triggering).
- `dash:abstract`: mark a class as abstract (`rdfs:domain rdfs:Class`).
- `dash:composite`: annotate parent→child composition (cascading deletes, tree UIs).
  
  Note: AffordanceScanner.scan() will detect these DASH SHACL extensions (e.g. dash:applicableToClass, dash:shape, dash:abstract, dash:composite) and surface them as affordance hints for the agent.
  
#### 8.2.2 Datatype Unions
- `dash:DateOrDateTime`, `dash:StringOrLangString`: predefined `rdf:List` of `sh:or` constraints.
  
#### 8.2.3 Reification Support
- `dash:reifiableBy`, `dash:reificationRequired`: attach metadata shapes to reified property values.
  
Example:
```turtle
ex:PersonShape-age
  a sh:PropertyShape ;
  sh:path ex:age ;
  dash:reifiableBy ex:ProvenanceShape ;
  dash:reificationRequired true .
```
  
#### 8.2.4 Suggestion Generators & Fixes
- `dash:propertySuggestionGenerator`, `dash:suggestionGenerator`: SPARQL-UPDATE or JS hint to repair constraint violations.
- `dash:GraphUpdate`, `dash:addedTriple`, `dash:deletedTriple`: represent suggested fixes as RDF.
  
#### 8.2.5 Validation Result Types
- `dash:SuccessResult`, `dash:FailureResult`: record successful validations and engine errors.
  
Use these extensions when you need richer UI guidance, automated fixes, or advanced result modeling beyond the SHACL core.
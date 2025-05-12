# CLI SPARQL Results & Observations

This document summarizes the end-to-end testing of the SPARQL toolchain via the `cogitarelink` CLI, including QID discovery for "CI-Compass" (Q108615661) and membership lookup.

## 1. Session Overview
- Exercised the newly wired SPARQL tools registered in `cli_main()`.
- Activated the project venv, installed editable dev package, and verified `cogitarelink --list-tools` lists SPARQL commands.

## 2. Endpoint & Tools
- Primary endpoint: https://qlever.cs.uni-freiburg.de/api/wikidata
- Tools tested:
  - `execute_local_query` (in-memory TTL + SELECT)
  - `sparql_query` for SELECT and DESCRIBE (remote)
  - `parse_sparql_query`, `build_graph_from_query` (OBQC wrappers)
  - CLI registration of parsers, validators, execs, top-level and end-to-end workflows

## 3. QID Discovery for "CI-Compass"
1. Tried primary label lookup:
   ```sparql
   PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
   SELECT ?item WHERE { ?item rdfs:label "CI-Compass"@en } LIMIT 1
   ```
   - *Result:* no rows ("CI-Compass" is stored as an alias)
2. Queried aliases via SKOS:
   ```sparql
   PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
   SELECT ?item WHERE { ?item skos:altLabel "CI-Compass"@en } LIMIT 1
   ```
   - *Result:* `http://www.wikidata.org/entity/Q108615661`
3. Fallback via MediaWiki REST API:
   ```bash
   curl 'https://www.wikidata.org/w/api.php?action=wbsearchentities&format=json&search=CI-Compass&language=en'
   ```
   - Confirms: **Q108615661**

## 4. Inspecting the Item
- `DESCRIBE` via SPARQLWrapper failed on QLever (RDF/XML parse error).
- Switched to blanket SELECT of outgoing triples:
  ```sparql
  PREFIX wd: <http://www.wikidata.org/entity/>
  SELECT DISTINCT ?p ?o WHERE { wd:Q108615661 ?p ?o } LIMIT 20
  ```
- Observed key properties:
  - `skos:prefLabel`, `rdfs:label`, `schema:name`: primary label
  - `skos:altLabel`: "cicompass", "CI-Compass"
  - `schema:description`: project description
  - `wdt:P17`: country (United States)
  - `wdt:P31`: instance-of (science project, research grant, etc.)
  - Identifiers: P1813 (official name), P2002 (Twitter username), P2650 (NSF award IDs), P2769 (grant amount)
  - Temporal: P580/P582 (start/end dates)

## 5. Membership Lookup (P710)
```sparql
PREFIX wd:   <http://www.wikidata.org/entity/>
PREFIX wdt:  <http://www.wikidata.org/prop/direct/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?member ?label WHERE {
  wd:Q108615661 wdt:P710 ?member .
  OPTIONAL { ?member rdfs:label ?label FILTER(LANG(?label) = "en") }
} LIMIT 10
```
- *Results:*
  - Q108576266: Center for Research Computing, University of Notre Dame
  - Q1423756: Texas Tech University
  - Q6030821: Information Sciences Institute
  - Q6608367: Indiana University
  - Q7312413: Renaissance Computing Institute

## 6. What Worked
- Local in-memory queries and SELECTs via `sparql_query` on QLever mirror.
- Correct SPARQL registration in the CLI.
- Alias lookup via `skos:altLabel` returned the correct QID.

## 7. What Needs Improvement
- **DESCRIBE/describe_resource**: handle RDF/XML or force support for Turtle/N-Triples.
- **sparql_discover**, **ld_fetch**, **sparql_json_to_jsonld**: still untested; add unit and integration tests.
- **OBQC validator tools**: need example queries and ontology tests.
- **End-to-end agent guidance**: add prompting examples to retrieve labels, descriptions, and participants automatically.

---
*Document generated after CLI SPARQL integration testing.*
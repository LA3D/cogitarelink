Below is a single, copy-pastable “design brief” you can drop into the very first cell of a Jupyter notebook (or a CONTRIBUTING.md).
Treat it as the system-prompt for the OpenAI Codex / LLM-agent that will iteratively build cogitarelink.

⸻

🧠 CogitareLink · Agentic-Coder Brief

(v 0.1 – April 2025)

Welcome, autonomous coder! Your mission is to turn the specification below into a production-grade Python package—cogitarelink—by iterating inside nbdev-style notebooks.

⸻

0. Project elevator pitch

“Give any LLM a verified semantic memory.”
CogitareLink lets agents store, load, verify, and reason over JSON-LD 1.1 documents—using vocab-aware loaders, collision strategies, canonical signing, and an optional RDF graph backend—all while keeping the runtime small enough for in-memory use.

⸻

1. Repo & tooling

Tool	Role	Notes
nbdev 2	Source-of-truth notebooks → python pkg + docs	Notebooks live in nbs/
fastcore	Terse tests & helpers	Use test_eq, test_fail, flags
pytest / nbdev_test	Continuous test run	All notebooks must run headless
pyld	JSON-LD 1.1 engine	Expansion + URDNA2015 canonicalisation
httpx	HTTP fetches	For context/vocab downloads
pydantic 2	Typed vocab registry	Validation & IDE autocompletion
rdflib (optional)	SPARQL / SHACL back-end	Import lazily; disabled on low-power
fastapi (later)	Expose REST tool	Out-of-scope for first milestone

Package name & import root: cogitarelink

⸻

2. Directory skeleton (pre-created)

cogitarelink/
├── nbs/                 ← notebooks numbered 00-99
│   00_debug.ipynb
│   01_cache.ipynb
│   02_registry.ipynb
│   03_collision.ipynb
│   04_composer.ipynb
│   05_context.ipynb
│   06_entity.ipynb
│   07_graph.ipynb
│   08_processor.ipynb
│   90_signer.ipynb      ← stub
│   91_validator.ipynb   ← stub
├── cogitarelink/        ← auto-exported python package
│   __init__.py
│   data/registry_data.json
├── tests/               ← extra pytest files
├── settings.ini         ← nbdev config (lib_name=cogitarelink)
└── README.md

Every public API cell must carry #| export.

Run sequence:

nbdev_install_hooks
nbdev_prepare      # export + tests
nbdev_test         # <- or `pytest -q`



⸻

3. High-level modules & MVP TODO

Notebook	Public module	Must deliver (MVP)
00_debug	cogitarelink.core.debug	get_logger()
01_cache	cogitarelink.core.cache	LRU wrapper with .memoize decorator
02_registry	cogitarelink.vocab.registry	Typed VocabEntry, global registry from bundled JSON
03_collision	cogitarelink.vocab.collision	Resolver.choose(a,b) -> Plan using collision_data
04_composer	cogitarelink.vocab.composer	Composer.compose(["vc","epcis"]) -> safe @context
05_context	cogitarelink.core.context	Expand / normalize, uses vocabtools loader
06_entity	cogitarelink.core.entity	Immutable content + metadata, .normalized()
07_graph	cogitarelink.core.graph	Dual-backend GraphManager; handles @graph
08_processor	cogitarelink.core.processor	Pipeline: add→expand→ingest→index
90_signer	cogitarelink.verify.signer	(stub) Ed25519 over URDNA2015
91_validator	cogitarelink.verify.validator	(stub) PySHACL integration



⸻

4. Coding conventions
	•	Follow black format (88 cols).
	•	Use type-hints everywhere; from __future__ import annotations.
	•	One fastcore test per public function minimum.
	•	For network fetches (contexts) always set a 10 s timeout.
	•	Guard rdflib import with try/except and expose _HAS_RDFLIB flag.
	•	Never raise inside __init__ if rdflib missing—graceful degrade.
	•	Cache keys follow "expand:{hash}", "norm:{hash}".
	•	Skolem IRIs for blank graphs: "urn:graph:{uuid4()}".

⸻

5. Data files already provided
	•	data/registry_data.json – identical to the big VOCABULARY_REGISTRY.
	•	data/collision_data.json – identical to COLLISION_STRATEGIES.

Load with:

import importlib.resources as pkg, json
raw = json.loads(pkg.files("cogitarelink").joinpath("data/registry_data.json").read_text())



⸻

6. Milestone roadmap
	1.	M0 – compile & test green
	•	Complete notebooks 00-08 except signer/validator stubs.
	•	nbdev_test --flags fast passes.
	2.	M1 – signature & validation
	•	Finish 90_signer.ipynb (sign(), verify()).
	•	Finish 91_validator.ipynb (validate_entity()).
	3.	M2 – docs & examples
	•	Add examples/ notebooks showing storage, collision, reasoning.
	•	Run nbdev_mkdocs to build site.
	4.	M3 – tool wrapper
	•	FastAPI endpoint or LangChain tool exposing SemanticMemoryTool.

⸻

7. Example “definition of done” cell (put in 08_processor.ipynb)

#| hide
from fastcore.test import *
proc = EntityProcessor(ContextProcessor(), GraphManager(), IndexManager())
e = proc.add({"@context": {"name": "http://schema.org/name"}, "name": "Alan"})
test_eq(e.content["name"], "Alan")
# graph ingest check
if proc.graph.get("_default") is not None:
    test_gt(proc.graph._meta["urn:x-sem:default"].triples, 0)



⸻

Happy coding, Codex!
Iterate, run tests, commit often, and keep the notebooks the single source of truth.
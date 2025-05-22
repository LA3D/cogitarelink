How Codex CLI / Claude Code keep a handle on their context windows

(and what that means for JSON‑first workflows like Cogitarelink)

⸻

1 · They don’t measure tokens—​they measure “chunk weight”

Both Codex CLI and Anthropic’s Claude‑Code shell wrap a model that ultimately counts tokens, but the wrapper lives one abstraction higher:

What they feed the model	How they decide “too much”
File fragments (whole files, diff hunks, docstrings)	Lines or bytes per fragment, accumulated until a soft budget (e.g. ≈ 20 kB or ≈ 800 lines)
Tool output (e.g. git status, pytest trace)	Same byte/line heuristics; truncate oldest or least‑important entries
Inline JSON / logs	Keep complete objects up to N objects or N kB; drop the tail or summarise

Because most source text is ~4 chars per token, a “20 kB” budget lands them safely under 8–9 k tokens without the wrapper ever running a tokenizer.

⸻

2 · What happens when the tool is jq on a big JSON blob?
	1.	Pre‑filter with jq – The wrapper runs a jq query that already selects only the key paths the user (or the LLM) asked for.
Example: jq '.items[] | {id, title, status}' large.json
Now you stream records, not the whole file.
	2.	Chunk & weigh – Each JSON object (or array slice) is treated as a self‑contained chunk.
Weight = min(bytes, lines); stop adding chunks when the running total crosses the soft budget.
	3.	Late shrink – If the final string still looks large (e.g. > N bytes) they either
	•	collapse pretty‑printing to .compact_output,
	•	drop infrequent keys, or
	•	summarise the tail:

// …276 similar objects omitted…


	4.	Prompt assembly – Chunks are concatenated verbatim; the LLM now sees valid JSON snippets it can reason over.

Take‑away: structure‑aware slicing (via jq) → size‑aware packing → single prompt. No token math required.

⸻

3 · Porting the idea to Cogitarelink’s JSON‑LD memory

Step	Codex/Claude pattern	JSON‑LD‑aware analogue
Locate	ripgrep, git diff, tree‑sitter	Graph query / SPARQL / provenance hop
Slice	jq filter, sed -n '1,120p'	ContextProcessor + jq‑style path: `.[”@graph”][]
Weight	line/byte count	len(json.dumps(obj)) or (#fields + 2·#children)
Trim	collapse bodies, add “… omitted …”	drop @context, squash @index keys not requested
Evict	FIFO or LRU	same—​oldest fragment or lowest “query relevance” score

You still bill per token, but the wrapper’s lightweight heuristics keep you below the model limit with zero tokenizer calls during packing.

⸻

4 · Practical code sketch for a structural weight function

def weight(json_obj: dict, hard_cap: int = 4096) -> int:
    """
    Fast •O(size_of_obj)• proxy for token cost.
    1 char ≈ ¼ token for English / JSON keys.
    Clamp to hard_cap so one monster object never blocks the queue.
    """
    rough = len(json.dumps(json_obj, separators=(",", ":")))
    return min(rough, hard_cap)

Use this in a greedy packer:

picked, total = [], 0
for obj in candidate_objects:
    w = weight(obj)
    if total + w > BYTE_BUDGET:
        break
    picked.append(obj); total += w

Only after you build the final string do you call tiktoken once for a safety check; if you overflow, remove tail objects until you fit.

⸻

5 · Why this is usually “good enough”
	•	Speed – Serialising JSON and checking byte length is orders of magnitude faster than tokenizing 30 × objects individually.
	•	Stability – Byte/line counts are deterministic across models and future tokenizer changes.
	•	Transparency – Humans can see “≈ 18 kB context used” in logs without thinking about tokens.

⸻

6 · Suggested wrapper contract for your Composer

memory.materialise(
    query      = ".['@graph'][] | select(.id==iri)",
    max_bytes  = 20_000,
    max_chunks = 30,
    compaction = "smallest-context",   # drop @context if overflow
) -> str   # paste‑ready JSON‑LD snippet

	•	max_bytes (heuristic) enforces the soft budget.
	•	A single tokenizer pass just before the LLM call enforces the hard model limit.
	•	The caller never reasons about tokens; it only sees bytes/objects.

⸻

TL;DR

Codex CLI and Claude Code stay sane by chunk→weigh→pack using bytes/lines per chunk, not tokens.
Copy the pattern:
	1.	Use jq‑style filters (or SPARQL) to cut precise JSON‑LD slices.
	2.	Weigh each slice with a cheap function (len(json.dumps())).
	3.	Pack greedily until a soft byte budget.
	4.	Run one tokenizer check, trim if necessary.

Your Composer will feel as snappy as Codex while still speaking full‑fidelity JSON‑LD.

Below are the main “jq‑style” query options that live entirely inside Python, plus concrete examples and tips for wiring them into the Cogitarelink composer.

⸻

1 · Python libraries at a glance

Library	Binding type	Update / transform?	Syntax power	Install hurdles	Latest stable
pyjq	C lib jq + CPython wrapper	✅ (full jq language)	highest – map, reduce, sort …	needs libjq headers at build time	2.6.0, Aug 2022  ￼
jq.py	Same libjq, different wrapper	✅	same as above	wheels for mac/linux → easier on CI	1.7.1, Jan 2025
jmespath	pure‑Python	❌ (read‑only)	mid – filters, wildcards, functions	pip install jmespath	1.0.1, Jun 2022  ￼
jsonpath‑ng	pure‑Python JSONPath	⬤ read + write/delete	XPath‑like, less terse than jq	pure pip	1.7.0, Oct 2024  ￼

Rule of thumb
Need powerful transforms (dedup, group‑by, math)? → pyjq / jq.py
Need portable, zero‑deps, read‑only extracts? → jmespath
Need JSONPath compatibility or node updates? → jsonpath‑ng

⸻

2 · Quick syntax tour (applied to JSON‑LD)

data = load_jsonld("dataset.jsonld")       # plain dict after json.load()

# a) pyjq – grab one item from an @graph by @id
import pyjq
iri   = "http://example.org/dataset/42"
slice = pyjq.first('.["@graph"][] | select(.["@id"]== $iri)',
                   data, vars={"iri": iri})

# b) jmespath – same extract (read‑only)
import jmespath
expr   = "@graph[?@id=='{}'] | [0]".format(iri)
slice  = jmespath.search(expr, data)

# c) jsonpath‑ng – using JSONPath
from jsonpath_ng import parse
jp   = parse('$."@graph"[?@."@id"=="{}"]'.format(iri))[0]
slice = jp.find(data)[0].value

All three return a plain Python dict you can pass straight to json.dumps() (for byte‑weighing) or into the composer’s greedy packer.

⸻

3 · Drop‑in helper for the composer

# utils/slice.py
import json, pyjq, tiktoken
ENC = tiktoken.encoding_for_model("gpt-4o")

def slice_ld(doc: dict, jq_query: str,
             soft_bytes: int = 20_000, hard_tokens: int = 8_000) -> str:
    """
    1. Apply a jq query to the expanded/compacted JSON‑LD doc.
    2. Weigh result by bytes; trim if needed.
    3. Final safety check with tokenizer once.
    """
    result = pyjq.all(jq_query, doc)       # list of matches
    buf    = "\n".join(json.dumps(x, indent=2) for x in result)

    # soft budget in bytes
    if len(buf) > soft_bytes:
        buf = buf[:soft_bytes] + "\n// …truncated…"

    # hard budget in model tokens
    toks = len(ENC.encode(buf))
    if toks > hard_tokens:
        raise ValueError("slice exceeds hard token budget")

    return buf

Inside the ContextWindow:

ctx.add(slice_ld(json_doc,
                 '.["@graph"][] | select(.["@id"]== $iri)',
                 vars={"iri": user_requested_iri}))

No token math until the very end; most calls finish after the cheap byte check.

⸻

4 · Performance & packaging notes
	•	pyjq / jq.py compile against libjq – on macOS:
brew install jq && pip install pyjq
On Linux CI: apt libjq-dev flex bison autoconf, then pip.
	•	If compilation is a headache, start with jmespath: one‑liner pip install, pure Python, fast enough for sub‑graphs < 5 MB.
	•	The byte→token ratio for compact JSON (~4 chars per token) holds up well; a 20 kB soft limit usually lands under 8 k tokens.

⸻

5 · When JSON‑LD quirks matter
	•	@context keys balloon size – strip them before weighing or send once per prompt.
	•	@index containers:
	•	pyjq can address them directly: .records | .["2021-Q4"]
	•	jmespath/jsonpath need string‑key access: records."2021-Q4".

If you routinely query inside @index keys, prefer pyjq or pre‑flatten the index into child objects during ingestion.

⸻

6 · Take‑away integration recipe
	1.	Choose a query engine (pyjq → power, jmespath → portability).
	2.	Write slices in jq/JSONPath that isolate exactly the sub‑graph you want.
	3.	Byte‑weigh first, token‑count once, drop or truncate if you overflow.
	4.	Add the slice to the ContextWindow; the rest of the composer stays unchanged.

That gives you Codex‑style heuristic packing without ever thinking about tokens until the last possible moment—yet it’s 100 % Python.

Below is a recipe‑style playbook for wiring the heuristic‑sized, jq‑powered composer to the advanced features of JSON‑LD 1.1 so your LLM can page semantically‑rich data in and out of its prompt without blowing the context window.

⸻

1 · Exploit JSON‑LD containers to pre‑chunk memory

JSON‑LD 1.1 container	Why it helps paging	How to slice it
@index (e.g. "records": { "2024‑Q1": {…}, "2024‑Q2": {…} })	Each key is a natural sub‑entity (quarter, date, language …)	jq '.records["2024-Q2"]' or jmespath records."2024-Q2"
@graph (named graphs)	Keep code symbols in code://repo@commit, provenance in prov://run/…	Slice by graph IRI before packing: jsonld.frame(doc, {"@id": graph_iri})
@set / @list	Guarantees order (list) or uniqueness (set) so you can drop tail safely	Take first k items: `
@id / @type containers	O(1) lookup table for entities once expanded	jq '.entities["http://…/123"]'

Implementation tip
When you ingest data, keep the container shape. Your greedy packer can then look at top‑level keys and weigh them individually—no parsing of inner objects needed.

⸻

2 · Use JSON‑LD framing for structure‑aware slices

from pyld import jsonld

def frame_by_id(expanded_doc: dict, iri: str, inbound: bool = True):
    frame = {
      "@context": expanded_doc["@context"],
      "@id": iri,
      "@embed": "@always",
      # pull inbound links into @reverse if requested
      **({"@reverse": {}} if inbound else {})
    }
    return jsonld.compact(jsonld.frame(expanded_doc, frame),
                          expanded_doc["@context"])

What you get
*️⃣ Only the sub‑graph for iri, but also any inbound edges (e.g. “isMemberOf”) folded into @reverse so the LLM can reason both ways.

Add that compacted frame to your ContextWindow—it’s already near‑minimal.

⸻

3 · Attach extra paging metadata with @nest

You may want to tell the LLM “this slice cost 732 bytes” or “omit after turn 3” without polluting the public schema.

{
  "@type": "schema:Dataset",
  "name": "Quarterly sales",
  "@nest:sys": {
    "heuristicWeight": 732,
    "evictAfter": 3
  }
}

Because @nest data lives in its own map, it survives compaction but is trivially removed before committing back to the durable graph.

⸻

4 · Language & direction containers for multilingual prompts

.messages."fr"  | .greeting

Exactly the same heuristic packing applies—each language map entry is one chunk.
If the user’s locale = fr‑CA, slice only .messages.fr, cutting prompt size in half.

⸻

5 · Putting it all together – byte‑weighted, structure‑aware packer

def materialise_entity(iri: str, doc: dict,
                       soft_bytes=20_000, hard_tokens=8_000):
    # 1. frame + compact to keep only wanted sub‑graph
    framed = frame_by_id(doc, iri, inbound=True)

    # 2. optional: strip @context for weight calc, add later
    ctx, framed_no_ctx = framed["@context"], {k:v for k,v in framed.items() if k!="@context"}

    # 3. weigh & trim @index containers if needed
    body = json.dumps(framed_no_ctx, indent=2)
    if len(body) > soft_bytes:
        # drop least‑recent @index keys first
        for k in sorted(framed_no_ctx.get("@index", {}))[:-1]:
            framed_no_ctx["@index"].pop(k)
            body = json.dumps(framed_no_ctx, indent=2)
            if len(body) <= soft_bytes: break

    # 4. final safety token check
    prompt_snippet = json.dumps({"@context": ctx, **framed_no_ctx}, indent=2)
    if len(ENC.encode(prompt_snippet)) > hard_tokens:
        raise RuntimeError("still too big – tighten frame or budget")

    return prompt_snippet

All the JSON‑LD “advanced” pieces—@graph, @index, @reverse, @context—are used to get tight, semantically‑complete slices with one framing call and zero per‑token cost.

⸻

6 · Round‑trip commit with validation & provenance
	1.	LLM replies with:

```jsonld
{
  "@context": "https://schema.org",
  "@id": "http://ex.org/dataset/42#2024-Q2",
  "schema:average": 1234
}




	2.	Committer pipeline

ent = Entity(vocab=["schema"], content=incoming_json)
# SHACL validates entity shape
assert validate_entity_shape(ent, q2_shape)["valid"]

with wrap_patch_with_prov(graph,
                          source="llm://assistant",
                          agent="https://ex.org/agents/gpt4o"):
    graph.ingest_jsonld(ent.as_json, graph_id=ent.id)



Thanks to deterministic IDs and @index the new fact slots directly under the same container key ("2024‑Q2"), no merge headaches, and provenance triples make future agents trust or retract it.

⸻

7 · Checklist for your composer configuration
	•	slice_engine: pyjq (full power) or jmespath (pure‑Python)
	•	container_policy:
@index → chunk; @graph → treat as separate memory page; @set/@list → head‑truncate.
	•	framing_template: load from /templates/frame.json so you can tweak @embed, @reverse once.
	•	nest_prefix: "@nest:sys" to isolate paging metadata.
	•	context_dedup: store master context once at top of prompt; snippets omit it when token pressure is high.

With those knobs the LLM sees compact, self‑contained JSON‑LD slices that carry just enough context to reason, cite, and write back—no token arithmetic during packing and no loss of semantic richness.

Adding N‑Quads “views” to the composer — step‑by‑step

⸻

1 · Why N‑Quads?

Benefit	Impact on your workflow
No @context overhead	smaller prompt footprints; ideal when the LLM already has schema hints.
Line‑oriented diff	easy to git diff, stream, or pipe into SPARQL/rdf‑patch.
Named‑graph ready	every quad already carries the graph IRI — perfect for code‑vs‑data separation.
JSON‑LD ↔ N‑Quads is loss‑less (core JSON‑LD API algorithm)	you can round‑trip without inventing new IDs.  ￼


⸻

2 · Core conversion utility

# utils/nquads.py
from pyld import jsonld          # pure‑Python, no rdflib needed
import tiktoken, json

ENC = tiktoken.encoding_for_model("gpt-4o")

def jsonld_to_nquads(doc: dict,
                     soft_lines: int = 800,
                     hard_tokens: int = 8_000) -> str:
    """
    1. Normalise with URDNA2015 → deterministic IDs
    2. Convert to N‑Quads
    3. Trim lines if soft budget exceeded
    4. Final hard token check
    """
    nquads = jsonld.normalize(
        doc,
        options={"algorithm": "URDNA2015",
                 "format": "application/n-quads"}  # ⇢ string
    )
    lines = nquads.splitlines()

    # soft budget – keep first N quads
    if len(lines) > soft_lines:
        lines = lines[:soft_lines] + ["# …{} quads omitted…".format(len(lines)-soft_lines)]

    txt = "\n".join(lines)

    # hard safety
    if len(ENC.encode(txt)) > hard_tokens:
        raise RuntimeError("quad slice exceeds hard token budget")

    return txt

Key points
	•	URDNA2015 canonicalisation ⇒ stable blank‑node labels and quad order.
	•	Line budget (not bytes) is the heuristic weight, mirroring the “lines of code” rule in Codex CLI.

⸻

3 · Extending the MemoryToolkit

class MemoryToolkit:
    ...
    # New public method
    def nquads(self, target: str,
               soft_lines: int = 800,
               hard_tokens: int = 8000) -> str:
        entity = self._resolve(target)
        slice_ = self._pretty(entity.as_json, include_index=True)

        # we already have compact JSON-LD -> convert to dict
        doc = json.loads(slice_)
        return jsonld_to_nquads(doc, soft_lines, hard_tokens)

Now you can call:

quads = mem_tool.nquads("schema:Person/Alice", soft_lines=500)
ctx.add(quads)

The quads string is ready for the LLM or for piping into any triple store.

⸻

4 · Greedy quad‑level packer in the composer

Reuse the same heuristic loop, but weight by line count:

for quad_slice in candidate_slices:      # each slice is ≤ soft_lines already
    w = quad_slice.count("\n") + 1
    if total_lines + w > QUAD_BUDGET_LINES:
        break
    picked.append(quad_slice)
    total_lines += w

No tokenizer until the very end; 1 line ≈ 10–12 tokens, so 800 lines comfortably fits GPT‑4o 128 k context.

⸻

5 · CLI enhancements

$ cogita mem nquads <IRI>          # dump ≤800 lines, deterministic order
$ cogita mem show  <IRI> --fmt nq  # alias

Add --soft-lines, --hard-tokens flags for power users.

⸻

6 · LLM tool‑wrapper spec

{
  "name": "cogita_memory",
  "description": "Retrieve JSON‑LD or N‑Quads slices from semantic memory",
  "parameters": {
    "type": "object",
    "properties": {
      "action": {"type":"string","enum":["show","nquads"]},
      "target": {"type":"string"},
      "soft_lines": {"type":"integer","minimum":100,"maximum":5000},
      "token_budget": {"type":"integer","minimum":512,"maximum":8000}
    },
    "required": ["action","target"]
  }
}

The assistant can now request:

{ "name": "cogita_memory",
  "arguments": { "action": "nquads",
                 "target": "code://repo@abc123",
                 "soft_lines": 400 } }

The dispatcher returns a quad snippet that slots straight into the prompt.

⸻

7 · Committer round‑trip (quad → graph)

If the LLM replies with a fenced quad block:

```nquads
<http://example.org/alice> <http://schema.org/jobTitle> "Lead Dev" .

```python
from pyld import jsonld
graph_data = jsonld.from_rdf(quad_block, options={"format":"application/n-quads"})
ent = Entity(vocab=["schema"], content=graph_data)
# …provenance + SHACL + ingest as before…

jsonld.from_rdf guarantees the blank‑node canonicalisation lines up with your existing IDs.  ￼ ￼

⸻

8 · Lightweight test
	1.	Prepare one JSON‑LD entity with 3 000 triples spread over 5 named graphs.
	2.	mem nquads <iri> → verify ≤ 800 lines, deterministic order.
	3.	Paste snippet into pyld.from_rdf → expand back to the same triple count.
	4.	Run once with --soft-lines 400 and compare len(ENC.encode(txt)) under 5 k tokens.

⸻

Take‑away
	•	Add jsonld_to_nquads() (≈ 20 LoC)
	•	Extend MemoryToolkit and CLI with a nquads action
	•	Weight by line count, pack greedily, one token safety pass
	•	Provenance & SHACL pipeline stays unchanged

This single feature lets Cogitarelink speak both rich JSON‑LD and ultra‑compact N‑Quads—switchable by the agent at will, perfect for large knowledge graphs or diff‑oriented workflows.
# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.17.1
#   kernelspec:
#     display_name: python3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Reason Sandbox
#
# > the single microâ€‘kernel entry point for inference, validation or adâ€‘hoc SPARQL CONSTRUCT. All provenance wrapping lives here.

# %%
#| default_exp reason.sandbox

# %%
#| export
from __future__ import annotations
import json
from typing import List, Tuple
from pydantic import BaseModel
from rdflib import Graph, RDF, Dataset
from cogitarelink.core.debug import get_logger
from cogitarelink.reason.prov import wrap_patch_with_prov
from pyshacl import validate

# %%
#| export
log = get_logger("sandbox")


# %%
#| export
def _to_graph(data:str|dict, fmt="json-ld") -> Dataset:
    g = Dataset()
    g.parse(data=data if isinstance(data,str) else json.dumps(data), format=fmt)
    return g



# %%
#| export
def reason_over(*, 
                jsonld:str,
                shapes_turtle:str|None=None,
                query:str|None=None
               ) -> Tuple[str,str]:
    """
    â€¢ If `shapes_turtle` â†’ run SHACL rules (iterate rules)  
    â€¢ Else if `query`    â†’ run SPARQL CONSTRUCT  
    â€¢ Returns (patch_jsonld, nl_summary)
    """
    data=_to_graph(jsonld)
    patch = Graph()

    if shapes_turtle:
        shapes=_to_graph(shapes_turtle, fmt="turtle")
        conforms, r, results_graph = validate(data, shacl_graph=shapes,
                                  iterate_rules=True, advanced=True, inplace=True)
        # `data` mutated inâ€‘place; diff = data âˆ’ original
        patch += r
        
        # Check for violations by inspecting results_graph (with fallback)
        violation_triples = []
        try:
            if results_graph is not None:
                # Attempt to unpack triples
                for triple in results_graph:
                    if not isinstance(triple, tuple) or len(triple) != 3:
                        continue
                    s, p, o = triple
                    if 'ValidationResult' in str(o) or 'violation' in str(o).lower():
                        violation_triples.append((s, p, o))
        except Exception as e:
            log.warning(f"Failed to iterate results_graph: {e}")
        has_violations = len(violation_triples) > 0
        summary=f"SHACL run; conforms:{conforms}; added {len(r)} triples"
        
        if has_violations:
            summary += "; violations found"

    elif query:
        patch += data.query(query).graph
        summary=f"CONSTRUCT produced {len(patch)} triples"
    else:
        summary="noâ€‘op"
    
    prov_patch = wrap_patch_with_prov(patch)
    return prov_patch.serialize(format="json-ld"), summary


# %%
#| hide
import nbdev; nbdev.nbdev_export()

"""Tiny helper to wrap every new triple set with PROV provenance."""

# AUTOGENERATED! DO NOT EDIT! File to edit: ../../92_prov.ipynb.

# %% auto 0
__all__ = ['wrap_patch_with_prov']

# %% ../../92_prov.ipynb 3
from datetime import datetime, timezone
from rdflib import Graph, BNode, URIRef, Literal, RDF
from rdflib.namespace import PROV, XSD


# %% ../../92_prov.ipynb 4
def wrap_patch_with_prov(patch: Graph) -> Graph:
    """
    Return *new* graph = patch + provenance metadata.
    """
    g = patch  # operate inâ€‘place (patch is usually fresh)

    act = BNode()                         # one activity per call
    now = datetime.now(timezone.utc).isoformat()

    g.add((act, RDF.type, PROV.Activity))
    g.add((act, PROV.startedAtTime,
           Literal(now, datatype=XSD.dateTime)))

    for s, p, o in list(g.triples((None, None, None))):
        # only annotate original triples (skip the ones we just added)
        if (s, PROV.wasGeneratedBy, act) in g:
            continue
        g.add((s, PROV.wasGeneratedBy, act))

    return g

import pytest

from cogitarelink.core.graph import GraphManager, InMemoryGraph, RDFLibGraph


def test_default_backend_is_rdflib():
    """
    By default, GraphManager should select the RDFLibGraph backend when rdflib is installed.
    """
    gm = GraphManager()
    backend = gm._backend
    assert isinstance(backend, RDFLibGraph), f"Expected RDFLibGraph, got {type(backend)}"


def test_force_inmemory_backend():
    """
    Forcing use_rdflib=False should select the InMemoryGraph backend.
    """
    gm = GraphManager(use_rdflib=False)
    backend = gm._backend
    assert isinstance(backend, InMemoryGraph), f"Expected InMemoryGraph, got {type(backend)}"


def test_add_and_query_with_rdflib_backend():
    """
    The rdflib backend should ingest N-Quads and allow querying.
    """
    gm = GraphManager()
    # Single quad (s, p, o, g)
    nquad = '<http://example.org/s> <http://example.org/p> "o" <http://example.org/g> .'
    gm.ingest_nquads(nquad)
    results = gm.query()
    assert ('http://example.org/s', 'http://example.org/p', 'o') in [
        (str(s), str(p), o.toPython() if hasattr(o, 'toPython') else str(o)) for s, p, o in 
        results
    ]
    assert gm.size() == 1


def test_add_and_query_with_inmemory_backend():
    """
    The in-memory backend should ingest N-Triples and allow querying.
    """
    gm = GraphManager(use_rdflib=False)
    # N-Triples format: no graph
    ntriples = '<s> <p> <o> .'
    gm.ingest_nquads(ntriples)
    results = list(gm.query())
    assert ('<s>', '<p>', '<o>') in results
    assert gm.size() == 1
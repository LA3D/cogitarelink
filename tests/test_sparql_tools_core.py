import pytest
import requests

from cogitarelink.tools.sparql_tools import (
    sparql_query,
    describe_resource,
    sparql_discover,
    ld_fetch,
    sparql_json_to_jsonld,
    validate_query_against_ontology,
    check_query_patterns,
    generate_query_fixes,
    refine_query_with_ontology,
)


class DummyResponse:
    def __init__(self, text: str = "", status_code: int = 200):
        self.text = text
        self.status_code = status_code
    def raise_for_status(self):
        if self.status_code != 200:
            raise requests.HTTPError(f"HTTP {self.status_code}")


def test_functions_exist():
    # Ensure all core functions are available
    funcs = [
        sparql_query,
        describe_resource,
        sparql_discover,
        ld_fetch,
        sparql_json_to_jsonld,
        validate_query_against_ontology,
        check_query_patterns,
        generate_query_fixes,
        refine_query_with_ontology,
    ]
    assert all(callable(f) for f in funcs)


def test_validate_query_against_ontology_delegates(monkeypatch):
    # Monkey-patch the underlying OBQC check_query
    called = {}
    def fake_check(query, ontology_ttl=None, ontology_path=None):
        called['query'] = query
        called['ontology_ttl'] = ontology_ttl
        called['ontology_path'] = ontology_path
        return {'valid': True}

    import cogitarelink.reason.obqc as obqc_mod
    monkeypatch.setattr(obqc_mod, 'check_query', fake_check)
    result = validate_query_against_ontology(
        "SELECT * WHERE {}", ontology_ttl="ttl-data", ontology_path=None
    )
    assert result == {'valid': True}
    assert called['query'] == "SELECT * WHERE {}"
    assert called['ontology_ttl'] == "ttl-data"


@pytest.mark.parametrize("func,args", [
    (sparql_query, ("http://example.org", "SELECT * WHERE {}")),
    (describe_resource, ("http://example.org", "http://example.org/resource")),
    (sparql_discover, ("http://example.org",)),
    (ld_fetch, ("http://example.org/resource",)),
    (sparql_json_to_jsonld, ('{"results":{"bindings":[]}}',)),
    (check_query_patterns, ("SELECT * WHERE {}",)),
    (generate_query_fixes, ("SELECT * WHERE {}", {'issues': []})),
    (refine_query_with_ontology, ("SELECT * WHERE {}",)),
])
def test_stub_functions_raise_not_implemented(func, args):
    # All stub functions should raise NotImplementedError by default
    with pytest.raises(NotImplementedError):
        func(*args)
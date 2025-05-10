import pytest
import json
from cogitarelink.tools.sparql import sparql_query, sparql_discover, ld_fetch, sparql_json_to_jsonld


def test_sparql_json_to_jsonld_minimal():
    sample = {
        "head": {"vars": ["s"]},
        "results": {"bindings": [
            {"s": {"type": "uri", "value": "http://example.org/foo"}}
        ]}
    }
    out = sparql_json_to_jsonld(sample, base_uri="urn:test")
    doc = json.loads(out)
    assert isinstance(doc, dict)
    assert "@graph" in doc
    graph = doc["@graph"]
    assert isinstance(graph, list) and len(graph) == 1
    row = graph[0]
    # Check that variable 's' became @id
    assert "s" in row
    assert isinstance(row["s"], dict)
    assert row["s"].get("@id") == "http://example.org/foo"


@pytest.mark.parametrize("endpoint,uri,expected_type", [
    ("https://dbpedia.org/sparql",
     "<http://dbpedia.org/resource/Douglas_Adams>",
     "DBpedia"),
    ("https://query.wikidata.org/sparql",
     "<http://www.wikidata.org/entity/Q42>",
     "Wikidata"),
])
def test_ask_and_select_queries(endpoint, uri, expected_type):
    # Test ASK
    ask_q = f"ASK {{ {uri} ?p ?o }}"
    try:
        res = sparql_query(endpoint, ask_q, query_type="ASK")
    except Exception as e:
        pytest.skip(f"ASK query to {endpoint} failed: {e}")
    assert res.get("success") is True
    assert isinstance(res.get("result"), bool)

    # Test SELECT
    select_q = f"SELECT ?p WHERE {{ {uri} ?p ?o }} LIMIT 1"
    try:
        res2 = sparql_query(endpoint, select_q, query_type="SELECT")
    except Exception as e:
        pytest.skip(f"SELECT query to {endpoint} failed: {e}")
    assert res2.get("success") is True
    results = res2.get("results")
    assert isinstance(results, list)
    # may be empty if no triples, but should be a list


def test_construct_no_store():
    endpoint = "https://dbpedia.org/sparql"
    uri = "<http://dbpedia.org/resource/Douglas_Adams>"
    q = (
        f"CONSTRUCT {{ {uri} a ?type }} "
        f"WHERE {{ {uri} a ?type }} LIMIT 1"
    )
    try:
        res = sparql_query(endpoint, q, query_type="CONSTRUCT", result_format="turtle", store_result=False)
    except Exception as e:
        pytest.skip(f"CONSTRUCT query to {endpoint} failed: {e}")
    assert res.get("success") is True
    data = res.get("data")
    assert isinstance(data, str)
    # should contain the URI
    assert "Douglas_Adams" in data


def test_ld_fetch_wikidata_jsonld():
    uri = "https://www.wikidata.org/wiki/Special:EntityData/Q42.jsonld"
    try:
        res = ld_fetch(uri, result_format="json-ld", store_result=False)
    except Exception as e:
        pytest.skip(f"ld_fetch to {uri} failed: {e}")
    assert res.get("success") is True
    data = res.get("data")
    assert isinstance(data, str)
    # Should be valid JSON
    doc = json.loads(data)
    assert isinstance(doc, (dict, list))


def test_sparql_discover_introspection():
    endpoint = "https://qlever.cs.uni-freiburg.de/api/wikidata"
    try:
        res = sparql_discover(endpoint)
    except Exception as e:
        pytest.skip(f"sparql_discover to {endpoint} failed: {e}")
    assert res.get("endpoint") == endpoint
    preds = res.get("predicates")
    assert isinstance(preds, list)
    # Should discover at least one predicate
    assert len(preds) >= 1
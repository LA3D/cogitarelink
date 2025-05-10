import pytest
pytest.skip("Obsolete SPARQL tests: deprecated interface", allow_module_level=True)

# Test ontology in Turtle format
test_ontology = """
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix schema: <https://schema.org/> .
@prefix ex: <http://example.org/> .

# Classes
ex:Person a rdfs:Class .
ex:Book a rdfs:Class .
ex:Organization a rdfs:Class .

# Properties
ex:name a rdf:Property ;
    rdfs:domain ex:Person ;
    rdfs:range rdfs:Literal .

ex:author a rdf:Property ;
    rdfs:domain ex:Book ;
    rdfs:range ex:Person .

ex:publisher a rdf:Property ;
    rdfs:domain ex:Book ;
    rdfs:range ex:Organization .

ex:worksFor a rdf:Property ;
    rdfs:domain ex:Person ;
    rdfs:range ex:Organization .

# Property with multiple domains
ex:title a rdf:Property ;
    schema:domainIncludes ex:Book ;
    schema:domainIncludes ex:Organization ;
    rdfs:range rdfs:Literal .
"""

class MockResponse:
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code
        
    def raise_for_status(self):
        if self.status_code != 200:
            raise Exception(f"HTTP Error: {self.status_code}")

def test_sparql_json_to_jsonld():
    """Test conversion of SPARQL JSON results to JSON-LD."""
    # Sample SPARQL JSON result
    sparql_json = """{
        "head": {
            "vars": ["s", "p", "o"]
        },
        "results": {
            "bindings": [
                {
                    "s": {"type": "uri", "value": "http://example.org/person1"},
                    "p": {"type": "uri", "value": "http://example.org/name"},
                    "o": {"type": "literal", "value": "John Doe"}
                },
                {
                    "s": {"type": "uri", "value": "http://example.org/person1"},
                    "p": {"type": "uri", "value": "http://example.org/age"},
                    "o": {"type": "literal", "value": "25", "datatype": "http://www.w3.org/2001/XMLSchema#integer"}
                }
            ]
        }
    }"""
    
    # Convert to JSON-LD
    jsonld_str = sparql_json_to_jsonld(sparql_json, base_uri="http://example.org/test")
    
    # Parse back to JSON to test structure
    jsonld = json.loads(jsonld_str)
    
    # Check structure
    test_eq(jsonld["@id"], "http://example.org/test")
    test_eq(jsonld["@type"], "sparql:ResultSet")
    test_eq(len(jsonld["@graph"]), 2)
    test_eq(jsonld["sparql:resultVariable"], ["s", "p", "o"])
    
    # Verify first result
    first_result = jsonld["@graph"][0]
    test_eq(first_result["s"]["@id"], "http://example.org/person1")
    test_eq(first_result["p"]["@id"], "http://example.org/name")
    test_eq(first_result["o"], "John Doe")

@patch('cogitarelink.tools.sparql.SPARQLWrapper')
def test_sparql_query(mock_sparqlwrapper):
    """Test SPARQL query execution."""
    # Configure mock
    mock_instance = MagicMock()
    mock_sparqlwrapper.return_value = mock_instance
    
    mock_response = MagicMock()
    mock_instance.query.return_value = mock_response
    
    # Create sample results
    mock_response.response = MockResponse(json.dumps({
        "head": {"vars": ["s", "p", "o"]},
        "results": {"bindings": [
            {"s": {"type": "uri", "value": "http://example.org/resource1"}}
        ]}
    }))
    mock_response.convert.return_value = {
        "head": {"vars": ["s", "p", "o"]},
        "results": {"bindings": [
            {"s": {"type": "uri", "value": "http://example.org/resource1"}}
        ]}
    }
    
    # Call the function
    result = sparql_query(
        endpoint_url="http://example.org/sparql",
        query="SELECT * WHERE { ?s ?p ?o }",
        query_type="SELECT"
    )
    
    # Check the result
    test_eq(result["success"], True)
    test_eq(result["query_type"], "SELECT")
    test_eq(len(result["results"]), 1)
    test_eq(result["results"][0]["s"]["value"], "http://example.org/resource1")

@patch('cogitarelink.tools.sparql.sparql_query')
def test_describe_resource(mock_sparql_query):
    """Test DESCRIBE convenience function."""
    # Configure mock
    mock_sparql_query.return_value = {
        "success": True,
        "query_type": "DESCRIBE",
        "data": "<http://example.org/resource1> <http://example.org/name> 'Test' ."
    }
    
    # Call the function
    result = describe_resource(
        endpoint_url="http://example.org/sparql",
        uri="http://example.org/resource1"
    )
    
    # Check that describe_resource called sparql_query correctly
    mock_sparql_query.assert_called_once()
    args, kwargs = mock_sparql_query.call_args
    test_eq(kwargs["endpoint_url"], "http://example.org/sparql")
    test_eq(kwargs["query"], "DESCRIBE <http://example.org/resource1>")
    test_eq(kwargs["query_type"], "DESCRIBE")
    
    # Check the result was passed through
    test_eq(result["success"], True)
    test_eq(result["query_type"], "DESCRIBE")

@patch('cogitarelink.tools.sparql.httpx.get')
def test_ld_fetch(mock_get):
    """Test Linked Data fetching."""
    # Configure mock
    mock_get.return_value = MockResponse(
        text='{"@context": {"ex": "http://example.org/"}, "@id": "http://example.org/resource1"}',
        status_code=200
    )
    
    # Mock GraphManager
    with patch('cogitarelink.tools.sparql.GraphManager') as mock_gm:
        mock_gm_instance = MagicMock()
        mock_gm.return_value = mock_gm_instance
        
        # Call the function
        result = ld_fetch(
            uri="http://example.org/resource1",
            store_result=True
        )
        
        # Check results
        test_eq(result["success"], True)
        test_eq(result["uri"], "http://example.org/resource1")
        test_eq(result["stored"], True)

def test_check_query_patterns():
    """Test checking SPARQL query patterns."""
    # Test a query with issues (missing LIMIT, Cartesian product)
    query = """
    PREFIX ex: <http://example.org/>
    SELECT ?person ?book
    WHERE {
        ?person a ex:Person .
        ?book a ex:Book .
    }
    """
    
    result = check_query_patterns(query)
    
    # Check that issues were found
    test_eq(result["success"], True)
    test_gt(len(result["warnings"]), 0)
    
    # Verify at least one warning type
    warning_types = [w["type"] for w in result["warnings"]]
    test_contains(warning_types, "missing_limit")
    
    # Test a query with no issues
    good_query = """
    PREFIX ex: <http://example.org/>
    SELECT ?person ?name
    WHERE {
        ?person a ex:Person .
        ?person ex:name ?name .
    }
    LIMIT 10
    """
    
    good_result = check_query_patterns(good_query)
    test_eq(len(good_result["warnings"]), 0)

def test_generate_query_fixes():
    """Test generating fixes for query issues."""
    # Create validation result with warnings
    validation = {
        "warnings": [
            {
                "type": "missing_limit",
                "message": "Query does not include a LIMIT clause"
            }
        ]
    }
    
    # Test query
    query = """
    PREFIX ex: <http://example.org/>
    SELECT ?person ?name
    WHERE {
        ?person a ex:Person .
        ?person ex:name ?name .
    }
    """
    
    # Generate fixes
    fixes = generate_query_fixes(query, validation)
    
    # Verify results
    test_eq(fixes["success"], True)
    test_eq(fixes["needs_fixes"], True)
    test_gt(len(fixes["fix_explanations"]), 0)
    test_ne(fixes["fixed_query"], query)  # Should be different after fix
    test_contains(fixes["fixed_query"], "LIMIT")  # Should have added LIMIT

@patch('cogitarelink.tools.sparql.validate_query_against_ontology')
@patch('cogitarelink.tools.sparql.check_query_patterns')
def test_refine_query_with_ontology(mock_check_patterns, mock_validate):
    """Test the entire query refinement workflow."""
    # Configure mocks
    mock_check_patterns.return_value = {
        "query_type": "SELECT",
        "warnings": [
            {
                "type": "missing_limit",
                "message": "Query does not include a LIMIT clause"
            }
        ]
    }
    
    mock_validate.return_value = {
        "valid": False,
        "violations": [
            "Domain violation for ex:name - expected ex:Person"
        ]
    }
    
    # Test with query that needs refinement
    query = """
    PREFIX ex: <http://example.org/>
    SELECT ?book ?name
    WHERE {
        ?book a ex:Book .
        ?book ex:name ?name .
    }
    """
    
    # Call refinement
    with patch('cogitarelink.tools.sparql.generate_query_fixes') as mock_fixes:
        # Configure mock fixes
        mock_fixes.side_effect = [
            # First call - fix patterns
            {
                "needs_fixes": True,
                "fixed_query": query + " LIMIT 100",
                "fix_explanations": ["Added LIMIT 100"]
            },
            # Second call - fix ontology issues
            {
                "needs_fixes": True,
                "fixed_query": """
                PREFIX ex: <http://example.org/>
                SELECT ?book ?name
                WHERE {
                    ?book a ex:Book .
                    ?person a ex:Person .
                    ?person ex:name ?name .
                    ?book ex:author ?person .
                }
                LIMIT 100
                """,
                "fix_explanations": ["Fixed domain violation for ex:name"]
            }
        ]
        
        result = refine_query_with_ontology(query, ontology_ttl=test_ontology)
        
        # Verify refinement process
        test_eq(result["success"], True)
        test_gt(len(result["iterations"]), 0)
        test_ne(result["refined_query"], query)
import pytest
from rdflib import Graph, URIRef, Literal
from cogitarelink.tools.sparql import sparql_parser_tools, sparql_validator_tools
from cogitarelink.tools.sparql import SPARQLToolAgent

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

# Test data for local query execution
test_data = """
@prefix ex: <http://example.org/> .

ex:john a ex:Person ;
    ex:name "John Smith" ;
    ex:worksFor ex:CompanyA .

ex:mary a ex:Person ;
    ex:name "Mary Jones" ;
    ex:worksFor ex:CompanyB .

ex:book1 a ex:Book ;
    ex:title "SPARQL for Beginners" ;
    ex:author ex:john .

ex:CompanyA a ex:Organization ;
    ex:title "Company A" .

ex:CompanyB a ex:Organization ;
    ex:title "Company B" .
"""

def test_parse_sparql_query():
    """Test that the SPARQL query parser correctly extracts components."""
    parser_tools = sparql_parser_tools()
    
    # Test a simple query
    query = """
    PREFIX ex: <http://example.org/>
    SELECT ?person ?name
    WHERE {
        ?person a ex:Person .
        ?person ex:name ?name .
    }
    """
    
    result = parser_tools["parse_sparql_query"](query)
    
    # Check basic structure
    assert result["success"] == True
    assert result["query_type"] in ["SelectQuery", "Select"]
    assert "?person" in result["variables"]
    assert "?name" in result["variables"]
    
    # Check prefix extraction
    assert "ex" in result["prefixes"]
    assert result["prefixes"]["ex"] == "http://example.org/"
    
    # Check BGP extraction
    assert len(result["bgps"]) >= 2  # At least two triple patterns
    
    # Find the name pattern
    name_pattern = None
    for triple in result["bgps"]:
        if triple["predicate"] == "ex:name":
            name_pattern = triple
            break
    
    assert name_pattern is not None
    assert name_pattern["subject"].startswith("?")
    assert name_pattern["object"].startswith("?")

def test_build_graph_from_query():
    """Test that a SPARQL query is correctly converted to an RDF graph."""
    parser_tools = sparql_parser_tools()
    
    query = """
    PREFIX ex: <http://example.org/>
    SELECT ?book ?author
    WHERE {
        ?book a ex:Book .
        ?book ex:author ?author .
        ?author a ex:Person .
    }
    """
    
    result = parser_tools["build_graph_from_query"](query)
    
    # Check success
    assert result["success"] == True
    
    # Check that we got a JSON-LD graph
    assert "jsonld" in result
    assert isinstance(result["jsonld"], dict)
    
    # Check that we have the right number of triples
    assert result["triples_count"] >= 5  # 3 from the query + 2 for variable types

def test_validate_query_against_ontology():
    """Test that SPARQL query validation correctly identifies issues."""
    validator_tools = sparql_validator_tools()
    
    # Test a valid query
    valid_query = """
    PREFIX ex: <http://example.org/>
    SELECT ?person ?name
    WHERE {
        ?person a ex:Person .
        ?person ex:name ?name .
    }
    """
    
    valid_result = validator_tools["validate_query_against_ontology"](valid_query, test_ontology)
    assert valid_result["valid"] == True
    assert valid_result["violations_count"] == 0
    
    # Test a domain violation
    invalid_query = """
    PREFIX ex: <http://example.org/>
    SELECT ?book ?name
    WHERE {
        ?book a ex:Book .
        ?book ex:name ?name .  # ex:name is only for ex:Person
    }
    """
    
    invalid_result = validator_tools["validate_query_against_ontology"](invalid_query, test_ontology)
    assert invalid_result["valid"] == False
    assert invalid_result["violations_count"] > 0
    assert any("domain" in v.lower() for v in invalid_result["violations"])

def test_generate_query_fixes():
    """Test that the system can generate fixes for invalid queries."""
    validator_tools = sparql_validator_tools()
    
    # First validate a query with issues
    query = """
    PREFIX ex: <http://example.org/>
    SELECT ?book ?name
    WHERE {
        ?book a ex:Book .
        ?book ex:name ?name .  # ex:name is only for ex:Person
    }
    """
    
    validation = validator_tools["validate_query_against_ontology"](query, test_ontology)
    
    # Now generate fixes
    fixes = validator_tools["generate_query_fixes"](query, validation)
    
    # Check that we got a response
    assert fixes["success"] == True
    assert fixes["needs_fixes"] == True
    
    # Check that we got some guidance
    assert len(fixes["fix_explanations"]) > 0
    assert len(fixes["guidance"]) > 0

def test_check_query_patterns():
    """Test that common SPARQL pattern issues are detected."""
    validator_tools = sparql_validator_tools()
    
    # Test a query with potential cartesian product
    query = """
    PREFIX ex: <http://example.org/>
    SELECT ?person ?title
    WHERE {
        ?person a ex:Person .
        ?book ex:title ?title .  # ?book only appears once, not connected to ?person
    }
    """
    
    result = validator_tools["check_query_patterns"](query)
    
    # Check that we identified some warnings
    assert result["success"] == True
    assert len(result["warnings"]) > 0 or len(result["issues"]) > 0

def test_execute_local_query():
    """Test executing a SPARQL query against a local graph."""
    from cogitarelink.tools.sparql import sparql_execution_tools
    execution_tools = sparql_execution_tools()
    
    # Test a simple SELECT query
    query = """
    PREFIX ex: <http://example.org/>
    SELECT ?person ?name
    WHERE {
        ?person a ex:Person .
        ?person ex:name ?name .
    }
    """
    
    result = execution_tools["execute_local_query"](query, test_data)
    
    # Check success and results
    assert result["success"] == True
    assert result["query_type"] == "SELECT"
    assert len(result["results"]) == 2  # We have two persons in our test data
    
    # Check that we got both John and Mary
    names = [row["name"] for row in result["results"]]
    assert any("John" in name for name in names)
    assert any("Mary" in name for name in names)

def test_sparql_tool_agent():
    """Test the complete SPARQL tool agent workflow."""
    agent = SPARQLToolAgent()
    
    # Test the refinement workflow (assumes mock validation - we won't test real refinement here)
    query = """
    PREFIX ex: <http://example.org/>
    SELECT ?book ?name
    WHERE {
        ?book a ex:Book .
        ?book ex:name ?name .  # ex:name is only for ex:Person
    }
    """
    
    # Execute a local query
    result = agent.end_to_end_query(
        query=query, 
        data_graph=test_data,
        ontology_ttl=test_ontology,
        validate_first=True,
        auto_refine=True
    )
    
    # Check that we completed the workflow
    assert "workflow" in result
    assert len(result["workflow"]) >= 2  # At least validation and execution steps
    
    # Check that validation step was included
    validation_step = next((step for step in result["workflow"] if step["step"] == "validation"), None)
    assert validation_step is not None
    
    # Check that execution step was included
    execution_step = next((step for step in result["workflow"] if step["step"] == "execution"), None)
    assert execution_step is not None
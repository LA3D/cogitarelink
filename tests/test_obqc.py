import pytest
from cogitarelink.reason.obqc import check_query

# Test ontology
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

def test_valid_query():
    """Test that a valid query passes checks"""
    query = """
    PREFIX ex: <http://example.org/>
    SELECT ?person ?name
    WHERE {
        ?person a ex:Person .
        ?person ex:name ?name .
    }
    """
    result = check_query(query, test_ontology)
    assert "violation" not in result.lower(), f"Valid query raised issues: {result}"

def test_domain_violation():
    """Test that domain violations are detected"""
    query = """
    PREFIX ex: <http://example.org/>
    SELECT ?book ?name
    WHERE {
        ?book a ex:Book .
        ?book ex:name ?name .
    }
    """
    result = check_query(query, test_ontology)
    assert "domain" in result.lower(), f"Domain violation not detected: {result}"

def test_undefined_property():
    """Test that undefined properties are detected"""
    query = """
    PREFIX ex: <http://example.org/>
    SELECT ?person ?age
    WHERE {
        ?person a ex:Person .
        ?person ex:age ?age .
    }
    """
    result = check_query(query, test_ontology)
    assert "not defined" in result.lower(), f"Undefined property not detected: {result}"

def test_multiple_domain_warning():
    """Test that properties with multiple domains generate warnings"""
    query = """
    PREFIX ex: <http://example.org/>
    SELECT ?something ?title
    WHERE {
        ?something ex:title ?title .
    }
    """
    result = check_query(query, test_ontology)
    assert "multiple domain" in result.lower(), f"Multiple domain warning not detected: {result}"

def test_bgp_extraction():
    """Test extraction of basic graph patterns from complex queries"""
    query = """
    PREFIX ex: <http://example.org/>
    SELECT ?person ?org
    WHERE {
        ?person a ex:Person ;
                ex:name "John" ;
                ex:worksFor ?org .
        ?org a ex:Organization .
    }
    """
    result = check_query(query, test_ontology)
    assert "violation" not in result.lower(), f"Valid complex query raised issues: {result}"
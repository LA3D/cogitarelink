# CogitareLink SPARQL Tools Implementation Specification

This document provides specific implementation guidelines for integrating SPARQL and Linked Data tools into the CogitareLink framework, based on experiments and analysis conducted in the repository.

## 1. Module Structure

Create a new submodule in the CogitareLink codebase:

```
cogitarelink/
  tools/
    sparql/
      __init__.py       # Exports functions and specs
      query.py          # Core query functions
      discover.py       # Endpoint discovery functions
      fetch.py          # Linked Data retrieval functions
      transform.py      # Format conversion utilities
      memory.py         # Memory integration helpers
      specs.py          # Function specifications
      cache.py          # Optional caching layer
```

## 2. Core Function Definitions

### 2.1 Query Functions (query.py)

```python
from typing import Dict, Any, Optional, List, Union
import requests
from rdflib import Dataset, Graph

from ...core.graph import GraphManager
from ...core.debug import get_logger
from ..transform import sparql_json_to_jsonld

log = get_logger("tools.sparql")

def sparql_query(
    endpoint_url: str,
    query: str,
    query_type: str = "SELECT",
    result_format: str = "json",
    store_result: bool = False,
    graph_id: Optional[str] = None,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Execute a SPARQL query against any endpoint.
    
    Args:
        endpoint_url: SPARQL endpoint URL
        query: SPARQL query text
        query_type: One of SELECT, ASK, CONSTRUCT, DESCRIBE
        result_format: Preferred result format
        store_result: Whether to store graph results in memory
        graph_id: Named graph ID for storage (defaults to endpoint URL if None)
        timeout: Request timeout in seconds
        
    Returns:
        Dictionary with query results and metadata
    """
    # Default graph_id if not provided
    if graph_id is None:
        graph_id = f"sparql_{endpoint_url.replace('://', '_').replace('/', '_')}"
    
    # Determine Accept header
    accept = _determine_accept_header(query_type, result_format)
    
    # Send request
    params = {'query': query}
    headers = {'Accept': accept, 'User-Agent': 'cogitarelink-sparql/0.1'}
    
    try:
        resp = requests.get(endpoint_url, params=params, headers=headers, timeout=timeout)
        resp.raise_for_status()
        data = resp.text
        
        # Process result based on query type
        if query_type.upper() in ('SELECT', 'ASK'):
            result = {
                "success": True,
                "query_type": query_type,
                "format": result_format,
                "endpoint": endpoint_url,
                "data": data
            }
            
            # Optionally convert to JSON-LD and store
            if store_result and result_format == 'json':
                jsonld = sparql_json_to_jsonld(data, endpoint_url)
                _store_data(jsonld, 'json-ld', graph_id)
                result["stored"] = True
                result["graph_id"] = graph_id
                result["data_size"] = len(jsonld)
            
            return result
        else:  # CONSTRUCT or DESCRIBE
            result = {
                "success": True,
                "query_type": query_type,
                "format": result_format,
                "endpoint": endpoint_url,
                "data_size": len(data)
            }
            
            # Optionally ingest into memory
            if store_result:
                triple_count = _store_data(data, result_format, graph_id)
                _add_provenance(graph_id, endpoint_url, query)
                
                result["stored"] = True
                result["triple_count"] = triple_count
                result["graph_id"] = graph_id
            else:
                result["data"] = data
                
            return result
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "endpoint": endpoint_url,
            "query_type": query_type
        }

def describe_resource(
    endpoint_url: str,
    uri: str,
    result_format: str = "json-ld",
    store_result: bool = True,
    graph_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience wrapper for DESCRIBE queries.
    
    Args:
        endpoint_url: SPARQL endpoint URL
        uri: URI of the resource to describe
        result_format: Preferred result format
        store_result: Whether to store graph results in memory
        graph_id: Named graph ID for storage (defaults to the URI if None)
        
    Returns:
        Dictionary with query results and metadata
    """
    # Default to using URI as graph_id if not provided
    if graph_id is None:
        graph_id = uri
        
    # Construct DESCRIBE query
    query = f"DESCRIBE <{uri}>"
    
    # Execute query with describe type
    return sparql_query(
        endpoint_url=endpoint_url,
        query=query,
        query_type="DESCRIBE",
        result_format=result_format,
        store_result=store_result,
        graph_id=graph_id
    )

def _determine_accept_header(query_type: str, format: str) -> str:
    """Helper to determine the appropriate Accept header"""
    q = query_type.upper()
    if q in ("SELECT", "ASK"):
        if format == "xml":
            return "application/sparql-results+xml"
        return "application/sparql-results+json"
    if q in ("CONSTRUCT", "DESCRIBE"):
        # RDF serialization formats
        if format in ("json-ld", "jsonld"):
            return "application/ld+json"
        if format == "n-triples":
            return "application/n-triples"
        if format == "n-quads":
            return "application/n-quads"
        if format == "xml":
            return "application/rdf+xml"
        return "text/turtle"
    raise ValueError(f"Unknown query type: {query_type}")

def _store_data(data: str, format: str, graph_id: str) -> int:
    """Parse and store RDF data in memory"""
    ds = Dataset()
    
    # Parse data based on format
    if format in ('json-ld', 'jsonld'):
        ds.parse(data=data, format='json-ld')
    elif format == 'turtle':
        ds.parse(data=data, format='turtle')
    elif format == 'xml':
        ds.parse(data=data, format='xml')
    elif format == 'n-triples':
        ds.parse(data=data, format='nt')
    else:
        # Try multiple formats
        for fmt in ['json-ld', 'turtle', 'nt', 'xml']:
            try:
                ds.parse(data=data, format=fmt)
                break
            except Exception:
                continue
                
    # Serialize to N-Quads for ingestion
    nquads = ds.serialize(format='nquads')
    
    # Store in GraphManager
    gm = GraphManager(use_rdflib=True)
    gm.ingest_nquads(nquads, graph_id=graph_id)
    
    # Return the triple count
    return len(list(ds.quads((None, None, None, None))))

def _add_provenance(graph_id: str, endpoint_url: str, query: str) -> None:
    """Add provenance for the query and results"""
    from datetime import datetime
    
    timestamp = datetime.now().isoformat()
    
    # Create provenance triples using W3C PROV-O
    prov_data = f"""
    <{graph_id}> <http://www.w3.org/ns/prov#wasGeneratedBy> _:query_{timestamp.replace(":", "_")} .
    _:query_{timestamp.replace(":", "_")} <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/ns/prov#Activity> .
    _:query_{timestamp.replace(":", "_")} <http://www.w3.org/ns/prov#used> <{endpoint_url}> .
    _:query_{timestamp.replace(":", "_")} <http://www.w3.org/ns/prov#startedAtTime> "{timestamp}"^^<http://www.w3.org/2001/XMLSchema#dateTime> .
    _:query_{timestamp.replace(":", "_")} <http://www.w3.org/ns/prov#value> "{query.replace('"', '\\"')}"^^<http://www.w3.org/2001/XMLSchema#string> .
    """
    
    # Store provenance in a separate named graph
    gm = GraphManager(use_rdflib=True)
    gm.ingest_nquads(prov_data, graph_id=f"{graph_id}_prov")
```

### 2.2 Linked Data Fetching (fetch.py)

```python
from typing import Dict, Any, Optional
import requests
from rdflib import Dataset

from ...core.graph import GraphManager
from ...core.debug import get_logger
from .query import _store_data, _add_provenance

log = get_logger("tools.sparql.fetch")

def ld_fetch(
    uri: str,
    format: str = "json-ld",
    store_result: bool = True,
    graph_id: Optional[str] = None,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Fetch a Linked Data resource.
    
    Args:
        uri: URI to fetch
        format: Preferred format (json-ld, turtle, xml, n-triples)
        store_result: Whether to store in memory
        graph_id: Named graph ID for storage (defaults to URI if None)
        timeout: Request timeout in seconds
        
    Returns:
        Dictionary with resource data and metadata
    """
    # Default to using URI as graph_id
    if graph_id is None:
        graph_id = uri
        
    # Map format to Accept header
    accept_map = {
        'json-ld': 'application/ld+json',
        'turtle': 'text/turtle',
        'xml': 'application/rdf+xml',
        'n-triples': 'application/n-triples'
    }
    accept = accept_map.get(format, 'application/ld+json')
    headers = {'Accept': accept, 'User-Agent': 'cogitarelink-ld-fetch/0.1'}
    
    try:
        resp = requests.get(uri, headers=headers, timeout=timeout)
        resp.raise_for_status()
        data = resp.text
        
        result = {
            "success": True,
            "uri": uri,
            "format": format,
            "data_size": len(data)
        }
        
        # Optionally store in memory
        if store_result:
            triple_count = _store_data(data, format, graph_id)
            _add_provenance(graph_id, uri, f"FETCH {uri}")
            
            result["stored"] = True
            result["triple_count"] = triple_count
            result["graph_id"] = graph_id
        else:
            result["data"] = data
            
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "uri": uri,
            "format": format
        }
```

### 2.3 Endpoint Discovery (discover.py)

```python
from typing import Dict, Any, List, Optional
import requests
from rdflib import Graph, Namespace
from rdflib.namespace import RDF, VOID
from urllib.parse import urlparse

from ...core.debug import get_logger
from .query import sparql_query

log = get_logger("tools.sparql.discover")

def sparql_discover(
    endpoint_url: str,
    method: str = "all",
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Discover SPARQL endpoint capabilities.
    
    Args:
        endpoint_url: SPARQL endpoint URL
        method: Discovery method (void, service-description, introspection, all)
        timeout: Request timeout in seconds
        
    Returns:
        Dictionary with endpoint metadata
    """
    result = {
        "endpoint": endpoint_url,
        "success": True,
        "method": method,
        "prefixes": {}
    }
    
    # Try VoID discovery
    if method in ('void', 'all'):
        void_result = _discover_void(endpoint_url, timeout)
        if void_result:
            result.update(void_result)
    
    # Try service description
    if method in ('service-description', 'all'):
        service_result = _discover_service_description(endpoint_url, timeout)
        if service_result:
            result.update(service_result)
    
    # Try introspection
    if method in ('introspection', 'all'):
        introspection_result = _discover_introspection(endpoint_url, timeout)
        if introspection_result:
            result.update(introspection_result)
    
    # Extract common prefixes
    if 'samplePredicates' in result:
        result['prefixes'].update(_extract_prefixes(result['samplePredicates']))
    
    return result

def _discover_void(endpoint_url: str, timeout: int) -> Optional[Dict[str, Any]]:
    """Discover endpoint using VoID description"""
    try:
        # Look for VoID at .well-known/void
        url_parts = urlparse(endpoint_url)
        base_url = f"{url_parts.scheme}://{url_parts.netloc}"
        void_url = f"{base_url}/.well-known/void"
        
        resp = requests.get(void_url, timeout=timeout)
        if resp.status_code != 200:
            return None
            
        # Parse VoID description
        g = Graph()
        g.parse(data=resp.text, format='turtle')
        
        datasets = []
        void = Namespace("http://rdfs.org/ns/void#")
        
        for ds in g.subjects(RDF.type, void.Dataset):
            dataset_info = {'uri': str(ds)}
            
            # Extract sparqlEndpoint
            for endpoint in g.objects(ds, void.sparqlEndpoint):
                dataset_info['sparqlEndpoint'] = str(endpoint)
            
            # Extract triples count
            for triples in g.objects(ds, void.triples):
                dataset_info['triples'] = int(triples)
            
            # Extract data dumps
            for dump in g.objects(ds, void.dataDump):
                if 'dataDumps' not in dataset_info:
                    dataset_info['dataDumps'] = []
                dataset_info['dataDumps'].append(str(dump))
            
            datasets.append(dataset_info)
        
        return {
            "void_url": void_url,
            "datasets": datasets
        }
    
    except Exception as e:
        return {"void_error": str(e)}

def _discover_service_description(endpoint_url: str, timeout: int) -> Optional[Dict[str, Any]]:
    """Discover endpoint using SPARQL Service Description"""
    try:
        # Query for service description
        query = "DESCRIBE <" + endpoint_url + ">"
        
        resp = requests.get(
            endpoint_url,
            params={"query": query},
            headers={"Accept": "text/turtle"},
            timeout=timeout
        )
        
        if resp.status_code != 200:
            return None
            
        # Parse service description
        g = Graph()
        g.parse(data=resp.text, format='turtle')
        
        # Extract default and named graphs
        sd = Namespace("http://www.w3.org/ns/sparql-service-description#")
        
        default_graphs = []
        for dg in g.objects(None, sd.defaultGraph):
            default_graphs.append(str(dg))
        
        named_graphs = []
        for ng in g.objects(None, sd.namedGraph):
            # Get the actual graph name
            for name in g.objects(ng, sd.name):
                named_graphs.append(str(name))
        
        # Extract supported features
        features = []
        for feature in g.objects(None, sd.feature):
            features.append(str(feature))
        
        return {
            "defaultGraphs": default_graphs,
            "namedGraphs": named_graphs,
            "supportedFeatures": features
        }
    
    except Exception as e:
        return {"service_description_error": str(e)}

def _discover_introspection(endpoint_url: str, timeout: int) -> Optional[Dict[str, Any]]:
    """Discover endpoint using lightweight introspection queries"""
    try:
        # Query for some sample predicates
        predicate_query = "SELECT DISTINCT ?p WHERE { ?s ?p ?o } LIMIT 20"
        predicate_result = sparql_query(
            endpoint_url=endpoint_url,
            query=predicate_query,
            query_type="SELECT",
            result_format="json",
            timeout=timeout
        )
        
        if not predicate_result.get("success", False):
            return {"introspection_error": "Failed to query predicates"}
        
        # Extract predicates from result
        import json
        data = json.loads(predicate_result["data"])
        predicates = [b["p"]["value"] for b in data["results"]["bindings"]]
        
        # Query for some sample classes
        class_query = """
        SELECT DISTINCT ?type WHERE {
          ?s a ?type .
        } LIMIT 20
        """
        
        class_result = sparql_query(
            endpoint_url=endpoint_url,
            query=class_query,
            query_type="SELECT",
            result_format="json",
            timeout=timeout
        )
        
        classes = []
        if class_result.get("success", False):
            data = json.loads(class_result["data"])
            classes = [b["type"]["value"] for b in data["results"]["bindings"]]
        
        return {
            "samplePredicates": predicates,
            "sampleClasses": classes
        }
    
    except Exception as e:
        return {"introspection_error": str(e)}

def _extract_prefixes(uris: List[str]) -> Dict[str, str]:
    """Extract common namespace prefixes from URIs"""
    # Common prefixes to look for
    known_prefixes = {
        "http://www.w3.org/1999/02/22-rdf-syntax-ns#": "rdf",
        "http://www.w3.org/2000/01/rdf-schema#": "rdfs",
        "http://www.w3.org/2001/XMLSchema#": "xsd",
        "http://www.w3.org/2004/02/skos/core#": "skos",
        "http://www.w3.org/ns/prov#": "prov",
        "http://schema.org/": "schema",
        "http://purl.org/dc/terms/": "dcterms",
        "http://purl.org/dc/elements/1.1/": "dc",
        "http://xmlns.com/foaf/0.1/": "foaf",
        "http://www.wikidata.org/entity/": "wd",
        "http://www.wikidata.org/prop/direct/": "wdt",
        "http://www.wikidata.org/prop/": "p",
        "http://www.wikidata.org/prop/statement/": "ps",
        "http://www.wikidata.org/prop/qualifier/": "pq"
    }
    
    prefixes = {}
    
    # Check each URI against known prefixes
    for uri in uris:
        for namespace, prefix in known_prefixes.items():
            if uri.startswith(namespace):
                prefixes[prefix] = namespace
    
    # Try to derive other prefixes from URI patterns
    namespace_counts = {}
    for uri in uris:
        if '#' in uri:
            namespace = uri.split('#')[0] + '#'
            namespace_counts[namespace] = namespace_counts.get(namespace, 0) + 1
        else:
            # Take up to the last path segment
            parts = uri.split('/')
            if len(parts) > 3:  # More than just http://domain
                namespace = '/'.join(parts[:-1]) + '/'
                namespace_counts[namespace] = namespace_counts.get(namespace, 0) + 1
    
    # Add common namespaces that appear multiple times
    for namespace, count in namespace_counts.items():
        if count >= 3 and namespace not in known_prefixes.values():
            # Generate a prefix from the domain name
            domain = urlparse(namespace).netloc.split('.')[-2]
            if domain and domain not in prefixes.values():
                prefixes[domain] = namespace
    
    return prefixes
```

### 2.4 Transform Utilities (transform.py)

```python
from typing import Dict, Any, List
import json
import hashlib
from datetime import datetime

def sparql_json_to_jsonld(sparql_json: str, base_uri: str = None) -> str:
    """
    Convert SPARQL JSON results to JSON-LD format.
    
    Args:
        sparql_json: SPARQL results in JSON format
        base_uri: Base URI for the result set
        
    Returns:
        JSON-LD string
    """
    # Parse the SPARQL JSON
    try:
        data = json.loads(sparql_json)
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON input")
    
    # Prepare JSON-LD context with common prefixes
    context = {
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "xsd": "http://www.w3.org/2001/XMLSchema#",
        "schema": "http://schema.org/"
    }
    
    # Add prefixes based on terms in the results
    context.update(_extract_context_from_results(data))
    
    # Default base URI if not provided
    if not base_uri:
        base_uri = "urn:sparql:result:" + datetime.now().strftime("%Y%m%d%H%M%S")
    
    # Build the result graph
    graph = []
    
    # Process bindings if present
    bindings = data.get("results", {}).get("bindings", [])
    
    for i, binding in enumerate(bindings):
        # Create a unique ID for this result
        binding_str = json.dumps(binding, sort_keys=True)
        result_id = f"{base_uri}/result/{hashlib.md5(binding_str.encode()).hexdigest()}"
        
        # Create the result object
        result_obj = {
            "@id": result_id,
            "@type": "schema:SearchResult",
            "schema:position": i + 1
        }
        
        # Process each variable binding
        for var_name, value in binding.items():
            value_type = value.get("type", "literal")
            value_content = value.get("value", "")
            
            if value_type == "uri":
                # URI reference
                result_obj[var_name] = {"@id": value_content}
            elif value_type == "literal":
                # Plain literal
                if "xml:lang" in value:
                    result_obj[var_name] = {
                        "@value": value_content,
                        "@language": value.get("xml:lang")
                    }
                elif "datatype" in value:
                    result_obj[var_name] = {
                        "@value": value_content,
                        "@type": value.get("datatype")
                    }
                else:
                    result_obj[var_name] = value_content
            elif value_type == "bnode":
                # Blank node reference
                result_obj[var_name] = {"@id": "_:" + value_content}
        
        graph.append(result_obj)
    
    # Build the final JSON-LD document
    jsonld = {
        "@context": context,
        "@id": base_uri,
        "@type": "schema:SearchResultsPage",
        "schema:query": data.get("query", ""),
        "schema:timestamp": datetime.now().isoformat(),
        "schema:totalResults": len(bindings),
        "@graph": graph
    }
    
    # Handle ASK queries
    if "boolean" in data:
        jsonld["@type"] = "schema:AskResult"
        jsonld["schema:result"] = data["boolean"]
    
    return json.dumps(jsonld, indent=2)

def _extract_context_from_results(data: Dict[str, Any]) -> Dict[str, str]:
    """Extract namespaces from result values to build context"""
    context = {}
    common_namespaces = {
        "http://www.wikidata.org/entity/": "wd",
        "http://www.wikidata.org/prop/direct/": "wdt",
        "http://dbpedia.org/resource/": "dbr",
        "http://dbpedia.org/ontology/": "dbo",
        "http://purl.org/dc/terms/": "dcterms",
        "http://xmlns.com/foaf/0.1/": "foaf"
    }
    
    # Look through bindings for URIs
    bindings = data.get("results", {}).get("bindings", [])
    for binding in bindings:
        for value in binding.values():
            if value.get("type") == "uri":
                uri = value.get("value", "")
                
                # Check against common namespaces
                for namespace, prefix in common_namespaces.items():
                    if uri.startswith(namespace) and prefix not in context:
                        context[prefix] = namespace
    
    return context
```

### 2.5 Tool Specifications (specs.py)

```python
from typing import Dict, Any, List

# SPARQL Query Tool Specification
SPARQL_QUERY_SPEC: Dict[str, Any] = {
    "name": "sparql_query",
    "description": "Execute SPARQL 1.1 queries against endpoints and optionally store results in memory",
    "parameters": {
        "type": "object",
        "properties": {
            "endpoint_url": {
                "type": "string",
                "description": "The URL of the SPARQL endpoint"
            },
            "query": {
                "type": "string", 
                "description": "SPARQL query text (SELECT, ASK, CONSTRUCT, or DESCRIBE)"
            },
            "query_type": {
                "type": "string",
                "enum": ["SELECT", "ASK", "CONSTRUCT", "DESCRIBE"],
                "description": "The type of SPARQL query",
                "default": "SELECT"
            },
            "result_format": {
                "type": "string",
                "enum": ["json", "xml", "turtle", "n-triples", "json-ld"],
                "description": "Preferred response format",
                "default": "json"
            },
            "store_result": {
                "type": "boolean",
                "description": "Whether to store the results in memory",
                "default": False
            },
            "graph_id": {
                "type": "string",
                "description": "Optional ID for the named graph to store results in"
            }
        },
        "required": ["endpoint_url", "query"]
    }
}

# Describe Resource Tool Specification
DESCRIBE_RESOURCE_SPEC: Dict[str, Any] = {
    "name": "describe_resource",
    "description": "Fetch complete data about a resource using SPARQL DESCRIBE",
    "parameters": {
        "type": "object",
        "properties": {
            "endpoint_url": {
                "type": "string",
                "description": "The URL of the SPARQL endpoint"
            },
            "uri": {
                "type": "string",
                "description": "URI of the resource to describe"
            },
            "result_format": {
                "type": "string",
                "enum": ["json-ld", "turtle", "n-triples", "xml"],
                "description": "Preferred response format",
                "default": "json-ld"
            },
            "store_result": {
                "type": "boolean",
                "description": "Whether to store the results in memory",
                "default": True
            },
            "graph_id": {
                "type": "string",
                "description": "Optional ID for the named graph to store results in (defaults to URI)"
            }
        },
        "required": ["endpoint_url", "uri"]
    }
}

# SPARQL Discover Tool Specification
SPARQL_DISCOVER_SPEC: Dict[str, Any] = {
    "name": "sparql_discover",
    "description": "Discover SPARQL endpoint capabilities and metadata",
    "parameters": {
        "type": "object",
        "properties": {
            "endpoint_url": {
                "type": "string",
                "description": "The URL of the SPARQL endpoint"
            },
            "method": {
                "type": "string",
                "enum": ["void", "service-description", "introspection", "all"],
                "description": "Discovery method",
                "default": "all"
            }
        },
        "required": ["endpoint_url"]
    }
}

# Linked Data Fetch Tool Specification
LD_FETCH_SPEC: Dict[str, Any] = {
    "name": "ld_fetch",
    "description": "Fetch and parse Linked Data from a URI",
    "parameters": {
        "type": "object",
        "properties": {
            "uri": {
                "type": "string",
                "description": "URI to fetch"
            },
            "format": {
                "type": "string",
                "enum": ["json-ld", "turtle", "xml", "n-triples"],
                "description": "Preferred format",
                "default": "json-ld"
            },
            "store_result": {
                "type": "boolean",
                "description": "Whether to store in memory",
                "default": True
            },
            "graph_id": {
                "type": "string",
                "description": "Optional ID for the named graph to store results in (defaults to URI)"
            }
        },
        "required": ["uri"]
    }
}

# Export all specifications in a list for registration
SPARQL_TOOL_SPECS: List[Dict[str, Any]] = [
    SPARQL_QUERY_SPEC,
    DESCRIBE_RESOURCE_SPEC,
    SPARQL_DISCOVER_SPEC,
    LD_FETCH_SPEC
]
```

### 2.6 Package Initialization (__init__.py)

```python
"""
SPARQL and Linked Data Tools for CogitareLink
These tools allow agents to discover, query, and integrate data from
SPARQL endpoints and Linked Data resources.
"""

from .query import sparql_query, describe_resource
from .discover import sparql_discover
from .fetch import ld_fetch
from .specs import (
    SPARQL_QUERY_SPEC, 
    DESCRIBE_RESOURCE_SPEC, 
    SPARQL_DISCOVER_SPEC, 
    LD_FETCH_SPEC,
    SPARQL_TOOL_SPECS
)

# Export all functions and specifications
__all__ = [
    'sparql_query',
    'describe_resource',
    'sparql_discover',
    'ld_fetch',
    'SPARQL_QUERY_SPEC',
    'DESCRIBE_RESOURCE_SPEC', 
    'SPARQL_DISCOVER_SPEC',
    'LD_FETCH_SPEC',
    'SPARQL_TOOL_SPECS'
]
```

## 3. Tool Registration and Agent Integration

### 3.1 Tool Registration in CogitareLink

Add the following to an appropriate module in CogitareLink (e.g., `cogitarelink/core/agent.py` or similar):

```python
from ..tools.sparql import (
    sparql_query,
    describe_resource,
    sparql_discover,
    ld_fetch,
    SPARQL_TOOL_SPECS
)

def register_sparql_tools(registry):
    """Register SPARQL and Linked Data tools with the agent's tool registry"""
    registry.register_tool(
        "sparql_query",
        sparql_query,
        SPARQL_TOOL_SPECS[0]
    )
    
    registry.register_tool(
        "describe_resource",
        describe_resource,
        SPARQL_TOOL_SPECS[1]
    )
    
    registry.register_tool(
        "sparql_discover",
        sparql_discover,
        SPARQL_TOOL_SPECS[2]
    )
    
    registry.register_tool(
        "ld_fetch",
        ld_fetch,
        SPARQL_TOOL_SPECS[3]
    )
```

### 3.2 Agent Prompt Engineering

Include the following as guidance for the agent using these tools:

```python
SPARQL_AGENT_GUIDANCE = """
# SPARQL and Linked Data Tools Guide

You have access to tools that allow you to discover, query, and integrate data from SPARQL endpoints and Linked Data resources.

## Discovery Workflow

When encountering a new SPARQL endpoint:
1. Use sparql_discover to identify capabilities, prefixes, and graphs
2. Start with simple queries to understand the data structure
3. Use the discovered prefixes in subsequent queries

Example: 
```
sparql_discover(
  endpoint_url="https://qlever.cs.uni-freiburg.de/api/wikidata"
)
```

## Query Patterns

### For fact finding (SELECT):
```
sparql_query(
  endpoint_url="https://qlever.cs.uni-freiburg.de/api/wikidata",
  query="SELECT ?item ?itemLabel WHERE { ?item wdt:P31 wd:Q5 . OPTIONAL { ?item rdfs:label ?itemLabel . FILTER(LANG(?itemLabel) = 'en') } } LIMIT 5",
  query_type="SELECT",
  store_result=False
)
```

### For retrieving complete entity data (DESCRIBE):
```
describe_resource(
  endpoint_url="https://qlever.cs.uni-freiburg.de/api/wikidata",
  uri="http://www.wikidata.org/entity/Q42",
  store_result=True
)
```
Tje 
### For custom graph patterns (CONSTRUCT):
```
sparql_query(
  endpoint_url="https://qlever.cs.uni-freiburg.de/api/wikidata",
  query="CONSTRUCT { ?person <http://schema.org/name> ?name . ?person <http://schema.org/birthDate> ?birth . } WHERE { ?person wdt:P31 wd:Q5 . ?person wdt:P569 ?birth . OPTIONAL { ?person rdfs:label ?name . FILTER(LANG(?name) = 'en') } } LIMIT 5",
  query_type="CONSTRUCT",
  store_result=True,
  graph_id="famous_people"
)
```

### For fetching linked data directly:
```
ld_fetch(
  uri="https://www.wikidata.org/wiki/Special:EntityData/Q42.jsonld",
  format="json-ld",
  store_result=True
)
```

## Best Practices

1. Start with DISCOVERY to understand the endpoint
2. Use PREFIX declarations in all queries
3. Include OPTIONAL patterns for potentially missing properties
4. Add FILTER(LANG(?label) = 'en') for readable labels
5. Set appropriate LIMIT to avoid large result sets
6. Use graph_id to organize data in memory
7. Use CONSTRUCT for creating custom knowledge graphs
8. Follow external identifiers to enrich your knowledge
"""
```

## 4. Example Tool Usage

Here are a few examples of how to use these tools:

### 4.1 Entity Discovery Workflow

```python
# 1. Discover endpoint capabilities
discovery_result = sparql_discover(
    endpoint_url="https://qlever.cs.uni-freiburg.de/api/wikidata"
)

# 2. Find entity by name
entity_result = sparql_query(
    endpoint_url="https://qlever.cs.uni-freiburg.de/api/wikidata",
    query="""
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?entity WHERE {
      ?entity rdfs:label "Douglas Adams"@en .
    }
    LIMIT 1
    """,
    query_type="SELECT"
)

# 3. Fetch full entity data
import json
bindings = json.loads(entity_result["data"])["results"]["bindings"]
entity_uri = bindings[0]["entity"]["value"]  # e.g. http://www.wikidata.org/entity/Q42

# 4. Retrieve complete entity description
entity_data = describe_resource(
    endpoint_url="https://qlever.cs.uni-freiburg.de/api/wikidata",
    uri=entity_uri,
    store_result=True
)
```

### 4.2 Linked Data Traversal

```python
# 1. Find external identifier
external_id_result = sparql_query(
    endpoint_url="https://qlever.cs.uni-freiburg.de/api/wikidata",
    query="""
    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    SELECT ?entity ?id WHERE {
      ?entity wdt:P214 ?id .  # VIAF ID
    }
    LIMIT 1
    """,
    query_type="SELECT"
)

# 2. Construct external resource URL
import json
bindings = json.loads(external_id_result["data"])["results"]["bindings"]
viaf_id = bindings[0]["id"]["value"]
viaf_url = f"https://viaf.org/viaf/{viaf_id}/rdf.xml"

# 3. Fetch the external resource
external_data = ld_fetch(
    uri=viaf_url,
    format="xml",
    store_result=True,
    graph_id=f"viaf_{viaf_id}"
)
```

## 5. Testing Strategy

### 5.1 Unit Tests

Create unit tests for:

1. **Format Conversion**:
   - Test SPARQL JSON → JSON-LD conversion
   - Test RDF format detection and parsing

2. **Query Execution**:
   - Test various query types against public endpoints
   - Test error handling for malformed queries

3. **Discovery**:
   - Test extraction of prefixes from URIs
   - Test VoID, service description parsing

### 5.2 Integration Tests

Create integration tests for:

1. **Memory Integration**:
   - Test that triples are correctly stored in GraphManager
   - Verify provenance tracking

2. **Agent Interaction**:
   - Test tool registration with agent
   - Verify function specifications

### 5.3 End-to-End Tests

Create scenario-based tests:

1. **Black Cat Scenario**:
   - Execute the Black Cat workflow end-to-end
   - Verify correct extraction of properties

2. **Follow-Your-Nose**:
   - Test cross-endpoint data integration
   - Verify entity linking

## 6. Documentation

### 6.1 Tool Documentation

Document each tool function with:

- Clear function purpose
- All parameters with type information
- Return value structure
- Example usage
- Error handling

### 6.2 Agent Guidance

Create detailed guidance for agents on:

- When to use each tool
- How to construct effective queries
- Query patterns for common tasks
- Error recovery strategies
- Best practices for memory management

## 7. Deployment and Integration

### 7.1 Package Requirements

Add to CogitareLink's requirements:

```
requests>=2.28.0
rdflib>=6.2.0
```

### 7.2 Configuration Options

Add configuration options for:

- Default timeout values
- Rate limiting
- Caching behavior
- Standard prefixes

### 7.3 Versioning and Compatibility

Ensure compatibility with:

- Various SPARQL endpoint implementations
- Different RDF serialization formats
- CogitareLink's GraphManager interface

## Conclusion

This implementation specification provides a detailed blueprint for integrating SPARQL and Linked Data tools into the CogitareLink framework. By following this approach, developers can create a powerful, agent-driven system for exploring, querying, and integrating semantic web resources into CogitareLink's memory model.

The design emphasizes flexibility, discoverability, and effective agent-tool interaction, embodying the "Software 2.0" principles where intelligence resides in the agent rather than in complex procedural code.
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
# # SPARQL Tools for Semantic Memory
# > Tools for working with SPARQL and Linked Data in CogitareLink

# %%
#| default_exp tools.sparql
# SYNC_TEST

# %%
#| export
from __future__ import annotations
import json
import re
import httpx
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
from rdflib import Graph
from rdflib.namespace import RDF
from cogitarelink.reason.prov import wrap_patch_with_prov
from cogitarelink.core.graph import GraphManager
_HAS_RDFLIB = True

from cogitarelink.core.debug import get_logger
from cogitarelink.core.graph import GraphManager

# %%
#| export
log = get_logger("sparql")

 # %%
 #| export
# Parser/Validator/Agent scaffolding removed: only core SPARQL functions remain


# %%
#| export
def sparql_query(
    endpoint_url: str,
    query: str,
    query_type: str = "SELECT",
    result_format: str = "json",
    store_result: bool = False,
    graph_id: Optional[str] = None,
    timeout: int = 30,
) -> Dict[str, Any]:
    """
    Execute a SPARQL query against a SPARQL 1.1 endpoint.

    Args:
        endpoint_url: URL of the SPARQL endpoint
        query: SPARQL query string (SELECT, ASK, CONSTRUCT, DESCRIBE)
        query_type: One of 'SELECT', 'ASK', 'CONSTRUCT', 'DESCRIBE'
        result_format: Desired result format (e.g. 'json', 'turtle', 'json-ld')
        store_result: Whether to ingest CONSTRUCT/DESCRIBE results into memory
        graph_id: Named graph identifier for stored results
        timeout: HTTP request timeout in seconds

    Returns:
        A dict containing raw results or ingestion metadata.
    """
    if not _HAS_RDFLIB:
        raise ImportError("RDFLib and SPARQLWrapper are required for SPARQL querying")
    
    # Default graph_id if not provided and storage is requested
    if store_result and graph_id is None:
        graph_id = f"sparql_{endpoint_url.replace('://', '_').replace('/', '_')}"
    
    # Set up SPARQLWrapper with endpoint and timeout
    sparql = SPARQLWrapper(endpoint_url)
    sparql.setTimeout(timeout)
    
    # Set the query
    sparql.setQuery(query)
    
    # Set result format based on query type and requested format
    if query_type.upper() in ("SELECT", "ASK"):
        if result_format.lower() == "json":
            sparql.setReturnFormat(JSON)
        elif result_format.lower() == "xml":
            sparql.setReturnFormat(XML)
        elif result_format.lower() == "csv":
            sparql.setReturnFormat(CSV)
        elif result_format.lower() == "tsv":
            sparql.setReturnFormat(TSV)
        else:
            log.warning(f"Unsupported format {result_format} for {query_type}, using JSON")
            sparql.setReturnFormat(JSON)
            result_format = "json"
    else:  # CONSTRUCT or DESCRIBE
        if result_format.lower() == "json-ld":
            sparql.addCustomParameter("format", "application/ld+json")
        elif result_format.lower() == "turtle":
            sparql.addCustomParameter("format", "text/turtle")
        elif result_format.lower() == "n-triples":
            sparql.addCustomParameter("format", "application/n-triples")
        elif result_format.lower() == "xml":
            sparql.addCustomParameter("format", "application/rdf+xml")
    
    try:
        # Execute the query
        results = sparql.query()
        
        # Process results based on query type
        if query_type.upper() in ("SELECT", "ASK"):
            if result_format.lower() == "json":
                data = results.convert()
                
                # For ASK queries, extract the boolean result
                if query_type.upper() == "ASK":
                    result = {
                        "success": True,
                        "query_type": "ASK",
                        "result": data.get("boolean", False),
                        "format": "json"
                    }
                else:  # SELECT
                    result = {
                        "success": True,
                        "query_type": "SELECT",
                        "results": data.get("results", {}).get("bindings", []),
                        "format": "json",
                        "vars": data.get("head", {}).get("vars", [])
                    }
            else:
                # Raw string result for other formats
                data = results.response.read().decode('utf-8')
                result = {
                    "success": True,
                    "query_type": query_type,
                    "data": data,
                    "format": result_format
                }
        else:  # CONSTRUCT or DESCRIBE
            # Get the raw RDF content
            content = results.response.read().decode('utf-8')
            
            result = {
                "success": True,
                "query_type": query_type,
                "format": result_format,
                "data_size": len(content)
            }
            
            # Store result if requested
            if store_result:
                # Parse the RDF content
                g = Graph()
                
                if result_format.lower() == "json-ld":
                    g.parse(data=content, format="json-ld")
                elif result_format.lower() == "turtle":
                    g.parse(data=content, format="turtle")
                elif result_format.lower() == "n-triples":
                    g.parse(data=content, format="nt")
                elif result_format.lower() == "xml":
                    g.parse(data=content, format="xml")
                
                # Get triples count
                triple_count = len(g)
                
                # Store in GraphManager (if available)
                gm = GraphManager(use_rdflib=True)
                
                # Convert to N-Quads for ingestion
                nquads = g.serialize(format="nquads")
                gm.ingest_nquads(nquads, graph_id=graph_id)
                
                result["stored"] = True
                result["triple_count"] = triple_count
                result["graph_id"] = graph_id
            else:
                result["data"] = content
                
        return result
        
    except Exception as e:
        log.error(f"SPARQL query error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "query_type": query_type,
            "endpoint": endpoint_url
        }


# %%
#| export
def ld_fetch(
    uri: str,
    format: str = "json-ld",
    store_result: bool = True,
    graph_id: Optional[str] = None,
    timeout: int = 30,
) -> Dict[str, Any]:
    """
    Fetch a Linked Data resource and ingest into memory.

    Args:
        uri: The resource URI to fetch
        format: Preferred RDF format ('json-ld', 'turtle', 'xml', 'n-triples')
        store_result: Whether to ingest the fetched data into memory
        graph_id: Named graph identifier for stored results
        timeout: HTTP request timeout in seconds

    Returns:
        A dict with fetch metadata and ingestion counts.
    """
    if not _HAS_RDFLIB:
        raise ImportError("RDFLib is required for processing Linked Data")
    
    # Default to using URI as graph_id if not provided and storage is requested
    if store_result and graph_id is None:
        graph_id = uri
    
    # Map format to Accept header value
    format_to_accept = {
        "json-ld": "application/ld+json",
        "turtle": "text/turtle",
        "xml": "application/rdf+xml",
        "n-triples": "application/n-triples"
    }
    
    # Prepare headers with content negotiation
    headers = {
        "Accept": format_to_accept.get(format.lower(), "application/ld+json"),
        "User-Agent": "cogitarelink-ld-fetch/0.1"
    }
    
    try:
        # Use httpx for the request
        response = httpx.get(uri, headers=headers, timeout=timeout, follow_redirects=True)
        response.raise_for_status()
        
        content = response.text
        content_type = response.headers.get("content-type", "").split(";")[0].strip()
        
        # Base result structure
        result = {
            "success": True,
            "uri": uri,
            "format": format,
            "content_type": content_type,
            "data_size": len(content),
            "status_code": response.status_code
        }
        
        # Store the result if requested
        if store_result:
            # Parse based on content type or requested format
            g = Graph()
            
            # Try to determine actual format based on content type
            parse_format = None
            if "json" in content_type:
                parse_format = "json-ld"
            elif "turtle" in content_type:
                parse_format = "turtle"
            elif "rdf+xml" in content_type:
                parse_format = "xml"
            elif "n-triples" in content_type:
                parse_format = "nt"
            else:
                # Fall back to requested format
                parse_format = {
                    "json-ld": "json-ld", 
                    "turtle": "turtle", 
                    "xml": "xml", 
                    "n-triples": "nt"
                }.get(format.lower(), "json-ld")
            
            try:
                # Parse the content
                g.parse(data=content, format=parse_format)
                
                # Get triples count
                triple_count = len(g)
                
                # Store in GraphManager
                gm = GraphManager(use_rdflib=True)
                
                # Convert to N-Quads for ingestion
                nquads = g.serialize(format="nquads")
                gm.ingest_nquads(nquads, graph_id=graph_id)
                
                result["stored"] = True
                result["triple_count"] = triple_count
                result["graph_id"] = graph_id
                
            except Exception as parse_error:
                # If parsing fails, try alternative formats
                log.warning(f"Failed to parse as {parse_format}, trying alternatives: {str(parse_error)}")
                for alt_format in ["json-ld", "turtle", "xml", "nt"]:
                    if alt_format == parse_format:
                        continue
                    
                    try:
                        g = Graph()
                        g.parse(data=content, format=alt_format)
                        
                        # Get triples count
                        triple_count = len(g)
                        
                        # Store in GraphManager
                        gm = GraphManager(use_rdflib=True)
                        
                        # Convert to N-Quads for ingestion
                        nquads = g.serialize(format="nquads")
                        gm.ingest_nquads(nquads, graph_id=graph_id)
                        
                        result["stored"] = True
                        result["triple_count"] = triple_count
                        result["graph_id"] = graph_id
                        result["actual_format"] = alt_format
                        
                        break
                    except Exception:
                        continue
                
                if "stored" not in result:
                    result["success"] = False
                    result["error"] = f"Failed to parse content in any supported format: {str(parse_error)}"
                    # Include the raw content if parsing failed
                    result["data"] = content
        else:
            # Include the raw content if not storing
            result["data"] = content
            
        return result
        
    except Exception as e:
        log.error(f"LD fetch error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "uri": uri
        }


# %%
#| export
def sparql_json_to_jsonld(
    sparql_json: str,
    base_uri: Optional[str] = None,
) -> str:
    """
    Convert SPARQL SELECT/ASK JSON results into a JSON-LD document.

    Args:
        sparql_json: JSON string from a SELECT/ASK query
        base_uri: Optional base URI for the result document

    Returns:
        A JSON-LD string representing the result set.
    """
    
    import json
    from datetime import datetime
    import hashlib
    
    # Parse the SPARQL JSON
    try:
        if isinstance(sparql_json, str):
            data = json.loads(sparql_json)
        else:
            # Assume it's already a dict
            data = sparql_json
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON input")
    
    # Generate a default base URI if not provided
    if not base_uri:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        base_uri = f"urn:sparql:result:{timestamp}"
    
    # Prepare JSON-LD context with common prefixes
    context = {
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "xsd": "http://www.w3.org/2001/XMLSchema#",
        "schema": "http://schema.org/",
        "sparql": "http://www.w3.org/2005/sparql-results#"
    }
    
    # Handle ASK query results
    if "boolean" in data:
        jsonld = {
            "@context": context,
            "@id": base_uri,
            "@type": "sparql:AskResult",
            "sparql:boolean": data["boolean"],
            "schema:timestamp": datetime.now().isoformat()
        }
        return json.dumps(jsonld, indent=2)
    
    # Handle SELECT query results
    bindings = data.get("results", {}).get("bindings", [])
    vars_list = data.get("head", {}).get("vars", [])
    
    # Build the result graph as JSON-LD
    graph = []
    
    # Process each binding (result row)
    for i, binding in enumerate(bindings):
        # Create a unique ID for this result row
        row_hash = hashlib.md5(json.dumps(binding, sort_keys=True).encode()).hexdigest()
        result_id = f"{base_uri}/result/{row_hash}"
        
        # Create the result row object
        result_obj = {
            "@id": result_id,
            "@type": "sparql:ResultRow",
            "schema:position": i + 1
        }
        
        # Map each variable binding
        for var_name, value in binding.items():
            value_type = value.get("type", "literal")
            value_content = value.get("value", "")
            
            if value_type == "uri":
                # URI reference
                result_obj[var_name] = {"@id": value_content}
            elif value_type == "literal":
                # Literal with potential language or datatype
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
                # Blank node
                result_obj[var_name] = {"@id": "_:" + value_content}
        
        graph.append(result_obj)
    
    # Create the final JSON-LD document
    jsonld = {
        "@context": context,
        "@id": base_uri,
        "@type": "sparql:ResultSet",
        "sparql:resultVariable": vars_list,
        "schema:totalResults": len(bindings),
        "schema:timestamp": datetime.now().isoformat(),
        "@graph": graph
    }
    
    return json.dumps(jsonld, indent=2)


# %%
#| export
 #| export
def sparql_discover(
    endpoint_url: str,
    timeout: int = 30,
) -> Dict[str, Any]:
    """
    Discover a small sample of predicates via a lightweight SPARQL introspection query.
    """
    introspect = (
        "SELECT DISTINCT ?p WHERE { ?s ?p ?o } LIMIT 20"
    )
    res = sparql_query(
        endpoint_url=endpoint_url,
        query=introspect,
        query_type="SELECT",
        result_format="json",
        store_result=False,
        timeout=timeout
    )
    preds = [b.get("p", {}).get("value") for b in res.get("results", [])]
    return {"endpoint": endpoint_url, "predicates": preds}

def _discover_void(endpoint_url: str, timeout: int) -> Optional[Dict[str, Any]]:
    """Discover endpoint using VoID description."""
    try:
        from urllib.parse import urlparse
        import httpx
        
        # Try to find VoID at .well-known/void
        url_parts = urlparse(endpoint_url)
        base_url = f"{url_parts.scheme}://{url_parts.netloc}"
        void_url = f"{base_url}/.well-known/void"
        
        # Attempt to fetch VoID description
        response = httpx.get(void_url, timeout=timeout, follow_redirects=True)
        if response.status_code != 200:
            return None
        
        # Parse VoID description
        g = Graph()
        g.parse(data=response.text, format="turtle")
        
        datasets = []
        
        # VoID namespace
        VOID = Namespace("http://rdfs.org/ns/void#")
        
        # Extract dataset information
        for ds in g.subjects(RDF.type, VOID.Dataset):
            dataset_info = {'uri': str(ds)}
            
            # Extract SPARQL endpoint
            for endpoint in g.objects(ds, VOID.sparqlEndpoint):
                dataset_info['sparql_endpoint'] = str(endpoint)
            
            # Extract triples count
            for triples in g.objects(ds, VOID.triples):
                dataset_info['triples'] = int(triples)
            
            # Extract data dumps
            data_dumps = []
            for dump in g.objects(ds, VOID.dataDump):
                data_dumps.append(str(dump))
            
            if data_dumps:
                dataset_info['data_dumps'] = data_dumps
                
            datasets.append(dataset_info)
        
        return {
            "void_url": void_url,
            "datasets": datasets
        }
    except Exception as e:
        log.warning(f"VoID discovery failed: {str(e)}")
        return None

def _discover_service_description(endpoint_url: str, timeout: int) -> Optional[Dict[str, Any]]:
    """Discover endpoint using SPARQL Service Description."""
    try:
        import httpx
        
        # Construct SPARQL query for service description
        query = f"DESCRIBE <{endpoint_url}>"
        
        # Set appropriate headers for Turtle format
        headers = {
            "Accept": "text/turtle",
            "User-Agent": "cogitarelink-sparql-discover/0.1"
        }
        
        # Request parameters
        params = {"query": query}
        
        # Make the request
        response = httpx.get(
            endpoint_url,
            params=params,
            headers=headers,
            timeout=timeout,
            follow_redirects=True
        )
        
        if response.status_code != 200:
            return None
        
        # Parse service description
        g = Graph()
        g.parse(data=response.text, format="turtle")
        
        # Service description namespace
        SD = Namespace("http://www.w3.org/ns/sparql-service-description#")
        
        # Extract default and named graphs
        default_graphs = []
        for dg in g.objects(None, SD.defaultGraph):
            default_graphs.append(str(dg))
        
        named_graphs = []
        for ng in g.objects(None, SD.namedGraph):
            # Get the actual graph name
            for name in g.objects(ng, SD.name):
                named_graphs.append(str(name))
        
        # Extract supported features
        features = []
        for feature in g.objects(None, SD.feature):
            features.append(str(feature))
        
        return {
            "default_graphs": default_graphs,
            "named_graphs": named_graphs,
            "supported_features": features
        }
    except Exception as e:
        log.warning(f"Service description discovery failed: {str(e)}")
        return None

def _discover_introspection(endpoint_url: str, timeout: int) -> Optional[Dict[str, Any]]:
    """Discover endpoint using lightweight introspection queries."""
    try:
        # Query for sample predicates
        predicate_query = """
        SELECT DISTINCT ?p WHERE { 
            ?s ?p ?o 
        } LIMIT 20
        """
        
        predicate_result = sparql_query(
            endpoint_url=endpoint_url,
            query=predicate_query,
            query_type="SELECT",
            result_format="json",
            timeout=timeout
        )
        
        if not predicate_result.get("success", False):
            return None
        
        # Extract predicates
        predicates = []
        for binding in predicate_result.get("results", []):
            if "p" in binding and "value" in binding["p"]:
                predicates.append(binding["p"]["value"])
        
        # Query for sample classes
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
        
        # Extract classes
        classes = []
        if class_result.get("success", False):
            for binding in class_result.get("results", []):
                if "type" in binding and "value" in binding["type"]:
                    classes.append(binding["type"]["value"])
        
        return {
            "sample_predicates": predicates,
            "sample_classes": classes
        }
    except Exception as e:
        log.warning(f"Introspection discovery failed: {str(e)}")
        return None

 # Prefix extraction helper removed: agents should derive prefixes at runtime if needed


# %%
#| export
def check_query_patterns(query: str) -> Dict[str, Any]:
    """
    Basic syntax and safety checks for a SPARQL query.
    Uses RDFlib to validate syntax, and warns if SELECT/CONSTRUCT queries lack a LIMIT.
    """
    if not _HAS_RDFLIB:
        raise ImportError("RDFLib is required for SPARQL query analysis")
    from rdflib.plugins.sparql.parser import parseQuery
    try:
        # Syntax validation
        parseQuery(query)
        # Determine query type
        qt = "UNKNOWN"
        if re.search(r"\bSELECT\b", query, re.IGNORECASE):
            qt = "SELECT"
        elif re.search(r"\bASK\b", query, re.IGNORECASE):
            qt = "ASK"
        elif re.search(r"\bCONSTRUCT\b", query, re.IGNORECASE):
            qt = "CONSTRUCT"
        elif re.search(r"\bDESCRIBE\b", query, re.IGNORECASE):
            qt = "DESCRIBE"
        # Prepare response
        warnings: List[Dict[str, Any]] = []
        suggestions: List[str] = []
        if qt in ("SELECT", "CONSTRUCT") and "LIMIT" not in query.upper():
            warnings.append({
                "type": "missing_limit",
                "message": "Query does not include a LIMIT clause, which could return too many results",
                "severity": "medium"
            })
            suggestions.append("Add a LIMIT clause to avoid potentially large result sets.")
        return {
            "success": True,
            "query_type": qt,
            "warnings": warnings,
            "suggestions": suggestions
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }



# %%
#| export
def generate_query_fixes(
    query: str,
    validation_result: Dict[str, Any],
) -> str:
    """
    Generate suggested fixes for a SPARQL query based on validation results.

    Args:
        query: Original SPARQL query string
        validation_result: Results from validate_query_against_ontology or check_query_patterns

    Returns:
        A dict with fix suggestions and explanations.
    """
    if not _HAS_RDFLIB:
        raise ImportError("RDFLib is required for SPARQL query analysis")
    
    result = {
        "success": True,
        "needs_fixes": False,
        "original_query": query,
        "fixed_query": query,
        "fix_explanations": [],
        "guidance": []
    }
    
    # Check if validation result indicates issues to fix
    has_issues = False
    
    # Check for issues from check_query_patterns
    if "warnings" in validation_result and validation_result.get("warnings"):
        has_issues = True
        result["needs_fixes"] = True
        
        # Work with a mutable copy of the query
        fixed_query = query
        
        # Apply fixes based on warning types
        for warning in validation_result["warnings"]:
            warning_type = warning.get("type", "")
            message = warning.get("message", "")
            
            if warning_type == "missing_limit":
                # Add a LIMIT clause if missing
                if not re.search(r'\bLIMIT\b\s+\d+', fixed_query, re.IGNORECASE):
                    # Find where to insert the LIMIT
                    if re.search(r'\bORDER\s+BY\b', fixed_query, re.IGNORECASE):
                        # Insert after ORDER BY clause
                        fixed_query = re.sub(
                            r'(\bORDER\s+BY\b.+?)(\s*})$', 
                            r'\1 LIMIT 100\2', 
                            fixed_query, 
                            flags=re.IGNORECASE | re.DOTALL
                        )
                    else:
                        # Insert before the final closing brace
                        fixed_query = re.sub(
                            r'(\s*})$', 
                            r' LIMIT 100\1', 
                            fixed_query, 
                            flags=re.DOTALL
                        )
                    
                    result["fix_explanations"].append("Added LIMIT 100 clause to prevent large result sets.")
                    result["guidance"].append("Adjust the LIMIT value based on how many results you need.")
            
            elif warning_type == "unbound_variables":
                # Specific handling requires more context about the query structure
                # Just provide guidance for now
                result["fix_explanations"].append(f"Unbound variables detected: {message}")
                result["guidance"].append("Add triple patterns in the WHERE clause to bind all variables used in the SELECT clause.")
            
            elif warning_type == "cartesian_product":
                # Guidance only, as fixing requires domain knowledge
                result["fix_explanations"].append("Cartesian product detected in query.")
                result["guidance"].append("Add join conditions between disconnected parts of your query to avoid performance issues.")
            
            elif warning_type == "literal_without_filter":
                # Suggest using FILTER with regex for literals
                literals = re.findall(r'([\'"]\w+[\'"])', fixed_query)
                if literals:
                    example_literal = literals[0].strip('\'"')
                    result["fix_explanations"].append("Fixed literals to use FILTER with case-insensitive matching.")
                    result["guidance"].append(
                        f"Consider using patterns like: FILTER(REGEX(str(?var), \"{example_literal}\", \"i\"))"
                    )
        
        # Update the fixed query if changes were made
        if fixed_query != query:
            result["fixed_query"] = fixed_query
    
    # Check for issues from validate_query_against_ontology
    if "violations" in validation_result and validation_result.get("violations"):
        has_issues = True
        result["needs_fixes"] = True
        
        # Process ontology validation issues
        violations = validation_result.get("violations", [])
        for violation in violations:
            # Extract meaningful parts of the violation
            domain_issue = re.search(r'domain.*?\b(\w+:\w+)\b', violation, re.IGNORECASE)
            range_issue = re.search(r'range.*?\b(\w+:\w+)\b', violation, re.IGNORECASE)
            undefined_issue = re.search(r'Property\s+(\S+)\s+is not defined', violation, re.IGNORECASE)
            
            if domain_issue:
                # Domain violation - suggest adding type
                property_term = domain_issue.group(1)
                result["fix_explanations"].append(f"Domain violation for {property_term}")
                result["guidance"].append(f"Add the correct type to subjects using {property_term}.")
            
            elif range_issue:
                # Range violation - suggest adding type
                property_term = range_issue.group(1)
                result["fix_explanations"].append(f"Range violation for {property_term}")
                result["guidance"].append(f"Ensure objects of {property_term} have the correct type.")
            
            elif undefined_issue:
                # Undefined property - suggest alternatives
                property_term = undefined_issue.group(1)
                result["fix_explanations"].append(f"Undefined property: {property_term}")
                result["guidance"].append("Check for typos or use a defined property from the ontology.")
            
            else:
                # Generic violation
                result["fix_explanations"].append(f"Ontology violation: {violation}")
                result["guidance"].append("Review the ontology to understand valid property usage patterns.")
    
    # If no issues found, note this in the result
    if not has_issues:
        result["needs_fixes"] = False
        result["guidance"].append("No significant issues detected. The query appears to be well-formed.")
    
    return result

def _fix_limit_clause(query: str) -> str:
    """Add a LIMIT clause to a SPARQL query if missing."""
    import re
    
    # Check if LIMIT already exists
    if re.search(r'\bLIMIT\b\s+\d+', query, re.IGNORECASE):
        return query
    
    # Find insertion point (after ORDER BY if present, otherwise before final closing brace)
    if re.search(r'\bORDER\s+BY\b', query, re.IGNORECASE):
        return re.sub(
            r'(\bORDER\s+BY\b.+?)(\s*})$', 
            r'\1 LIMIT 100\2', 
            query, 
            flags=re.IGNORECASE | re.DOTALL
        )
    else:
        return re.sub(
            r'(\s*})$', 
            r' LIMIT 100\1', 
            query, 
            flags=re.DOTALL
        )


# %%
#| export
def refine_query_with_ontology(
    query: str,
    ontology_ttl: Optional[str] = None,
    ontology_path: Optional[str] = None,
    max_iterations: int = 3
) -> Dict[str, Any]:
    """
    Iteratively refine a SPARQL query using ontology validation and pattern fixes.

    Args:
        query: SPARQL query string to refine
        ontology_ttl: Ontology in Turtle format as a string
        ontology_path: Path to an ontology file on disk
        max_iterations: Maximum number of refinement iterations

    Returns:
        A dict with the refinement process and results.
    """
    if not _HAS_RDFLIB:
        raise ImportError("RDFLib is required for SPARQL query refinement")
        
    # Initialize the result structure
    result = {
        "success": True,
        "original_query": query,
        "refined_query": query,
        "iterations": [],
        "is_valid": False,
        "refinement_complete": False
    }
    
    current_query = query
    iterations = 0
    
    # First, check for syntactic issues with query patterns
    pattern_check = check_query_patterns(current_query)
    
    if pattern_check.get("warnings", []):
        # Apply syntactic fixes first
        pattern_fixes = generate_query_fixes(current_query, pattern_check)
        
        if pattern_fixes.get("needs_fixes", False):
            current_query = pattern_fixes.get("fixed_query", current_query)
            
            # Record this iteration
            result["iterations"].append({
                "type": "pattern_check",
                "issues_found": len(pattern_check.get("warnings", [])),
                "fixed_query": current_query,
                "explanations": pattern_fixes.get("fix_explanations", []),
                "guidance": pattern_fixes.get("guidance", [])
            })
            
            iterations += 1
    
    # Now iterate through ontology-based validation and fixes
    while iterations < max_iterations:
        # Validate against ontology
        validation = validate_query_against_ontology(
            current_query, 
            ontology_ttl=ontology_ttl,
            ontology_path=ontology_path
        )
        
        # Check if validation succeeded
        if not validation.get("valid", False) and validation.get("violations", []):
            # Generate fixes based on validation results
            fixes = generate_query_fixes(current_query, validation)
            
            if fixes.get("needs_fixes", False):
                # Apply the fixes
                current_query = fixes.get("fixed_query", current_query)
                
                # Record this iteration
                result["iterations"].append({
                    "type": "ontology_validation",
                    "issues_found": len(validation.get("violations", [])),
                    "fixed_query": current_query,
                    "explanations": fixes.get("fix_explanations", []),
                    "guidance": fixes.get("guidance", [])
                })
                
                iterations += 1
            else:
                # No more fixes needed or possible
                break
        else:
            # Query is valid according to ontology
            result["is_valid"] = True
            result["refinement_complete"] = True
            break
    
    # Update the result with final query and status
    result["refined_query"] = current_query
    result["iterations_count"] = iterations
    
    # If we hit max iterations without completing, note this
    if iterations >= max_iterations and not result["is_valid"]:
        result["refinement_complete"] = False
        result["message"] = f"Reached maximum iterations ({max_iterations}) without fully resolving all issues."
    
    return result


# %%
#| hide
import nbdev; nbdev.nbdev_export()

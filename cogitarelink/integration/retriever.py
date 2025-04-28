"""Framework-agnostic linked data retriever."""

from __future__ import annotations
from typing import Dict, List, Any, Optional, Union, Tuple
import re
import json
import uuid
import httpx
import time
from urllib.parse import urljoin, urlparse
from copy import deepcopy
from io import BytesIO

from ..core.debug import get_logger
from ..core.cache import InMemoryCache
from ..vocab.registry import registry

log = get_logger("retriever")
_cache = InMemoryCache(maxsize=256)

__all__ = ['json_parse', 'rdf_to_jsonld', 'search_wikidata', 'LODResource', 'LODRetriever']

def json_parse(content, uri=None):
    """Parse JSON content with error handling and recovery.
    
    Args:
        content: JSON content to parse
        uri: Optional URI for context in error messages
        
    Returns:
        tuple: (parsed_data, error_message)
            - parsed_data will be None if parsing failed
            - error_message will be None if parsing succeeded
    """
    try:
        # First try standard parsing
        return json.loads(content), None
    except json.JSONDecodeError as e:
        # Try to identify and fix common issues
        if "Unterminated string" in str(e):
            line_no = e.lineno
            col_no = e.colno
            
            # Try to recover by adding a closing quote
            lines = content.split('\n')
            if line_no <= len(lines):
                try:
                    # Try to fix the specific line by adding a missing quote
                    error_line = lines[line_no-1]
                    fixed_line = error_line[:col_no] + '"' + error_line[col_no:]
                    lines[line_no-1] = fixed_line
                    fixed_content = '\n'.join(lines)
                    
                    # Try parsing the fixed content
                    return json.loads(fixed_content), None
                except:
                    pass
        
        # Try a more lenient parser if available
        try:
            import json5
            return json5.loads(content), None
        except ImportError:
            pass
        except Exception:
            pass
            
        # As a last resort, try to extract valid JSON objects
        try:
            object_pattern = re.compile(r'\{[^{}]*\}')
            matches = object_pattern.findall(content)
            
            if matches:
                # Try to parse the largest match
                largest_match = max(matches, key=len)
                return json.loads(largest_match), "Partial JSON extracted"
        except:
            pass
            
        return None, f"Failed to parse JSON: {str(e)}"

def rdf_to_jsonld(content, format="turtle", base_uri=None):
    """Convert RDF content to JSON-LD.
    
    Args:
        content: RDF content in specified format
        format: RDF format (turtle, xml, n3, etc.)
        base_uri: Base URI for the RDF content
        
    Returns:
        tuple: (jsonld_data, error_message)
            - jsonld_data will be None if conversion failed
            - error_message will be None if conversion succeeded
    """
    try:
        from rdflib import Graph
        
        # Parse the RDF
        g = Graph()
        g.parse(data=content, format=format, publicID=base_uri)
        
        # Convert to JSON-LD
        jsonld_str = g.serialize(format="json-ld")
        
        # Parse the JSON-LD
        jsonld_data = json.loads(jsonld_str)
        
        # Handle the case where it's a list instead of a dict
        if isinstance(jsonld_data, list):
            # Wrap the list in a standard JSON-LD structure
            jsonld_doc = {
                "@context": {},
                "@graph": jsonld_data
            }
            return jsonld_doc, None
        
        return jsonld_data, None
        
    except Exception as primary_error:
        # First fallback: Try with BytesIO
        try:
            g = Graph()
            g.parse(BytesIO(content.encode('utf-8')), format=format, publicID=base_uri)
            
            # Convert to JSON-LD
            jsonld_str = g.serialize(format="json-ld")
            jsonld_data = json.loads(jsonld_str)
            
            # Handle list case
            if isinstance(jsonld_data, list):
                jsonld_doc = {
                    "@context": {},
                    "@graph": jsonld_data
                }
                return jsonld_doc, None
            
            return jsonld_data, None
        except Exception:
            pass
        
        # Second fallback: Try other formats if format was specified as "unknown"
        if format == "unknown":
            for fallback_format in ["turtle", "xml", "n3", "nt"]:
                try:
                    g = Graph()
                    g.parse(data=content, format=fallback_format, publicID=base_uri)
                    
                    # Convert to JSON-LD
                    jsonld_str = g.serialize(format="json-ld")
                    jsonld_data = json.loads(jsonld_str)
                    
                    # Handle list case
                    if isinstance(jsonld_data, list):
                        jsonld_doc = {
                            "@context": {},
                            "@graph": jsonld_data
                        }
                        return jsonld_doc, None
                    
                    return jsonld_data, None
                except:
                    continue
        
        # If we get here, all conversion attempts failed
        return None, f"RDF conversion error: {str(primary_error)}"

def search_wikidata(query, limit=10, language="en"):
    """
    Search Wikidata API for entities matching the query string.
    
    Args:
        query (str): The search term to look for
        limit (int): Maximum number of results to return (default: 10)
        language (str): Language code for labels and descriptions (default: "en")
        
    Returns:
        list: List of dictionaries containing entity information
    """
    import httpx
    
    # Construct the Wikidata API search URL
    url = "https://www.wikidata.org/w/api.php"
    
    # Set up the parameters for the search
    params = {
        "action": "wbsearchentities",
        "format": "json",
        "search": query,
        "language": language,
        "limit": str(limit),
        "type": "item"
    }
    
    try:
        # Make the request to the Wikidata API
        response = httpx.get(url, params=params)
        
        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            
            # Extract the relevant information from each search result
            results = []
            for item in data.get("search", []):
                result = {
                    "id": item.get("id"),
                    "uri": f"http://www.wikidata.org/entity/{item.get('id')}",
                    "label": item.get("label"),
                    "description": item.get("description", "No description available"),
                    "url": item.get("url", f"https://www.wikidata.org/wiki/{item.get('id')}")
                }
                results.append(result)
            
            return results
        else:
            return [{"error": f"API request failed with status code {response.status_code}"}]
            
    except Exception as e:
        return [{"error": f"An error occurred: {str(e)}"}]

class LODResource:
    """Represents a Linked Open Data resource."""
    
    def __init__(self, uri, data=None):
        self.uri = uri
        self.data = data or {}
        self.metadata = {
            "retrieval_time": time.time(),
            "id": str(uuid.uuid4())
        }
        
    def to_json_ld(self):
        """Convert to JSON-LD representation."""
        if "@context" not in self.data:
            return {"@context": {}, **self.data}
        return self.data
        
    def to_entity(self, vocab=None):
        """Convert to Entity if available."""
        try:
            from ..core.entity import Entity
            
            # Use provided vocab or try to detect
            if not vocab:
                # Basic detection based on URI
                if "wikidata.org" in self.uri:
                    vocab = ["schema"]
                elif "schema.org" in self.uri:
                    vocab = ["schema"]
                else:
                    vocab = ["schema"]  # Default
                    
            return Entity(vocab=vocab, content=self.data)
        except ImportError:
            log.warning("Entity class not available for conversion")
            return None

class LODRetriever:
    """Framework-agnostic retriever for Linked Open Data."""
    
    def __init__(self, cache=None):
        """Initialize the retriever."""
        self.cache = cache or InMemoryCache()
        # Use registry from the vocab module
        self.registry = registry
        # Create a client session
        self.client = httpx.Client(follow_redirects=True, timeout=10.0)
        
    def retrieve(self, uri):
        """
        Retrieve a resource from a URI.
        
        Args:
            uri (str): The URI to retrieve
            
        Returns:
            dict: Result containing:
                - success: boolean indicating if retrieval was successful
                - data: JSON-LD data if success is True
                - error: Error message if success is False
                - metadata: Additional information about the retrieval
        """
        # Check cache first
        cache_key = f"lod:{uri}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        # Analyze the URI to determine the best access strategy
        strategy = self.determine_access_strategy(uri)
        
        # Attempt to retrieve using the strategy
        result = self._fetch_with_strategy(uri, strategy)
        
        # If successful, process the content
        if result.get("success", False):
            processed = self._process_content(uri, result)
            
            # Cache the successful result
            if processed.get("success", False):
                self.cache.set(cache_key, processed)
                
            return processed
        
        # Return the failed result
        return result
    
    def determine_access_strategy(self, uri):
        """
        Determine the best access strategy for a URI.
        
        Args:
            uri (str): The URI to analyze
            
        Returns:
            dict: Strategy information
        """
        # Default strategy
        strategy = {
            "method": "direct",
            "url": uri,
            "headers": {},
            "format": "unknown"
        }
        
        # Parse the URI to extract components
        parsed = urlparse(uri)
        domain = parsed.netloc.lower()
        path = parsed.path.lower()
        
        # Try to match with known patterns from registry
        known_source = None
        
        # Check against registry entries
        for prefix, entry in self.registry._v.items():
            # Check primary URI
            entry_uri = str(entry.uris.get("primary", ""))
            if entry_uri and (uri.startswith(entry_uri) or domain in entry_uri):
                known_source = prefix
                break
                
            # Check alternate URIs
            alt_uris = entry.uris.get("alternates", [])
            if any(uri.startswith(str(alt)) or domain in str(alt) for alt in alt_uris):
                known_source = prefix
                break
        
        # Apply source-specific strategies
        if known_source:
            # Get the entry
            entry = self.registry[known_source]
            
            # Wikidata strategy
            if known_source == "wikidata":
                strategy["method"] = "direct"
                strategy["url"] = f"{uri}.ttl"
                strategy["format"] = "turtle"
                
            # Schema.org strategy
            elif known_source == "schema":
                if path in ["", "/"]:
                    # Schema.org vocabulary
                    strategy["method"] = "content_negotiation"
                    strategy["url"] = uri
                    strategy["headers"] = {"Accept": "application/ld+json"}
                    strategy["format"] = "json-ld"
                else:
                    # Schema.org term
                    strategy["method"] = "html_analysis"
                    strategy["url"] = uri
                    strategy["format"] = "html"
                    
            # Dublin Core strategy
            elif known_source == "dc":
                strategy["method"] = "content_negotiation"
                strategy["url"] = uri
                strategy["headers"] = {"Accept": "text/turtle,application/rdf+xml"}
                strategy["format"] = "turtle"
                
            # Default content negotiation for known sources
            else:
                strategy["method"] = "content_negotiation"
                strategy["url"] = uri
                strategy["headers"] = {"Accept": "application/ld+json,application/json,text/turtle,application/rdf+xml"}
        
        # Pattern-based strategies for common domains
        elif "wikidata.org" in domain and "/entity/" in path:
            # Wikidata entity
            entity_id = path.split("/")[-1]
            if entity_id.startswith("Q") or entity_id.startswith("P"):
                strategy["method"] = "direct"
                strategy["url"] = f"{uri}.ttl"
                strategy["format"] = "turtle"
                
        elif "dbpedia.org" in domain:
            # DBpedia
            strategy["method"] = "content_negotiation"
            strategy["url"] = uri
            strategy["headers"] = {"Accept": "application/ld+json,application/json,text/turtle"}
            strategy["format"] = "json-ld"
            
        # Special case for HTML with embedded metadata
        elif any(d in domain for d in ["schema.org", "gs1.org", "w3.org"]):
            strategy["method"] = "html_analysis"
            strategy["url"] = uri
            strategy["format"] = "html"
        
        return strategy
    
    def _fetch_with_strategy(self, uri, strategy):
        """
        Fetch data using the specified access strategy.
        
        Args:
            uri (str): Original URI
            strategy (dict): Access strategy details
            
        Returns:
            dict: Result of the fetch operation
        """
        method = strategy.get("method", "direct")
        url = strategy.get("url", uri)
        headers = strategy.get("headers", {})
        
        try:
            if method == "direct":
                # Direct HTTP request
                response = self.client.get(url, headers=headers)
                
                return {
                    "success": response.status_code == 200,
                    "url": str(response.url),
                    "content_type": response.headers.get("content-type", ""),
                    "content": response.text,
                    "headers": dict(response.headers),
                    "status_code": response.status_code
                }
                
            elif method == "content_negotiation":
                # Content negotiation with specific Accept header
                response = self.client.get(url, headers=headers)
                
                return {
                    "success": response.status_code == 200,
                    "url": str(response.url),
                    "content_type": response.headers.get("content-type", ""),
                    "content": response.text,
                    "headers": dict(response.headers),
                    "status_code": response.status_code
                }
                
            elif method == "html_analysis":
                # Fetch HTML and analyze for linked data
                response = self.client.get(url, headers=headers)
                
                if response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"Failed to fetch URL: {response.status_code}",
                        "status_code": response.status_code
                    }
                
                # Analyze HTML for embedded data
                html_analysis = self._analyze_html(response.text, str(response.url))
                
                return {
                    "success": True,
                    "url": str(response.url),
                    "content_type": "text/html",
                    "content": response.text,
                    "headers": dict(response.headers),
                    "status_code": response.status_code,
                    "html_analysis": html_analysis
                }
            
            else:
                # Unknown method, use direct access
                response = self.client.get(url)
                
                return {
                    "success": response.status_code == 200,
                    "url": str(response.url),
                    "content_type": response.headers.get("content-type", ""),
                    "content": response.text,
                    "headers": dict(response.headers),
                    "status_code": response.status_code
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Fetch error: {str(e)}"
            }
    
    def _analyze_html(self, html, url):
        """
        Analyze HTML to find linked data.
        
        Args:
            html (str): HTML content
            url (str): URL of the HTML document
            
        Returns:
            dict: Analysis results
        """
        from bs4 import BeautifulSoup
        
        try:
            soup = BeautifulSoup(html, "html.parser")
            
            # Look for JSON-LD script tags
            jsonld_scripts = soup.select("script[type='application/ld+json']")
            if jsonld_scripts:
                return {
                    "extraction_method": "embedded_jsonld",
                    "data_location": "script[type='application/ld+json']",
                    "count": len(jsonld_scripts)
                }
            
            # Look for alternate links to JSON-LD
            jsonld_links = soup.select("link[rel='alternate'][type='application/ld+json']")
            if jsonld_links:
                href = jsonld_links[0].get("href")
                if href:
                    return {
                        "extraction_method": "follow_reference",
                        "data_location": href,
                        "count": len(jsonld_links)
                    }
            
            # Look for RDFa
            if soup.select("[vocab], [typeof], [property], [resource]"):
                return {
                    "extraction_method": "rdfa",
                    "data_location": "html",
                    "count": len(soup.select("[vocab], [typeof], [property], [resource]"))
                }
            
            # Look for Microdata
            if soup.select("[itemscope], [itemtype], [itemprop]"):
                return {
                    "extraction_method": "microdata",
                    "data_location": "html",
                    "count": len(soup.select("[itemscope], [itemtype], [itemprop]"))
                }
            
            # Check for links to data files
            data_links = []
            for link in soup.select("a[href]"):
                href = link.get("href", "")
                text = link.get_text().lower()
                if any(term in href.lower() or term in text for term in 
                       ["json-ld", "jsonld", "rdf", "turtle", "n3", "owl"]):
                    data_links.append(href)
            
            if data_links:
                return {
                    "extraction_method": "follow_reference",
                    "data_location": data_links[0],
                    "count": len(data_links),
                    "all_references": data_links
                }
            
            # Default - no structured data found
            return {
                "extraction_method": "none",
                "data_location": None,
                "count": 0
            }
            
        except Exception as e:
            return {
                "extraction_method": "error",
                "error": str(e)
            }
    
    def _process_content(self, uri, fetch_result):
        """
        Process the fetched content based on its type.
        
        Args:
            uri (str): Original URI
            fetch_result (dict): Result from _fetch_with_strategy
            
        Returns:
            dict: Processed result with JSON-LD data
        """
        content_type = fetch_result.get("content_type", "").lower()
        content = fetch_result.get("content", "")
        url = fetch_result.get("url", uri)
        
        # Handle JSON-LD content
        if "application/ld+json" in content_type or "application/json" in content_type:
            json_ld, error = json_parse(content, uri=url)
            
            if json_ld:
                return {
                    "success": True,
                    "data": json_ld,
                    "format": "json-ld",
                    "source_uri": uri,
                    "content_type": content_type
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to parse JSON-LD: {error}",
                    "source_uri": uri
                }
        
        # Handle Turtle content
        elif "text/turtle" in content_type or "application/x-turtle" in content_type:
            json_ld, error = rdf_to_jsonld(content, format="turtle", base_uri=url)
            
            if json_ld:
                return {
                    "success": True,
                    "data": json_ld,
                    "format": "json-ld",
                    "source_uri": uri,
                    "content_type": content_type,
                    "converted_from": "turtle"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to convert Turtle: {error}",
                    "source_uri": uri
                }
        
        # Handle RDF/XML content
        elif "application/rdf+xml" in content_type or "application/xml" in content_type:
            json_ld, error = rdf_to_jsonld(content, format="xml", base_uri=url)
            
            if json_ld:
                return {
                    "success": True,
                    "data": json_ld,
                    "format": "json-ld",
                    "source_uri": uri,
                    "content_type": content_type,
                    "converted_from": "rdf-xml"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to convert RDF/XML: {error}",
                    "source_uri": uri
                }
        
        # Handle HTML content
        elif "text/html" in content_type or "application/xhtml+xml" in content_type:
            html_analysis = fetch_result.get("html_analysis", {})
            extraction_method = html_analysis.get("extraction_method", "")
            
            if extraction_method == "embedded_jsonld":
                # Extract JSON-LD from HTML
                from bs4 import BeautifulSoup
                
                soup = BeautifulSoup(content, "html.parser")
                jsonld_scripts = soup.select("script[type='application/ld+json']")
                
                if not jsonld_scripts:
                    return {
                        "success": False,
                        "error": "No JSON-LD script tags found",
                        "source_uri": uri
                    }
                
                # Extract and parse the first JSON-LD script
                script = jsonld_scripts[0]
                json_ld, error = json_parse(script.string, uri=url)
                
                if json_ld:
                    return {
                        "success": True,
                        "data": json_ld,
                        "format": "json-ld",
                        "source_uri": uri,
                        "content_type": content_type,
                        "extracted_from": "html-script"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to parse embedded JSON-LD: {error}",
                        "source_uri": uri
                    }
                    
            elif extraction_method == "rdfa":
                # Extract RDFa
                try:
                    from rdflib import Graph
                    
                    g = Graph()
                    g.parse(data=content, format="rdfa", publicID=url)
                    
                    # Convert to JSON-LD
                    json_ld, error = rdf_to_jsonld(g.serialize(format="turtle"), format="turtle", base_uri=url)
                    
                    if json_ld:
                        return {
                            "success": True,
                            "data": json_ld,
                            "format": "json-ld",
                            "source_uri": uri,
                            "content_type": content_type,
                            "extracted_from": "html-rdfa"
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"Failed to convert RDFa: {error}",
                            "source_uri": uri
                        }
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Failed to extract RDFa: {str(e)}",
                        "source_uri": uri
                    }
                    
            elif extraction_method == "microdata":
                # Extract Microdata
                try:
                    from rdflib import Graph
                    try:
                        from rdflib_microdata import MicrodataParser
                        
                        g = Graph()
                        MicrodataParser(g).parse_data(content, url)
                        
                        # Convert to JSON-LD
                        json_ld, error = rdf_to_jsonld(g.serialize(format="turtle"), format="turtle", base_uri=url)
                        
                        if json_ld:
                            return {
                                "success": True,
                                "data": json_ld,
                                "format": "json-ld",
                                "source_uri": uri,
                                "content_type": content_type,
                                "extracted_from": "html-microdata"
                            }
                        else:
                            return {
                                "success": False,
                                "error": f"Failed to convert Microdata: {error}",
                                "source_uri": uri
                            }
                    except ImportError:
                        return {
                            "success": False,
                            "error": "rdflib_microdata module not available",
                            "source_uri": uri
                        }
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Failed to extract Microdata: {str(e)}",
                        "source_uri": uri
                    }
            
            # Try a generic approach
            try:
                # Try to find embedded JSON-LD
                from bs4 import BeautifulSoup
                
                soup = BeautifulSoup(content, "html.parser")
                jsonld_scripts = soup.select("script[type='application/ld+json']")
                
                if jsonld_scripts:
                    script = jsonld_scripts[0]
                    json_ld, error = json_parse(script.string, uri=url)
                    
                    if json_ld:
                        return {
                            "success": True,
                            "data": json_ld,
                            "format": "json-ld",
                            "source_uri": uri,
                            "content_type": content_type,
                            "extracted_from": "html-script"
                        }
                
                # Try RDFa as a fallback
                try:
                    from rdflib import Graph
                    
                    g = Graph()
                    g.parse(data=content, format="rdfa", publicID=url)
                    
                    if len(g) > 0:
                        # Convert to JSON-LD
                        json_ld, error = rdf_to_jsonld(g.serialize(format="turtle"), format="turtle", base_uri=url)
                        
                        if json_ld:
                            return {
                                "success": True,
                                "data": json_ld,
                                "format": "json-ld",
                                "source_uri": uri,
                                "content_type": content_type,
                                "extracted_from": "html-rdfa"
                            }
                except:
                    pass
                    
            except Exception:
                pass
            
            # If all extraction methods failed, return failure
            return {
                "success": False,
                "error": "Could not extract linked data from HTML",
                "source_uri": uri,
                "content_type": content_type
            }
        
        # Handle unknown content types
        else:
            # Try to guess format
            if content.strip().startswith("{") or content.strip().startswith("["):
                # Looks like JSON, try to parse as JSON-LD
                json_ld, error = json_parse(content, uri=url)
                
                if json_ld:
                    return {
                        "success": True,
                        "data": json_ld,
                        "format": "json-ld",
                        "source_uri": uri,
                        "content_type": content_type,
                        "guessed_format": "json"
                    }
            
            if content.strip().startswith("@prefix") or content.strip().startswith("@base"):
                # Looks like Turtle, try to parse
                json_ld, error = rdf_to_jsonld(content, format="turtle", base_uri=url)
                
                if json_ld:
                    return {
                        "success": True,
                        "data": json_ld,
                        "format": "json-ld",
                        "source_uri": uri,
                        "content_type": content_type,
                        "guessed_format": "turtle"
                    }
            
            if content.strip().startswith("<?xml") or content.strip().startswith("<rdf:RDF"):
                # Looks like RDF/XML, try to parse
                json_ld, error = rdf_to_jsonld(content, format="xml", base_uri=url)
                
                if json_ld:
                    return {
                        "success": True,
                        "data": json_ld,
                        "format": "json-ld",
                        "source_uri": uri,
                        "content_type": content_type,
                        "guessed_format": "rdf-xml"
                    }
            
            # Try multiple formats in sequence
            for format_name in ["turtle", "xml", "n3", "nt"]:
                try:
                    json_ld, error = rdf_to_jsonld(content, format=format_name, base_uri=url)
                    
                    if json_ld:
                        return {
                            "success": True,
                            "data": json_ld,
                            "format": "json-ld",
                            "source_uri": uri,
                            "content_type": content_type,
                            "converted_from": format_name
                        }
                except:
                    pass
            
            # If all formats failed, return failure
            return {
                "success": False,
                "error": f"Unsupported content type: {content_type}",
                "source_uri": uri
            }
    
    def get_entity_details(self, entity_id):
        """
        Get detailed information about a Wikidata entity.
        
        Args:
            entity_id (str): Wikidata entity ID (e.g., "Q42")
            
        Returns:
            dict: Detailed entity information
        """
        if not entity_id.startswith("Q"):
            entity_id = f"Q{entity_id}"
        
        entity_uri = f"http://www.wikidata.org/entity/{entity_id}"
        
        # Retrieve entity data
        result = self.retrieve(entity_uri)
        
        if not result.get("success", False):
            return {
                "success": False,
                "error": result.get("error", "Failed to retrieve entity")
            }
        
        json_ld = result.get("data", {})
        graph = json_ld.get("@graph", [])
        
        # Find the main entity node
        main_node = None
        for node in graph:
            if node.get("@id") == entity_uri:
                main_node = node
                break
        
        if not main_node:
            return {
                "success": False,
                "error": "Entity node not found in the graph"
            }
        
        # Extract key information
        p31_key = "http://www.wikidata.org/prop/direct/P31"  # instance of
        label_key = "http://www.w3.org/2000/01/rdf-schema#label"
        desc_key = "http://schema.org/description"
        
        # Extract instance of values
        instance_of = []
        if p31_key in main_node:
            for val in main_node[p31_key]:
                if isinstance(val, dict) and "@id" in val:
                    instance_of.append(val["@id"])
        
        # Extract labels
        labels = {}
        if label_key in main_node:
            for label in main_node[label_key]:
                if isinstance(label, dict) and "@value" in label and "@language" in label:
                    labels[label["@language"]] = label["@value"]
        
        # Extract descriptions
        descriptions = {}
        if desc_key in main_node:
            for desc in main_node[desc_key]:
                if isinstance(desc, dict) and "@value" in desc and "@language" in desc:
                    descriptions[desc["@language"]] = desc["@value"]
        
        # Create a structured result
        entity_details = {
            "id": entity_id,
            "uri": entity_uri,
            "labels": labels,
            "descriptions": descriptions,
            "instance_of": instance_of,
            "properties": {},
            "success": True
        }
        
        # Extract a few common properties
        common_properties = {
            "P18": "image",
            "P569": "date of birth",
            "P570": "date of death",
            "P856": "website",
            "P27": "country of citizenship",
            "P106": "occupation"
        }
        
        for p_id, name in common_properties.items():
            prop_key = f"http://www.wikidata.org/prop/direct/P{p_id[1:]}" if p_id.startswith("P") else f"http://www.wikidata.org/prop/direct/{p_id}"
            if prop_key in main_node:
                entity_details["properties"][name] = main_node[prop_key]
        
        return entity_details
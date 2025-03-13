"""This module provides tools for working with JSON-LD vocabularies in the cogitarelink library. It implements core vocabulary exploration, fetching, and navigation capabilities that allow AI agents to understand semantic relationships between terms. The module includes functions for retrieving vocabularies from web sources, extracting embedded JSON-LD, and converting between RDF formats. It enables agents to "follow their nose" through linked data by traversing concept definitions and relationships."""

# AUTOGENERATED! DO NOT EDIT! File to edit: ../01_vocabulary.ipynb.

# %% auto 0
__all__ = ['jsonld_merge']

# %% ../01_vocabulary.ipynb 6
from fastcore.basics import *
from fastcore.meta import *
from fastcore.test import *
import json
from rdflib import Graph
from pyld import jsonld
from typing import List, Dict, Any, Optional, Union
from bs4 import BeautifulSoup as bs
import httpx

# %% ../01_vocabulary.ipynb 7
from .core import *

# %% ../01_vocabulary.ipynb 8
def jsonld_merge(docs:list) -> dict:
    """Merge multiple JSON-LD documents into one."""
    if not docs:
        return {"@context": {}, "@graph": []}
    
    # Start with a copy of the first document
    result = docs[0].copy() if docs else {"@context": {}, "@graph": []}
    
    # Initialize @graph if not present
    if '@graph' not in result:
        result['@graph'] = []
    
    # Initialize @context if not present
    if '@context' not in result:
        result['@context'] = {}
    
    # Process the remaining documents
    for doc in docs[1:]:
        # Handle @graph
        if '@graph' in doc:
            result['@graph'].extend(doc['@graph'])
        elif isinstance(doc, list):
            # Handle case where doc is a list of entities
            result['@graph'].extend(doc)
        elif '@id' in doc:
            # Handle case where doc is a single entity
            result['@graph'].append(doc)
        
        # Merge @context if present
        if '@context' in doc and isinstance(doc['@context'], dict):
            result['@context'].update(doc['@context'])
    
    return result


# %% ../01_vocabulary.ipynb 9
@patch
def fetch_vocabulary(self:LinkedDataKnowledge, 
                    uri:str, # URI of vocabulary to fetch
                    follow_link_header:bool=True, # Whether to follow Link headers
                    debug:bool=False # Enable detailed debug output
                    ) -> 'LinkedDataKnowledge':
    "Fetch a vocabulary and add it to the knowledge base"
    client = httpx.Client(follow_redirects=True)
    
    if debug:
        print(f"Requesting {uri} with content negotiation...")
    
    # Try with explicit content negotiation
    accept_headers = [
        "application/ld+json",
        "application/rdf+xml",
        "text/turtle",
        "application/n-triples",
        "text/n3"
    ]
    
    # Join with quality values to prioritize formats
    accept_header = ", ".join([
        f"{accept_headers[i]};q={1.0 - i*0.1}" for i in range(len(accept_headers))
    ])
    
    response = client.get(
        uri,
        headers={"Accept": accept_header}
    )
    
    if debug:
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        print(f"Content preview: {response.text[:200]}...")
    
    if response.status_code != 200:
        raise ValueError(f"Failed to fetch vocabulary: {response.status_code}")
    
    # Special case for Schema.org - follow the link header
    if follow_link_header and 'link' in response.headers:
        link_header = response.headers['link']
        if debug:
            print(f"Found Link header: {link_header}")
        
        # Parse the link header
        import re
        links = re.findall(r'<([^>]+)>;\s*rel="([^"]+)"(?:;\s*type="([^"]+)")?', link_header)
        
        for link_uri, rel, content_type in links:
            if rel == "alternate" and content_type == "application/ld+json":
                if debug:
                    print(f"Following link to JSON-LD: {link_uri}")
                
                # Make the link absolute if it's relative
                if link_uri.startswith("/"):
                    from urllib.parse import urlparse
                    parsed_uri = urlparse(uri)
                    base_url = f"{parsed_uri.scheme}://{parsed_uri.netloc}"
                    link_uri = base_url + link_uri
                
                # Fetch the JSON-LD context
                jsonld_response = client.get(link_uri)
                
                if jsonld_response.status_code == 200:
                    try:
                        jsonld_data = jsonld_response.json()
                        if debug:
                            print(f"Successfully loaded JSON-LD from link")
                        
                        # Merge with existing knowledge
                        self.data = jsonld_merge([self.data, jsonld_data])
                        return self
                    except Exception as e:
                        if debug:
                            print(f"Error parsing JSON-LD from link: {e}")
    
    # Get content type ONCE, before using it multiple times
    content_type = response.headers.get('Content-Type', '').split(';')[0].strip()
    
    # Special case for HTML responses - check for embedded RDFa or JSON-LD
    if content_type == 'text/html':
        if debug:
            print("Response is HTML - checking for embedded structured data")
        self.extract_jsonld_from_html(response.text)
        
        # If we found some data, return
        if '@graph' in self.data and len(self.data['@graph']) > 0:
            if debug:
                print(f"Found {len(self.data['@graph'])} entities in embedded JSON-LD")
            return self
        
        # Also check for RDFa
        try:
            g = Graph()
            g.parse(data=response.text, format='rdfa', publicID=uri)
            if len(g) > 0:
                if debug:
                    print(f"Found {len(g)} RDFa triples in HTML")
                jsonld_data = json.loads(g.serialize(format='json-ld'))
                self.data = jsonld_merge([self.data, jsonld_data])
                return self
        except Exception as e:
            if debug:
                print(f"Error parsing RDFa: {e}")
    
    # Try to determine format from content type or content
    rdf_format = _determine_rdf_format(content_type, response.text)
    
    if not rdf_format:
        # Special case for Schema.org
        if 'schema.org' in uri:
            # Try to fetch the JSON-LD context directly
            jsonld_uri = "https://schema.org/docs/jsonldcontext.jsonld"
            if debug:
                print(f"Trying to fetch Schema.org JSON-LD context directly: {jsonld_uri}")
            
            jsonld_response = client.get(jsonld_uri)
            if jsonld_response.status_code == 200:
                try:
                    jsonld_data = jsonld_response.json()
                    if debug:
                        print(f"Successfully loaded Schema.org JSON-LD context")
                    
                    # Merge with existing knowledge
                    self.data = jsonld_merge([self.data, jsonld_data])
                    return self
                except Exception as e:
                    if debug:
                        print(f"Error parsing Schema.org JSON-LD context: {e}")
        
        # Try each format until one works
        for fmt in ['xml', 'turtle', 'n3', 'nt', 'json-ld']:
            try:
                if debug:
                    print(f"Trying to parse as {fmt}...")
                g = Graph()
                g.parse(data=response.text, format=fmt)
                if len(g) > 0:
                    if debug:
                        print(f"Successfully parsed as {fmt}, found {len(g)} triples")
                    rdf_format = fmt
                    break
            except Exception as e:
                if debug:
                    print(f"Failed to parse as {fmt}: {e}")
    
    if not rdf_format:
        raise ValueError(f"Could not determine format for {uri}")
    
    g = Graph()
    g.parse(data=response.text, format=rdf_format)
    jsonld_data = json.loads(g.serialize(format='json-ld'))
    
    # Handle the case where RDFLib returns a list instead of a document with @graph
    if isinstance(jsonld_data, list):
        if '@graph' in self.data:
            self.data['@graph'].extend(jsonld_data)
        else:
            self.data['@graph'] = jsonld_data
    else:
        self.data = jsonld_merge([self.data, jsonld_data])
    
    return self


# %% ../01_vocabulary.ipynb 10
@patch
def extract_jsonld_from_html(self:LinkedDataKnowledge, html:str) -> 'LinkedDataKnowledge':
    "Extract JSON-LD from HTML script tags and add to knowledge base"
    soup = bs(html, 'html.parser')
    jsonld_scripts = soup.select('script[type="application/ld+json"]')
    
    print(f"Found {len(jsonld_scripts)} JSON-LD script tags")
    
    extracted_data = []
    for script in jsonld_scripts:
        try:
            script_data = json.loads(script.string)
            extracted_data.append(script_data)
        except json.JSONDecodeError:
            pass  # Skip invalid JSON
    
    print(f"Extracted {len(extracted_data)} valid JSON-LD objects")
    
    if extracted_data:
        # Special case for Schema.org - it often has the vocabulary in a specific format
        for data in extracted_data:
            if '@context' in data and 'https://schema.org' in str(data['@context']):
                if '@graph' in data:
                    print(f"Found Schema.org graph with {len(data['@graph'])} entities")
                    # If we have existing data, merge
                    if '@graph' in self.data:
                        self.data['@graph'].extend(data['@graph'])
                    else:
                        self.data['@graph'] = data['@graph']
                    
                    # Update context
                    if '@context' not in self.data:
                        self.data['@context'] = data['@context']
                    elif isinstance(self.data['@context'], dict) and isinstance(data['@context'], dict):
                        self.data['@context'].update(data['@context'])
                else:
                    # Might be a single entity
                    print("Found Schema.org single entity")
                    if '@graph' not in self.data:
                        self.data['@graph'] = []
                    
                    # Add entity data (excluding @context which we handle separately)
                    entity_data = {k: v for k, v in data.items() if k != '@context'}
                    if entity_data:  # Only add if there's actual entity data
                        self.data['@graph'].append(entity_data)
                    
                    # Update context
                    if '@context' not in self.data:
                        self.data['@context'] = data['@context']
                    elif isinstance(self.data['@context'], dict) and isinstance(data['@context'], dict):
                        self.data['@context'].update(data['@context'])
    
    return self


# %% ../01_vocabulary.ipynb 11
@patch
def create_scoped_context(self:LinkedDataKnowledge, 
                         domain:str, # Domain name (e.g., "Person")
                         domain_properties:List[str], # Properties for this domain
                         base_uri:str="https://schema.org/" # Base URI for the domain
                         ) -> 'LinkedDataKnowledge':
    "Create a scoped context for domain-specific knowledge organization"
    
    scoped_context = {
        "@context": {
            "@version": 1.1,
            domain: {
                "@id": f"{base_uri}{domain}",
                "@context": {
                    prop: {"@id": f"{base_uri}{prop}"} 
                    for prop in domain_properties
                }
            }
        }
    }
    
    # Apply the scoped context
    self.data = jsonld.compact(self.data, scoped_context["@context"])
    return self

# %% ../01_vocabulary.ipynb 12
def _determine_rdf_format(content_type:str, content:str) -> str:
    "Determine RDF format from content type and content preview"
    format_mapping = {
        'application/rdf+xml': 'xml',
        'text/turtle': 'turtle', 
        'application/n-triples': 'nt',
        'application/n-quads': 'nquads',
        'text/n3': 'n3',
        'application/trig': 'trig',
        'application/ld+json': 'json-ld'
    }
    
    # First check the content type
    rdf_format = format_mapping.get(content_type)
    
    # Special case: if it's application/json, check if it might be JSON-LD
    if not rdf_format and content_type == 'application/json':
        # Try to parse as JSON first
        try:
            json_data = json.loads(content)
            # Check for JSON-LD indicators
            if isinstance(json_data, dict) and ('@context' in json_data or '@graph' in json_data):
                return 'json-ld'
            elif isinstance(json_data, list) and len(json_data) > 0:
                # Check first item for JSON-LD structure
                if isinstance(json_data[0], dict) and ('@id' in json_data[0] or '@type' in json_data[0]):
                    return 'json-ld'
        except:
            pass  # Not valid JSON, continue with other checks
    
    # If still no format, try to guess from content
    if not rdf_format:
        if content.strip().startswith('<'):
            if 'xmlns:rdf' in content or '<rdf:RDF' in content:
                rdf_format = 'xml'
            else:
                # Could be HTML with embedded RDFa
                soup = bs(content, 'html.parser')
                if soup.select('[property], [typeof]'):
                    rdf_format = 'rdfa'
        elif '@prefix' in content:
            rdf_format = 'turtle'
        elif content.strip().startswith('{'):
            # Try to parse as JSON to see if it might be JSON-LD
            try:
                json_data = json.loads(content)
                # Check for JSON-LD indicators
                if isinstance(json_data, dict) and ('@context' in json_data or '@graph' in json_data):
                    rdf_format = 'json-ld'
                elif isinstance(json_data, list) and len(json_data) > 0:
                    # Check first item for JSON-LD structure
                    if isinstance(json_data[0], dict) and ('@id' in json_data[0] or '@type' in json_data[0]):
                        rdf_format = 'json-ld'
            except:
                pass  # Not valid JSON
    
    return rdf_format


# %% ../01_vocabulary.ipynb 17
@patch
def summarize_vocabulary(self:LinkedDataKnowledge) -> str:
    """Analyze and summarize the vocabulary structure.
    
    Returns:
        str: Markdown-formatted summary of the vocabulary
    
    Examples:
        >>> kb = LinkedDataKnowledge()
        >>> kb.fetch_vocabulary("https://schema.org/")
        >>> summary = kb.summarize_vocabulary()
        >>> display(Markdown(summary))
    """
    graph = self.data.get('@graph', [])
    if not graph:
        return "Vocabulary is empty"
    
    # Count entity types
    classes = []
    properties = []
    other_types = {}
    
    for entity in graph:
        entity_type = entity.get('@type', [])
        if not isinstance(entity_type, list):
            entity_type = [entity_type]
            
        # Check if it's a class
        if any('Class' in t for t in entity_type):
            classes.append(entity)
        # Check if it's a property
        elif any('Property' in t for t in entity_type):
            properties.append(entity)
        # Count other types
        else:
            for t in entity_type:
                if t:
                    type_name = t.split('/')[-1] if '/' in t else t
                    other_types[type_name] = other_types.get(type_name, 0) + 1
    
    # Prepare summary
    lines = ["# Vocabulary Summary", ""]
    
    # Basic statistics
    lines.append(f"## Overview")
    lines.append(f"- Total entities: {len(graph)}")
    lines.append(f"- Classes: {len(classes)}")
    lines.append(f"- Properties: {len(properties)}")
    if other_types:
        lines.append("- Other types:")
        for type_name, count in sorted(other_types.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  - {type_name}: {count}")
    
    # Top-level classes (those without a superclass or with external superclasses)
    top_classes = []
    for cls in classes:
        superclasses = []
        for key, value in cls.items():
            if 'subClassOf' in key:
                if isinstance(value, list):
                    superclasses.extend([v.get('@id') for v in value if isinstance(v, dict) and '@id' in v])
                elif isinstance(value, dict) and '@id' in value:
                    superclasses.append(value['@id'])
        
        # Check if all superclasses are external (not in this vocabulary)
        internal_superclasses = [s for s in superclasses if any(e.get('@id') == s for e in classes)]
        if not internal_superclasses:
            top_classes.append(cls)
    
    if top_classes:
        lines.append("\n## Top-Level Classes")
        for i, cls in enumerate(sorted(top_classes, key=lambda x: x.get('@id', ''))[:10]):
            cls_id = cls.get('@id', 'Unknown')
            cls_name = cls_id.split('/')[-1] if '/' in cls_id else cls_id
            
            # Get label if available
            label = cls_name
            for key, value in cls.items():
                if 'label' in key.lower():
                    if isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict) and '@value' in item:
                                label = item['@value']
                                break
                    elif isinstance(value, str):
                        label = value
                    break
            
            lines.append(f"### {label}")
            lines.append(f"**ID**: `{cls_id}`")
            
            # Get comment/description if available
            for key, value in cls.items():
                if 'comment' in key.lower() or 'description' in key.lower():
                    if isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict) and '@value' in item:
                                lines.append(f"**Description**: {item['@value']}")
                                break
                    elif isinstance(value, str):
                        lines.append(f"**Description**: {value}")
                    break
            
            # Count properties that have this class in their domain
            related_props = []
            for prop in properties:
                for key, value in prop.items():
                    if 'domain' in key.lower():
                        domain_matches = False
                        if isinstance(value, list):
                            for domain in value:
                                if isinstance(domain, dict) and domain.get('@id') == cls_id:
                                    domain_matches = True
                                    break
                        elif isinstance(value, dict) and value.get('@id') == cls_id:
                            domain_matches = True
                        
                        if domain_matches:
                            related_props.append(prop)
                            break
            
            if related_props:
                lines.append(f"**Properties**: {len(related_props)}")
                lines.append("Top properties:")
                for prop in related_props[:5]:
                    prop_id = prop.get('@id', 'Unknown')
                    prop_name = prop_id.split('/')[-1] if '/' in prop_id else prop_id
                    
                    # Get label if available
                    prop_label = prop_name
                    for key, value in prop.items():
                        if 'label' in key.lower():
                            if isinstance(value, list):
                                for item in value:
                                    if isinstance(item, dict) and '@value' in item:
                                        prop_label = item['@value']
                                        break
                            elif isinstance(value, str):
                                prop_label = value
                            break
                    
                    lines.append(f"- `{prop_label}`: {prop_id}")
                
                if len(related_props) > 5:
                    lines.append(f"- ... and {len(related_props) - 5} more")
            
            lines.append("")  # Empty line between classes
        
        if len(top_classes) > 10:
            lines.append(f"... and {len(top_classes) - 10} more top-level classes")
    
    # Most-used properties (those with the most domains)
    if properties:
        property_domains = {}
        for prop in properties:
            prop_id = prop.get('@id', '')
            domains = []
            
            for key, value in prop.items():
                if 'domain' in key.lower():
                    if isinstance(value, list):
                        for domain in value:
                            if isinstance(domain, dict) and '@id' in domain:
                                domains.append(domain['@id'])
                    elif isinstance(value, dict) and '@id' in value:
                        domains.append(value['@id'])
            
            property_domains[prop_id] = len(domains)
        
        if property_domains:
            lines.append("\n## Most Used Properties")
            for prop_id, domain_count in sorted(property_domains.items(), key=lambda x: x[1], reverse=True)[:10]:
                prop = next((p for p in properties if p.get('@id') == prop_id), None)
                if prop:
                    prop_name = prop_id.split('/')[-1] if '/' in prop_id else prop_id
                    
                    # Get label if available
                    prop_label = prop_name
                    for key, value in prop.items():
                        if 'label' in key.lower():
                            if isinstance(value, list):
                                for item in value:
                                    if isinstance(item, dict) and '@value' in item:
                                        prop_label = item['@value']
                                        break
                            elif isinstance(value, str):
                                prop_label = value
                            break
                    
                    lines.append(f"### {prop_label}")
                    lines.append(f"**ID**: `{prop_id}`")
                    lines.append(f"**Used by**: {domain_count} classes")
                    
                    # Get comment/description if available
                    for key, value in prop.items():
                        if 'comment' in key.lower() or 'description' in key.lower():
                            if isinstance(value, list):
                                for item in value:
                                    if isinstance(item, dict) and '@value' in item:
                                        lines.append(f"**Description**: {item['@value']}")
                                        break
                            elif isinstance(value, str):
                                lines.append(f"**Description**: {value}")
                            break
                    
                    lines.append("")  # Empty line between properties
    
    return "\n".join(lines)


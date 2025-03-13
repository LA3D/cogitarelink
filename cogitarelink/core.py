"""The LinkedDataKnowledge class serves as the foundational memory structure for working with linked data in JSON-LD format. It provides methods for storing, querying, and visualizing knowledge graphs, with a focus on making linked data exploration intuitive and accessible."""

# AUTOGENERATED! DO NOT EDIT! File to edit: ../00_core.ipynb.

# %% auto 0
__all__ = ['LinkedDataKnowledge', 'describe', 'view']

# %% ../00_core.ipynb 5
from fastcore.basics import *
from fastcore.meta import *
from fastcore.test import *
import json
from rdflib import Graph
from pyld import jsonld
from typing import List, Dict, Any, Optional, Union

# %% ../00_core.ipynb 7
class LinkedDataKnowledge:
    "Represents a knowledge base of linked data in JSON-LD format"
    def __init__(self, 
                 data:Dict=None, # Initial knowledge data
                ):
        self.data = data or {"@context": {}, "@graph": []}
        
    def __repr__(self): return f"LinkedDataKnowledge with {len(self.data.get('@graph', []))} entities"

# %% ../00_core.ipynb 9
@patch
def _repr_markdown_(self:LinkedDataKnowledge) -> str:
    "Rich markdown representation for notebook display"
    md = [f"## LinkedDataKnowledge"]
    
    # Context summary
    context = self.data.get('@context', {})
    md.append(f"### Context ({len(context)} prefixes)")
    
    # Show the first few context entries
    if context:
        md.append("```json")
        context_preview = dict(list(context.items())[:5])
        if len(context) > 5:
            md.append(json.dumps(context_preview, indent=2) + "\n... and more")
        else:
            md.append(json.dumps(context, indent=2))
        md.append("```")
    
    # Graph summary
    graph = self.data.get('@graph', [])
    md.append(f"### Graph ({len(graph)} entities)")
    
    # Show types of entities in the graph
    if graph:
        types = {}
        for entity in graph:
            entity_type = entity.get('@type')
            if isinstance(entity_type, list):
                for t in entity_type:
                    types[t] = types.get(t, 0) + 1
            elif entity_type:
                types[entity_type] = types.get(entity_type, 0) + 1
        
        if types:
            md.append("**Entity types:**")
            for t, count in sorted(types.items(), key=lambda x: x[1], reverse=True):
                md.append(f"- {t}: {count}")
    
    # Show a sample entity if available
    if graph:
        md.append("\n**Sample entity:**")
        md.append("```json")
        md.append(json.dumps(graph[0], indent=2))
        md.append("```")
    
    # If using @included, show that too
    if '@included' in self.data:
        included = self.data['@included']
        md.append(f"\n### Included ({len(included)} entities)")
        md.append("**Types of included entities:**")
        
        # Count types of included entities
        included_types = {}
        for entity in included:
            entity_type = entity.get('@type')
            if isinstance(entity_type, list):
                for t in entity_type:
                    included_types[t] = included_types.get(t, 0) + 1
            elif entity_type:
                included_types[entity_type] = included_types.get(entity_type, 0) + 1
        
        for t, count in sorted(included_types.items(), key=lambda x: x[1], reverse=True):
            md.append(f"- {t}: {count}")
    
    return "\n".join(md)


# %% ../00_core.ipynb 10
def _format_entity_markdown(entity:Dict) -> str:
    "Format a single entity as markdown"
    md = []
    
    # Entity ID and type
    entity_id = entity.get('@id', 'No ID')
    entity_type = entity.get('@type', ['Unknown'])
    if isinstance(entity_type, list):
        entity_type = ', '.join(entity_type)
    
    md.append(f"### {entity_type}: {entity_id}")
    
    # Properties
    for prop, values in entity.items():
        if prop in ['@id', '@type']:
            continue
            
        # Format the property name
        prop_name = prop.split('/')[-1] if '/' in prop else prop
        md.append(f"**{prop_name}**:")
        
        # Format values
        for val in values:
            if isinstance(val, dict):
                if '@value' in val:
                    value_text = val['@value']
                    if '@language' in val:
                        value_text += f" @{val['@language']}"
                    md.append(f"- {value_text}")
                elif '@id' in val:
                    md.append(f"- [{val['@id']}]({val['@id']})")
                else:
                    md.append(f"- {val}")
            else:
                md.append(f"- {val}")
    
    return "\n".join(md)

@patch
def query_markdown(self:LinkedDataKnowledge,
                  query_type:str, # Type of query: "property", "type", "value" 
                  query_value:str, # Value to search for
                  ) -> str:
    "Query the knowledge base and return results as markdown"
    results = self.query(query_type, query_value)
    
    if not results:
        return f"*No results found for {query_type}='{query_value}'*"
    
    md = [f"# Query Results: {query_type}='{query_value}'", 
          f"Found {len(results)} matching entities"]
    
    # Format each result entity
    for i, entity in enumerate(results[:5]):  # Limit to first 5 for readability
        md.append(f"\n## Result {i+1}")
        md.append(_format_entity_markdown(entity))
    
    if len(results) > 5:
        md.append(f"\n*...and {len(results)-5} more results*")
    
    return "\n".join(md)


# %% ../00_core.ipynb 11
@patch
def _has_type(self:LinkedDataKnowledge, entity:dict, type_str:str) -> bool:
    """Check if entity has the specified type, handling various type formats."""
    if not entity or not type_str:
        return False
        
    entity_types = entity.get('@type', [])
    if not isinstance(entity_types, list):
        entity_types = [entity_types]
    
    # Handle empty types
    if not entity_types:
        return False
    
    # Try exact match first (most efficient)
    if type_str in entity_types:
        return True
    
    # For prefixed names like "rdfs:Class" or "rdf:Property", try direct string matching
    # This handles cases where the prefix isn't in the context but is used in entity types
    if ':' in type_str and any(t.endswith(type_str.split(':')[1]) for t in entity_types):
        return True
    
    # Prepare for URI and prefixed name handling
    context = self.data.get('@context', {})
    
    # Standard RDF prefixes that might not be in the context
    standard_prefixes = {
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "owl": "http://www.w3.org/2002/07/owl#",
        "xsd": "http://www.w3.org/2001/XMLSchema#"
    }
    
    # Add standard prefixes to context if not already present
    for prefix, uri in standard_prefixes.items():
        if prefix not in context:
            context[prefix] = uri
    
    # Convert type_str to expanded URI if it's a prefixed name
    expanded_type_str = None
    if ':' in type_str and not type_str.startswith(('http://', 'https://')):
        prefix, local = type_str.split(':', 1)
        if prefix in context:
            prefix_uri = context[prefix]
            if isinstance(prefix_uri, str):
                if prefix_uri.endswith('/') or prefix_uri.endswith('#'):
                    expanded_type_str = f"{prefix_uri}{local}"
                else:
                    expanded_type_str = f"{prefix_uri}/{local}"
    
    # Convert entity_types to expanded URIs and prefixed names for comparison
    for entity_type in entity_types:
        # Check if expanded type_str matches entity_type
        if expanded_type_str and (expanded_type_str == entity_type or expanded_type_str in entity_type):
            return True
            
        # If entity_type is a full URI and type_str is a prefixed name
        if entity_type.startswith(('http://', 'https://')) and ':' in type_str and not type_str.startswith(('http://', 'https://')):
            # Extract the local name from the URI to match against prefixed name
            for prefix, uri in context.items():
                if isinstance(uri, str) and entity_type.startswith(uri):
                    local_part = entity_type[len(uri):]
                    if local_part.startswith('/') or local_part.startswith('#'):
                        local_part = local_part[1:]
                    prefixed = f"{prefix}:{local_part}"
                    if prefixed == type_str:
                        return True
                        
        # If type_str is a full URI and entity_type is a prefixed name
        if type_str.startswith(('http://', 'https://')) and ':' in entity_type and not entity_type.startswith(('http://', 'https://')):
            prefix, local = entity_type.split(':', 1)
            if prefix in context:
                prefix_uri = context[prefix]
                if isinstance(prefix_uri, str):
                    if prefix_uri.endswith('/') or prefix_uri.endswith('#'):
                        expanded = f"{prefix_uri}{local}"
                    else:
                        expanded = f"{prefix_uri}/{local}"
                    if expanded == type_str or expanded in type_str:
                        return True
    
    # Check for local name match (e.g., "Class" matches "rdfs:Class" or "http://.../Class")
    if not type_str.startswith(('http://', 'https://')) and not ':' in type_str:
        # Check if any type ends with the local name
        if any(t.split('/')[-1] == type_str or 
               t.split('#')[-1] == type_str or
               ((':' in t) and t.split(':')[-1] == type_str)
               for t in entity_types):
            return True
    
    # Finally, try substring match as a fallback
    # This is less reliable but catches some edge cases
    return any(type_str in t for t in entity_types)


# %% ../00_core.ipynb 12
@patch
def display_entity(self:LinkedDataKnowledge, entity_id:str) -> str:
    "Display a specific entity by ID as markdown"
    
    # First try in @graph
    for entity in self.data.get('@graph', []):
        if entity.get('@id') == entity_id:
            return _format_entity_markdown(entity)
    
    # Then try in @included if present
    for entity in self.data.get('@included', []):
        if entity.get('@id') == entity_id:
            return _format_entity_markdown(entity)
    
    # If it's the main entity in a resource-centric view
    if self.data.get('@id') == entity_id:
        return _format_entity_markdown(self.data)
    
    return f"*Entity with ID '{entity_id}' not found*"

@patch
def summarize_markdown(self:LinkedDataKnowledge) -> str:
    "Provide a concise markdown summary of the knowledge base"
    
    md = ["# Knowledge Base Summary"]
    
    # Count contexts, entities, and included entities
    context_count = len(self.data.get('@context', {}))
    graph_count = len(self.data.get('@graph', []))
    included_count = len(self.data.get('@included', [])) if '@included' in self.data else 0
    
    md.append(f"- **Contexts:** {context_count}")
    md.append(f"- **Graph Entities:** {graph_count}")
    if included_count:
        md.append(f"- **Included Entities:** {included_count}")
    
    # Summarize entity types
    all_types = {}
    
    # Check @graph
    for entity in self.data.get('@graph', []):
        entity_type = entity.get('@type')
        if isinstance(entity_type, list):
            for t in entity_type:
                all_types[t] = all_types.get(t, 0) + 1
        elif entity_type:
            all_types[entity_type] = all_types.get(entity_type, 0) + 1
    
    # Check @included
    for entity in self.data.get('@included', []):
        entity_type = entity.get('@type')
        if isinstance(entity_type, list):
            for t in entity_type:
                all_types[t] = all_types.get(t, 0) + 1
        elif entity_type:
            all_types[entity_type] = all_types.get(entity_type, 0) + 1
    
    # Check main entity if resource-centric
    if '@id' in self.data and '@type' in self.data:
        entity_type = self.data.get('@type')
        if isinstance(entity_type, list):
            for t in entity_type:
                all_types[t] = all_types.get(t, 0) + 1
        elif entity_type:
            all_types[entity_type] = all_types.get(entity_type, 0) + 1
    
    if all_types:
        md.append("\n## Entity Types")
        for t, count in sorted(all_types.items(), key=lambda x: x[1], reverse=True)[:10]:
            md.append(f"- **{t}**: {count}")
        if len(all_types) > 10:
            md.append(f"- *...and {len(all_types)-10} more types*")
    
    return "\n".join(md)


# %% ../00_core.ipynb 13
@patch
def find_entity(self:LinkedDataKnowledge, 
               entity_id:str=None, # Full or partial entity ID to find
               term_type:str=None, # Filter by type (e.g., "Class", "Property")
               label:str=None, # Find by label text
               prioritize_label:bool=True, # Whether to prioritize label matches over ID matches
               case_sensitive:bool=False # Whether searches should be case sensitive
              ) -> list: # Matching entities
    """Find entities in the graph by ID, type, or label.
    
    This function provides flexible entity lookup by:
    - ID (full URI, prefixed name, or local name)
    - Type (class or property type)
    - Label (exact or partial match)
    
    Args:
        entity_id: Full or partial entity ID to find
        term_type: Filter by type (e.g., "Class", "Property")
        label: Find by label text
        prioritize_label: Whether to prioritize label matches over ID matches
        case_sensitive: Whether searches should be case sensitive
        
    Returns:
        list: Matching entities
    """
    results = []
    label_results = []
    id_results = []
    graph = self.data.get('@graph', [])
    
    # Handle case sensitivity
    if entity_id and not case_sensitive:
        entity_id = entity_id.lower()
    if label and not case_sensitive:
        label = label.lower()
    
    # Process each entity, checking ID, type, and label as needed
    for entity in graph:
        # First check if entity matches the type filter (if specified)
        if term_type and not self._has_type(entity, term_type):
            continue  # Skip entities that don't match the type filter
        
        # Track if this entity matched any criteria
        matched = False
        
        # Match by ID if specified
        if entity_id and isinstance(entity.get('@id'), str):
            entity_uri = entity.get('@id')
            
            # Handle case sensitivity for URI
            if not case_sensitive:
                compare_uri = entity_uri.lower()
            else:
                compare_uri = entity_uri
            
            # Check for exact match, substring match, or path segment match
            if (entity_id == compare_uri or
                entity_id in compare_uri or
                compare_uri.split('/')[-1] == entity_id or
                compare_uri.split('#')[-1] == entity_id):
                
                id_results.append(entity)
                matched = True
        
        # Match by label (even if we already matched by ID)
        if label or (prioritize_label and entity_id):
            search_term = label if label else entity_id
            
            for key, value in entity.items():
                if 'label' in key.lower():
                    # Handle different label formats
                    if isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict) and '@value' in item:
                                item_value = str(item.get('@value', ''))
                                if not case_sensitive:
                                    item_value = item_value.lower()
                                
                                if search_term in item_value:
                                    label_results.append(entity)
                                    matched = True
                                    break
                            else:
                                item_str = str(item)
                                if not case_sensitive:
                                    item_str = item_str.lower()
                                    
                                if search_term in item_str:
                                    label_results.append(entity)
                                    matched = True
                                    break
                    elif isinstance(value, str):
                        if not case_sensitive:
                            compare_value = value.lower()
                        else:
                            compare_value = value
                            
                        if search_term in compare_value:
                            label_results.append(entity)
                            matched = True
                            break
        
        # If only term_type is specified (no ID or label), add any matching entity
        if term_type and not entity_id and not label and not matched:
            results.append(entity)
    
    # Special case: if only term_type is specified, return all entities that matched the type
    if term_type and not entity_id and not label:
        return results
    
    # Combine results with label matches first (if prioritizing labels)
    if prioritize_label:
        # Remove duplicates while preserving order
        seen = set()
        for entity in label_results + id_results:
            entity_id = entity.get('@id')
            if entity_id not in seen:
                seen.add(entity_id)
                results.append(entity)
    else:
        # Traditional approach: ID matches first, then label matches
        results = id_results + [e for e in label_results if e not in id_results]
    
    return results


# %% ../00_core.ipynb 17
@patch
def get_entity_description(self:LinkedDataKnowledge, entity:dict) -> str:
    "Get a formatted description of an entity"
    if not entity:
        return "No entity provided"
    
    lines = []
    
    # Entity ID
    entity_id = entity.get('@id', 'Unknown ID')
    lines.append(f"## Entity: {entity_id}")
    
    # Entity type
    entity_type = entity.get('@type', [])
    if not isinstance(entity_type, list):
        entity_type = [entity_type]
    lines.append(f"**Type**: {', '.join(entity_type)}")
    
    # Labels
    labels = []
    for key, value in entity.items():
        if 'label' in key.lower():
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict) and '@value' in item:
                        labels.append(f"{item.get('@value')} ({item.get('@language', 'no language')})")
                    else:
                        labels.append(str(item))
            else:
                labels.append(str(value))
    
    if labels:
        lines.append(f"**Labels**: {', '.join(labels)}")
    
    # Comments/Definitions
    comments = []
    for key, value in entity.items():
        if 'comment' in key.lower() or 'definition' in key.lower():
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict) and '@value' in item:
                        comments.append(item.get('@value'))
                    else:
                        comments.append(str(item))
            else:
                comments.append(str(value))
    
    if comments:
        lines.append("\n**Definition**:")
        for comment in comments:
            lines.append(f"- {comment}")
    
    # Relationships
    relationships = []
    for key, value in entity.items():
        if key not in ['@id', '@type'] and not any(x in key.lower() for x in ['label', 'comment', 'definition']):
            relationships.append((key, value))
    
    if relationships:
        lines.append("\n**Relationships**:")
        for rel_name, rel_value in relationships:
            if isinstance(rel_value, list):
                lines.append(f"- {rel_name}:")
                for item in rel_value:
                    if isinstance(item, dict) and '@id' in item:
                        lines.append(f"  - {item['@id']}")
                    elif isinstance(item, dict) and '@value' in item:
                        lines.append(f"  - {item['@value']}")
                    else:
                        lines.append(f"  - {item}")
            else:
                if isinstance(rel_value, dict) and '@id' in rel_value:
                    lines.append(f"- {rel_name}: {rel_value['@id']}")
                elif isinstance(rel_value, dict) and '@value' in rel_value:
                    lines.append(f"- {rel_name}: {rel_value['@value']}")
                else:
                    lines.append(f"- {rel_name}: {rel_value}")
    
    return "\n".join(lines)


# %% ../00_core.ipynb 18
@patch
def query(self:LinkedDataKnowledge,
         query_type:str, # Type of query: "property", "type", "value"
         query_value:str # Value to search for
         ) -> list:
    """Queries JSON-LD data for specific properties, types, or values."""
    # First, try to expand the query value if it's a prefixed term
    expanded_value = query_value
    
    # Handle prefixed terms (like schema:Person)
    if ':' in query_value and not query_value.startswith(('http://', 'https://')):
        prefix, local = query_value.split(':', 1)
        if prefix in self.data.get('@context', {}):
            prefix_uri = self.data['@context'][prefix]
            if isinstance(prefix_uri, str):
                if prefix_uri.endswith('/') or prefix_uri.endswith('#'):
                    expanded_value = f"{prefix_uri}{local}"
                else:
                    expanded_value = f"{prefix_uri}/{local}"
    
    # Handle non-prefixed terms that might be defined in context
    elif not query_value.startswith(('http://', 'https://')):
        # Check if term is defined in @context
        if query_value in self.data.get('@context', {}):
            term_def = self.data['@context'][query_value]
            if isinstance(term_def, dict) and '@id' in term_def:
                expanded_value = term_def['@id']
            elif isinstance(term_def, str):
                expanded_value = term_def
        
        # Check if there's a @vocab that would apply
        elif '@vocab' in self.data.get('@context', {}):
            vocab = self.data['@context']['@vocab']
            if vocab.endswith('/') or vocab.endswith('#'):
                expanded_value = f"{vocab}{query_value}"
            else:
                expanded_value = f"{vocab}/{query_value}"
    
    # Convert JSON-LD to expanded form for consistent access
    expanded = jsonld.expand(self.data)
    results = []
    
    if query_type == "property":
        # Find entities with a specific property (using both original and expanded)
        for entity in expanded:
            if query_value in entity or expanded_value in entity:
                results.append(entity)
    elif query_type == "type":
        # Find entities of a specific type (using both original and expanded)
        for entity in expanded:
            if '@type' not in entity:
                continue
                
            types = entity['@type']
            if not isinstance(types, list):
                types = [types]
                
            if query_value in types or expanded_value in types:
                results.append(entity)
    elif query_type == "value":
        # Find entities with properties containing a specific value
        for entity in expanded:
            for prop, values in entity.items():
                if prop == "@id" or prop == "@type":
                    continue
                for val in values:
                    if "@value" in val and val["@value"] == query_value:
                        results.append(entity)
                        break
    
    return results


# %% ../00_core.ipynb 19
def describe(self, path:str="") -> str:
    "Describe the structure at the given path in a human-readable format"
    # Implementation that combines exploration and visualization
    pass

# %% ../00_core.ipynb 20
def view(self, entity_id:str=None, term_type:str=None, label:str=None) -> None:
    "Find and display entities in a rich format"
    entities = self.find_entity(entity_id, term_type, label)
    if not entities:
        print(f"No entities found matching the criteria")
        return
    
    for entity in entities:
        display(Markdown(self.get_entity_description(entity)))

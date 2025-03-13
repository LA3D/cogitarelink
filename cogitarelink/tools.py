"""This module provides tools for AI agents to explore and interact with linked data structures. These tools are designed to work with the Claudette library to enable Claude to navigate and understand JSON-LD data."""

# AUTOGENERATED! DO NOT EDIT! File to edit: ../04_tools.ipynb.

# %% auto 0
__all__ = ['find_vocabulary_term', 'follow_relationship', 'explore_dataset', 'search_dataset', 'get_dataset_evidence',
           'collect_evidence', 'summarize_evidence']

# %% ../04_tools.ipynb 3
from fastcore.basics import *
from fastcore.meta import *
from fastcore.test import *
from IPython.display import Markdown, display
from .core import LinkedDataKnowledge
from .navigation import *
from claudette import tool, Chat, models
import json
from typing import List, Dict, Any, Optional, Union, Set
import datetime



# %% ../04_tools.ipynb 7
@tool
def find_vocabulary_term(
    term: str,  # Term to find (e.g., "Person", "schema:Person", or full URI)
    vocab_name: str = "default",  # Name of vocabulary to search in
    search_type: str = "all"  # Search by: "id", "label", "type", or "all"
) -> str:  # Definition and details of the term
    """Find a specific term in a vocabulary and return its definition.
    
    Args:
        term: The term to search for (can be a partial name, prefixed term, or full URI)
        vocab_name: Name of the vocabulary to search in (use "default" for the main vocabulary)
        search_type: How to search ("id", "label", "type", or "all")
        
    Returns:
        A markdown-formatted description of the term(s) found
    """
    # Get the knowledge base from the global context
    if 'kb' not in globals():
        return "No vocabulary loaded. Please load a vocabulary first."
    
    kb = globals()['kb']
    
    # Find entities matching the term
    entities = []
    if search_type in ["id", "all"]:
        entities.extend(kb.find_entity(entity_id=term))
    if search_type in ["label", "all"]:
        entities.extend(kb.find_entity(label=term))
    if search_type in ["type", "all"]:
        # For type searches, we need to check the @type property directly
        for entity in kb.data.get('@graph', []):
            entity_type = entity.get('@type', '')
            # Handle both list and string types
            if isinstance(entity_type, list):
                if any(term in t for t in entity_type):
                    entities.append(entity)
            elif term in str(entity_type):
                entities.append(entity)
    
    # Remove duplicates by ID
    unique_entities = []
    seen_ids = set()
    for entity in entities:
        entity_id = entity.get('@id', '')
        if entity_id not in seen_ids:
            seen_ids.add(entity_id)
            unique_entities.append(entity)
    
    if not unique_entities:
        return f"No terms found matching '{term}' in the vocabulary."
    
    # Format the results
    output = [f"# Found {len(unique_entities)} terms matching '{term}'"]
    
    for i, entity in enumerate(unique_entities):
        output.append(f"\n## Term {i+1}: {entity.get('@id', 'Unknown ID').split('/')[-1]}")
        output.append(kb.get_entity_description(entity))
    
    return "\n".join(output)


# %% ../04_tools.ipynb 10
@tool
def follow_relationship(
    entity_id: str,  # ID of the entity to start from
    relationship: str = None,  # Relationship to follow (or None to list all)
    include_inverse: bool = False  # Whether to include inverse relationships
) -> str:  # Related entities or available relationships
    """Follow a relationship from an entity to find related entities.
    
    Args:
        entity_id: The ID of the entity to start from
        relationship: The relationship to follow, or None to list available relationships
        include_inverse: Whether to include relationships where this entity is the object
        
    Returns:
        A markdown-formatted description of the related entities or available relationships
    """
    # Get the knowledge base from the global context
    if 'kb' not in globals():
        return "No vocabulary loaded. Please load a vocabulary first."
    
    kb = globals()['kb']
    
    # Find the starting entity
    entities = kb.find_entity(entity_id=entity_id)
    if not entities:
        return f"Entity '{entity_id}' not found."
    
    entity = entities[0]
    entity_id_full = entity.get('@id', 'Unknown')
    entity_label = entity_id_full.split('/')[-1]
    
    # If no relationship specified, list available relationships
    if relationship is None:
        relationships = kb.follow_relationship(entity_id_full, None, include_inverse)
        
        if not relationships:
            return f"Entity '{entity_label}' has no relationships."
        
        output = [f"# Available relationships for '{entity_label}'"]
        
        # Group relationships by type (direct vs inverse)
        direct_rels = [r for r in relationships if not r.startswith('^')]
        inverse_rels = [r[1:] for r in relationships if r.startswith('^')]
        
        if direct_rels:
            output.append("\n## Direct relationships (where this entity is the subject)")
            for rel in direct_rels:
                rel_label = rel.split('/')[-1] if '/' in rel else rel
                output.append(f"- {rel_label}")
        
        if inverse_rels:
            output.append("\n## Inverse relationships (where this entity is the object)")
            for rel in inverse_rels:
                rel_label = rel.split('/')[-1] if '/' in rel else rel
                output.append(f"- {rel_label}")
        
        return "\n".join(output)
    
    # Follow the specified relationship
    related_entities = kb.follow_relationship(entity_id_full, relationship)
    
    if not related_entities:
        return f"No entities found related to '{entity_label}' via '{relationship}'."
    
    # Format the results
    output = [f"# Entities related to '{entity_label}' via '{relationship}'"]
    
    for i, related in enumerate(related_entities):
        related_id = related.get('@id', 'Unknown')
        related_label = related_id.split('/')[-1]
        output.append(f"\n## {i+1}. {related_label}")
        output.append(kb.get_entity_description(related))
    
    return "\n".join(output)

# %% ../04_tools.ipynb 13
@tool
def explore_dataset(
    path: str = "",  # Path to explore in the dataset
    max_size: int = 4000  # Maximum size of returned JSON
) -> str:  # Dataset fragment
    """Explore the dataset structure at the given path.
    
    Args:
        path: The path to explore, using dot notation (e.g., "recordSet[0].field")
        max_size: Maximum size of the returned JSON in characters
        
    Returns:
        A markdown-formatted representation of the data at the specified path
    """
    # Get the dataset knowledge base from the global context
    if 'dataset_kb' not in globals():
        return "No dataset loaded. Please load a dataset first."
    
    dataset_kb = globals()['dataset_kb']
    
    try:
        # Navigate to the specified path
        current = dataset_kb.data
        if path:
            parts = path.split(".")
            for part in parts:
                if "[" in part and part.endswith("]"):
                    name, idx_str = part.split("[", 1)
                    idx = int(idx_str[:-1])
                    if name:
                        current = current[name][idx]
                    else:
                        current = current[idx]
                else:
                    current = current[part]
        
        # Format the result based on its type
        if isinstance(current, dict):
            # For dictionaries, show a structured view
            output = [f"# Structure at path: {path or 'root'}"]
            
            # Special handling for entities with @id and @type
            if '@id' in current:
                output.append(f"**ID**: `{current['@id']}`")
            if '@type' in current:
                type_val = current['@type']
                if isinstance(type_val, list):
                    output.append(f"**Type**: {', '.join([f'`{t}`' for t in type_val])}")
                else:
                    output.append(f"**Type**: `{type_val}`")
            
            # List other keys and their types
            output.append("\n## Properties")
            for key, value in current.items():
                if key in ['@id', '@type']:
                    continue
                    
                if isinstance(value, dict):
                    if '@id' in value:
                        output.append(f"- **{key}**: Reference to `{value['@id']}`")
                    else:
                        output.append(f"- **{key}**: Complex object with {len(value)} properties")
                elif isinstance(value, list):
                    output.append(f"- **{key}**: List with {len(value)} items")
                else:
                    output.append(f"- **{key}**: {value}")
            
            # Add a JSON representation
            json_str = json.dumps(current, indent=2)
            if len(json_str) > max_size:
                json_str = json_str[:max_size] + "..."
            output.append("\n## Raw JSON")
            output.append("```json")
            output.append(json_str)
            output.append("```")
            
            return "\n".join(output)
            
        elif isinstance(current, list):
            # For lists, show a summary and the first few items
            output = [f"# List at path: {path or 'root'}"]
            output.append(f"Contains {len(current)} items")
            
            # Show details for the first few items
            for i, item in enumerate(current[:5]):
                output.append(f"\n## Item {i+1}")
                if isinstance(item, dict):
                    if '@id' in item:
                        output.append(f"**ID**: `{item['@id']}`")
                    if '@type' in item:
                        type_val = item['@type']
                        if isinstance(type_val, list):
                            output.append(f"**Type**: {', '.join([f'`{t}`' for t in type_val])}")
                        else:
                            output.append(f"**Type**: `{type_val}`")
                    
                    # List a few key properties
                    keys = [k for k in item.keys() if k not in ['@id', '@type']]
                    if keys:
                        output.append("\n**Properties**:")
                        for key in keys[:5]:
                            value = item[key]
                            if isinstance(value, (dict, list)):
                                output.append(f"- **{key}**: Complex value")
                            else:
                                output.append(f"- **{key}**: {value}")
                        
                        if len(keys) > 5:
                            output.append(f"- ... and {len(keys) - 5} more properties")
                else:
                    output.append(f"Value: {item}")
            
            if len(current) > 5:
                output.append(f"\n... and {len(current) - 5} more items")
            
            # Add a JSON representation of the first few items
            json_str = json.dumps(current[:5], indent=2)
            if len(json_str) > max_size:
                json_str = json_str[:max_size] + "..."
            output.append("\n## Raw JSON (first 5 items)")
            output.append("```json")
            output.append(json_str)
            output.append("```")
            
            return "\n".join(output)
            
        else:
            # For simple values, just show the value
            return f"# Value at path: {path or 'root'}\n\n{current}"
            
    except (KeyError, IndexError, TypeError) as e:
        return f"Error accessing path '{path}': {str(e)}"

# %% ../04_tools.ipynb 16
@tool
def search_dataset(
    query: str,  # Text to search for in the dataset
    case_sensitive: bool = False  # Whether search should be case sensitive
) -> str:  # Search results
    """Search for text in the dataset and return matching paths.
    
    Args:
        query: Text to search for in the dataset
        case_sensitive: Whether search should be case sensitive
        
    Returns:
        A markdown-formatted list of paths where the query was found
    """
    # Get the dataset knowledge base from the global context
    if 'dataset_kb' not in globals():
        return "No dataset loaded. Please load a dataset first."
    
    dataset_kb = globals()['dataset_kb']
    
    # Search results will be stored as (path, context)
    results = []
    
    def search_obj(obj, path=""):
        """Recursively search through an object"""
        if isinstance(obj, dict):
            # Search in keys
            for k, v in obj.items():
                # Check if key contains the query
                k_str = str(k)
                if (query in k_str) if case_sensitive else (query.lower() in k_str.lower()):
                    results.append((f"{path}.{k}" if path else k, "key"))
                
                # Search in values
                search_obj(v, f"{path}.{k}" if path else k)
                
        elif isinstance(obj, list):
            # Search in list items
            for i, item in enumerate(obj):
                search_obj(item, f"{path}[{i}]")
                
        elif isinstance(obj, str):
            # Search in string values
            if (query in obj) if case_sensitive else (query.lower() in obj.lower()):
                # Truncate long strings for display
                display_val = obj[:50] + "..." if len(obj) > 50 else obj
                results.append((path, display_val))
    
    # Start the search from the root
    search_obj(dataset_kb.data)
    
    if not results:
        return f"No matches found for '{query}'"
    
    # Format the results
    output = [f"# Found {len(results)} matches for '{query}'"]
    
    # Group results by type
    key_matches = [r for r in results if r[1] == "key"]
    value_matches = [r for r in results if r[1] != "key"]
    
    if key_matches:
        output.append("\n## Matching keys")
        for path, _ in key_matches[:10]:
            output.append(f"- `{path}`")
        if len(key_matches) > 10:
            output.append(f"- ... and {len(key_matches) - 10} more")
    
    if value_matches:
        output.append("\n## Matching values")
        for path, value in value_matches[:10]:
            output.append(f"- `{path}` = \"{value}\"")
        if len(value_matches) > 10:
            output.append(f"- ... and {len(value_matches) - 10} more")
    
    return "\n".join(output)

# %% ../04_tools.ipynb 19
@tool
def get_dataset_evidence(
    topic: str,  # Topic to find evidence about
    max_results: int = 5  # Maximum number of evidence items to return
) -> str:  # Evidence from the dataset
    """Find evidence in the dataset about a specific topic.
    
    Args:
        topic: Topic to find evidence about
        max_results: Maximum number of evidence items to return
        
    Returns:
        A markdown-formatted collection of evidence about the topic
    """
    # Get the dataset knowledge base from the global context
    if 'dataset_kb' not in globals():
        return "No dataset loaded. Please load a dataset first."
    
    dataset_kb = globals()['dataset_kb']
    
    # First use search_dataset to find relevant paths
    search_results = search_dataset(topic)
    
    if "No matches found" in search_results:
        return f"No evidence found for topic: '{topic}'"
    
    # Extract paths from search results
    import re
    path_pattern = r'`([^`]+)`'
    paths = re.findall(path_pattern, search_results)
    
    # Collect evidence
    evidence = []
    
    for path in paths:
        # Skip paths that are just key names
        if path.count('.') == 0 and '[' not in path:
            continue
            
        try:
            # Navigate to the path
            current = dataset_kb.data
            parts = path.split('.')
            
            for part in parts:
                if '[' in part and part.endswith(']'):
                    name, idx_str = part.split('[', 1)
                    idx = int(idx_str[:-1])
                    if name:
                        current = current[name][idx]
                    else:
                        current = current[idx]
                else:
                    current = current[part]
            
            # Add context to the evidence
            if isinstance(current, dict):
                # For dictionaries, include ID and type if available
                context = {}
                if '@id' in current:
                    context['id'] = current['@id']
                if '@type' in current:
                    context['type'] = current['@type']
                if 'name' in current:
                    context['name'] = current['name']
                
                evidence.append({
                    'path': path,
                    'context': context,
                    'value': current
                })
            else:
                # For simple values, include the parent object for context
                parent_path = '.'.join(path.split('.')[:-1])
                last_part = path.split('.')[-1]
                
                parent = dataset_kb.data
                for part in parent_path.split('.'):
                    if '[' in part and part.endswith(']'):
                        name, idx_str = part.split('[', 1)
                        idx = int(idx_str[:-1])
                        if name:
                            parent = parent[name][idx]
                        else:
                            parent = parent[idx]
                    else:
                        parent = parent[part]
                
                context = {'property': last_part}
                if isinstance(parent, dict):
                    if '@id' in parent:
                        context['id'] = parent['@id']
                    if '@type' in parent:
                        context['type'] = parent['@type']
                    if 'name' in parent:
                        context['name'] = parent['name']
                
                evidence.append({
                    'path': path,
                    'context': context,
                    'value': current
                })
        except (KeyError, IndexError, TypeError) as e:
            # Skip paths that can't be resolved
            continue
    
    # Limit the number of evidence items
    evidence = evidence[:max_results]
    
    if not evidence:
        return f"No structured evidence found for topic: '{topic}'"
    
    # Format the evidence
    output = [f"# Evidence for topic: '{topic}'"]
    
    for i, item in enumerate(evidence):
        output.append(f"\n## Evidence {i+1}")
        output.append(f"**Path**: `{item['path']}`")
        
        # Add context information
        if item['context']:
            output.append("\n**Context**:")
            for k, v in item['context'].items():
                output.append(f"- {k}: {v}")
        
        # Add the value
        output.append("\n**Value**:")
        if isinstance(item['value'], dict):
            # For dictionaries, show a summary
            keys = list(item['value'].keys())
            output.append(f"Object with {len(keys)} properties:")
            for k in keys[:5]:
                v = item['value'][k]
                if isinstance(v, (dict, list)):
                    output.append(f"- {k}: (complex value)")
                else:
                    output.append(f"- {k}: {v}")
            if len(keys) > 5:
                output.append(f"- ... and {len(keys) - 5} more properties")
        elif isinstance(item['value'], list):
            # For lists, show a summary
            output.append(f"List with {len(item['value'])} items")
        else:
            # For simple values, show the value
            output.append(str(item['value']))
    
    return "\n".join(output)

# %% ../04_tools.ipynb 22
@tool
def collect_evidence(topic:str, observation:str, source_term:str=None, importance:str="medium") -> str:
    "Collect evidence about a topic during linked data exploration"
    global kb
    
    if not hasattr(kb, 'evidence_collection'): kb.evidence_collection = []
    
    evidence_item = {
        "topic": topic,
        "observation": observation,
        "source": source_term,
        "importance": importance,
        "timestamp": datetime.datetime.now().isoformat()
    }
    
    kb.evidence_collection.append(evidence_item)
    
    return f"Evidence collected about '{topic}' (importance: {importance}). Total evidence items: {len(kb.evidence_collection)}"


# %% ../04_tools.ipynb 23
@tool
def summarize_evidence(topic:str=None) -> str:
    "Summarize collected evidence, optionally filtered by topic"
    global kb
    
    if not hasattr(kb, 'evidence_collection') or not kb.evidence_collection:
        return "No evidence has been collected yet."
    
    # Filter by topic if provided
    if topic:
        evidence_items = [item for item in kb.evidence_collection if topic.lower() in item["topic"].lower()]
    else:
        evidence_items = kb.evidence_collection
    
    if not evidence_items:
        return f"No evidence found for topic '{topic}'."
    
    # Group evidence by topic
    topics = {}
    for item in evidence_items:
        if item["topic"] not in topics: topics[item["topic"]] = []
        topics[item["topic"]].append(item)
    
    # Format the evidence as markdown
    result = f"# Evidence Collection Summary ({len(evidence_items)} items)\n\n"
    
    # First, list high importance items
    high_importance = [item for item in evidence_items if item["importance"] == "high"]
    if high_importance:
        result += "## Key Findings\n"
        for item in high_importance:
            result += f"- **{item['topic']}**: {item['observation']}\n"
        result += "\n"
    
    # Then organize by topic
    result += "## Detailed Findings by Topic\n\n"
    for topic, items in topics.items():
        result += f"### {topic} ({len(items)} findings)\n"
        for item in items:
            result += f"- {item['observation']}"
            if item['source']: result += f" (Source: {item['source']})"
            result += "\n"
        result += "\n"
    
    # Add a section for relationships between topics
    result += "## Relationships Between Topics\n"
    result += "Consider how these topics relate to each other to form a complete data model.\n\n"
    
    return result

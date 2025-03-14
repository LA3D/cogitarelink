"""The navigation module provides tools for traversing and exploring knowledge structures. It enables LLM agents to follow relationships between entities, find paths, explore neighborhoods, and visualize knowledge graphs."""

# AUTOGENERATED! DO NOT EDIT! File to edit: ../02_navigation.ipynb.

# %% auto 0
__all__ = []

# %% ../02_navigation.ipynb 4
from fastcore.basics import *
from fastcore.meta import *
from fastcore.test import *
from IPython.display import Markdown, display
import matplotlib
import matplotlib.pyplot
import json
from typing import List, Dict, Any, Optional, Union, Set

# %% ../02_navigation.ipynb 5
from .core import *
from .vocabulary import *


# %% ../02_navigation.ipynb 7
@patch
def _is_reference_to(self:LinkedDataKnowledge, 
                    value:Any, 
                    entity_id:str
                    ) -> bool:
    """Check if a value references a specific entity ID.
    
    Helper method for relationship navigation.
    """
    if isinstance(value, dict) and '@id' in value and value['@id'] == entity_id:
        return True
    elif isinstance(value, list):
        return any(self._is_reference_to(item, entity_id) for item in value)
    return False

# %% ../02_navigation.ipynb 9
@patch
def follow_relationship(self:LinkedDataKnowledge,
                       entity_id:str, # ID of entity to start from
                       relationship:str=None, # Relationship to follow (or None to list all)
                       include_inverse:bool=False # Whether to include inverse relationships
                       ) -> Union[List[Dict], List[str]]:
    """Follow a relationship from an entity to find related entities.
    
    Args:
        entity_id: The ID of the entity to start from
        relationship: The relationship to follow, or None to list available relationships
        include_inverse: Whether to include relationships where this entity is the object
        
    Returns:
        Either a list of related entities (if relationship is specified) or 
        a list of available relationship names (if relationship is None)
    
    Examples:
        >>> kb = LinkedDataKnowledge(...)
        >>> # List available relationships
        >>> relationships = kb.follow_relationship("http://example.org/Person")
        >>> # Follow a specific relationship
        >>> related = kb.follow_relationship("http://example.org/Person", "rdfs:subClassOf")
    """
    # Find the starting entity
    entities = self.find_entity(entity_id=entity_id)
    if not entities:
        return []
    
    entity = entities[0]
    
    # If no relationship specified, list available relationships
    if relationship is None:
        relationships = []
        # Direct relationships (where this entity is the subject)
        for key in entity.keys():
            if key not in ['@id', '@type']:
                relationships.append(key)
        
        # Inverse relationships (where this entity is the object)
        if include_inverse:
            entity_id_full = entity.get('@id')
            if entity_id_full:
                for graph_entity in self.data.get('@graph', []):
                    if graph_entity.get('@id') != entity_id_full:  # Skip self-references
                        for key, value in graph_entity.items():
                            if key not in ['@id', '@type']:
                                # Check if this entity is referenced
                                if self._is_reference_to(value, entity_id_full):
                                    inverse_rel = f"^{key}"  # Mark inverse relationships with ^
                                    if inverse_rel not in relationships:
                                        relationships.append(inverse_rel)
        
        return sorted(relationships)
    
    # Handle inverse relationships (marked with ^)
    if relationship.startswith('^'):
        inverse_rel = relationship[1:]  # Remove the ^ prefix
        entity_id_full = entity.get('@id')
        if not entity_id_full:
            return []
            
        related_entities = []
        for graph_entity in self.data.get('@graph', []):
            if graph_entity.get('@id') != entity_id_full:  # Skip self-references
                if inverse_rel in graph_entity:
                    if self._is_reference_to(graph_entity[inverse_rel], entity_id_full):
                        related_entities.append(graph_entity)
        
        return related_entities
    
    # Follow the specified relationship
    if relationship not in entity:
        return []
    
    related_values = entity[relationship]
    if not isinstance(related_values, list):
        related_values = [related_values]
    
    # Collect related entities
    related_entities = []
    for value in related_values:
        # Handle reference objects (with @id)
        if isinstance(value, dict) and '@id' in value:
            related_id = value['@id']
            found_entities = self.find_entity(entity_id=related_id)
            if found_entities:
                related_entities.extend(found_entities)
            else:
                # If the entity isn't in the graph, create a minimal representation
                related_entities.append({'@id': related_id})
        # Handle literal values
        elif not isinstance(value, dict):
            # For literal values, create a virtual entity to represent it
            related_entities.append({
                '@value': value,
                '@relationship': relationship
            })
    
    return related_entities

# %% ../02_navigation.ipynb 11
@patch
def follow_relationship_across_graphs(self:LinkedDataKnowledge,
                                     entity_id:str, # ID of the entity to start from
                                     relationship:str=None, # Relationship to follow (or None to list all)
                                     include_inverse:bool=False, # Whether to include inverse relationships
                                     graph_id:str=None # Specific graph to search, or None for all
                                    ) -> Union[List[str], List[Dict]]:
    "Follow a relationship from an entity across all graphs or in a specific graph"
    results = []
    
    # Determine which graphs to search
    if graph_id:
        if not graph_id.startswith(('did:', 'http://', 'https://')):
            graph_id = f"did:cogitarelink:graph:{graph_id}"
        
        if hasattr(self, 'graphs') and graph_id in self.graphs:
            graph_data = self.graphs[graph_id]['data']
            temp_kb = LinkedDataKnowledge(graph_data)
            graph_results = temp_kb.follow_relationship(entity_id, relationship, include_inverse)
            results.extend(graph_results)
    else:
        # Search in main graph
        main_results = self.follow_relationship(entity_id, relationship, include_inverse)
        results.extend(main_results)
        
        # Search in all named graphs
        if hasattr(self, 'graphs'):
            for gid, graph_info in self.graphs.items():
                graph_data = graph_info['data']
                temp_kb = LinkedDataKnowledge(graph_data)
                graph_results = temp_kb.follow_relationship(entity_id, relationship, include_inverse)
                results.extend(graph_results)
    
    # Remove duplicates while preserving order
    if relationship is not None:
        # For entity results, deduplicate by @id
        seen_ids = set()
        unique_results = []
        for entity in results:
            entity_id = entity.get('@id')
            if entity_id and entity_id not in seen_ids:
                seen_ids.add(entity_id)
                unique_results.append(entity)
        return unique_results
    else:
        # For relationship names, deduplicate by string value
        return list(dict.fromkeys(results))

# %% ../02_navigation.ipynb 13
@patch
def navigate_path(self:LinkedDataKnowledge,
                 start_entity:str, # Starting entity ID
                 path:List[str], # List of relationships to follow
                 ) -> List[Dict]:
    """Navigate a path of relationships from a starting entity.
    
    Args:
        start_entity: The ID of the entity to start from
        path: A list of relationship names to follow in sequence
        
    Returns:
        A list of entities found at the end of the path
        
    Examples:
        >>> kb = LinkedDataKnowledge(...)
        >>> # Follow a path of relationships
        >>> results = kb.navigate_path("http://example.org/Person", 
        ...                           ["rdfs:subClassOf", "rdfs:subClassOf"])
    """
    if not path:
        return self.find_entity(entity_id=start_entity)
    
    current_entities = self.find_entity(entity_id=start_entity)
    if not current_entities:
        return []
    
    for rel in path:
        next_entities = []
        for entity in current_entities:
            entity_id = entity.get('@id')
            if entity_id:
                related = self.follow_relationship(entity_id, rel)
                next_entities.extend(related)
        
        if not next_entities:
            return []  # Path ended prematurely
        
        current_entities = next_entities
    
    return current_entities

# %% ../02_navigation.ipynb 15
@patch
def explore_graph(self:LinkedDataKnowledge,
                 graph_id:str, # Graph ID to explore
                 entity_id:str=None, # Specific entity to examine (optional)
                 property_name:str=None, # Specific property to examine (optional)
                 sample_size:int=5 # Number of sample entities to show
                ) -> str:
    "Explore a graph or specific entity within a graph"
    # Ensure graph_id is properly formatted
    if not graph_id.startswith(('did:', 'http://', 'https://')):
        graph_id = f"did:cogitarelink:graph:{graph_id}"
    
    # Check if graph exists
    if not hasattr(self, 'graphs') or graph_id not in self.graphs:
        # Check if we're trying to explore the main graph
        if graph_id == "did:cogitarelink:graph:main":
            graph_data = self.data
        else:
            return f"Graph not found: {graph_id}"
    else:
        graph_data = self.graphs[graph_id]['data']
    
    # If a specific entity is requested
    if entity_id:
        # Find the entity in the graph
        entity = None
        
        # Look in @graph
        for e in graph_data.get('@graph', []):
            if e.get('@id') == entity_id or e.get('@id').endswith(entity_id):
                entity = e
                break
        
        # If not found, look in @included if present
        if not entity and '@included' in graph_data:
            for e in graph_data['@included']:
                if e.get('@id') == entity_id or e.get('@id').endswith(entity_id):
                    entity = e
                    break
        
        # If not found, check if the main entity itself matches
        if not entity and '@id' in graph_data and (graph_data['@id'] == entity_id or graph_data['@id'].endswith(entity_id)):
            entity = graph_data
        
        if entity:
            # If a specific property is requested
            if property_name:
                if property_name in entity:
                    return f"# Property: {property_name}\n\n```json\n{json.dumps(entity[property_name], indent=2)}\n```"
                else:
                    return f"Property not found: {property_name}"
            
            # Return the full entity
            return f"# Entity: {entity.get('@id')}\n\n```json\n{json.dumps(entity, indent=2)}\n```"
        
        return f"Entity not found: {entity_id}"
    
    # Otherwise, provide an overview of the graph
    entities = graph_data.get('@graph', [])
    
    # Also include entities from @included if present
    included_entities = graph_data.get('@included', [])
    
    # Include the main entity if it has an @id
    if '@id' in graph_data:
        main_entity = {k: v for k, v in graph_data.items() if k not in ['@graph', '@included', '@context']}
        if '@id' in main_entity:
            entities = [main_entity] + entities
    
    total_entities = len(entities) + len(included_entities)
    
    output = [
        f"# Graph: {graph_id}",
        f"Contains {total_entities} entities ({len(entities)} in @graph, {len(included_entities)} in @included)",
        ""
    ]
    
    # Count entity types across both @graph and @included
    type_counts = {}
    for entity in entities + included_entities:
        entity_type = entity.get('@type')
        if isinstance(entity_type, list):
            for t in entity_type:
                type_counts[t] = type_counts.get(t, 0) + 1
        elif entity_type:
            type_counts[entity_type] = type_counts.get(entity_type, 0) + 1
    
    if type_counts:
        output.append("## Entity Types")
        for t, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            output.append(f"- {t}: {count}")
        if len(type_counts) > 10:
            output.append(f"- ... and {len(type_counts) - 10} more types")
        output.append("")
    
    # Sample entities from both @graph and @included
    all_entities = entities + included_entities
    sample_entities = all_entities[:min(sample_size, len(all_entities))]
    
    output.append(f"## Sample Entities (showing {len(sample_entities)} of {total_entities})")
    for entity in sample_entities:
        entity_id = entity.get('@id', 'Unknown ID')
        entity_type = entity.get('@type', 'Unknown Type')
        if isinstance(entity_type, list):
            entity_type = ', '.join(entity_type)
        
        output.append(f"- **{entity_id}** (Type: {entity_type})")
    
    return "\n".join(output)


# %% ../02_navigation.ipynb 16
@patch
def get_neighborhood(self:LinkedDataKnowledge,
                    entity_id:str, # Central entity
                    depth:int=1, # How many relationship steps to include
                    max_relations:int=None, # Maximum number of relations to follow (None for all)
                    include_inverse:bool=False # Whether to include inverse relationships
                    ) -> Dict:
    """Get a subgraph centered around an entity.
    
    Args:
        entity_id: The ID of the central entity
        depth: How many relationship steps to include (1 = direct relationships only)
        max_relations: Maximum number of relationships to follow per entity
        include_inverse: Whether to include inverse relationships
        
    Returns:
        A dictionary with the subgraph in JSON-LD format
        
    Examples:
        >>> kb = LinkedDataKnowledge(...)
        >>> # Get the immediate neighborhood of an entity
        >>> subgraph = kb.get_neighborhood("http://example.org/Person")
        >>> # Get a larger neighborhood with depth 2
        >>> subgraph = kb.get_neighborhood("http://example.org/Person", depth=2)
    """
    # Find the central entity
    entities = self.find_entity(entity_id=entity_id)
    if not entities:
        return {"@graph": []}
    
    central_entity = entities[0]
    collected_entities = {central_entity.get('@id'): central_entity}
    
    # BFS to explore the neighborhood
    current_ids = [central_entity.get('@id')]
    visited = set(current_ids)
    
    for _ in range(depth):
        next_ids = []
        
        for current_id in current_ids:
            # Get relationships for this entity
            # Pass the include_inverse parameter to respect the setting
            relationships = self.follow_relationship(current_id, None, include_inverse)
            
            # Limit the number of relationships if specified
            if max_relations is not None and len(relationships) > max_relations:
                relationships = relationships[:max_relations]
            
            # Follow each relationship
            for rel in relationships:
                related_entities = self.follow_relationship(current_id, rel)
                
                for entity in related_entities:
                    entity_id = entity.get('@id')
                    if entity_id and entity_id not in visited:
                        collected_entities[entity_id] = entity
                        next_ids.append(entity_id)
                        visited.add(entity_id)
        
        current_ids = next_ids
        if not current_ids:
            break  # No more entities to explore
    
    # Create a subgraph with the collected entities
    subgraph = {
        "@context": self.data.get('@context', {}),
        "@graph": list(collected_entities.values())
    }
    
    return subgraph


# %% ../02_navigation.ipynb 18
@patch
def get_neighborhood_across_graphs(self:LinkedDataKnowledge,
                                  entity_id:str, # Central entity
                                  depth:int=1, # How many relationship steps to include
                                  max_relations:int=None, # Maximum number of relations to follow per entity
                                  include_inverse:bool=False, # Whether to include inverse relationships
                                  include_all_graphs:bool=True, # Whether to include all graphs
                                  graph_ids:List[str]=None, # Specific graphs to include, or None for all if include_all_graphs=True
                                  debug:bool=False # Enable debug output
                                 ) -> Dict:
    "Get a subgraph centered around an entity, searching across multiple graphs"
    result = {"@context": {}, "@graph": []}
    
    # Find the entity in all graphs
    entity_found = False
    seen_entity_ids = set()
    
    # First check the main graph
    main_neighborhood = self.get_neighborhood(entity_id, depth, max_relations, include_inverse)
    if debug:
        print(f"Main neighborhood entities: {len(main_neighborhood.get('@graph', []))}")
        for e in main_neighborhood.get('@graph', []):
            print(f"  - {e.get('@id')}")
            
    if main_neighborhood and len(main_neighborhood.get('@graph', [])) > 0:
        entity_found = True
        
        # Add entities, avoiding duplicates
        for entity in main_neighborhood.get('@graph', []):
            entity_id = entity.get('@id')
            if entity_id and entity_id not in seen_entity_ids:
                seen_entity_ids.add(entity_id)
                result["@graph"].append(entity)
        
        # Merge contexts
        if '@context' in main_neighborhood and '@context' in result:
            if isinstance(main_neighborhood['@context'], dict) and isinstance(result['@context'], dict):
                result['@context'].update(main_neighborhood['@context'])
    
    if debug:
        print(f"After main graph, result has {len(result.get('@graph', []))} entities")
        print(f"Seen IDs: {seen_entity_ids}")
    
    # Then check named graphs
    if hasattr(self, 'graphs'):
        graphs_to_check = []
        if include_all_graphs:
            graphs_to_check = list(self.graphs.keys())
        elif graph_ids:
            graphs_to_check = [
                gid if gid.startswith(('did:', 'http://', 'https://')) else f"did:cogitarelink:graph:{gid}"
                for gid in graph_ids
            ]
        
        if debug:
            print(f"Checking {len(graphs_to_check)} named graphs")
            
        for graph_id in graphs_to_check:
            if graph_id in self.graphs:
                if debug:
                    print(f"Processing graph: {graph_id}")
                    
                graph_data = self.graphs[graph_id]['data']
                temp_kb = LinkedDataKnowledge(graph_data)
                graph_neighborhood = temp_kb.get_neighborhood(entity_id, depth, max_relations, include_inverse)
                
                if debug:
                    print(f"  Graph neighborhood entities: {len(graph_neighborhood.get('@graph', []))}")
                    for e in graph_neighborhood.get('@graph', []):
                        print(f"    - {e.get('@id')}")
                
                if graph_neighborhood and len(graph_neighborhood.get('@graph', [])) > 0:
                    entity_found = True
                    
                    # Add entities, avoiding duplicates
                    for entity in graph_neighborhood.get('@graph', []):
                        entity_id = entity.get('@id')
                        if entity_id and entity_id not in seen_entity_ids:
                            if debug:
                                print(f"  Adding new entity: {entity_id}")
                            seen_entity_ids.add(entity_id)
                            result["@graph"].append(entity)
                        elif debug:
                            print(f"  Skipping duplicate: {entity_id}")
                    
                    # Merge contexts
                    if '@context' in graph_neighborhood and '@context' in result:
                        if isinstance(graph_neighborhood['@context'], dict) and isinstance(result['@context'], dict):
                            result['@context'].update(graph_neighborhood['@context'])
    
    if not entity_found:
        return {"@context": {}, "@graph": []}
    
    if debug:
        print(f"Final result has {len(result.get('@graph', []))} entities")
        print(f"Final seen IDs: {seen_entity_ids}")
    
    return result


# %% ../02_navigation.ipynb 21
@patch
def visualize_neighborhood(self:LinkedDataKnowledge,
                          entity_id:str, # Central entity
                          depth:int=1, # How many relationship steps to include
                          max_relations:int=None, # Maximum number of relations per entity
                          include_inverse:bool=True, # Whether to include inverse relationships
                          ) -> None:
    """Visualize the neighborhood of an entity.
    
    This method creates a visualization of the subgraph centered around an entity.
    It requires networkx and matplotlib to be installed.
    
    Args:
        entity_id: The ID of the central entity
        depth: How many relationship steps to include
        max_relations: Maximum number of relationships to follow per entity
        include_inverse: Whether to include inverse relationships
    """
    try:
        import networkx as nx
        import matplotlib.pyplot as plt
        from matplotlib.lines import Line2D
    except ImportError:
        print("This visualization requires networkx and matplotlib. Install with:")
        print("pip install networkx matplotlib")
        return
    
    # Get the neighborhood
    subgraph = self.get_neighborhood(entity_id, depth, max_relations, include_inverse)
    entities = subgraph.get('@graph', [])
    
    if not entities:
        print(f"No entities found for {entity_id}")
        return
    
    # Create a graph
    G = nx.DiGraph()
    
    # Add nodes
    for entity in entities:
        entity_id = entity.get('@id')
        if not entity_id:
            continue
            
        # Get a label for the node
        label = entity_id.split('/')[-1]
        if '#' in label:
            label = label.split('#')[-1]
            
        # Get entity type
        entity_type = entity.get('@type')
        if isinstance(entity_type, list):
            entity_type = entity_type[0] if entity_type else "Unknown"
            
        # Simplify type for display
        if isinstance(entity_type, str):
            if '/' in entity_type:
                entity_type = entity_type.split('/')[-1]
            if '#' in entity_type:
                entity_type = entity_type.split('#')[-1]
        
        G.add_node(entity_id, label=label, type=entity_type)
    
    # Add edges
    for entity in entities:
        source_id = entity.get('@id')
        if not source_id:
            continue
            
        for rel, values in entity.items():
            if rel in ['@id', '@type']:
                continue
                
            if not isinstance(values, list):
                values = [values]
                
            for value in values:
                if isinstance(value, dict) and '@id' in value:
                    target_id = value['@id']
                    if target_id in G:
                        # Simplify relationship name
                        rel_label = rel.split('/')[-1]
                        if '#' in rel_label:
                            rel_label = rel_label.split('#')[-1]
                            
                        G.add_edge(source_id, target_id, label=rel_label)
    
    # Create a figure
    plt.figure(figsize=(12, 10))
    
    # Use a layout that works well for small graphs
    pos = nx.spring_layout(G, k=0.5, iterations=50)
    
    # Draw nodes with different colors based on type
    node_types = set(nx.get_node_attributes(G, 'type').values())
    color_map = plt.cm.get_cmap('tab10', len(node_types))
    type_to_color = {t: color_map(i) for i, t in enumerate(node_types)}
    
    for t in node_types:
        nodes = [n for n, data in G.nodes(data=True) if data.get('type') == t]
        nx.draw_networkx_nodes(G, pos, nodelist=nodes, node_color=[type_to_color[t]],
                              node_size=500, alpha=0.8)
    
    # Draw edges
    nx.draw_networkx_edges(G, pos, width=1.0, alpha=0.5, arrowsize=15)
    
    # Draw labels
    labels = nx.get_node_attributes(G, 'label')
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=10)
    
    # Draw edge labels
    edge_labels = nx.get_edge_attributes(G, 'label')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8)
    
    # Create a legend
    legend_elements = [Line2D([0], [0], marker='o', color='w', markerfacecolor=type_to_color[t],
                             label=t, markersize=10) for t in node_types]
    plt.legend(handles=legend_elements, loc='upper right')
    
    plt.title(f"Neighborhood of {entity_id.split('/')[-1]}", fontsize=14)
    plt.axis('off')
    plt.tight_layout()
    plt.show()

# %% ../02_navigation.ipynb 26
@patch
def find_paths(self:LinkedDataKnowledge,
              start_entity:str, # Starting entity ID
              end_entity:str, # Target entity ID
              max_depth:int=3, # Maximum path length
              ) -> List[List[Dict]]:
    """Find paths between two entities.
    
    Args:
        start_entity: The ID of the starting entity
        end_entity: The ID of the target entity
        max_depth: Maximum path length to consider
        
    Returns:
        A list of paths, where each path is a list of entities
        
    Examples:
        >>> kb = LinkedDataKnowledge(...)
        >>> # Find paths between two entities
        >>> paths = kb.find_paths("http://example.org/Person", 
        ...                      "http://example.org/Thing")
    """
    # Find the start and end entities
    start_entities = self.find_entity(entity_id=start_entity)
    end_entities = self.find_entity(entity_id=end_entity)
    
    if not start_entities or not end_entities:
        return []
    
    start_id = start_entities[0].get('@id')
    end_id = end_entities[0].get('@id')
    
    if not start_id or not end_id:
        return []
    
    # Special case: start and end are the same
    if start_id == end_id:
        return [[start_entities[0]]]
    
    # BFS to find paths
    paths = []
    queue = [([start_id], set([start_id]))]  # (path, visited)
    
    while queue and len(paths) < 10:  # Limit to 10 paths for efficiency
        path, visited = queue.pop(0)
        current_id = path[-1]
        
        # Check if we've reached the target
        if current_id == end_id:
            # Convert path of IDs to path of entities
            entity_path = []
            for path_id in path:
                entities = self.find_entity(entity_id=path_id)
                if entities:
                    entity_path.append(entities[0])
            paths.append(entity_path)
            continue
        
        # Stop if we've reached max depth
        if len(path) >= max_depth + 1:  # +1 because path includes start entity
            continue
        
        # Explore neighbors
        relationships = self.follow_relationship(current_id, None)
        for rel in relationships:
            related_entities = self.follow_relationship(current_id, rel)
            for entity in related_entities:
                next_id = entity.get('@id')
                if next_id and next_id not in visited:
                    new_path = path + [next_id]
                    new_visited = visited.copy()
                    new_visited.add(next_id)
                    queue.append((new_path, new_visited))
    
    return paths


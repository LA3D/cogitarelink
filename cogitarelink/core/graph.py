"""Triple store with flexible backends for managing semantic data."""

# AUTOGENERATED! DO NOT EDIT! File to edit: ../../07_graph.ipynb.

# %% ../../07_graph.ipynb 3
from __future__ import annotations
from typing import Any, Dict, List, Tuple, Iterable
import uuid

from .debug import get_logger
from .entity import Entity
log = get_logger("graph")

# optional rdflib
try:
    from rdflib import Graph, ConjunctiveGraph, URIRef, Dataset
    _HAS_RDFLIB = True
except ModuleNotFoundError:
    _HAS_RDFLIB = False

# %% auto 0
__all__ = ['log', 'GraphBackend', 'InMemoryGraph', 'GraphManager']

# %% ../../07_graph.ipynb 5
class GraphBackend:
    "Backend protocol â€“ concrete classes must implement these methods."

    def add_nquads(self, nquads: str, graph_id: str | None = None) -> None: ...
    def triples(self, subj=None, pred=None, obj=None) -> Iterable[Tuple]: ...
    def size(self) -> int: ...
    def add_named_graph(self, graph_id: str, nquads: str): ...

# %% ../../07_graph.ipynb 7
class InMemoryGraph(GraphBackend):
    """In-memory graph using rdflib ConjunctiveGraph as a lightweight fallback."""
    def __init__(self):
        # Use RDFLib Graph instead of deprecated ConjunctiveGraph
        self._g = Graph()
        self._manual = False
        self._triples: set[tuple[str,str,str]] = set()

    def add_nquads(self, nquads: str, graph_id: str | None = None) -> None:
        # Fallback to manual parsing if no absolute IRIs present
        if '://' not in nquads:
            self._manual = True
            for line in nquads.strip().splitlines():
                parts = line.rstrip(' .').split(' ', 3)
                if len(parts) >= 3:
                    s, p, o = parts[0], parts[1], parts[2]
                    self._triples.add((s, p, o))
            return
        # Use rdflib to parse N-Quads or N-Triples, with nt fallback
        try:
            self._g.parse(data=nquads, format='nquads')
        except Exception:
            # Fallback to N-Triples parser
            self._g.parse(data=nquads, format='nt')

    def triples(self, subj=None, pred=None, obj=None):
        # Yield from manual store if active
        if self._manual:
            for s, p, o in self._triples:
                if subj and subj != s:   continue
                if pred and pred != p:   continue
                if obj  and obj  != o:   continue
                yield s, p, o
            return
        # Otherwise yield from rdflib graph
        yield from self._g.triples((subj, pred, obj))

    def size(self) -> int:
        # Count manual triples if fallback, else rdflib graph size
        return len(self._triples) if self._manual else len(self._g)

    def add_named_graph(self, graph_id: str, nquads: str):
        # Delegate to add_nquads for named graphs
        self.add_nquads(nquads, graph_id)


# %% ../../07_graph.ipynb 9
if _HAS_RDFLIB:
    class RDFLibGraph(GraphBackend):
        "Delegate to rdflib Dataset (quad store)."
        def __init__(self):
            self.ds = Dataset()

        def add_nquads(self, nquads: str, graph_id: str | None = None) -> None:
            self.ds.parse(data=nquads, format="nquads")

        def triples(self, subj=None, pred=None, obj=None):
            q = self.ds.quads((subj, pred, obj, None))
            for s, p, o, _ctx in q: yield s, p, o

        def size(self): return len(self.ds)
        def add_named_graph(self, graph_id, nquads):
            g = self.ds.graph(graph_id)
            g.parse(data=nquads, format="nquads")

# %% ../../07_graph.ipynb 11
class GraphManager:
    """
    Facade that auto-selects backend.

    Parameters
    ----------
    use_rdflib : bool | 'auto'
        * 'auto'  â†’ choose rdflib when import succeeded.
        * True    â†’ require rdflib else RuntimeError.
        * False   â†’ force in-memory backend.
    """

    def __init__(self, use_rdflib: bool | str = "auto"):
        if use_rdflib == "auto":
            use_rdflib = _HAS_RDFLIB
        if use_rdflib:
            if not _HAS_RDFLIB:
                raise RuntimeError("rdflib not available")
            self._backend: GraphBackend = RDFLibGraph()          # type: ignore
        else:
            self._backend = InMemoryGraph()
        # Store parent-child relationships
        self.parent_child_map: Dict[str, List[str]] = {}
        # Track named graphs for @graph entries
        self.named_graphs: Dict[str, List[str]] = {}

    # ------------------------------------------------------------------
    # proxy helpers
    # ------------------------------------------------------------------
    def ingest_nquads(self, nquads: str, graph_id: str | None = None): 
        self._backend.add_nquads(nquads, graph_id)
    
    def query(self, subj=None, pred=None, obj=None):
        return list(self._backend.triples(subj, pred, obj))
    
    def size(self): 
        return self._backend.size()
    
    def ingest_entity(self, ent:"Entity", parent_id: str | None = None):
        """
        Ingest entity and its children into the graph store
        
        Parameters
        ----------
        ent: Entity to ingest
        parent_id: Optional ID of parent entity for tracking relationships
        """
        # Check if the entity contains a @graph array (multi-graph document)
        if '@graph' in ent.content and isinstance(ent.content['@graph'], list):
            # Process each @graph entry as a separate named graph
            self._process_graph_array(ent)
        else:
            # Standard single-entity processing
            # First ingest the entity itself
            self.ingest_nquads(ent.normalized)
            
            # Track parent-child relationship
            if parent_id:
                if parent_id not in self.parent_child_map:
                    self.parent_child_map[parent_id] = []
                self.parent_child_map[parent_id].append(ent.id)
                
                # Add parent-child relationship as a triple 
                parent_rel = f'<{parent_id}> <http://schema.org/hasPart> <{ent.id}> .'
                self.ingest_nquads(parent_rel)
                
                # Also add inverse relationship
                child_rel = f'<{ent.id}> <http://schema.org/isPartOf> <{parent_id}> .'
                self.ingest_nquads(child_rel)
            
            # Process each child entity
            for child in ent.children:
                # Create a named graph for the child
                graph_id = f"{ent.id}#child"
                self._backend.add_named_graph(graph_id, child.normalized)
                
                # Also ingest the child with parent relationship
                self.ingest_entity(child, ent.id)
    
    def _process_graph_array(self, ent:"Entity"):
        """
        Process an entity containing a @graph array
        Treats each graph entry as a separate named graph
        
        Parameters
        ----------
        ent: Entity with @graph property
        """
        # Start a list to track graph IDs
        graph_entries = []
        shared_context = ent.as_json.get('@context', {})
        
        # Process each entry in the @graph array
        for i, graph_entry in enumerate(ent.content['@graph']):
            if not isinstance(graph_entry, dict):
                continue
                
            # Generate a unique graph ID if not provided
            entry_id = graph_entry.get('@id')
            if not entry_id:
                entry_id = f"urn:graph:{uuid.uuid4()}"
                graph_entry['@id'] = entry_id
            
            # Create a named graph for this entry
            graph_id = entry_id
            
            # Apply the shared context if entry doesn't have its own
            if '@context' not in graph_entry:
                graph_entry_with_context = {**graph_entry, '@context': shared_context}
            else:
                graph_entry_with_context = graph_entry
                
            # Create an Entity for this graph entry
            graph_entity = Entity(vocab=ent.vocab, content=graph_entry_with_context)
            
            # Store the entity in its own named graph
            self._backend.add_named_graph(graph_id, graph_entity.normalized)
            
            # Track this graph entry
            graph_entries.append(entry_id)
            
            # Also process any children of this graph entry
            for child in graph_entity.children:
                child_graph_id = f"{entry_id}#child"
                self._backend.add_named_graph(child_graph_id, child.normalized)
                self.ingest_entity(child, entry_id)
        
        # Store the list of graph entries for this entity
        self.named_graphs[ent.id] = graph_entries
        
        # Also ingest the container entity itself in the default graph
        container_entity = {
            '@id': ent.id,
            '@type': 'GraphContainer',
            'graphs': graph_entries
        }
        if shared_context:
            container_entity['@context'] = shared_context
            
        container = Entity(vocab=ent.vocab, content=container_entity)
        self.ingest_nquads(container.normalized)
    
    def get_children(self, entity_id: str) -> List[str]:
        """Get all child entity IDs for a given entity"""
        return self.parent_child_map.get(entity_id, [])
        
    def get_graph_entries(self, entity_id: str) -> List[str]:
        """Get all named graph entry IDs for a @graph container entity"""
        return self.named_graphs.get(entity_id, [])

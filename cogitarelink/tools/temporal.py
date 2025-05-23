"""Integration of LLM reasoning with temporal knowledge graphs"""

# AUTOGENERATED! DO NOT EDIT! File to edit: ../../73_temporal_llm_integration.ipynb.

# %% auto 0
__all__ = ['log', 'TEMPORAL_FUNCTION_SPEC', 'temporal_reasoning_tool', 'integrate_temporal_with_shacl_reasoning']

# %% ../../73_temporal_llm_integration.ipynb 2
from typing import Union, List, Dict, Tuple, Optional
from pydantic import BaseModel, ConfigDict
from rdflib import Graph, Namespace, URIRef, Literal as RDFLiteral, BNode
from rdflib.namespace import RDF, RDFS, OWL, XSD, TIME
from pyshacl import validate
import uuid
from ..core.graph import GraphManager
from ..reason.prov import wrap_patch_with_prov
from ..core.debug import get_logger
from cogitarelink.core.temporal import (
    TimeInstant, TimeInterval, Event, InstantReification, 
    IntervalReification, LifespanReification, Namespaces,
    infer_temporal_relations, event_to_jsonld, create_test_events
)

# %% ../../73_temporal_llm_integration.ipynb 3
log = get_logger("temporal.llm")

# %% ../../73_temporal_llm_integration.ipynb 4
TEMPORAL_FUNCTION_SPEC: Dict = {
  "name": "temporal_reasoning",
  "description": "Reason over temporal events and their relationships",
  "parameters": {
    "type": "object",
    "properties": {
      "operation": {
        "type": "string",
        "enum": ["analyze_relations", "calculate_duration", "check_overlap", "find_participants"],
        "description": "Operation to perform on temporal data"
      },
      "event_data": {
        "type": "string",
        "description": "JSON-LD event data to analyze"
      },
      "query_params": {
        "type": "object",
        "description": "Additional parameters for the operation"
      }
    },
    "required": ["operation", "event_data"]
  }
}

# %% ../../73_temporal_llm_integration.ipynb 5
def temporal_reasoning_tool(operation: str, event_data: str, query_params: Optional[Dict] = None) -> str:
    """Tool for temporal reasoning over event data
    
    Args:
        operation: Operation to perform (analyze_relations, calculate_duration, check_overlap, find_participants)
        event_data: JSON-LD event data to analyze
        query_params: Additional parameters for the operation
        
    Returns:
        Results of the temporal reasoning operation as JSON string
    """
    # Parse the event data from JSON-LD
    try:
        event_json = json.loads(event_data) if isinstance(event_data, str) else event_data
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON-LD data"})
    
    # Create a graph from the JSON-LD
    g = Graph()
    try:
        g.parse(data=json.dumps(event_json), format="json-ld")
    except Exception as e:
        return json.dumps({"error": f"Error parsing JSON-LD: {str(e)}"})
    
    # Apply temporal inference
    inferred_graph = infer_temporal_relations(g)
    
    # Process according to operation
    if operation == "analyze_relations":
        return _analyze_temporal_relations(inferred_graph, query_params or {})
    elif operation == "calculate_duration":
        return _calculate_durations(inferred_graph, query_params or {})
    elif operation == "check_overlap":
        return _check_event_overlap(inferred_graph, query_params or {})
    elif operation == "find_participants":
        return _find_event_participants(inferred_graph, query_params or {})
    else:
        return json.dumps({"error": f"Unknown operation: {operation}"})

# %% ../../73_temporal_llm_integration.ipynb 6
def _analyze_temporal_relations(graph, params):
    """Analyze temporal relationships between events in the graph"""
    # Query for temporal relationships
    query = """
    PREFIX temp: <https://example.org/temporal-relations#>
    PREFIX event: <https://example.org/event-ontology#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT ?event1 ?event1Label ?relation ?event2 ?event2Label
    WHERE {
        ?event1 a event:Event ;
               rdfs:label ?event1Label ;
               event:hasTimeInterval ?interval1 .
        ?interval1 ?relation ?interval2 .
        ?event2 a event:Event ;
               rdfs:label ?event2Label ;
               event:hasTimeInterval ?interval2 .
        FILTER(STRSTARTS(STR(?relation), STR(temp:)))
        FILTER(?event1 != ?event2)
    }
    ORDER BY ?event1 ?relation ?event2
    """
    
    results = graph.query(query)
    
    relations = []
    for row in results:
        relation_name = str(row.relation).split('#')[-1]
        relations.append({
            "event1": str(row.event1),
            "event1Name": str(row.event1Label),
            "relation": relation_name,
            "event2": str(row.event2),
            "event2Name": str(row.event2Label)
        })
    
    return json.dumps({
        "operation": "analyze_relations",
        "relations": relations,
        "count": len(relations)
    })

# %% ../../73_temporal_llm_integration.ipynb 7
def _calculate_durations(graph, params):
    """Calculate durations of events in the graph"""
    # Query for event durations
    query = """
    PREFIX event: <https://example.org/event-ontology#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX time: <http://www.w3.org/2006/time#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    
    SELECT ?event ?eventLabel ?start ?end
    WHERE {
        ?event a event:Event ;
               rdfs:label ?eventLabel ;
               event:hasTimeInterval ?interval .
        ?interval time:hasBeginning/time:inXSDDateTime ?start .
        OPTIONAL { ?interval time:hasEnd/time:inXSDDateTime ?end . }
    }
    ORDER BY ?start
    """
    
    results = graph.query(query)
    
    durations = []
    for row in results:
        event_id = str(row.event)
        event_name = str(row.eventLabel)
        start_time = row.start.toPython() if hasattr(row.start, 'toPython') else str(row.start)
        
        if hasattr(row, 'end') and row.end:
            end_time = row.end.toPython() if hasattr(row.end, 'toPython') else str(row.end)
            
            # Calculate duration if both start and end are available
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                duration_seconds = (end_dt - start_dt).total_seconds()
                duration_str = str(timedelta(seconds=duration_seconds))
            except Exception as e:
                duration_seconds = None
                duration_str = f"Error: {str(e)}"
        else:
            end_time = None
            duration_seconds = None
            duration_str = "Unknown (no end time)"
        
        durations.append({
            "eventId": event_id,
            "eventName": event_name,
            "startTime": start_time,
            "endTime": end_time,
            "durationSeconds": duration_seconds,
            "durationFormatted": duration_str
        })
    
    return json.dumps({
        "operation": "calculate_duration",
        "durations": durations,
        "count": len(durations)
    })

# %% ../../73_temporal_llm_integration.ipynb 8
def _check_event_overlap(graph, params):
    """Check for overlapping events in the graph"""
    # Query for overlapping events
    query = """
    PREFIX temp: <https://example.org/temporal-relations#>
    PREFIX event: <https://example.org/event-ontology#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT ?event1 ?event1Label ?event2 ?event2Label
    WHERE {
      ?event1 a event:Event ;
             rdfs:label ?event1Label ;
             event:hasTimeInterval ?interval1 .
      ?event2 a event:Event ;
             rdfs:label ?event2Label ;
             event:hasTimeInterval ?interval2 .
      # Get events that overlap in the temporal sense
      {
        ?interval1 temp:overlaps ?interval2 .
      } UNION {
        ?interval1 temp:contains ?interval2 .
      } UNION {
        ?interval1 temp:during ?interval2 .
      }
      FILTER(?event1 != ?event2)
    }
    """
    
    results = graph.query(query)
    
    overlaps = []
    for row in results:
        overlaps.append({
            "event1": str(row.event1),
            "event1Name": str(row.event1Label),
            "event2": str(row.event2),
            "event2Name": str(row.event2Label),
        })
    
    return json.dumps({
        "operation": "check_overlap",
        "overlaps": overlaps,
        "hasOverlaps": len(overlaps) > 0,
        "count": len(overlaps)
    })

# %% ../../73_temporal_llm_integration.ipynb 9
def _find_event_participants(graph, params):
    """Find participants in events from the graph"""
    # Query for event participants
    query = """
    PREFIX event: <https://example.org/event-ontology#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT ?event ?eventLabel ?participant ?participantName ?role
    WHERE {
        ?event a event:Event ;
               rdfs:label ?eventLabel ;
               event:hasParticipant ?participant .
        OPTIONAL { ?participant rdfs:label ?participantName . }
        OPTIONAL { ?participant event:hasRole ?role . }
    }
    ORDER BY ?event ?participant
    """
    
    results = graph.query(query)
    
    # Organize participants by event
    events = {}
    for row in results:
        event_id = str(row.event)
        if event_id not in events:
            events[event_id] = {
                "eventId": event_id,
                "eventName": str(row.eventLabel),
                "participants": []
            }
        
        participant = {
            "participantId": str(row.participant),
            "participantName": str(row.participantName) if hasattr(row, 'participantName') and row.participantName else None,
            "role": str(row.role) if hasattr(row, 'role') and row.role else None
        }
        
        events[event_id]["participants"].append(participant)
    
    return json.dumps({
        "operation": "find_participants",
        "events": list(events.values()),
        "count": len(events)
    })

# %% ../../73_temporal_llm_integration.ipynb 10
def integrate_temporal_with_shacl_reasoning(event_data, shapes_turtle=None, query=None):
    """Integrate temporal reasoning with SHACL validation
    
    Args:
        event_data: Event data as JSON-LD
        shapes_turtle: Optional SHACL shapes in turtle format
        query: Optional SPARQL CONSTRUCT query
        
    Returns:
        Combined reasoning results
    """
    # First use the reason_over function from sandbox module
    jsonld_str = json.dumps(event_data) if isinstance(event_data, dict) else event_data
    patch_jsonld, summary = reason_over(
        jsonld=jsonld_str,
        shapes_turtle=shapes_turtle,
        query=query
    )
    
    # Now perform temporal reasoning on the result
    temporal_result = temporal_reasoning_tool(
        operation="analyze_relations",
        event_data=patch_jsonld
    )
    
    return {
        "shacl_summary": summary,
        "temporal_analysis": json.loads(temporal_result),
        "combined_jsonld": json.loads(patch_jsonld)
    }

#!/usr/bin/env python
"""
Explore an external JSON-LD context with cogitarelink
"""

from cogitarelink.vocab.registry import VocabularyRegistry
from cogitarelink.vocab.composer import ContextComposer
from cogitarelink.core.context import ContextProcessor
from cogitarelink.core.entity import Entity
import json
from typing import Dict, Any, Optional
import sys

def explore_context(context_url: str, sample_data: Optional[Dict[str, Any]] = None):
    """Explore a JSON-LD context using cogitarelink"""
    print(f"Exploring context: {context_url}")
    
    # Initialize the registry
    registry = VocabularyRegistry()
    
    # Register the external context
    registry.register_context_from_url(
        "earth616", 
        context_url, 
        description="Earth616 Ontology Context"
    )
    
    # Create a context processor with our registry
    processor = ContextProcessor(registry=registry)
    
    # Print information about the registered context
    print("\nRegistered vocabularies:")
    for vocab_id, vocab in registry.vocabularies.items():
        print(f"  {vocab_id}: {vocab.description}")
        
    # Get the context composer to examine the context
    composer = ContextComposer(registry=registry)
    
    # Generate a composed context with just our vocabulary
    composed = composer.compose(["earth616"])
    
    # Pretty print the composed context
    print("\nComposed context:")
    print(json.dumps(composed, indent=2))
    
    # Detect vocabulary terms
    print("\nVocabulary analysis:")
    detected = registry.detect_vocabularies(composed)
    for vocab_id, confidence in detected.items():
        print(f"  {vocab_id}: {confidence:.2f} confidence")
    
    # If sample data was provided, process it
    if sample_data:
        print("\nProcessing sample data with context:")
        
        # Create an entity with our context
        entity = Entity(data=sample_data, context=composed)
        
        # Show the normalized form
        print("\nNormalized form:")
        print(json.dumps(entity.normalized_form, indent=2))
        
        # Expand the document
        expanded = processor.expand(sample_data, context=composed)
        print("\nExpanded form:")
        print(json.dumps(expanded, indent=2))

if __name__ == "__main__":
    # Default context URL
    context_url = (
        "https://raw.githubusercontent.com/crcresearch/earth616_ontology"
        "/refs/heads/main/release/contexts/latest/context-base.jsonld"
    )
    
    # Override with command line arg if provided
    if len(sys.argv) > 1:
        context_url = sys.argv[1]
    
    # Simple sample data using the context (customize as needed)
    sample_data = {
        "@context": "https://raw.githubusercontent.com/crcresearch/earth616_ontology/refs/heads/main/release/contexts/latest/context-base.jsonld",
        "@type": "Event",
        "name": "Sample Event",
        "description": "A sample event using the Earth616 ontology context",
        "startTime": "2023-01-01T00:00:00Z"
    }
    
    explore_context(context_url, sample_data)
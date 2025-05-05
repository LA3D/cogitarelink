#!/usr/bin/env python
"""
Script that directly uses the VocabToolAgent to work with earth616 ontology
"""
import json
import sys
from pathlib import Path
from cogitarelink.cli.vocab_tools import VocabToolAgent

# Constants for the earth616 ontology resources
CONTEXT_URL = "https://raw.githubusercontent.com/crcresearch/earth616_ontology/refs/heads/main/release/contexts/latest/context-base.jsonld"
ONTOLOGY_URL = "https://raw.githubusercontent.com/crcresearch/earth616_ontology/refs/heads/main/release/ontology/latest/ontology.ttl"
PREFIX = "earth616"
URI_BASE = "https://ontology.crc.nd.edu/earth616/"

def main():
    """Main function to explore earth616 ontology using the VocabToolAgent directly"""
    # Create a VocabToolAgent instance
    agent = VocabToolAgent(name="earth616-agent")
    
    print("Exploring earth616 ontology with VocabToolAgent")
    print("-" * 50)
    
    # Step 1: Retrieve the context
    print("\n1. Retrieving context file...")
    context_result = agent.run_tool("retrieve_vocabulary_resource", uri=CONTEXT_URL)
    
    if not context_result.get("success", False):
        print(f"Error retrieving context: {context_result.get('error', 'Unknown error')}")
        return 1
    
    context = context_result.get("content")
    print(f"Retrieved context with {len(str(context))} bytes")
    
    # Step 2: Add the context as a temporary vocabulary
    print("\n2. Adding earth616 as a temporary vocabulary...")
    add_result = agent.run_tool("add_temp_vocabulary", 
                              prefix=PREFIX,
                              uri=URI_BASE,
                              inline_context=context,
                              description="Earth616 Ontology Context")
    
    if not add_result.get("success", False):
        print(f"Error adding vocabulary: {add_result.get('error', 'Unknown error')}")
        return 1
    
    print(f"Added vocabulary: {add_result.get('status', 'Status unknown')}")
    
    # Step 3: Get vocabulary info
    print("\n3. Getting details about earth616 vocabulary...")
    vocab_info = agent.run_tool("get_vocabulary_info", prefix=PREFIX)
    
    if not vocab_info.get("success", False):
        print(f"Error getting vocabulary info: {vocab_info.get('error', 'Unknown error')}")
    else:
        print(f"Vocabulary info:")
        print(f"  Prefix: {vocab_info.get('prefix')}")
        print(f"  URI: {vocab_info.get('uri')}")
        print(f"  Context: {vocab_info.get('context', {}).get('url')}")
        if 'context' in vocab_info and 'inline' in vocab_info['context']:
            if vocab_info['context']['inline']:
                print(f"  Context size: {len(str(vocab_info['context']['inline']))} bytes")
    
    # Step 4: Compose a context with earth616
    print("\n4. Composing a context with earth616...")
    compose_result = agent.run_tool("compose_context", 
                                  prefixes=[PREFIX],
                                  support_nest=True)
    
    if not compose_result.get("success", False):
        print(f"Error composing context: {compose_result.get('error', 'Unknown error')}")
    else:
        context_obj = compose_result.get("context", {})
        print(f"Composed context with {len(str(context_obj))} bytes")
        
        # Save the composed context to a file
        context_file = Path("earth616_composed_context.json")
        with open(context_file, "w") as f:
            json.dump(context_obj, f, indent=2)
        
        print(f"Saved composed context to {context_file}")
    
    # Step 5: Try to retrieve and process the TTL ontology
    print("\n5. Retrieving ontology TTL file...")
    ttl_result = agent.run_tool("retrieve_vocabulary_resource", 
                              uri=ONTOLOGY_URL,
                              format_hint="turtle")
    
    if not ttl_result.get("success", False):
        print(f"Error retrieving TTL: {ttl_result.get('error', 'Unknown error')}")
    else:
        ttl_content = ttl_result.get("content")
        print(f"Retrieved TTL with {len(str(ttl_content))} bytes")
        
        # Step 6: Convert TTL to JSON-LD
        print("\n6. Converting TTL to JSON-LD...")
        convert_result = agent.run_tool("convert_format", 
                                      content=ttl_content,
                                      from_format="turtle",
                                      to_format="json-ld")
        
        if not convert_result.get("success", False):
            print(f"Error converting TTL: {convert_result.get('error', 'Unknown error')}")
        else:
            jsonld_data = convert_result.get("data", {})
            
            # Save the converted JSON-LD to a file
            jsonld_file = Path("earth616_ontology.jsonld")
            with open(jsonld_file, "w") as f:
                json.dump(jsonld_data, f, indent=2)
            
            print(f"Converted TTL to JSON-LD with {len(str(jsonld_data))} bytes")
            print(f"Saved JSON-LD to {jsonld_file}")
            print(f"Generated {len(jsonld_data) if isinstance(jsonld_data, list) else 1} JSON-LD nodes")
    
    # Step 7: Create a sample data structure
    print("\n7. Creating a sample data structure...")
    example_data = {
        "@context": context_obj,
        "@type": "Event",
        "@id": "urn:example:event:1234",
        "name": "Supply Chain Event",
        "description": "A supply chain event using the Earth616 ontology context",
        "startTime": "2023-01-01T08:00:00Z",
        "endTime": "2023-01-02T00:00:00Z",
        "location": {
            "@type": "Place",
            "name": "Manufacturing Facility",
            "address": {
                "@type": "PostalAddress",
                "addressLocality": "South Bend",
                "addressRegion": "IN",
                "addressCountry": "US"
            }
        },
        "participant": [
            {
                "@type": "Organization",
                "@id": "urn:example:org:manufacturer",
                "name": "Example Manufacturing Inc."
            },
            {
                "@type": "Organization",
                "@id": "urn:example:org:logistics",
                "name": "Logistics Provider LLC"
            }
        ]
    }
    
    # Save the example to a file
    example_file = Path("earth616_example.json")
    with open(example_file, "w") as f:
        json.dump(example_data, f, indent=2)
    
    print(f"Created and saved sample data to {example_file}")
    
    # Step 8: Convert the example to Turtle format
    print("\n8. Converting example to Turtle format...")
    turtle_result = agent.run_tool("convert_format", 
                                 content=example_data,
                                 from_format="json-ld",
                                 to_format="turtle")
    
    if not turtle_result.get("success", False):
        print(f"Error converting to Turtle: {turtle_result.get('error', 'Unknown error')}")
    else:
        turtle_content = turtle_result.get("data")
        
        # Save the Turtle representation to a file
        turtle_file = Path("earth616_example.ttl")
        with open(turtle_file, "w") as f:
            f.write(turtle_content)
        
        print(f"Converted example to Turtle format with {len(turtle_content)} bytes")
        print(f"Saved Turtle representation to {turtle_file}")
    
    print("\nExploration complete!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python
"""
Create and validate a data structure using the earth616 ontology
"""
import json
import subprocess
import sys
from pathlib import Path

# Constants for the earth616 ontology resources
CONTEXT_URL = "https://raw.githubusercontent.com/crcresearch/earth616_ontology/refs/heads/main/release/contexts/latest/context-base.jsonld"
PREFIX = "earth616"
URI_BASE = "https://ontology.crc.nd.edu/earth616/"

def run_cogitarelink_tool(tool_name, args):
    """Run a cogitarelink CLI tool and return the result"""
    args_json = json.dumps(args)
    cmd = ["cogitarelink", "--run-tool", tool_name, "--args", args_json]
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running tool: {e}")
        print(f"STDERR: {e.stderr}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing output as JSON: {e}")
        print(f"Output: {result.stdout}")
        sys.exit(1)

def create_example():
    """Create and validate an example using earth616 ontology"""
    print("Creating and validating example earth616 data structure")
    print("-" * 50)
    
    # Step 1: Add the earth616 vocabulary (if not already added)
    print("\n1. Adding earth616 as a temporary vocabulary...")
    context = run_cogitarelink_tool("retrieve_vocabulary_resource", {
        "uri": CONTEXT_URL
    })
    
    add_result = run_cogitarelink_tool("add_temp_vocabulary", {
        "prefix": PREFIX,
        "uri": URI_BASE,
        "inline_context": context,
        "description": "Earth616 Ontology Context"
    })
    print(f"Added vocabulary: {add_result.get('status', 'Failed')}")
    
    # Step 2: Compose a context with earth616
    print("\n2. Composing a context with earth616...")
    composed = run_cogitarelink_tool("compose_context", {
        "prefixes": [PREFIX],
        "support_nest": True
    })
    
    # Make sure we have a proper context
    if isinstance(composed, dict) and "@context" in composed:
        context_obj = composed
    else:
        context_obj = {"@context": composed}
    
    # Step 3: Create an example structure
    print("\n3. Creating an example data structure...")
    
    # Create an example supply chain event
    example_data = {
        "@context": CONTEXT_URL,
        "@type": "Event",
        "@id": "urn:example:event:1234",
        "name": "Product Shipping Event",
        "description": "Shipment of products from manufacturing to distribution center",
        "startTime": "2023-04-01T08:00:00Z",
        "endTime": "2023-04-01T10:30:00Z",
        "location": {
            "@type": "Place",
            "name": "Manufacturing Facility Alpha",
            "address": {
                "@type": "PostalAddress",
                "addressLocality": "Grand Rapids",
                "addressRegion": "MI",
                "addressCountry": "US"
            },
            "geo": {
                "@type": "GeoCoordinates",
                "latitude": 42.9634,
                "longitude": -85.6681
            }
        },
        "result": {
            "@type": "Product",
            "@id": "urn:example:product:5678",
            "name": "Industrial Widget XL-5",
            "description": "Heavy-duty industrial widget for manufacturing",
            "identifier": {
                "@type": "PropertyValue",
                "propertyID": "SKU",
                "value": "WDG-XL5-2023"
            }
        },
        "participant": [
            {
                "@type": "Organization",
                "@id": "urn:example:org:alpha",
                "name": "Alpha Manufacturing Inc.",
                "role": "Manufacturer"
            },
            {
                "@type": "Organization",
                "@id": "urn:example:org:logistics",
                "name": "QuickShip Logistics",
                "role": "Shipper"
            }
        ]
    }
    
    # Save the example to a file
    example_file = Path("earth616_example.json")
    with open(example_file, "w") as f:
        json.dump(example_data, f, indent=2)
    
    print(f"Saved example to {example_file}")
    
    # Step 4: Validate the example (if validation tools are available)
    print("\n4. Processing the example...")
    try:
        processed = run_cogitarelink_tool("process_entity", {
            "data": example_data,
            "context": composed
        })
        print(f"Processed entity result: {processed.get('status', 'Failed')}")
        
        # If we have entity info, display it
        if "entity" in processed:
            entity = processed["entity"]
            print(f"Entity ID: {entity.get('id')}")
            print(f"Entity Types: {entity.get('types')}")
            print(f"Entity Properties: {len(entity.get('properties', []))}")
    except Exception as e:
        print(f"Processing failed (this is expected if the tool doesn't exist): {e}")
        
    # Step 5: Convert to different formats
    print("\n5. Converting example to different formats...")
    
    # Try to convert to turtle
    try:
        turtle = run_cogitarelink_tool("convert_format", {
            "content": example_data,
            "from_format": "json-ld",
            "to_format": "turtle"
        })
        
        # Save turtle version
        turtle_file = Path("earth616_example.ttl")
        with open(turtle_file, "w") as f:
            f.write(turtle)
        
        print(f"Saved Turtle representation to {turtle_file}")
    except Exception as e:
        print(f"Turtle conversion failed: {e}")
    
    print("\nExample creation complete!")

if __name__ == "__main__":
    create_example()
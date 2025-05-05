#!/usr/bin/env python
"""
Script to explore and validate Earth616 SHACL shapes with cogitarelink
"""
import json
import sys
from pathlib import Path
from cogitarelink.cli.vocab_tools import VocabToolAgent

# Constants for the earth616 ontology resources
CONTEXT_URL = "https://raw.githubusercontent.com/crcresearch/earth616_ontology/refs/heads/main/release/contexts/latest/context-base.jsonld"
ONTOLOGY_URL = "https://raw.githubusercontent.com/crcresearch/earth616_ontology/refs/heads/main/release/ontology/latest/ontology.ttl"
SHAPES_URL = "https://raw.githubusercontent.com/crcresearch/earth616_ontology/main/release/shapes/shacl/latest/shapes.ttl"
PREFIX = "earth616"
URI_BASE = "https://ontology.crc.nd.edu/earth616/"

def main():
    """Explore and validate Earth616 SHACL shapes"""
    # Create a VocabToolAgent instance
    agent = VocabToolAgent(name="earth616-shapes-agent")
    
    print("Exploring earth616 SHACL shapes")
    print("-" * 50)
    
    # Step 1: Retrieve the SHACL shapes
    print("\n1. Retrieving SHACL shapes...")
    shapes_result = agent.run_tool("retrieve_vocabulary_resource", 
                                 uri=SHAPES_URL,
                                 format_hint="turtle")
    
    if not shapes_result.get("success", False):
        print(f"Error retrieving shapes: {shapes_result.get('error', 'Unknown error')}")
        return 1
    
    shapes_content = shapes_result.get("content")
    print(f"Retrieved SHACL shapes with {len(str(shapes_content))} bytes")
    
    # Save the raw shapes to a file
    shapes_file = Path("earth616_shapes.ttl")
    with open(shapes_file, "w") as f:
        f.write(shapes_content)
    
    print(f"Saved SHACL shapes to {shapes_file}")
    
    # Step 2: Convert SHACL shapes to JSON-LD for analysis
    print("\n2. Converting SHACL shapes to JSON-LD...")
    convert_result = agent.run_tool("convert_format", 
                                  content=shapes_content,
                                  from_format="turtle",
                                  to_format="json-ld")
    
    if not convert_result.get("success", False):
        print(f"Error converting shapes: {convert_result.get('error', 'Unknown error')}")
        return 1
    
    shapes_jsonld = convert_result.get("data", {})
    
    # Save the JSON-LD shapes to a file
    shapes_jsonld_file = Path("earth616_shapes.jsonld")
    with open(shapes_jsonld_file, "w") as f:
        json.dump(shapes_jsonld, f, indent=2)
    
    print(f"Converted SHACL shapes to JSON-LD with {len(str(shapes_jsonld))} bytes")
    print(f"Saved JSON-LD shapes to {shapes_jsonld_file}")
    
    # Step 3: Analyze the shape constraints
    print("\n3. Analyzing shape constraints...")
    
    # Helper function to extract shape information
    def extract_shapes(jsonld_data):
        """Extract shape information from JSON-LD data"""
        shapes = []
        
        # Process nodes to find NodeShapes and PropertyShapes
        for node in jsonld_data if isinstance(jsonld_data, list) else [jsonld_data]:
            # Look for node shapes
            if isinstance(node, dict):
                node_types = node.get("@type", [])
                if not isinstance(node_types, list):
                    node_types = [node_types]
                
                # Check if this is a SHACL shape
                is_shape = any(t in ["http://www.w3.org/ns/shacl#NodeShape", "sh:NodeShape"] for t in node_types)
                
                if is_shape:
                    shape_info = {
                        "id": node.get("@id", "unknown"),
                        "type": "NodeShape",
                        "target_class": node.get("http://www.w3.org/ns/shacl#targetClass", 
                                              node.get("sh:targetClass")),
                        "properties": []
                    }
                    
                    # Extract property constraints
                    property_shapes = node.get("http://www.w3.org/ns/shacl#property", 
                                            node.get("sh:property", []))
                    
                    if not isinstance(property_shapes, list):
                        property_shapes = [property_shapes]
                    
                    for prop in property_shapes:
                        if isinstance(prop, dict):
                            prop_info = {
                                "path": prop.get("http://www.w3.org/ns/shacl#path", 
                                              prop.get("sh:path")),
                                "min_count": prop.get("http://www.w3.org/ns/shacl#minCount", 
                                                   prop.get("sh:minCount")),
                                "max_count": prop.get("http://www.w3.org/ns/shacl#maxCount", 
                                                   prop.get("sh:maxCount")),
                                "class": prop.get("http://www.w3.org/ns/shacl#class", 
                                               prop.get("sh:class")),
                                "datatype": prop.get("http://www.w3.org/ns/shacl#datatype", 
                                                  prop.get("sh:datatype")),
                                "node": prop.get("http://www.w3.org/ns/shacl#node", 
                                              prop.get("sh:node"))
                            }
                            
                            # Clean up None values
                            prop_info = {k: v for k, v in prop_info.items() if v is not None}
                            
                            shape_info["properties"].append(prop_info)
                    
                    shapes.append(shape_info)
        
        return shapes
    
    # Extract and analyze shape information
    shapes = extract_shapes(shapes_jsonld)
    
    # Save the extracted shape info to a file
    shapes_info_file = Path("earth616_shapes_info.json")
    with open(shapes_info_file, "w") as f:
        json.dump(shapes, f, indent=2)
    
    print(f"Extracted {len(shapes)} shapes")
    print(f"Saved shape information to {shapes_info_file}")
    
    # Print some information about the shapes
    if shapes:
        print("\nShape Information Summary:")
        for i, shape in enumerate(shapes[:5]):  # Show first 5 shapes
            print(f"\nShape {i+1}: {shape['id']}")
            print(f"  Target Class: {shape.get('target_class')}")
            print(f"  Properties: {len(shape.get('properties', []))}")
            
            # Show some property constraints
            for j, prop in enumerate(shape.get('properties', [])[:3]):  # Show first 3 properties
                print(f"    Property {j+1}: {prop.get('path')}")
                constraints = []
                if 'min_count' in prop:
                    constraints.append(f"minCount={prop['min_count']}")
                if 'max_count' in prop:
                    constraints.append(f"maxCount={prop['max_count']}")
                if 'class' in prop:
                    constraints.append(f"class={prop['class']}")
                if 'datatype' in prop:
                    constraints.append(f"datatype={prop['datatype']}")
                print(f"      Constraints: {', '.join(constraints)}")
        
        if len(shapes) > 5:
            print(f"\n... and {len(shapes) - 5} more shapes")
    
    # Step 4: Retrieve the context and register it
    print("\n4. Retrieving and registering Earth616 context...")
    context_result = agent.run_tool("retrieve_vocabulary_resource", uri=CONTEXT_URL)
    
    if not context_result.get("success", False):
        print(f"Error retrieving context: {context_result.get('error', 'Unknown error')}")
        return 1
    
    context = context_result.get("content")
    
    # Add the vocabulary to the registry
    add_result = agent.run_tool("add_temp_vocabulary", 
                              prefix=PREFIX,
                              uri=URI_BASE,
                              inline_context=context,
                              description="Earth616 Ontology Context")
    
    if not add_result.get("success", False):
        print(f"Error adding vocabulary: {add_result.get('error', 'Unknown error')}")
        return 1
    
    print(f"Added vocabulary: {add_result.get('status', 'Status unknown')}")
    
    # Step 5: Create a valid example based on the shapes
    print("\n5. Creating an example based on shape constraints...")
    
    # Compose a context
    compose_result = agent.run_tool("compose_context", 
                                  prefixes=[PREFIX],
                                  support_nest=True)
    
    if not compose_result.get("success", False):
        print(f"Error composing context: {compose_result.get('error', 'Unknown error')}")
        return 1
    
    context_obj = compose_result.get("context", {})
    
    # Choose a shape to create an example for (preferably an Event shape if available)
    event_shape = None
    for shape in shapes:
        target_class = shape.get('target_class', '')
        target_str = str(target_class)
        if 'Event' in target_str:
            event_shape = shape
            break
    
    if not event_shape:
        # Just use the first shape if no Event shape is found
        event_shape = shapes[0] if shapes else None
    
    if not event_shape:
        print("No shapes found to create an example from")
        return 1
    
    print(f"Creating example based on shape: {event_shape['id']}")
    
    # Build an example object based on the shape constraints
    example_data = {
        "@context": context_obj,
        "@type": event_shape.get('target_class', 'Event').split('/')[-1].split('#')[-1],
        "@id": "urn:example:event:shapecompliant"
    }
    
    # Add properties based on the shape constraints
    for prop in event_shape.get('properties', []):
        path = prop.get('path', '')
        if isinstance(path, dict):
            path = path.get('@id', '')
            
        # Extract the property name from the URI
        prop_name = path.split('/')[-1].split('#')[-1]
        
        # Create sample values based on constraints
        if 'class' in prop:
            # For object properties, create a nested object
            class_name = prop.get('class', '').split('/')[-1].split('#')[-1]
            
            if class_name in ['Person', 'Organization']:
                example_data[prop_name] = {
                    "@type": class_name,
                    "name": f"Example {class_name}"
                }
            elif class_name in ['Place', 'Location']:
                example_data[prop_name] = {
                    "@type": class_name,
                    "name": f"Example {class_name}",
                    "address": {
                        "@type": "PostalAddress",
                        "addressLocality": "South Bend",
                        "addressRegion": "IN",
                        "addressCountry": "US"
                    }
                }
            else:
                example_data[prop_name] = {
                    "@type": class_name,
                    "name": f"Example {class_name}"
                }
        elif 'datatype' in prop:
            # For data properties, create a sample literal
            datatype = prop.get('datatype', '').split('/')[-1].split('#')[-1]
            
            if datatype in ['dateTime', 'date']:
                example_data[prop_name] = "2023-01-01T00:00:00Z"
            elif datatype in ['integer', 'decimal', 'float']:
                example_data[prop_name] = 42
            elif datatype in ['boolean']:
                example_data[prop_name] = True
            else:
                example_data[prop_name] = f"Example {prop_name}"
        else:
            # Default to a string value
            example_data[prop_name] = f"Example {prop_name}"
    
    # Save the example to a file
    example_file = Path("earth616_shacl_example.json")
    with open(example_file, "w") as f:
        json.dump(example_data, f, indent=2)
    
    print(f"Created and saved SHACL-based example to {example_file}")
    
    print("\nExploration complete!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
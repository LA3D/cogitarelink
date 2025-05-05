#!/usr/bin/env python
"""
Script to explore the earth616 ontology using cogitarelink CLI tools
"""
import json
import subprocess
import sys

# Constants for the earth616 ontology resources
CONTEXT_URL = "https://raw.githubusercontent.com/crcresearch/earth616_ontology/refs/heads/main/release/contexts/latest/context-base.jsonld"
ONTOLOGY_URL = "https://raw.githubusercontent.com/crcresearch/earth616_ontology/refs/heads/main/release/ontology/latest/ontology.ttl"
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

def explore_earth616():
    """Explore the earth616 ontology using cogitarelink tools"""
    print("Exploring earth616 ontology with cogitarelink")
    print("-" * 50)
    
    # Step 1: Retrieve the context
    print("\n1. Retrieving context file...")
    context = run_cogitarelink_tool("retrieve_vocabulary_resource", {
        "uri": CONTEXT_URL
    })
    print(f"Retrieved context with {len(context)} bytes")
    
    # Step 2: Analyze the context
    print("\n2. Detecting vocabularies in the context...")
    detection = run_cogitarelink_tool("detect_vocabularies", {
        "inline_context": context
    })
    print("Detected vocabularies:")
    for vocab, confidence in detection.get("vocabularies", {}).items():
        print(f"  - {vocab}: {confidence:.2f} confidence")
    
    # Step 3: Add the context as a temporary vocabulary
    print("\n3. Adding earth616 as a temporary vocabulary...")
    add_result = run_cogitarelink_tool("add_temp_vocabulary", {
        "prefix": PREFIX,
        "uri": URI_BASE,
        "inline_context": context,
        "description": "Earth616 Ontology Context"
    })
    print(f"Added vocabulary: {add_result.get('status', 'Failed')}")
    
    # Step 4: Explore the registry to verify
    print("\n4. Exploring registry to verify addition...")
    registry = run_cogitarelink_tool("explore_registry", {})
    
    found = False
    print("Vocabularies in registry:")
    for vocab in registry.get("vocabularies", []):
        print(f"  - {vocab['prefix']}: {vocab['description']}")
        if vocab["prefix"] == PREFIX:
            found = True
    
    if not found:
        print(f"Warning: {PREFIX} not found in registry!")
    
    # Step 5: Get details about the added vocabulary
    print("\n5. Getting details about earth616 vocabulary...")
    vocab_info = run_cogitarelink_tool("get_vocabulary_info", {
        "prefix": PREFIX
    })
    
    print(f"Vocabulary info:")
    print(f"  Prefix: {vocab_info.get('prefix')}")
    print(f"  URI: {vocab_info.get('uri')}")
    print(f"  Terms: {len(vocab_info.get('terms', []))}")
    print(f"  Description: {vocab_info.get('description')}")
    
    # Step 6: Try to retrieve and process TTL
    print("\n6. Retrieving ontology TTL file...")
    ttl_content = run_cogitarelink_tool("retrieve_vocabulary_resource", {
        "uri": ONTOLOGY_URL,
        "format_hint": "turtle"
    })
    print(f"Retrieved TTL with {len(ttl_content)} bytes")
    
    # Step 7: Convert TTL to JSON-LD
    print("\n7. Converting TTL to JSON-LD...")
    ttl_converted = run_cogitarelink_tool("convert_format", {
        "content": ttl_content,
        "from_format": "turtle",
        "to_format": "json-ld"
    })
    print(f"Converted TTL to JSON-LD with {len(json.dumps(ttl_converted))} bytes")
    print(f"Generated {len(ttl_converted)} JSON-LD nodes")
    
    # Step 8: Try composing a context with earth616
    print("\n8. Composing a context with earth616...")
    composed = run_cogitarelink_tool("compose_context", {
        "prefixes": [PREFIX],
        "support_nest": True
    })
    
    if isinstance(composed, dict) and "@context" in composed:
        context_size = len(json.dumps(composed["@context"]))
        print(f"Composed context with {context_size} bytes")
    else:
        print(f"Composed result: {composed}")
    
    # Step 9. Analyze compatibility with schema.org
    print("\n9. Analyzing compatibility with schema.org...")
    try:
        compat = run_cogitarelink_tool("analyze_context_compatibility", {
            "prefix_a": PREFIX,
            "prefix_b": "schema"
        })
        print("Compatibility analysis:")
        print(f"  Collision count: {compat.get('collision_count', 'N/A')}")
        print(f"  Protected term conflicts: {compat.get('protected_conflicts', 'N/A')}")
    except Exception as e:
        print(f"Compatibility analysis failed: {e}")
    
    print("\nExploration complete!")

if __name__ == "__main__":
    explore_earth616()
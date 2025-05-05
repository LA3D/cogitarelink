#!/usr/bin/env python
"""Test script for the agent-enabled CLI"""

import json
import subprocess
import tempfile
from pathlib import Path

def run_agent_cli(args, input_data=None):
    """Run the agent CLI with given arguments and return the results"""
    cmd = ["python", "-m", "cogitarelink.cli.agent_cli"] + args
    
    if input_data:
        result = subprocess.run(
            cmd, 
            input=json.dumps(input_data).encode(),
            capture_output=True, 
            text=True
        )
    else:
        result = subprocess.run(cmd, capture_output=True, text=True)
    
    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError:
        output = result.stdout
    
    return {
        "returncode": result.returncode,
        "stdout": output,
        "stderr": result.stderr
    }

def main():
    """Run a series of tests on the agent CLI"""
    print("Testing agent-enabled CLI...")
    
    # Test 1: Get version
    print("\n1. Testing --version")
    version_result = run_agent_cli(["--version"])
    print(f"Return code: {version_result['returncode']}")
    print(f"Contains agent_guidance: {'agent_guidance' in version_result['stdout']}")
    
    # Test 2: List tools
    print("\n2. Testing --list-tools")
    list_result = run_agent_cli(["--list-tools"])
    print(f"Return code: {list_result['returncode']}")
    print(f"Contains tools_by_category: {'tools_by_category' in list_result['stdout']}")
    
    # Test 3: List earth616 category
    print("\n3. Testing --list-tools --category earth616")
    category_result = run_agent_cli(["--list-tools", "--category", "earth616"])
    print(f"Return code: {category_result['returncode']}")
    print(f"Contains earth616 category: {'earth616' in json.dumps(category_result['stdout'])}")
    
    # Test 4: Register earth616
    print("\n4. Testing register_earth616")
    register_result = run_agent_cli(["--run-tool", "register_earth616"])
    print(f"Return code: {register_result['returncode']}")
    success = register_result['stdout'].get('success', False) if isinstance(register_result['stdout'], dict) else False
    print(f"Success: {success}")
    
    # Test 5: Generate example
    if success:
        print("\n5. Testing generate_earth616_example")
        args = {"entity_type": "Event"}
        
        # Create a temporary file for arguments
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            json.dump(args, tmp)
            tmp_path = tmp.name
        
        example_result = run_agent_cli(["--run-tool", "generate_earth616_example", "--args-file", tmp_path])
        print(f"Return code: {example_result['returncode']}")
        example_success = example_result['stdout'].get('success', False) if isinstance(example_result['stdout'], dict) else False
        print(f"Success: {example_success}")
        
        if example_success and 'example' in example_result['stdout']:
            example = example_result['stdout']['example']
            print(f"Example type: {example.get('@type')}")
            print(f"Example has context: {'@context' in example}")
        
        # Clean up temporary file
        Path(tmp_path).unlink(missing_ok=True)
    
    print("\nTests completed!")

if __name__ == "__main__":
    main()
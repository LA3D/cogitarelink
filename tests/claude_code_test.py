#!/usr/bin/env python
"""
Test script that simulates how Claude Code would interact with the cogitarelink CLI.
This script demonstrates how to use the CLI commands to perform vocabulary operations.
"""
import json
import subprocess
import time
import sys
from pathlib import Path

# ANSI color codes for terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

def run_command(cmd, description=None):
    """Run a shell command and return the output"""
    if description:
        print(f"{YELLOW}=== {description} ==={RESET}")
        print(f"{BLUE}$ {cmd}{RESET}")
    
    # Run the command
    process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    # Format and print output
    if process.stdout:
        try:
            # Try to parse and pretty-print JSON
            data = json.loads(process.stdout)
            output = json.dumps(data, indent=2)
        except json.JSONDecodeError:
            output = process.stdout.strip()
        
        print(output)
    
    if process.returncode != 0:
        print(f"{RED}ERROR: {process.stderr}{RESET}")
    
    print()  # Empty line for spacing
    return process

def main():
    """Main function to test Claude Code interaction with cogitarelink CLI"""
    print(f"{GREEN}=== Claude Code Test for CogitareLink CLI ==={RESET}\n")
    
    # Get version
    run_command("cogitarelink --version", "Getting CogitareLink version")
    
    # List available tools
    run_command("cogitarelink --list-tools", "Listing available CLI tools")
    
    # Create a test JSON-LD context
    test_context = {
        "@context": {
            "schema": "https://schema.org/",
            "dct": "http://purl.org/dc/terms/",
            "name": "schema:name",
            "description": "schema:description"
        }
    }
    
    # Save context to a temporary file
    context_file = Path("./test_context.json")
    context_file.write_text(json.dumps(test_context))
    
    # Test detecting vocabularies in the context
    run_command(
        f'cogitarelink --run-tool detect_vocabularies --args \'{{"context_list": {json.dumps(test_context)}}}\'',
        "Detecting vocabularies in a context"
    )
    
    # Try to create a Croissant dataset (may not work if tool isn't properly registered)
    dataset_args = {
        "name": "Sample Dataset Created by Claude Code",
        "description": "This is a test dataset created to demonstrate the cogitarelink CLI"
    }
    run_command(
        f'cogitarelink --run-tool create_croissant_dataset --args \'{json.dumps(dataset_args)}\'',
        "Creating a Croissant dataset (may fail if tool not registered)"
    )
    
    # Search Wikidata for a term
    wikidata_args = {
        "query": "machine learning",
        "limit": 3
    }
    run_command(
        f'cogitarelink --run-tool wikidata_search --args \'{json.dumps(wikidata_args)}\'',
        "Searching Wikidata for 'machine learning'"
    )
    
    # Clean up
    if context_file.exists():
        context_file.unlink()
        
    print(f"{GREEN}=== Test Complete ==={RESET}")

if __name__ == "__main__":
    main()
"""
Test the fallback mechanism in extract_metadata when extruct is not available.
"""

import pytest
import sys
import importlib
from cogitarelink.cli.vocab_tools import VocabToolAgent

def test_extract_metadata_fallback():
    """Test that extract_metadata falls back to BeautifulSoup when extruct is unavailable."""
    agent = VocabToolAgent(name="test-fallback-agent")
    
    # Sample HTML with JSON-LD and OpenGraph
    html_sample = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Fallback Test</title>
        <!-- OpenGraph metadata -->
        <meta property="og:title" content="Fallback Test" />
        <meta property="og:type" content="website" />
        
        <!-- JSON-LD metadata -->
        <script type="application/ld+json">
        {
            "@context": "https://schema.org/",
            "@type": "WebPage",
            "name": "Fallback Test Page"
        }
        </script>
    </head>
    <body>
        <h1>Testing Fallback Mechanism</h1>
    </body>
    </html>
    """
    
    # Temporarily remove extruct from sys.modules to simulate it not being available
    had_extruct = False
    if 'extruct' in sys.modules:
        had_extruct = True
        extruct_module = sys.modules['extruct']
        del sys.modules['extruct']
    
    try:
        # Run extract_metadata, which should use the BeautifulSoup fallback
        result = agent.run_tool("extract_metadata", 
                              html_content=html_sample,
                              base_url="https://example.com/")
        
        # Check if we got a fallback note
        assert "note" in result
        assert "BeautifulSoup fallback" in result["note"]
        print(f"✓ Got fallback note: {result['note']}")
        
        # Verify success
        assert result["success"] is True
        
        # Check for presence of formats that should be available in fallback mode
        formats = result.get("formats", [])
        print(f"Detected formats in fallback mode: {formats}")
        
        # JSON-LD should be extracted in fallback mode
        if "json-ld" in formats:
            json_ld_data = result["metadata"]["json-ld"]
            assert len(json_ld_data) > 0
            assert json_ld_data[0].get("@type") == "WebPage"
            print("✓ Successfully extracted JSON-LD in fallback mode")
        
        # OpenGraph may also be extracted in fallback mode
        if "opengraph" in formats:
            og_data = result["metadata"]["opengraph"]
            assert len(og_data) > 0
            print("✓ Successfully extracted OpenGraph in fallback mode")
        
        return result
    
    finally:
        # Restore extruct module if it was present before
        if had_extruct:
            sys.modules['extruct'] = extruct_module

if __name__ == "__main__":
    result = test_extract_metadata_fallback()
    print(f"\nExtracted metadata formats: {result.get('formats', [])}")
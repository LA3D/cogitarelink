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
        
        # Verify success
        assert result.get("success") is True
        # Check for presence of extracted formats
        formats = result.get("formats", [])
        assert isinstance(formats, list)
        # At minimum, JSON-LD or OpenGraph data should be present
        assert any(fmt in formats for fmt in ("json-ld", "opengraph"))
        # Verify metadata structure
        metadata = result.get("metadata", {})
        assert isinstance(metadata, dict)
        for fmt in formats:
            assert fmt in metadata
            assert metadata[fmt]
        
    
    finally:
        # Restore extruct module if it was present before
        if had_extruct:
            sys.modules['extruct'] = extruct_module

if __name__ == "__main__":
    result = test_extract_metadata_fallback()
    print(f"\nExtracted metadata formats: {result.get('formats', [])}")
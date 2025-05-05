"""
Test the extract_metadata function that uses extruct for metadata extraction.
"""

import pytest
from cogitarelink.cli.vocab_tools import VocabToolAgent

def test_extract_metadata():
    """Test that the extract_metadata function correctly extracts metadata using extruct."""
    agent = VocabToolAgent(name="test-extruct-agent")
    
    # Sample HTML with JSON-LD, OpenGraph, and Microdata
    html_sample = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Metadata Extraction Test</title>
        <!-- OpenGraph metadata -->
        <meta property="og:title" content="Test Product" />
        <meta property="og:type" content="product" />
        <meta property="og:url" content="https://example.com/product/123" />
        
        <!-- JSON-LD metadata -->
        <script type="application/ld+json">
        {
            "@context": "https://schema.org/",
            "@type": "Product",
            "name": "Test Product",
            "description": "A test product for metadata extraction"
        }
        </script>
    </head>
    <body>
        <!-- Microdata -->
        <div itemscope itemtype="https://schema.org/Organization">
            <span itemprop="name">Example Company</span>
            <div itemprop="address" itemscope itemtype="https://schema.org/PostalAddress">
                <span itemprop="streetAddress">123 Main St</span>
                <span itemprop="addressLocality">Anytown</span>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Test extract_metadata with default options
    result = agent.run_tool("extract_metadata", 
                          html_content=html_sample,
                          base_url="https://example.com/")
    
    # Verify success
    assert result["success"] is True, f"Failed to extract metadata: {result.get('error', 'Unknown error')}"
    
    # Check which formats were detected
    formats = result.get("formats", [])
    print(f"Detected formats: {formats}")
    
    # Check for presence of different formats
    # This will vary based on extruct availability
    metadata = result.get("metadata", {})
    
    # JSON-LD should always be extracted 
    if "json-ld" in formats:
        assert "json-ld" in metadata
        json_ld_data = metadata["json-ld"]
        assert len(json_ld_data) > 0
        assert json_ld_data[0].get("@type") == "Product"
        print("✓ Successfully extracted JSON-LD")
    
    # OpenGraph may be extracted if extruct is available
    if "opengraph" in formats:
        assert "opengraph" in metadata
        og_data = metadata["opengraph"]
        assert len(og_data) > 0
        assert "og:title" in og_data[0]
        print("✓ Successfully extracted OpenGraph metadata")
    
    # Microdata may be extracted if extruct is available
    if "microdata" in formats:
        assert "microdata" in metadata
        microdata = metadata["microdata"]
        assert len(microdata) > 0
        print("✓ Successfully extracted Microdata")
    
    # Test formats-specific extraction (JSON-LD only)
    json_ld_result = agent.run_tool("extract_metadata",
                                  html_content=html_sample,
                                  base_url="https://example.com/",
                                  formats=["json-ld"])
    
    assert json_ld_result["success"] is True
    assert "json-ld" in json_ld_result.get("formats", [])
    assert len(json_ld_result.get("formats", [])) == 1
    print("✓ Successfully extracted JSON-LD with format filtering")
    
    # Test extract_embedded_jsonld (specialized function)
    json_ld_embedded = agent.run_tool("extract_embedded_jsonld",
                                    html_content=html_sample,
                                    base_url="https://example.com/")
    
    assert json_ld_embedded["success"] is True
    assert json_ld_embedded.get("count", 0) > 0
    assert json_ld_embedded.get("data")[0].get("@type") == "Product"
    print("✓ Successfully used extract_embedded_jsonld")
    
    return result

if __name__ == "__main__":
    result = test_extract_metadata()
    print(f"\nExtracted metadata count: {result.get('total_items', 0)}")
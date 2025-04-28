"""Test imports in the refactored package."""

def test_core_imports():
    """Test importing core modules"""
    from cogitarelink.core.entity import Entity
    from cogitarelink.core.graph import GraphManager
    from cogitarelink.core.processor import EntityProcessor
    from cogitarelink.core.context import ContextProcessor
    from cogitarelink.core.cache import InMemoryCache, DiskCache
    
    # Create basic objects to verify they're working
    cache = InMemoryCache()
    assert cache is not None
    
    # Just ensure we can create the objects
    assert Entity is not None
    assert GraphManager is not None
    assert EntityProcessor is not None
    assert ContextProcessor is not None

def test_vocab_imports():
    """Test importing vocabulary modules"""
    from cogitarelink.vocab.registry import registry
    from cogitarelink.vocab.composer import composer
    from cogitarelink.vocab.collision import Resolver
    
    # Make sure registry has some entries
    assert len(registry._v) > 0
    
    # Check composer is initialized
    assert composer is not None
    
    # Check resolver can be instantiated
    resolver = Resolver()
    assert resolver is not None

def test_verify_imports():
    """Test importing verification modules"""
    from cogitarelink.verify.signer import generate_keypair, sign, verify
    from cogitarelink.verify.validator import validate_entity
    
    # These may not run if dependencies aren't available, but should import
    assert generate_keypair is not None
    assert sign is not None
    assert verify is not None
    assert validate_entity is not None

def test_integration_imports():
    """Test importing integration modules"""
    from cogitarelink.integration.retriever import LODRetriever, json_parse, rdf_to_jsonld, search_wikidata
    
    # Check utility functions
    assert json_parse is not None
    assert rdf_to_jsonld is not None
    assert search_wikidata is not None
    
    # Check we can create the retriever
    retriever = LODRetriever()
    assert retriever is not None

if __name__ == "__main__":
    # Run tests directly when file executed
    test_core_imports()
    print("Core module imports successful")
    
    test_vocab_imports()
    print("Vocabulary module imports successful")
    
    test_verify_imports()
    print("Verification module imports successful")
    
    test_integration_imports()
    print("Integration module imports successful")
    
    print("All imports successful")
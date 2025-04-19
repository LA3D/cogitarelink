"""Vocabulary tools for working with semantic data sources."""

# AUTOGENERATED! DO NOT EDIT! File to edit: ../01_vocabularytools.ipynb.

# %% auto 0
__all__ = ['VOCABULARY_REGISTRY', 'COLLISION_STRATEGIES', 'VocabularyManager', 'create_vocab_aware_document_loader',
           'register_vocab_aware_loader', 'get_loaded_vocabularies', 'get_vocabulary_info',
           'detect_vocabularies_in_context', 'apply_url_transformation', 'apply_collision_strategy',
           'create_graph_partition', 'load_context_for_vocabulary', 'create_dataset_with_vocabulary',
           'add_dataset_to_memory', 'compact_entity_with_vocabulary']

# %% ../01_vocabularytools.ipynb 4
import json
import httpx
from pyld import jsonld
from typing import Dict, List, Optional, Any, Union
from rdflib import Graph
import copy
import uuid

# %% ../01_vocabularytools.ipynb 5
# Enhanced registry of vocabulary information with alternative URIs
VOCABULARY_REGISTRY = {
    "schema": {
        "uri": "https://schema.org/",
        "alternative_uris": ["http://schema.org/", "https://schema.org", "http://schema.org"],
        "prefix": "schema",
        "title": "Schema.org",
        "description": "Schema.org vocabulary for structured data on the internet",
        "version": "latest",
        "publisher": "Schema.org Community",
        "support_level": "direct",
        "resources": {
            "ttl": "https://schema.org/version/latest/schemaorg-current-https.ttl",
            "context": "https://schema.org/docs/jsonldcontext.jsonld",
            "homepage": "https://schema.org/"
        },
        "access_patterns": {
            "primary": "link_header_to_context",
            "fallbacks": ["direct_download"]
        },
        "url_transformations": [],
        "features": {
            "inline_context": False,
            "uses_protection": False,
            "supports_scoped_contexts": True
        },
        "common_terms": ["name", "description", "url", "image"],
        "common_types": ["Thing", "Person", "Organization", "Place", "Event", "Product"],
        "related_vocabs": ["dc", "foaf"]
    },
    
    "croissant": {
        "uri": "http://mlcommons.org/croissant/",
        "alternative_uris": ["https://mlcommons.org/croissant/"],
        "prefix": "croissant",
        "title": "CROISSANT",
        "description": "Community Resource for Open and Inclusive Scholarly Sources and Artifacts for Novel Technologies",
        "version": "1.0",
        "publisher": "MLCommons",
        "support_level": "direct",
        "resources": {
            "ttl": "https://raw.githubusercontent.com/mlcommons/croissant/main/docs/croissant.ttl",
            "context": "https://raw.githubusercontent.com/mlcommons/croissant/main/docs/context.jsonld",
            "homepage": "https://github.com/mlcommons/croissant"
        },
        "access_patterns": {
            "primary": "github_raw",
            "fallbacks": []
        },
        "url_transformations": [],
        "features": {
            "inline_context": True,
            "uses_protection": False,
            "supports_scoped_contexts": False
        },
        "common_terms": ["name", "description", "creator", "license"],
        "common_types": ["Dataset", "DatasetField", "Distribution"],
        "related_vocabs": ["schema", "dcat"]
    },
    
    "ro-crate": {
        "uri": "https://w3id.org/ro/crate/1.2-DRAFT/context",
        "alternative_uris": ["https://w3id.org/ro/crate/1.1/context", "https://w3id.org/ro/crate/context"],
        "prefix": "ro",
        "title": "RO-Crate",
        "description": "Research Object Crate (RO-Crate) metadata specification",
        "version": "1.2-DRAFT",
        "publisher": "ResearchObject.org",
        "support_level": "cache",
        "resources": {
            "ttl": None,
            "context": "https://w3id.org/ro/crate/1.2-DRAFT/context",
            "homepage": "https://www.researchobject.org/ro-crate/"
        },
        "access_patterns": {
            "primary": "persistent_uri",
            "fallbacks": []
        },
        "url_transformations": [],
        "features": {
            "inline_context": False,
            "uses_protection": False,
            "supports_scoped_contexts": False
        },
        "common_terms": ["name", "description", "author", "hasPart"],
        "common_types": ["Dataset", "CreativeWork", "Person"],
        "related_vocabs": ["schema", "dc"]
    },
    
    "vc": {
        "uri": "https://www.w3.org/ns/credentials/v2",
        "alternative_uris": ["https://www.w3.org/2018/credentials/v1", "https://www.w3.org/2018/credentials"],
        "prefix": "vc",
        "title": "Verifiable Credentials Data Model",
        "description": "W3C Verifiable Credentials data model and representations",
        "version": "v2",
        "publisher": "W3C",
        "support_level": "direct",
        "resources": {
            "ttl": None,
            "context": "https://www.w3.org/ns/credentials/v2",
            "backup": "https://raw.githubusercontent.com/w3c/vc-data-model/refs/heads/main/contexts/credentials/v2",
            "homepage": "https://www.w3.org/TR/vc-data-model-2.0/"
        },
        "access_patterns": {
            "primary": "github_raw",
            "fallbacks": ["direct_download"]
        },
        "url_transformations": [],
        "features": {
            "inline_context": False,
            "uses_protection": True,
            "supports_scoped_contexts": True
        },
        "common_terms": ["issuer", "credentialSubject", "validFrom", "validUntil"],
        "common_types": ["VerifiableCredential", "VerifiablePresentation"],
        "related_vocabs": ["schema"]
    },
    
    "epcis": {
        "uri": "https://ref.gs1.org/epcis/",
        "alternative_uris": ["https://gs1.org/epcis/", "http://gs1.org/epcis/", "https://gs1.github.io/EPCIS/"],
        "prefix": "epcis",
        "title": "EPCIS",
        "description": "GS1 EPCIS standard for supply chain visibility",
        "version": "2.0",
        "publisher": "GS1",
        "support_level": "direct",
        "resources": {
            "ttl": None,
            "context": "https://raw.githubusercontent.com/gs1/EPCIS/master/JSON-LD-Context/epcis-context-root.jsonld",
            "homepage": "https://ref.gs1.org/standards/epcis/"
        },
        "access_patterns": {
            "primary": "github_raw",
            "fallbacks": []
        },
        "url_transformations": [
            {
                "pattern": r"https://gs1\.github\.io/EPCIS/(.+\.jsonld)",
                "replacement": r"https://raw.githubusercontent.com/gs1/EPCIS/master/JSON-LD-Context/\1"
            }
        ],
        "features": {
            "inline_context": False,
            "uses_protection": True,
            "supports_scoped_contexts": False
        },
        "common_terms": ["eventTime", "epcList", "bizLocation", "bizStep"],
        "common_types": ["ObjectEvent", "AggregationEvent", "TransactionEvent"],
        "related_vocabs": []
    },
    
    "dc": {
        "uri": "http://purl.org/dc/terms/",
        "alternative_uris": ["http://purl.org/dc/elements/1.1/", "http://dublincore.org/"],
        "prefix": "dc",
        "title": "Dublin Core",
        "description": "Dublin Core Metadata Initiative Terms",
        "version": "terms",
        "publisher": "DCMI",
        "support_level": "cache",
        "resources": {
            "ttl": "https://www.dublincore.org/specifications/dublin-core/dcmi-terms/dublin_core_terms.ttl",
            "context": "https://www.dublincore.org/contexts/dc-terms/",
            "homepage": "https://www.dublincore.org/"
        },
        "access_patterns": {
            "primary": "direct_download",
            "fallbacks": []
        },
        "url_transformations": [],
        "features": {
            "inline_context": False,
            "uses_protection": False,
            "supports_scoped_contexts": False
        },
        "common_terms": ["title", "creator", "date", "subject"],
        "common_types": ["Agent", "BibliographicResource", "Location"],
        "related_vocabs": ["schema", "foaf"]
    },
    
    "foaf": {
        "uri": "http://xmlns.com/foaf/0.1/",
        "alternative_uris": ["http://xmlns.com/foaf/spec/", "http://xmlns.com/foaf/"],
        "prefix": "foaf",
        "title": "Friend of a Friend",
        "description": "Friend of a Friend vocabulary for describing people and their connections",
        "version": "0.1",
        "publisher": "FOAF Project",
        "support_level": "cache",
        "resources": {
            "ttl": "http://xmlns.com/foaf/spec/index.rdf",
            "context": None,
            "homepage": "http://xmlns.com/foaf/spec/"
        },
        "access_patterns": {
            "primary": "direct_download",
            "fallbacks": []
        },
        "url_transformations": [],
        "features": {
            "inline_context": False,
            "uses_protection": False,
            "supports_scoped_contexts": False
        },
        "common_terms": ["name", "mbox", "knows", "homepage"],
        "common_types": ["Person", "Organization", "Document"],
        "related_vocabs": ["schema", "dc"]
    },
    
    "dcat": {
        "uri": "http://www.w3.org/ns/dcat#",
        "alternative_uris": ["https://www.w3.org/ns/dcat#", "http://www.w3.org/ns/dcat"],
        "prefix": "dcat",
        "title": "Data Catalog Vocabulary",
        "description": "W3C Data Catalog Vocabulary for describing datasets",
        "version": "2",
        "publisher": "W3C",
        "support_level": "cache",
        "resources": {
            "ttl": "https://www.w3.org/ns/dcat2.ttl",
            "context": None,
            "homepage": "https://www.w3.org/TR/vocab-dcat-2/"
        },
        "access_patterns": {
            "primary": "direct_download",
            "fallbacks": []
        },
        "url_transformations": [],
        "features": {
            "inline_context": False,
            "uses_protection": False,
            "supports_scoped_contexts": False
        },
        "common_terms": ["distribution", "downloadURL", "accessURL", "theme"],
        "common_types": ["Dataset", "Distribution", "Catalog"],
        "related_vocabs": ["dc", "schema"]
    }
}


# %% ../01_vocabularytools.ipynb 6
# Enhanced collision strategies for vocabulary combinations
COLLISION_STRATEGIES = {
    # VC + EPCIS: Use property scoping to place EPCIS data within credentialSubject
    ("vc", "epcis"): {
        "strategy": "property_scoped",
        "primary": "vc",
        "property": "credentialSubject",
        "secondary": "epcis",
        "description": "Places EPCIS data within the VC credentialSubject property"
    },
    
    # Schema.org + Dublin Core: Use graph partitioning with schema as primary
    ("schema", "dc"): {
        "strategy": "graph_partition",
        "primary": "schema",
        "description": "Partitions the graph with Schema.org as the primary vocabulary"
    },
    
    # Schema.org + FOAF: Use property-specific mapping
    ("schema", "foaf"): {
        "strategy": "property_mapping",
        "mappings": {
            "foaf:name": "schema:name",
            "foaf:Person": "schema:Person",
            "foaf:knows": "schema:knows"
        },
        "description": "Maps FOAF properties to Schema.org equivalents"
    },
    
    # RO-Crate + DCAT: Use nested contexts
    ("ro-crate", "dcat"): {
        "strategy": "nested_contexts",
        "outer": "ro-crate",
        "inner": "dcat",
        "description": "Nests DCAT context within RO-Crate"
    },
    
    # PROV + Schema: Use context versioning
    ("prov", "schema"): {
        "strategy": "context_versioning",
        "context_version": "1.1",
        "description": "Uses JSON-LD 1.1 features to handle these vocabularies"
    },
    
    # SHACL + OWL: Keep separate with explicit references
    ("shacl", "owl"): {
        "strategy": "separate_graphs",
        "description": "Maintains separate graphs with explicit cross-references"
    },
    
    # Default strategy for any vocab with @protected terms
    ("*", "*_protected"): {
        "strategy": "graph_partition",
        "description": "Default strategy when any vocabulary uses @protected terms"
    }
}


# %% ../01_vocabularytools.ipynb 7
class VocabularyManager:
    "Manages vocabulary contexts and document loading"
    def __init__(self, registry=None): 
        self.registry = registry or VOCABULARY_REGISTRY
        self.context_cache = {}
        self.loaded_vocabs = set()
    
    def handle_direct_support(self, url, vocab_info):
        "Handle vocabularies that need direct intervention"
        if url in self.context_cache: return self.context_cache[url]
        
        # Get context location from resources
        context_location = vocab_info.get("resources", {}).get("context")
        if not context_location: return self._create_minimal_context(url, vocab_info)
        
        try:
            response = httpx.get(context_location)
            if response.status_code == 200:
                try:
                    context_data = response.json()
                    result = {'contextUrl': None, 'documentUrl': url, 'document': context_data}
                    self.context_cache[url] = result
                    return result
                except Exception as e:
                    print(f"Error parsing context JSON from {context_location}: {e}")
                    # Try backup if available
                    backup_location = vocab_info.get("resources", {}).get("backup")
                    if backup_location:
                        return self._try_backup_location(url, backup_location)
            else:
                # Try fallback access patterns
                fallbacks = vocab_info.get("access_patterns", {}).get("fallbacks", [])
                for pattern in fallbacks:
                    result = self._try_access_pattern(url, vocab_info, pattern)
                    if result: return result
        except Exception as e:
            print(f"Error fetching context from {context_location}: {e}")
        
        # Fallback to minimal context
        return self._create_minimal_context(url, vocab_info)
    
    def _try_backup_location(self, url, backup_location):
        "Try fetching from backup location"
        try:
            backup_resp = httpx.get(backup_location)
            if backup_resp.status_code == 200:
                backup_data = backup_resp.json()
                result = {'contextUrl': None, 'documentUrl': url, 'document': backup_data}
                self.context_cache[url] = result
                return result
        except Exception as backup_e:
            print(f"Error fetching from backup location: {backup_e}")
        return None
    
    def _try_access_pattern(self, url, vocab_info, pattern):
        "Try a specific access pattern for context retrieval"
        if pattern == "direct_download":
            try:
                response = httpx.get(url)
                if response.status_code == 200:
                    try:
                        context_data = response.json()
                        result = {'contextUrl': None, 'documentUrl': url, 'document': context_data}
                        self.context_cache[url] = result
                        return result
                    except: pass
            except: pass
        return None
    
    def _create_minimal_context(self, url, vocab_info):
        "Create a minimal context when all else fails"
        # Use inline context if available
        if vocab_info.get("features", {}).get("inline_context", False):
            # In a real implementation, we would extract this from examples
            default_context = {"@vocab": vocab_info.get("uri", url)}
            # Add common terms if available
            common_terms = vocab_info.get("common_terms", [])
            for term in common_terms:
                default_context[term] = f"{vocab_info.get('uri', url)}{term}"
        else:
            # Simplest fallback
            default_context = {"@vocab": vocab_info.get("uri", url)}
        
        result = {'contextUrl': None, 'documentUrl': url, 'document': default_context}
        self.context_cache[url] = result
        return result
    
    def handle_cache_support(self, url, vocab_info, default_loader):
        "Handle vocabularies that can be dereferenced but benefit from caching"
        if url in self.context_cache: return self.context_cache[url]
        
        # Apply URL transformations if defined
        transformed_url = self.apply_url_transformations(url, vocab_info)
        
        try:
            result = default_loader(transformed_url, {})
            self.context_cache[url] = result
            if transformed_url != url: self.context_cache[transformed_url] = result
            return result
        except Exception as e:
            print(f"Error using default loader for {transformed_url}: {e}")
            
            # Try with context location if different
            context_location = vocab_info.get("resources", {}).get("context")
            if context_location and context_location != url and context_location != transformed_url:
                try:
                    result = default_loader(context_location, {})
                    result['documentUrl'] = url
                    self.context_cache[url] = result
                    return result
                except Exception as inner_e:
                    print(f"Error fetching from context_location {context_location}: {inner_e}")
        
        # Fallback to minimal context
        return self._create_minimal_context(url, vocab_info)
    
    def apply_url_transformations(self, url, vocab_info):
        "Apply URL transformations defined in vocabulary info"
        import re
        
        transformations = vocab_info.get("url_transformations", [])
        for transform in transformations:
            pattern = transform.get("pattern")
            replacement = transform.get("replacement")
            if pattern and replacement:
                try:
                    transformed_url = re.sub(pattern, replacement, url)
                    if transformed_url != url:
                        print(f"Transformed URL: {url} -> {transformed_url}")
                        return transformed_url
                except Exception as e:
                    print(f"Error applying URL transformation: {e}")
        
        return url
    
    def handle_discovery_support(self, url, default_loader):
        "Handle unknown vocabularies by attempting to discover their structure"
        if url in self.context_cache: return self.context_cache[url]
        
        try:
            result = default_loader(url, {})
            self.context_cache[url] = result
            return result
        except Exception as e:
            print(f"Standard dereferencing failed for {url}: {e}")
        
        # Common URL variations to try
        variations = [
            f"{url}/context",
            f"{url.rstrip('/')}/context.jsonld",
            f"{url}/latest/context",
            f"{url.rstrip('/')}/.well-known/context.jsonld"
        ]
        
        for variation in variations:
            try:
                result = default_loader(variation, {})
                result['documentUrl'] = url
                self.context_cache[url] = result
                return result
            except Exception as e:
                print(f"Variation {variation} failed: {e}")
        
        # Fallback to minimal context
        minimal_context = {"@vocab": url}
        result = {'contextUrl': None, 'documentUrl': url, 'document': minimal_context}
        self.context_cache[url] = result
        return result
    
    def create_document_loader(self):
        "Create a document loader that handles vocabularies at different support levels"
        from pyld import jsonld
        default_loader = jsonld.get_document_loader()
        
        def vocab_aware_loader(url, options=None):
            "Custom document loader that handles different vocabulary support levels"
            options = options or {}
            
            # Check if this URL matches any known vocabulary
            for vocab_name, vocab_info in self.registry.items():
                vocab_uri = vocab_info.get("uri")
                if not vocab_uri: continue
                
                if url == vocab_uri or url.startswith(vocab_uri):
                    # Add to loaded vocabularies set
                    self.loaded_vocabs.add(vocab_name)
                    
                    support_level = vocab_info.get("support_level", "discover")
                    
                    if support_level == "direct":
                        return self.handle_direct_support(url, vocab_info)
                    elif support_level == "cache":
                        return self.handle_cache_support(url, vocab_info, default_loader)
                    else:  # "discover"
                        return self.handle_discovery_support(url, default_loader)
            
            # Check for URL transformations across all vocabularies
            for vocab_info in self.registry.values():
                transformed_url = self.apply_url_transformations(url, vocab_info)
                if transformed_url != url:
                    # Use the transformed URL with the default loader
                    try:
                        result = default_loader(transformed_url, options)
                        self.context_cache[url] = result
                        return result
                    except:
                        # If transformation fails, continue with original URL
                        pass
            
            # No match found, use default loader
            return default_loader(url, options)
        
        return vocab_aware_loader
    
    def get_loaded_vocabularies(self):
        "Get list of vocabularies that have been loaded"
        return list(self.loaded_vocabs)
    
    def get_vocabulary_info(self, vocab_name):
        "Get detailed information about a vocabulary"
        if vocab_name not in self.registry:
            return None
        return self.registry[vocab_name]
    
    def detect_vocabularies_in_context(context_list):
        """Detect which vocabularies are used in a given context list"""
        vocabs = []
        
        # Handle different context types
        if isinstance(context_list, str):
            context_list = [context_list]
        elif not isinstance(context_list, list):
            context_list = [context_list]
        
        # Check each context against registry entries
        for ctx in context_list:
            if isinstance(ctx, str):
                # Check if this URI matches or starts with any vocabulary URI
                for vocab_name, vocab_info in VOCABULARY_REGISTRY.items():
                    # Check primary URI
                    vocab_uri = vocab_info.get("uri", "")
                    if ctx == vocab_uri or ctx.startswith(vocab_uri):
                        vocabs.append(vocab_name)
                        continue
                    
                    # Check alternative URIs
                    alt_uris = vocab_info.get("alternative_uris", [])
                    for alt_uri in alt_uris:
                        if ctx == alt_uri or ctx.startswith(alt_uri):
                            vocabs.append(vocab_name)
                            break
            elif isinstance(ctx, dict):
                # Check @vocab and other mappings
                if "@vocab" in ctx:
                    vocab_uri = ctx["@vocab"]
                    for vocab_name, vocab_info in VOCABULARY_REGISTRY.items():
                        primary_uri = vocab_info.get("uri", "")
                        if vocab_uri == primary_uri:
                            vocabs.append(vocab_name)
                            continue
                        
                        # Check alternative URIs
                        alt_uris = vocab_info.get("alternative_uris", [])
                        if any(vocab_uri == alt_uri for alt_uri in alt_uris):
                            vocabs.append(vocab_name)
                
                # Check prefixes
                for vocab_name, vocab_info in VOCABULARY_REGISTRY.items():
                    prefix = vocab_info.get("prefix", "")
                    if prefix and prefix in ctx:
                        vocabs.append(vocab_name)
        
        # Remove duplicates
        return list(set(vocabs))


# %% ../01_vocabularytools.ipynb 8
# Create a singleton instance
_manager = VocabularyManager()

# %% ../01_vocabularytools.ipynb 10
# Export functions that use the singleton manager
def create_vocab_aware_document_loader(registry=None):
    "Create a document loader that handles vocabularies at different support levels"
    if registry: _manager.registry = registry
    return _manager.create_document_loader()

# %% ../01_vocabularytools.ipynb 11
def register_vocab_aware_loader():
    "Register our vocabulary-aware document loader with PyLD"
    from pyld import jsonld
    loader = create_vocab_aware_document_loader()
    jsonld.set_document_loader(loader)
    return loader

# %% ../01_vocabularytools.ipynb 12
def get_loaded_vocabularies():
    "Get list of vocabularies that have been loaded"
    return _manager.get_loaded_vocabularies()

# %% ../01_vocabularytools.ipynb 13
def get_vocabulary_info(vocab_name):
    "Get detailed information about a vocabulary"
    return _manager.get_vocabulary_info(vocab_name)


# %% ../01_vocabularytools.ipynb 14
def detect_vocabularies_in_context(context_list):
    """Detect which vocabularies are used in a given context list"""
    vocabs = []
    
    # Normalize input to list
    if not isinstance(context_list, list): context_list = [context_list]
    
    # Check each context against registry entries
    for ctx in context_list:
        if isinstance(ctx, str):
            # Check against all vocabulary URIs
            for vocab_name, vocab_info in VOCABULARY_REGISTRY.items():
                # Check primary URI
                if ctx == vocab_info.get("uri", "") or ctx.startswith(vocab_info.get("uri", "")):
                    vocabs.append(vocab_name)
                    continue
                    
                # Check alternative URIs if available
                for alt_uri in vocab_info.get("alternative_uris", []):
                    if ctx == alt_uri or ctx.startswith(alt_uri):
                        vocabs.append(vocab_name)
                        break
        elif isinstance(ctx, dict):
            # Check @vocab against URIs
            if "@vocab" in ctx:
                vocab_uri = ctx["@vocab"]
                for vocab_name, vocab_info in VOCABULARY_REGISTRY.items():
                    if vocab_uri == vocab_info.get("uri", "") or any(vocab_uri == alt for alt in vocab_info.get("alternative_uris", [])):
                        vocabs.append(vocab_name)
            
            # Check for prefixes in context
            for vocab_name, vocab_info in VOCABULARY_REGISTRY.items():
                prefix = vocab_info.get("prefix", "")
                if prefix and prefix in ctx:
                    vocabs.append(vocab_name)
    
    # Remove duplicates
    return list(set(vocabs))


# %% ../01_vocabularytools.ipynb 15
def apply_url_transformation(url):
    "Apply URL transformations from all vocabularies"
    for vocab_info in VOCABULARY_REGISTRY.values():
        transformed = _manager.apply_url_transformations(url, vocab_info)
        if transformed != url:
            return transformed
    return url


# %% ../01_vocabularytools.ipynb 17
def apply_collision_strategy(data, strategy):
    """Apply a collision strategy to the data"""
    if not strategy or not isinstance(data, dict) or "@context" not in data:
        return data
    
    strategy_type = strategy.get("strategy")
    
    if strategy_type == "property_scoped" and "property" in strategy:
        return _apply_property_scoped_strategy(data, strategy)
    elif strategy_type == "graph_partition":
        return create_graph_partition(data)
    elif strategy_type == "property_mapping":
        return _apply_property_mapping_strategy(data, strategy)
    elif strategy_type == "nested_contexts":
        return _apply_nested_contexts_strategy(data, strategy)
    elif strategy_type == "context_versioning":
        return _apply_context_versioning_strategy(data, strategy)
    elif strategy_type == "separate_graphs":
        return _apply_separate_graphs_strategy(data, strategy)
    
    return data


# %% ../01_vocabularytools.ipynb 18
def _apply_property_scoped_strategy(data, strategy):
    """Apply property-scoped context strategy"""
    import copy
    
    property_name = strategy["property"]
    if property_name in data and isinstance(data[property_name], dict):
        result = copy.deepcopy(data)
        
        # Create new context structure
        if isinstance(result["@context"], list) and len(result["@context"]) >= 2:
            new_context = {"@version": 1.1}
            
            # Use primary context as base
            primary_vocab = strategy.get("primary")
            if primary_vocab and primary_vocab in VOCABULARY_REGISTRY:
                primary_uri = VOCABULARY_REGISTRY[primary_vocab]["uri"]
                new_context["@vocab"] = primary_uri
            else:
                # Just use the first context
                new_context["@vocab"] = result["@context"][0]
            
            # Create scoped context for the property
            secondary_vocab = strategy.get("secondary")
            if secondary_vocab and secondary_vocab in VOCABULARY_REGISTRY:
                secondary_uri = VOCABULARY_REGISTRY[secondary_vocab]["uri"]
                new_context[property_name] = {
                    "@id": f"{new_context['@vocab']}{property_name}",
                    "@context": {"@vocab": secondary_uri},
                    "@protected": False
                }
            else:
                # Use second context from list
                new_context[property_name] = {
                    "@id": f"{new_context['@vocab']}{property_name}",
                    "@context": result["@context"][1],
                    "@protected": False
                }
            
            result["@context"] = new_context
            return result
    
    return data


# %% ../01_vocabularytools.ipynb 19
def _apply_property_mapping_strategy(data, strategy):
    """Apply property mapping strategy"""
    import copy
    
    result = copy.deepcopy(data)
    mappings = strategy.get("mappings", {})
    
    # Create a single context with mappings
    if isinstance(result["@context"], list):
        new_context = {"@version": 1.1}
        
        # Use first context as base
        if isinstance(result["@context"][0], str):
            new_context["@vocab"] = result["@context"][0]
        elif isinstance(result["@context"][0], dict):
            new_context.update(result["@context"][0])
        
        # Add mappings
        for source, target in mappings.items():
            src_prefix, src_term = source.split(":") if ":" in source else ("", source)
            new_context[src_term] = {"@id": target}
        
        result["@context"] = new_context
    
    return result


# %% ../01_vocabularytools.ipynb 20
def _apply_nested_contexts_strategy(data, strategy):
    """Apply nested contexts strategy"""
    import copy
    
    result = copy.deepcopy(data)
    outer = strategy.get("outer")
    inner = strategy.get("inner")
    
    if outer and inner and outer in VOCABULARY_REGISTRY and inner in VOCABULARY_REGISTRY:
        outer_uri = VOCABULARY_REGISTRY[outer]["uri"]
        inner_uri = VOCABULARY_REGISTRY[inner]["uri"]
        
        # Create nested context structure
        new_context = {
            "@version": 1.1,
            "@vocab": outer_uri,
            "inner": {
                "@id": f"{outer_uri}inner",
                "@context": {"@vocab": inner_uri}
            }
        }
        
        result["@context"] = new_context
    
    return result

# %% ../01_vocabularytools.ipynb 21
def _apply_context_versioning_strategy(data, strategy):
    """Apply context versioning strategy"""
    import copy
    
    result = copy.deepcopy(data)
    version = strategy.get("context_version", "1.1")
    
    # Ensure context is an object with version
    if isinstance(result["@context"], list):
        new_context = {"@version": version}
        
        # Add all contexts from the list
        for ctx in result["@context"]:
            if isinstance(ctx, str):
                # Use a generated prefix
                prefix = f"ctx{len(new_context)}"
                new_context[prefix] = ctx
            elif isinstance(ctx, dict):
                # Merge the context object
                for k, v in ctx.items():
                    if k not in new_context:
                        new_context[k] = v
        
        result["@context"] = new_context
    
    return result


# %% ../01_vocabularytools.ipynb 22
def _apply_separate_graphs_strategy(data, strategy):
    """Apply separate graphs strategy"""
    # This is essentially a graph partition but with specific handling
    return create_graph_partition(data)


# %% ../01_vocabularytools.ipynb 23
def create_graph_partition(data):
    """Create a graph partition for data with conflicting contexts"""
    if not isinstance(data, dict): return data
        
    # Start building a graph structure
    graph = {"@graph": []}
    
    # Function to process nested objects recursively
    def process_object(obj, parent_id=None, link_property=None):
        if not isinstance(obj, dict): return obj
            
        # Ensure the object has an ID
        if "@id" not in obj and "id" not in obj:
            obj_id = f"urn:uuid:{uuid.uuid4()}"
            obj["@id"] = obj_id
        else:
            obj_id = obj.get("@id", obj.get("id"))
            
        # Create a copy for the graph
        graph_obj = copy.deepcopy(obj)
        
        # Process nested objects
        for key, value in list(graph_obj.items()):
            if isinstance(value, dict) and len(value) > 1:
                # Extract nested object
                nested_id = process_object(value, obj_id, key)
                # Replace with reference
                graph_obj[key] = {"@id": nested_id}
            elif isinstance(value, list):
                # Process list of objects
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        nested_id = process_object(item)
                        value[i] = {"@id": nested_id}
        
        # Add to graph
        graph["@graph"].append(graph_obj)
        
        # If this is a child object, link back to parent
        if parent_id and link_property:
            # Find the parent in the graph
            for entity in graph["@graph"]:
                if entity.get("@id") == parent_id:
                    # Add link to this object
                    entity[link_property] = {"@id": obj_id}
                    break
        
        return obj_id
    
    # Start processing with the root object
    process_object(data)
    return graph

# %% ../01_vocabularytools.ipynb 25
def load_context_for_vocabulary(vocab_name):
    """Load and return the context for a specific vocabulary"""
    # Check if the vocabulary is in our registry
    if vocab_name not in VOCABULARY_REGISTRY:
        raise ValueError(f"Unknown vocabulary: {vocab_name}")
    
    vocab_info = VOCABULARY_REGISTRY[vocab_name]
    vocab_uri = vocab_info["uri"]
    
    # Use our vocabulary manager to handle retrieval
    result = _manager.handle_direct_support(vocab_uri, vocab_info)
    
    # Return just the context document
    return result["document"]

# %% ../01_vocabularytools.ipynb 26
def create_dataset_with_vocabulary(dataset_data, vocab_name):
    """Create a dataset using a specific vocabulary"""
    # Load the context for the vocabulary
    context = load_context_for_vocabulary(vocab_name)
    
    # Create the dataset with the context
    dataset = {
        "@context": context,
        **dataset_data
    }
    
    return dataset


# %% ../01_vocabularytools.ipynb 27
def add_dataset_to_memory(memory, dataset_data, vocab_name):
    """Add a dataset to semantic memory with proper vocabulary handling"""
    # Register our vocabulary-aware document loader
    register_vocab_aware_loader()
    
    # Create the dataset with the vocabulary context
    dataset = create_dataset_with_vocabulary(dataset_data, vocab_name)
    
    # Add to memory
    return memory.add_jsonld(dataset)


# %% ../01_vocabularytools.ipynb 28
def compact_entity_with_vocabulary(entity, vocab_name):
    """Compact an entity using the proper context for a vocabulary"""
    from pyld import jsonld
    
    # Get the proper context object for this vocabulary
    context = load_context_for_vocabulary(vocab_name)
    
    # Compact using this context
    compacted = jsonld.compact(entity, context)
    
    return compacted

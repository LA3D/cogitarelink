# Verifiable Credentials Context Handling Improvements

## Current Issues

When handling Verifiable Credentials (VC) documents with credentialSubject properties, we currently encounter "protected term redefinition" errors due to conflicts between the VC vocabulary and Schema.org vocabulary. These errors occur because:

1. JSON-LD 1.1 introduces @protected terms to prevent accidental term overriding
2. Both VC and Schema.org vocabularies define some of the same terms as protected
3. Our current context composition strategy doesn't efficiently handle these protected term conflicts

While our current implementation works by catching these errors and applying fallback strategies, a more elegant solution would properly handle protected terms during context composition.

## Proposed Changes to the Composer Class

### 1. Enhanced Context Analysis

```markdown
- Add a `analyze_vocabularies` method to detect protected term conflicts before merging
- Implement protected term extraction for each vocabulary to identify potential conflicts
- Map relationships between vocabularies to understand how they are typically used together
```

### 2. Smart Vocabulary Segregation

```markdown
- Implement vocabulary-specific namespacing for potentially conflicting protected terms
- Add support for JSON-LD 1.1's @protected, @propagate, and scoped context features
- Use type-specific context application for different entity types in the same document
```

### 3. Context Composition Strategies

```markdown
- Add a new Strategy enum value: `protected_term_segregation`
- Implement protected term handling that applies different merging rules when protected terms are detected
- Create a more sophisticated version of the property_scoped strategy specifically for credential subjects
```

### 4. Implementation Details

#### Modified Composer.compose Method:

```python
def compose(self, prefixes: List[str], support_nest=False, propagate=True, 
           handle_protected=True) -> Dict[str, Any]:
    """
    Parameters
    ----------
    prefixes : list of registry prefixes, ordered by priority
    support_nest : bool, if True, add @nest support to the context
    propagate : bool, if False, add @propagate: false to prevent context inheritance
    handle_protected: bool, if True, use special protected term handling
    
    Returns
    -------
    dict – JSON-LD object ready to drop into a document: {"@context": ...}
    """
    # Implementation...
```

#### New Method for Protected Term Handling:

```python
def _handle_protected_terms(self, primary_ctx: Dict[str, Any], secondary_ctx: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle protected terms when merging contexts
    
    Parameters
    ----------
    primary_ctx: The primary context (higher priority)
    secondary_ctx: The secondary context to merge with the primary
    
    Returns
    -------
    A merged context with protected terms handled properly
    """
    # Implementation...
```

### 5. Special Handling for VC + Schema Combination

```markdown
- Add special handling for the specific case of VC + Schema.org vocabularies
- Implement proper credentialSubject handling at the context level
- Add a predefined context partition strategy for VC documents that isolates the credential subject context
```

### 6. Updates to collision_data.json

```json
{
  "('vc', 'schema')": {
    "strategy": "protected_term_segregation",
    "primary": "vc",
    "secondary": "schema",
    "description": "Handles protected term conflicts between VC and schema vocabularies"
  }
}
```

## Impact and Benefits

1. **Elimination of Warnings:** The changes will eliminate the protected term redefinition warnings
2. **Improved Processing:** More efficient processing without needing fallback error handling
3. **Better Standards Compliance:** Full compliance with JSON-LD 1.1 protected terms specification
4. **Enhanced Readability:** More clearly structured code for handling complex vocabulary interactions
5. **Future-proofing:** Better support for additional vocabularies that may use protected terms

## Implementation Timeline

1. Implement the analyze_vocabularies method
2. Add protected term detection and extraction
3. Create the new strategy enum and handler
4. Update the composer.compose method
5. Add special VC+Schema handling
6. Update collision_data.json
7. Test with various VC documents
8. Document the new behavior

## Testing Strategy

1. Create test cases for various combinations of vocabularies with protected terms
2. Ensure backward compatibility with existing code
3. Verify that no warnings or errors occur for VC processing
4. Test performance to ensure the enhancements don't significantly impact processing time
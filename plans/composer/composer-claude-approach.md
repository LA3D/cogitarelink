# Composer Architecture: Claude Code-Inspired Approach

## Motivation and Introduction

As Large Language Models (LLMs) become increasingly central to agent-based systems, we face a critical challenge: how to efficiently manage structured semantic knowledge within the constraints of LLM context windows while enabling powerful tool interactions. 

Cogitarelink has proven itself as an excellent system for managing richly-typed semantic knowledge with its high-quality JSON-LD processing, SHACL validation, and provenance tracking. However, the current architecture lacks the explicit mechanisms needed to:

1. Decide what knowledge should live in an LLM's context window
2. Materialize that knowledge into token-efficient representations
3. Execute tools and process their outputs effectively
4. Allow LLMs to commit generated knowledge back to durable storage

Looking at successful coding assistants like Claude Code and GitHub Copilot, we observe a convergence toward architectures that favor explicit knowledge navigation over embedding-based approaches. These systems demonstrate that a "follow-your-nose" strategy—where the AI traverses explicit relationships between entities—can create powerful, efficient experiences without the computational overhead and indirection of embedding-based retrieval.

This document outlines a refactoring plan that brings Cogitarelink's semantic strengths together with Claude Code's efficient tool architecture. The result will be a system that can:

- Navigate semantic graph structures with precision
- Serialize complex knowledge efficiently within token budgets
- Execute tools with strong validation and parallel processing
- Integrate with any LLM provider through a standardized adapter system

By embracing this approach, we maintain Cogitarelink's commitment to semantic integrity while enabling the flexible, powerful interactions that modern LLM applications demand.

## 1. Architectural Vision

The revised architecture brings Cogitarelink's semantic memory capabilities together with Claude Code's tool execution pattern, creating a system that:

1. **Efficiently manages semantic knowledge** within token budget constraints
2. **Provides robust tool execution** with standardized interfaces
3. **Follows a "follow-your-nose" approach** to knowledge navigation
4. **Supports flexible integration** with different LLM providers

## 2. Core Components to Modify

### 2.1. Cache (`core/cache.py`)

**Current state**: Basic LRU/TTL caching without token awareness.

**Changes needed**:
- Add token counting mechanism
- Implement token-aware eviction strategies
- Add specialized cache for context window fragments
- Support caching tool results with appropriate TTL

**Reasoning**: The cache needs to understand token constraints for LLMs and make intelligent decisions about what to keep in memory versus what to evict based on both relevance and token usage.

### 2.2. Registry (`vocab/registry.py`)

**Current state**: Registry for vocabulary prefixes without tool registry capabilities.

**Changes needed**:
- Add Tool registry mechanism similar to Claude Code's function registry
- Support for registering/loading tools from entry points
- Add metadata fields for token cost estimation
- Add categorization system for tools

**Reasoning**: The registry needs to expand beyond vocabulary management to include tools, enabling discovery, validation, and execution within the larger ecosystem.

### 2.3. Collision (`vocab/collision.py`)

**Current state**: Handles vocabulary collisions without awareness of tools or token budgets.

**Changes needed**:
- Add strategy for handling tool namespace collisions
- Modify to be aware of token budget when resolving collisions
- Add conflict resolution for tool execution order

**Reasoning**: As the system expands to handle both vocabulary and tool collisions, the collision resolver needs to account for token budgets and tool execution order.

### 2.4. Composer (`vocab/composer.py`)

**Current state**: Merges vocabularies without token optimization or serialization options.

**Changes needed**:
- Add `MaterializerComposer` class that optimizes for token usage
- Support for different serialization styles (compact, verbose)
- Method to estimate token count for composed contexts
- Interface to integrate with the context window system

**Reasoning**: The composer is central to creating compact, token-efficient representations of semantic knowledge that can fit within LLM context windows.

### 2.5. Entity (`core/entity.py`)

**Current state**: Immutable wrapper around JSON-LD without token-aware serialization.

**Changes needed**:
- Add serialization methods with token budget controls
- Version that supports immutable/mutable transitions for LLM edits
- Support for storing/retrieving tool execution results
- Method to extract relevant subgraphs for context windows

**Reasoning**: Entities need to be serializable in ways that respect token budgets while maintaining semantic integrity, and need flexibility for LLM interaction.

### 2.6. Graph (`core/graph.py`)

**Current state**: Basic triple store without token-aware retrieval or traversal.

**Changes needed**:
- Methods to extract semantic neighborhoods for context
- Retrieval methods optimized for token budgets
- Traversal functions for finding related entities based on queries
- Support for graph partitioning based on context window constraints

**Reasoning**: The graph manager needs to intelligently retrieve related knowledge while respecting token budgets, enabling "follow-your-nose" exploration.

### 2.7. Processor (`core/processor.py`)

**Current state**: Pipeline for managing JSON-LD entities without tool awareness.

**Changes needed**:
- Add tool execution pipeline
- Support for parsing LLM responses with structured sections
- Handling for committing LLM-generated knowledge
- Methods for retrieving semantically relevant entities

**Reasoning**: The processor needs to expand from entity management to include tool orchestration and LLM interaction.

## 3. CLI Tools Refactoring

### 3.1. CLI (`cli/cli.py` from 09_cli)

**Current state**: Basic tool registry and agent context without token awareness.

**Changes needed**:
- Transform `ToolRegistry` to align with JSON Schema-based tool definitions
- Add parameter types, descriptions, and validation
- Implement batched/parallel tool execution
- Enhance `AgentContext` with token counting and context window management

**Reasoning**: The CLI tools need to align with Claude Code's architecture for tool definitions, validation, and execution.

### 3.2. Vocab Tools (`cli/vocab_tools.py` from 09a_vocab_tools)

**Current state**: Collection of tools for vocabulary management without organization or token awareness.

**Changes needed**:
- Reorganize tool functions into logical packages
- Convert to Protocol-based system
- Add JSON Schema definitions for each tool
- Update for token-aware serialization

**Reasoning**: The vocabulary tools need to be restructured to align with the new architecture and organized into logical groupings.

### 3.3. Agent CLI (`cli/agent_cli.py` from 10_agent_cli)

**Current state**: Agent-oriented CLI without context window management or standardized tool interfaces.

**Changes needed**:
- Implement MCP client-server architecture
- Add support for parallel tool execution
- Add tool categories and discoverability
- Implement context window management
- Add committer pattern for LLM outputs

**Reasoning**: The agent CLI needs to be completely redesigned to support the new architecture, particularly around context window management and tool execution.

## 4. New Components to Create

### 4.1. Core Components

- `core/tokenizer.py`: Token counting functions for different LLM providers
- `core/tool_registry.py`: Formal tool registry with JSON Schema validation

### 4.2. Agent Package

- `agent/interfaces.py`: Protocol definitions for the architecture
- `agent/context_window.py`: Context window management with token budget
- `agent/materialiser.py`: Token-budgeted serialization of entities
- `agent/retrieval.py`: Intelligent retrieval of semantic knowledge
- `agent/committer.py`: Parsing and committing LLM-generated knowledge

### 4.3. Adapters

- `agent/adapters/`: LLM provider adapters for different services

## 5. Implementation Strategy

### 5.1. Phase 1: Core Infrastructure

1. Implement `core/tokenizer.py` and token counting
2. Create base interfaces in `agent/interfaces.py`
3. Update cache to be token-aware
4. Implement basic context window management

### 5.2. Phase 2: Tool System

1. Refactor `ToolRegistry` to use JSON Schema
2. Implement tool validation and execution
3. Add batched/parallel execution support
4. Create LLM adapters for common providers

### 5.3. Phase 3: Knowledge Management

1. Implement materializer for token-efficient serialization
2. Add retrieval strategies for semantic knowledge
3. Create committer for LLM-generated content
4. Update graph manager for token-aware traversal

### 5.4. Phase 4: CLI Refactoring

1. Refactor CLI tools to use new architecture
2. Implement agent CLI with MCP pattern
3. Reorganize vocabulary tools
4. Add tool categorization and discovery

## 6. Claude Code-Inspired Features to Emphasize

### 6.1. "Follow-Your-Nose" Approach

The architecture will focus on traversing explicit relationships in the semantic graph rather than using embeddings. This approach will:

- Follow explicit semantic relationships between entities
- Use graph traversal to find related knowledge
- Combine multiple tool calls to build comprehensive understanding
- Avoid the complexity and overhead of embedding-based systems

### 6.2. Tool Use Patterns

The architecture will adopt Claude Code's tool use patterns:

- JSON Schema-based tool definitions
- Standardized interfaces for tools
- Batched/parallel tool execution
- Tool categorization and discovery

### 6.3. Context Management

The architecture will implement Claude Code's context management approach:

- Token-aware context window management
- Efficient serialization of knowledge
- Intelligent eviction strategies
- Caching of tool results

## 7. Additional Considerations

Beyond the core architectural changes, these aspects should be addressed:

- **Error Handling**: More robust error handling with detailed diagnostics
- **Security**: Proper input validation and permission checks
- **Observability**: Standardized logging and metrics
- **Testing**: Specialized test helpers for the new architecture
- **Tool Versioning**: Explicit versioning for tool interfaces
- **Streaming**: Support for streaming responses from LLMs
- **Memory Optimization**: Efficient memory usage for large knowledge graphs
- **Configuration**: Standardized configuration management
- **Documentation**: Automatic documentation generation from schemas
- **Rate Limiting**: Manage rate limits for external API calls

## 8. Conclusion

This approach brings together Cogitarelink's semantic memory capabilities with Claude Code's efficient tool architecture. By adopting a "follow-your-nose" approach rather than relying on embeddings, we create a system that is both powerful and efficient, enabling the intelligent management of semantic knowledge within LLM context windows and providing robust tool execution capabilities.

The implementation will require significant refactoring of existing components but will result in a more capable, flexible, and maintainable system that aligns with modern LLM agent architectures while preserving Cogitarelink's semantic strengths.
"""Fill in a module description here"""

# AUTOGENERATED! DO NOT EDIT! File to edit: ../06_workflows.ipynb.

# %% auto 0
__all__ = ['create_workflow', 'run_workflow', 'create_agent']

# %% ../06_workflows.ipynb 4
from fastcore.basics import *
from fastcore.meta import *
from fastcore.test import *
from IPython.display import Markdown, display
from .core import LinkedDataKnowledge
from .navigation import *
from claudette import Chat, tool, toolloop, models
from .tools import find_vocabulary_term, follow_relationship, explore_dataset, search_dataset, get_dataset_evidence
import json
from typing import List, Dict, Any, Optional, Union, Set

# %% ../06_workflows.ipynb 6
def create_workflow(
    steps:List[str], # List of step instructions
    summary:str="Summarize what you've learned from this exploration." # Summary instruction
) -> str: # Workflow prompt
    "Create a simple step-by-step workflow prompt from a list of instructions"
    prompt = "I want you to explore this data step by step:\n\n"
    
    for i, step in enumerate(steps, 1):
        prompt += f"Step {i}: {step}\n\n"
    
    prompt += f"""For each step, use the appropriate tools to gather evidence, and explain what you find before moving to the next step.

{summary}"""
    
    return prompt

# %% ../06_workflows.ipynb 9
def run_workflow(
    agent, # Claude agent with tools
    workflow:str, # Workflow prompt
    kb=None, # Optional vocabulary knowledge base
    dataset_kb=None, # Optional dataset knowledge base
    trace=False # Whether to print the interaction trace
) -> Any: # Agent response
    "Run a workflow with the given agent and knowledge bases"
    # Set global variables if provided
    if kb is not None: globals()['kb'] = kb
    if dataset_kb is not None: globals()['dataset_kb'] = dataset_kb
    
    # Run the workflow
    trace_func = print if trace else None
    return agent.toolloop(workflow, trace_func=trace_func)

# %% ../06_workflows.ipynb 11
def create_agent(
    model:str="claude-3-5-sonnet-20241022", # Claude model to use
    sp:str=None # Optional system prompt
) -> Chat: # Chat agent
    "Create a Claude agent with linked data tools"
    if sp is None:
        sp = """You are a Linked Data Navigator that helps users explore and understand structured data.
When exploring linked data:
- Always cite specific paths and values from the data
- Follow relationships between concepts to build understanding
- Explain both the vocabulary definitions and how they're implemented in actual data
- Use a step-by-step approach to build comprehensive understanding"""
    
    return Chat(
        model=model,
        sp=sp,
        tools=[
            find_vocabulary_term,
            follow_relationship,
            explore_dataset,
            search_dataset,
            get_dataset_evidence
        ]
    )

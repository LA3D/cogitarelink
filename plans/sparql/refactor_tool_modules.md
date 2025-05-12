# Refactoring CogitareLink Tool Modules to Avoid Circular Imports
# Problem Statement
Circular imports between SPARQL and helper modules break CLI registration. E.g., `sparql.py` imports validators from `sparql_tools.py` and vice versa.
# Goals
1. Eliminate circular imports
2. Keep code in notebooks, exported via nbdev
3. Simplify CLI plugin registration
# Strategies
*Single module per suite* – merge all SPARQL code into one file, all retriever code into another
*Core vs Wrapper* – split low-level plumbing (e.g. `sparql_query`) and high-level wrappers into two modules with one-way imports
*Plugin Registration* – use `@agent.tools.register()` in notebooks and import modules in CLI
*Local Imports* – defer cross-tool imports to function scope
# Roadmap
1. Update Jupytext'ed notebooks
2. Run `nbdev_export` and reinstall
3. Verify with `cogitarelink --list-tools`
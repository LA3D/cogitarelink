Title: DASH Suggestions Vocabulary

URL Source: https://datashapes.org/suggestions.html

Markdown Content:
[Jump to Table of Contents](https://datashapes.org/suggestions.html#toc) [Pop Out Sidebar](https://datashapes.org/suggestions.html#toc)

Abstract
--------

This document introduces a declarative RDF data model to represent suggestions that can be used by tools to repair SHACL constraint violations \[[shacl](https://datashapes.org/suggestions.html#bib-shacl "Shapes Constraint Language (SHACL)")\]. The framework uses SPARQL \[[sparql11-query](https://datashapes.org/suggestions.html#bib-sparql11-query "SPARQL 1.1 Query Language")\] to describe updates that need to be applied to a graph in order to fix a given constraint violation. The document illustrates the use of the framework as part of the TopBraid platform.

Status of This Document
-----------------------

This document is a draft of a potential specification. It has no official standing of any kind and does not represent the support or consensus of any standards organization.

This document uses the prefix `dash` which represents the [DASH Data Shapes](http://datashapes.org/) namespace `http://datashapes.org/dash#` which is accessible via its URL `http://datashapes.org/dash`.

Table of Contents
-----------------

1.  [Abstract](https://datashapes.org/suggestions.html#abstract)
2.  [Status of This Document](https://datashapes.org/suggestions.html#sotd)
3.  [Scope of This Document](https://datashapes.org/suggestions.html#scope-of-this-document)
4.  [1. Overview](https://datashapes.org/suggestions.html#general)
5.  [2. Suggestions on Property Constraints](https://datashapes.org/suggestions.html#propertySuggestionGenerator)
    1.  [2.1 dash:SPARQLUpdateSuggestionGenerators](https://datashapes.org/suggestions.html#SPARQLUpdateSuggestionGenerator)
    2.  [2.2 dash:ScriptSuggestionGenerators](https://datashapes.org/suggestions.html#ScriptSuggestionGenerator)
6.  [3. Suggestions for SPARQL-based Constraints](https://datashapes.org/suggestions.html#suggestionGenerator)
7.  [A. References](https://datashapes.org/suggestions.html#references)
    1.  [A.1 Informative references](https://datashapes.org/suggestions.html#informative-references)

Note that this document covers both the general design of the test case framework and also illustrates specific tool support as part of [TopBraid platform](http://www.topquadrant.com/products/). The TopBraid binding should only be understood as one possible implementation and is in no way limiting the general applicability of the framework.

This document uses the prefix `dash` which represents the namespace `http://datashapes.org/dash#` which is accessible via its URL `http://datashapes.org/dash`.

The DASH Suggestions vocabulary provides a declarative data model for representing and sharing instructions on how to fix a data graph so that it no longer violates SHACL constraints. Suggestions represented using this vocabulary can be presented by tools to users as part of a semi-automated process, or employed by advanced tools to fully automate the repair of incorrect data.

The general design attaches instances of `dash:SuggestionGenerator` to SHACL constraint components or SPARQL-based constraints using the dedicated properties `dash:propertySuggestionGenerator` and `dash:suggestionGenerator`. The current version of the DASH vocabulary includes only one subclass of `dash:SuggestionGenerator`, called `dash:SPARQLUpdateSuggestionGenerator`. Each of these SPARQL-based suggestion generators includes a SPARQL UPDATE request that is executed with certain pre-bound variables, producing a change set consisting of triples to add and delete. The resulting change sets can be represented in RDF using the class `dash:GraphUpdate`, which points at triples to add or delete using the properties `dash:addedTriple` and `dash:deletedTriple`.

The following screenshots of [TopBraid EVN](http://www.topquadrant.com/products/topbraid-enterprise-vocabulary-net/) and [TopBraid EDG](http://www.topquadrant.com/products/topbraid-edg/) illustrates how the suggestions framework can be used to guide users with the repair of incorrect data:

![Image 1](https://datashapes.org/images/SHACL-Web-Violations.PNG)

![Image 2](https://datashapes.org/images/SHACL-Web-SchemaExample2.PNG)

The property `dash:propertySuggestionGenerator` is used to point from a `sh:ConstraintComponent` to an instance of `dash:SuggestionGenerator`. The following sections introduce the two currently supported kinds of suggestion generators:

*   [`dash:SPARQLUpdateSuggestionGenerator`](https://datashapes.org/suggestions.html#SPARQLUpdateSuggestionGenerator)
*   [`dash:ScriptSuggestionGenerator`](https://datashapes.org/suggestions.html#ScriptSuggestionGenerator)

Suggestions may be produced by a SPARQL UPDATE command. The following example illustrates how this mechanism can be used to represent a repair strategy for `sh:maxLength` constraints. If a string value is too long, the suggestion is to prune the string to the permitted maximum character length:

[Example 1](https://datashapes.org/suggestions.html#example-representing-a-suggestion-generator-for-sh-maxlength-property-constraints): Representing a suggestion generator for sh:maxLength property constraints

sh:MaxLengthConstraintComponent
  dash:propertySuggestionGenerator \[
      rdf:type dash:SPARQLUpdateSuggestionGenerator ;
      sh:message "Prune string to only {$maxLength} characters" ;
      sh:order 1 ;
      sh:update """
        DELETE {
            $focusNode $predicate $value .
        }
        INSERT {
            $focusNode $predicate $newValue .
        }
        WHERE {
            FILTER (isLiteral($value) && datatype($value) = xsd:string) .
            BIND (SUBSTR($value, 1, $maxLength) AS ?newValue) .
        }
        """ ;
    \] .

The example links the constraint component of `sh:maxLength` (`sh:MaxLengthConstraintComponent`) with a `dash:SPARQLUpdateSuggestionGenerator` using `dash:propertySuggestionGenerator`. The generator must have a string representation of a valid SPARQL UPDATE request as its value for `sh:update`. It may have a value for `sh:order` to indicate preference between multiple suggestions - a higher value indicates that the given suggestion is more likely to fix the issue than those with lower values. The suggestion may also provide a template string for a human-readable display label using `sh:message`. This string may contain placeholders for the parameters of the constraint component (here: `{$maxLength}`).

The SPARQL UPDATE is performed on the data graph containing the violated triples using pre-bound variables for each parameter of the constraint component, similar to how SPARQL-based constraint components are evaluated in SHACL. For example, the value of `sh:maxLength` is pre-bound to the variable `$maxLength`. Likewise, the variable `$predicate` must point at the `sh:path` of the property shape that caused the violation (if the value is a IRI), and `$focusNode` must point at the focus node (`sh:focusNode`) from the validation result. Finally, `$sourceShape` must be bound to the value of `sh:sourceShape`, `$sourceConstraintComponent` must point at the value of `sh:sourceConstraintComponent` and `$shapesGraph` must be the URI of the shapes graph.

If the suggestions are supposed to be presented to the user so that she can confirm them before they are applied, then the SPARQL UPDATE can be performed on a modified graph that includes the data graph triples but can record the triples that a given UPDATE would add or delete. The resulting adds and deletes can be attached to the `sh:ValidationResult` instance as part of a `dash:GraphUpdate` using the property `dash:suggestion`. This is illustrated in the following example.

[Example 2](https://datashapes.org/suggestions.html#example-representing-suggestions-for-a-specific-constraint-violation): Representing suggestions for a specific constraint violation

\[
    rdf:type sh:ValidationResult ;
    sh:focusNode ex:InvalidResource1 ;
    sh:resultPath schema:postalCode ;
    sh:resultSeverity sh:Violation ;
    sh:sourceConstraintComponent sh:MaxLengthConstraintComponent ;
    sh:value "58093" ;
    dash:suggestion \[
        rdf:type dash:GraphUpdate ;
        dash:addedTriple \[
            rdf:type rdf:Statement ;
            rdf:object "5809" ;
            rdf:predicate schema:postalCode ;
            rdf:subject ex:InvalidResource1 ;
        \] ;
        dash:deletedTriple \[
            rdf:type rdf:Statement ;
            rdf:object "58093" ;
            rdf:predicate schema:postalCode ;
            rdf:subject ex:InvalidResource1 ;
        \] ;
        sh:order 1 ;
    \]
\] .

As shown above, the results of applying a SPARQL UPDATE are represented as instances of `dash:GraphUpdate` and each added triple is represented using an instance of `rdf:Statement` and its properties `rdf:subject`, `rdf:predicate` and `rdf:object`. Likewise, the triples that shall be deleted are represented using the property `dash:deletedTriple`.

This requires TopBraid 7.0 or later.

Instances of `dash:ScriptSuggestionGenerator` implement suggestion generators that are backed by an [Active Data Shapes](http://datashapes.org/active) script. The script needs to return a JSON object or an array of JSON objects if it shall generate multiple suggestions. It may also return `null` to indicate that nothing was suggested.

Note that the whole script is evaluated as a (JavaScript) expression, and those will use the last value as result. So simply putting an object at the end of your script should do. Alternatively, define the bulk of the operation as a function and simply call that function in the script.

Each response object can have the following fields:

*   `message` a human readable message, defaults to the rdfs:label(s) of the suggestion generator
*   `add` an array of triples to add, each triple as an array with three nodes for subject, predicate and object
*   `delete` like add, for the triples to delete

Suggestions with neither added nor deleted triples will be discarded.

At execution time, the script operates on the data graph as the active graph, with the following pre-bound variables:

*   `focusNode`: the `NamedNode` that is the sh:focusNode of the validation result
*   `predicate`: the `NamedNode` representing the predicate of the validation result, assuming `sh:resultPath` is a URI
*   `value`: the value node from the validation result's `sh:value`, cast into the most suitable JavaScript object
*   the other pre-bound variables for the parameters of the constraint, e.g. in a `sh:maxCount` constraint it would be `maxCount`

The script will be executed in read-only mode, i.e. it cannot modify the graph.

This example implements the same use case as before, but using `dash:js`:

[Example 3](https://datashapes.org/suggestions.html#example-3)

sh:MaxLengthConstraintComponent
    dash:propertySuggestionGenerator \[
        a dash:ScriptSuggestionGenerator ;
        dash:js """
let newValue = value.substring(0, maxLength);
(
    {
        message: \`Prune to maximum length of ${maxLength} characters\`,
        add: \[
            \[ focusNode, predicate, newValue \]
        \],
        delete: \[
            \[ focusNode, predicate, value \]
        \]
    }
)
""" \] .

If a validation result has been produced by a SPARQL-based constraint (using `sh:sparql`), then the constraint may point at a suggestion generator similar to the previous section. The main difference is that fewer variables will be pre-bound when the UPDATE executes since there are no parameters.

The following example illustrates the use of the suggestions framework to ensure that the full name of a person is the concatenation of given name and family name.

[Example 4](https://datashapes.org/suggestions.html#example-suggestions-for-sparql-based-constraints): Suggestions for SPARQL-based constraints

\# baseURI: http://example.org
# imports: http://datashapes.org/dash
# prefix: ex

@prefix dash: <http://datashapes.org/dash#\> .
@prefix ex: <http://example.org#\> .
@prefix owl: <http://www.w3.org/2002/07/owl#\> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#\> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#\> .
@prefix sh: <http://www.w3.org/ns/shacl#\> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#\> .

<http://example.org\>
	a owl:Ontology ;
	owl:imports <http://datashapes.org/dash\> ;
	sh:declare \[
		a sh:PrefixDeclaration ;
		sh:namespace "http://example.org#"^^xsd:anyURI ;
		sh:prefix "ex" ;
	\] .

ex:Person
	a rdfs:Class, sh:NodeShape ;
	rdfs:label "Person" ;
	rdfs:subClassOf rdfs:Resource ;
	sh:property \[
		a sh:PropertyShape ;
		sh:path ex:familyName ;
		sh:datatype xsd:string ;
		sh:maxCount 1 ;
		sh:minCount 1 ;
	\] ;
	sh:property \[
		a sh:PropertyShape ;
		sh:path ex:fullName ;
		sh:datatype xsd:string ;
		sh:maxCount 1 ;
		sh:minCount 1 ;
	\] ;
	sh:property \[
		a sh:PropertyShape ;
		sh:path ex:givenName ;
		sh:datatype xsd:string ;
		sh:maxCount 1 ;
		sh:minCount 1 ;
	\] ;
	sh:sparql \[
		dash:suggestionGenerator ex:FullNameSuggestionGenerator ;
		sh:message "The full name should be \\"{?suggestedFullName}\\"" ;
		sh:prefixes <http://example.org\> ;
		sh:select """
			SELECT $this ?value ?suggestedFullName (ex:fullName AS ?path)
			WHERE {
				$this ex:fullName ?value .
				$this ex:givenName ?givenName .
				$this ex:familyName ?familyName .
				BIND (CONCAT(?givenName, \\" \\", ?familyName) AS ?suggestedFullName) .
				FILTER (?suggestedFullName != ?value) .
			}""" ;
	\] .
	
ex:FullNameSuggestionGenerator
	a dash:SPARQLUpdateSuggestionGenerator ;
	rdfs:label "Full name suggestion generator" ;
	sh:prefixes <http://example.org\> ;
	sh:update """
		DELETE {
			$focusNode ex:fullName ?oldFullName .
		}
		INSERT {
			$focusNode ex:fullName ?suggestedFullName .
		}
		WHERE {
			$focusNode ex:fullName ?oldFullName .
			$focusNode ex:givenName ?givenName .
			$focusNode ex:familyName ?familyName .
			BIND (CONCAT(?givenName, \\" \\", ?familyName) AS ?suggestedFullName) .
		}""" .

For the following data graph

[Example 5](https://datashapes.org/suggestions.html#example-example-instance-with-a-violation): Example instance with a violation

ex:JohnDoe
	a ex:Person ;
	ex:givenName "John" ;
	ex:familyName "Doe" ;
	ex:fullName "John Due" .

the suggestions framework would produce:

[Example 6](https://datashapes.org/suggestions.html#example-suggestions-for-the-sparql-based-constraint-above): Suggestions for the SPARQL-based constraint above

\[
	a sh:ValidationResult ;
	sh:focusNode ex:JohnDoe ;
	sh:resultPath ex:fullName ;
	sh:resultSeverity sh:Violation ;
	sh:sourceConstraint \_:b53919 ;
	sh:sourceConstraintComponent sh:SPARQLConstraintComponent ;
	sh:sourceShape ex:Person ;
	sh:value "John Due" ;
	dash:suggestion \[
		a dash:GraphUpdate ;
		dash:addedTriple \[
			a rdf:Statement ;
			rdf:subject ex:JohnDoe ;
			rdf:predicate ex:fullName ;
			rdf:object "John Doe" ;
		\] ;
		dash:deletedTriple \[
			a rdf:Statement ;
			rdf:subject ex:JohnDoe ;
			rdf:predicate ex:fullName ;
			rdf:object "John Due" ;
		\] ;
		sh:order 0 ;
	\] ;
\] .

In addition to using a single `sh:update` query, there is an alternative syntax that combines a SELECT query with an UPDATE:

[Example 7](https://datashapes.org/suggestions.html#example-suggestion-generator-combining-select-and-update-queries): Suggestion Generator combining SELECT and UPDATE queries

ex:FullNameSuggestionGenerator
	a dash:SPARQLUpdateSuggestionGenerator ;
	rdfs:label "Full name suggestion generator" ;
	sh:message "Set full name to {?suggestedFullName}" ;
	sh:prefixes <http://example.org\> ;
	sh:select """
		SELECT $this ?oldFullName ?suggestedFullName
		WHERE {
			$this ex:fullName ?oldFullName .
			$this ex:givenName ?givenName .
			$this ex:familyName ?familyName .
			BIND (CONCAT(?givenName, \\" \\", ?familyName) AS ?suggestedFullName) .
		}""" ;
	sh:update """
		DELETE {
			$this ex:fullName ?oldFullName .
		}
		INSERT {
			$this ex:fullName ?suggestedFullName .
		}
		WHERE {
		}""" .

In this variation, the system will use the variable bindings produced by the `sh:select` query to execute `sh:update` queries for each result row. This has the advantage that each suggestion may get a different `sh:message` (in the example above that would be based on the variable `?suggestedFullName`.

\[shacl\]

[Shapes Constraint Language (SHACL)](https://www.w3.org/TR/shacl/). Holger Knublauch; Dimitris Kontokostas. W3C. 20 July 2017. W3C Recommendation. URL: [https://www.w3.org/TR/shacl/](https://www.w3.org/TR/shacl/)

\[sparql11-query\]

[SPARQL 1.1 Query Language](https://www.w3.org/TR/sparql11-query/). Steven Harris; Andy Seaborne. W3C. 21 March 2013. W3C Recommendation. URL: [https://www.w3.org/TR/sparql11-query/](https://www.w3.org/TR/sparql11-query/)
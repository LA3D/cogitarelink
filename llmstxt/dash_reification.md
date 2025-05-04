Title: DASH Reification Support for SHACL

URL Source: https://datashapes.org/reification.html

Markdown Content:
[Jump to Table of Contents](https://datashapes.org/reification.html#toc) [Pop Out Sidebar](https://datashapes.org/reification.html#toc)

Abstract
--------

Reification is a mechanism to make RDF statements about other RDF statements. This document introduces a SHACL constraint component based on the property `dash:reifiableBy` that can be used to instruct processors about the shape that reified statements should conform to. `dash:reifiableBy` links a SHACL property shape with a SHACL node shape that may be used to drive user input or to validate reified statements.

Status of This Document
-----------------------

This document is a draft of a potential specification. It has no official standing of any kind and does not represent the support or consensus of any standards organization.

This document uses the prefix `dash` which represents the [DASH Data Shapes](http://datashapes.org/) namespace `http://datashapes.org/dash#` which is accessible via its URL `http://datashapes.org/dash`.

Table of Contents
-----------------

1.  [Abstract](https://datashapes.org/reification.html#abstract)
2.  [Status of This Document](https://datashapes.org/reification.html#sotd)
3.  [Goals](https://datashapes.org/reification.html#goals)
4.  [1. Background: Implementation Approaches to Reification in RDF](https://datashapes.org/reification.html#reification)
5.  [2. dash:reifiableBy](https://datashapes.org/reification.html#reifiableBy)
6.  [3. dash:reificationRequired](https://datashapes.org/reification.html#reificationRequired)
7.  [A. Reification SPARQL Functions supported by TopBraid](https://datashapes.org/reification.html#tosh)
    1.  [A.1 tosh:reificationURI](https://datashapes.org/reification.html#reificationURI)
    2.  [A.2 tosh:reificationURIOf](https://datashapes.org/reification.html#reificationURIOf)
    3.  [A.3 tosh:reificationSubject/Predicate/Object](https://datashapes.org/reification.html#reificationSubject)
    4.  [A.4 tosh:reifiedValue](https://datashapes.org/reification.html#reifiedValue)

This document introduces a general-purpose vocabulary that can easily be supported by APIs and tools from various vendors. The approach is, for example, implemented as part of [TopBraid EDG](https://www.topquadrant.com/).

Like most features from the DASH namespace, the specifications here may serve as input to future iterations of the official SHACL standards.

_Reification_ is the ability to make statements about statements. For example, you may want to track the date a statement was made and who made it:

ex:Bob ex:age 23 .
    # ex:date "2019-12-05"^^xsd:date ; 
    # ex:author ex:Claire ;

In its current stable version 1.1, the RDF data model is based on subject-predicate-object _triples_ only, but does not have a built-in mechanism to efficiently represent such reified statements. However, the upcoming version 1.2 includes support for an extension called [RDF-star](https://www.w3.org/groups/wg/rdf-star). RDF-star introduces a new type of RDF nodes that can represent a "quoted" triple, and these nodes can appear as subject or object of other triples, representing statements about these triples.

In the current RDF 1.2 draft, there are two syntaxes to represent such statements. The most general syntax uses <<...\>\> to enclose quoted triples:

[Example 1](https://datashapes.org/reification.html#example-1)

ex:Bob ex:age 23 .

<<ex:Bob ex:age 23\>\>
	ex:date "2019-12-05"^^xsd:date ;
	ex:author ex:Claire .

Alternatively, so-called annotations provide this short-hand for cases where a statement is both asserted and the subject of statements about statements:

[Example 2](https://datashapes.org/reification.html#example-2)

ex:Bob ex:age 23 {|
	ex:date "2019-12-05"^^xsd:date ;
	ex:author ex:Claire ;
|}

In TopBraid's current version, the syntax for that case uses \[\[ ... \]\]:

[Example 3](https://datashapes.org/reification.html#example-3)

ex:Bob ex:age 23 \[\[
	ex:date "2019-12-05"^^xsd:date ;
	ex:author ex:Claire ;
\]\] .

Furthermore, the current TopBraid implementation uses "long" URI nodes to represent quoted triples. These will only be visible when you browse source code but are usually hidden by the user interface. A future version of TopBraid will support RDF-star, for example once RDF 1.2 becomes official.

The property `dash:reifiableBy` can be used to link a SHACL property shape with one or more node shapes. Any reified statement must conform to these node shapes.

The following example states that all reified values of `ex:age` at the class `ex:Person` must conform to the (provenance) shape that defines date and author properties:

[Example 4](https://datashapes.org/reification.html#example-4)

ex:ProvenanceShape
	a sh:NodeShape ;
	sh:property \[
		a sh:PropertyShape ;
		sh:path ex:date ;
		sh:datatype xsd:date ;
		sh:maxCount 1 ;
		sh:order "0"^^xsd:decimal ;
	\] ;
	sh:property \[
		a sh:PropertyShape ;
		sh:path ex:author ;
		sh:nodeKind sh:IRI ;
		sh:maxCount 1 ;
		sh:order "1"^^xsd:decimal ;
	\] .

ex:PersonShape
	a sh:NodeShape ;
	sh:targetClass ex:Person ;
	sh:property ex:PersonShape-age .

ex:PersonShape-age
	a sh:PropertyShape ;
	sh:path ex:age ;
	sh:datatype xsd:integer ;
	sh:maxCount 1 ;
	**dash:reifiableBy** ex:ProvenanceShape .

Regardless of which specific reification implementation is chosen, the information above can be exploited by tools to drive and validate user input. For example, in TopBraid 6.3, the edit forms will display a "nested" form section that can be opened below each value that is of a reifiable property:

![Image 1](https://datashapes.org/images/Reification-Form-Edit-Bob.png)Similar reification shapes can be defined to attach metadata about SKOS labels, covering some of the use cases of SKOS-XL:

![Image 2](https://datashapes.org/images/Reification-Form-View-NL.png)Tools can use `dash:reifiableBy` triples to check for the presence of reified triples and then highlight them in the user interface. Then, as the user enters details, the shape definition can be used to drive the input forms.

The SHACL validation component for `dash:reifiableBy` is called `dash:ReifiableByConstraintComponent`. Depending on the implemented reification approach, it may produce constraint violations on the focus node, path and value node of the base triple, and then use [`sh:detail`](https://www.w3.org/TR/shacl/#results-detail) to list the problems that were found on the reification shape.

The property `dash:reificationRequired` can be used in conjunction with dash:reifiableBy to indicate that there must be at least one reification value for the focus node/path combination in the data graph.

In the following variation of the above example, there will be a constraint violation if the age of a person is _not_ reified by any triple.

[Example 5](https://datashapes.org/reification.html#example-5)

ex:PersonShape-age
	a sh:PropertyShape ;
	sh:path ex:age ;
	sh:datatype xsd:integer ;
	sh:maxCount 1 ;
	dash:reifiableBy ex:ProvenanceShape ;
	**dash:reificationRequired true .**

For example, this instance would be invalid:

[Example 6](https://datashapes.org/reification.html#example-6)

ex:InvalidPerson
    a ex:Person ;
    ex:age 42 .

This appendix lists some SPARQL functions that can be used within TopBraid to translate between reification URIs and triples. These functions may change and hopefully become obsolete in future versions, once TopBraid fully supports the upcoming SPARQL 1.2 functions. Meanwhile this section is provided as reference to TopBraid users.

The SPARQL function `tosh:reificationURI` constructs a URI that is used to represent a reified triple. The input is a subject, a predicate and an object node, and the output is a URI node that can then be used for example to add reified values or to query existing reifications.

The following query produces reification URIs for each triple that has `owl:Thing` as its subject and then fetches those reification URIs that have a value for `ex:creator`:

[Example 7](https://datashapes.org/reification.html#example-7)

SELECT \*
WHERE {
	BIND (owl:Thing AS ?s) .
	?s ?p ?o .
	BIND (tosh:reificationURI(?s, ?p, ?o) AS ?uri) .
	?uri ex:creator ?creator .
}

The SPARQL property function (magic property) `tosh:reificationURIOf` can be used to convert a reification URI (e.g., produced by `tosh:reificationURI`) back into subject, predicate and object components. It requires a reification URI on the left hand side and three unbound variables for subject, predicate and object on the right hand side.

In the following example query, we first iterate over all reification URIs that have a value for `ex:creator` and then disassemble them into subject, predicate and object components to learn the original triples that have been reified.

[Example 8](https://datashapes.org/reification.html#example-8)

SELECT \*
WHERE {
	?uri ex:creator ?creator .
	?uri tosh:reificationURIOf ( ?s ?p ?o ) .
}

The SPARQL functions `tosh:reificationSubject`, `tosh:reificationPredicate` and `tosh:reificationObject` can be used to convert a reification URI (e.g., produced by `tosh:reificationURI`) back into subject, predicate and object components.

In the following example query, we first iterate over all reification URIs that have a value for `ex:creator` and then disassemble them into subject, predicate and object components to learn the original triples that have been reified.

[Example 9](https://datashapes.org/reification.html#example-9)

SELECT \*
WHERE {
	?uri ex:creator ?creator .
	BIND (tosh:reificationSubject(?uri) AS ?s) .
	BIND (tosh:reificationPredicate(?uri) AS ?p) .
	BIND (tosh:reificationObject(?uri) AS ?o) .
}

The SPARQL function `tosh:reifiedValue` provides direct access to a value of a reified triple, e.g. the timestamp. It is primarily a convenience function to look up values if you already know subject, predicate and object.

The following example fetches the creator of the triple `owl:Thing rdf:type rdfs:Class`, if any exists.

[Example 10](https://datashapes.org/reification.html#example-10)

SELECT ?creator
WHERE {
	BIND (tosh:reifiedValue(owl:Thing, rdf:type, rdfs:Class, ex:creator) AS ?creator) . 
}
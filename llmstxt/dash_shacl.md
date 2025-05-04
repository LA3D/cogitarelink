Title: DASH Data Shapes Vocabulary

URL Source: https://datashapes.org/dash

Markdown Content:
[Jump to Table of Contents](https://datashapes.org/dash#toc) [Pop Out Sidebar](https://datashapes.org/dash#toc)

Abstract
--------

This document introduces the DASH Data Shapes Vocabulary, a collection of reusable extensions to SHACL for a wide range of use cases. In addition to a library of new SHACL constraint and target types, DASH also includes components for representing test cases, suggestions to fix constraint violations and an extended validation results vocabulary. Finally, DASH serves as a reference implementation of SHACL in SPARQL by providing default validators. DASH is intended to evolve as a standards-compliant open source vocabulary.

Status of This Document
-----------------------

This document is a draft of a potential specification. It has no official standing of any kind and does not represent the support or consensus of any standards organization.

This document uses the prefix `dash` which represents the [DASH Data Shapes](http://datashapes.org/) namespace `http://datashapes.org/dash#` which is accessible via its URL `http://datashapes.org/dash`. The vocabulary is available in the following formats:  
[Turtle](https://datashapes.org/dash.ttl), [JSON-LD](https://datashapes.org/dash.jsonld) and [RDF/XML](https://datashapes.org/dash.rdf).

Table of Contents
-----------------

1.  [Abstract](https://datashapes.org/dash#abstract)
2.  [Status of This Document](https://datashapes.org/dash#sotd)
3.  [1. Motivation and Design Goals](https://datashapes.org/dash#overview)
4.  [2. Constraint Components](https://datashapes.org/dash#constraints)
5.  [3. Shapes](https://datashapes.org/dash#shapes)
    1.  [3.1 dash:ListShape](https://datashapes.org/dash#ListShape)
6.  [4. Targets](https://datashapes.org/dash#targets)
    1.  [4.1 dash:AllObjectsTarget](https://datashapes.org/dash#AllObjectsTarget)
    2.  [4.2 dash:AllSubjectsTarget](https://datashapes.org/dash#AllSubjectsTarget)
    3.  [4.3 dash:HasValueTarget](https://datashapes.org/dash#HasValueTarget)
7.  [5. Validation Results](https://datashapes.org/dash#results)
    1.  [5.1 dash:SuccessResult](https://datashapes.org/dash#SuccessResult)
    2.  [5.2 dash:FailureResult](https://datashapes.org/dash#FailureResult)
8.  [6. Linking Data with Shapes](https://datashapes.org/dash#linking-data-with-shapes)
    1.  [6.1 dash:applicableToClass](https://datashapes.org/dash#applicableToClass)
    2.  [6.2 dash:shape](https://datashapes.org/dash#shape)
9.  [7. Abstract Classes](https://datashapes.org/dash#abstract-classes)
10.  [8. Union Datatypes](https://datashapes.org/dash#union-datatypes)
    1.  [8.1 dash:DateOrDateTime](https://datashapes.org/dash#DateOrDateTime)
    2.  [8.2 dash:StringOrLangString](https://datashapes.org/dash#StringOrLangString)
11.  [9. The Empty Shape dash:None](https://datashapes.org/dash#None)
12.  [10. Composites](https://datashapes.org/dash#composites)
13.  [11. SPARQL Validators](https://datashapes.org/dash#validators)
14.  [12. Suggestions Vocabulary](https://datashapes.org/dash#suggestions)
15.  [13. Test Cases](https://datashapes.org/dash#testcases)
16.  [14. Form Generation using SHACL and DASH](https://datashapes.org/dash#forms)
17.  [15. Reification Support for SHACL](https://datashapes.org/dash#reification)
18.  [A. References](https://datashapes.org/dash#references)
    1.  [A.1 Normative references](https://datashapes.org/dash#normative-references)
    2.  [A.2 Informative references](https://datashapes.org/dash#informative-references)

SHACL \[[shacl](https://datashapes.org/dash#bib-shacl "Shapes Constraint Language (SHACL)")\] is a W3C standard for the representation of structural data constraints. Being based on RDF and designed with its own extension mechanisms, the main SHACL vocabulary has been intended to be the starting point of an evolving linked data ecosystem. The DASH namespace presented in this document extends SHACL in a standards-compliant way, following the design patterns established by SHACL.

Some aspects of the DASH namespace are purely declarative extensions of the SHACL data model, e.g. [new types of validation results](https://datashapes.org/dash#results), subclassing `sh:AbstractResult`. But many components in DASH also provide executable instructions based on SPARQL \[[sparql11-query](https://datashapes.org/dash#bib-sparql11-query "SPARQL 1.1 Query Language")\]. Standards-compliant SHACL engines with full support for the SPARQL-based extension mechanisms will understand those extensions automatically, without requiring changes to the underlying engine implementation. Examples of this category include the new [constraint components](https://datashapes.org/dash#constraints) and [target types](https://datashapes.org/dash#targets). Finally, since the SHACL namespace itself does not include any executable SPARQL queries, DASH serves as a reference implementation of SHACL in SPARQL by providing default [validators](https://datashapes.org/dash#validators).

While the initial versions of DASH are maintained by TopQuadrant personnel, and TopBraid tools will provide optimized support for some of the DASH components, the explicit goal of DASH is to establish itself as a de-facto standard that is completely vendor neutral. We want to help the SHACL community grow. Contributions and suggestions for new features are more than welcome - please contact the author directly or join the discussion on the [mailing list](https://groups.google.com/forum/#!forum/topbraid-users). As new use cases are established, DASH will be continuously but carefully extended, without bloating the library. Some of the components in DASH are actually features that "almost" made it into the official SHACL standard, but were not included due to lack of time or technical disagreements within the W3C working group.

In order to use DASH in your SHACL file, add the following triple. The DASH namespace already imports the SHACL namespace, so no additional import is needed.

<http://example.org/myShapesGraph\> owl:imports <http://datashapes.org/dash\> .

DASH includes a library of new constraint types, implemented as SHACL constraint components. See the separate document on **[DASH Constraint Components](https://datashapes.org/constraints.html)**.

The DASH namespace includes some shape declarations that may be of general use. These shapes have no targets, but they can be references by other graphs through `sh:node` and similar means.

This shape can be used to verify that a given node is a well-formed RDF list. The node must either be `rdf:nil` and have neither `rdf:first` nor `rdf:rest`, or be different from `rdf:nil` and have exactly one `rdf:first` and exactly one `rdf:rest`. All nodes in the list must also fulfill the same conditions and there must not be cycles.

The advanced features of SHACL-SPARQL include an extension mechanism to define new types of target. These user-defined targets can be used in conjunction with the `sh:target` property.

A variation of this feature (and its companion [AllSubjectsTarget](https://datashapes.org/dash#AllSubjectsTarget)) had been part of earlier SHACL drafts but was taken out to simplify the core language by reducing the need to rely on the `sh:target` keyword.

The target type `dash:AllObjectsTarget` represents the set of all objects in the data graph. It can be used in cases where a shape is expected to apply to all objects, regardless of their subject or predicate. For example, it can be used to verify that a graph contains no literals with a language tag.

Since `dash:AllObjectsTarget` does not take any parameters, it is in principle sufficient to just have a single instance of that class that can be reused everywhere. For that purpose, the DASH namespace includes the instance `dash:AllObjects`.

The following example uses `dash:AllObjects` to verify that the data graph contains no literals.

ex:NoLiteralsShape
	a sh:NodeShape ;
	sh:target dash:AllObjects ;
	sh:nodeKind sh:BlankNodeOrIRI .

See [dash:AllObjectsTarget](https://datashapes.org/dash#AllObjectsTarget), only for subjects instead of objects.

The target type `dash:HasValueTarget` represents the set of all subjects that have a certain object value for a certain predicate.

The following example uses `dash:HasValueTarget` constrain the length of the postal code of addresses where the country is Australia.

ex:AustralianAddressShape
	a sh:NodeShape ;
	sh:target \[
		a dash:HasValueTarget ;
		dash:predicate ex:country ;
		dash:object ex:Australia ;
	\] ;
	sh:property \[
		a sh:PropertyShape ;
		sh:path ex:postalCode ;
		sh:minLength 4 ;
		sh:maxLength 4 ;
	\] .

DASH introduces various new subclasses of `sh:AbstractResult` that can be used to represent different kinds of validation results.

The SHACL standard itself has no result type to represent successful validation steps. Only violations (or warnings or info items) are produced by default. However, in some cases it would be informative to a user which shapes have been validated at all, e.g. to record the date of previous successful runs. The class `dash:SuccessResult` can be used in such cases.

The following example represents the successful execution of a given shape against a given focus node. If no `sh:focusNode` is provided, then the assumption is that it validated OK for all target nodes. If no `sh:sourceConstraintComponent` is provided, then the assumption is that the shape validated OK for all its components.

[Example 1](https://datashapes.org/dash#example-1)

\[
	a dash:SuccessResult ;
	sh:sourceShape ex:PersonShape ;
	sh:sourceConstraintComponent sh:MinCountConstraintComponent ;
\] .

The class `dash:FailureResult` can be used to represent failures during the execution of a SHACL validation process. Examples of failures include unsupported recursion or invalid shapes graphs. SHACL itself does not include vocabulary to represent those, but rather leaves reporting of failures as an implementation detail to engines. Many engines will simply throw an error ("exception") to signal a failure. However, in some cases it is useful to record such failures as part of the validation results graph.

The following example represents a failure due to an unsupported recursion within a nested `sh:node` constraint.

[Example 2](https://datashapes.org/dash#example-2)

\[
	a dash:FailureResult ;
	sh:focusNode ex:JoeDoe ;
	sh:sourceShape ex:MyRecursiveShape ;
	sh:sourceConstraintComponent sh:NodeConstraintComponent ;
\] .

The properties in this section have been introduced to fill perceived gaps in the practical use of the official SHACL namespace.

The property `dash:applicableToClass` is a softer version of `sh:targetClass`. If a shape is linked to a class via `sh:targetClass` then validation will be triggered, meaning "all instances of the class must conform to the shape". The property `dash:applicableToClass` points from a shape to a class and means "some instances of the class may conform to the shape". This loose association is often helpful to enumerate candidate shapes to categorize a collection of instances. Another example use case is for user interfaces to display a list of possible views that are available for a class.

[Example 3](https://datashapes.org/dash#example-3)

ex:AdultPersonShape
	a sh:NodeShape ;
	dash:applicableToClass ex:Person ;
	sh:property \[
		sh:path ex:age ;
		sh:datatype xsd:integer ;
		sh:minInclusive 18 ;
	\] .

The property `dash:shape` can be used to state that a subject resource has a given shape. This property can, for example, be used to capture results of SHACL validation on static data. The property is similar to `sh:targetNode`, but the differences are that `dash:shape` does not automatically trigger validation, the `dash:shape` triples are located in the data graph (not shapes graph), and the direction is inverted from subject to object.

[Example 4](https://datashapes.org/dash#example-4)

ex:JeanMichel
	a ex:Person ;
	ex:age 20 ;
	dash:shape ex:AdultPersonShape .

Abstract classes are well-established in object oriented systems. A class is called abstract if it cannot have direct instances - only non-abstract subclasses of an abstract class can be instantiated directly. Despite having a variety in application areas in the RDF world, there is no established standard to express that an RDFS class is abstract. This is in part due to the fact that RDF Schema and OWL have a different notion of inheritance as well as type inference that may be regarded as a contradiction to the traditional notion of abstractness. However, at a minimum, a flag to mark classes as abstract would be useful for user input tools to prevent the user from creating instances of certain classes. The SHACL vocabulary itself has examples of abstract classes, such as `sh:AbstractResult`.

DASH introduces a simple property `dash:abstract` that can be attached to any class in a data model (i.e. the property has `rdfs:domain rdfs:Class`). If this property is set to `true` then the associated class is supposed to be abstract. No constraint validation is currently associated with this constraint, although it would be easy to formulate a corresponding constraint component in the future.

[Example 5](https://datashapes.org/dash#example-5)

ex:GeoEntity
	a rdfs:Class ;
	dash:abstract true .

ex:Country
	a rdfs:Class ;
	rdfs:subClassOf ex:GeoEntity .

In many use cases, a datatype property can take one out of several datatypes, for example either `xsd:date` or `xsd:dateTime`. The syntax to represent those cases in pure SHACL can become a bit repetitive, as it would look like:

[Example 6](https://datashapes.org/dash#example-representing-a-union-of-datatypes): Representing a union of datatypes

ex:DateOrDateTimeShape
	a sh:NodeShape ;
	sh:property \[
		sh:path ex:timeStamp ;
		sh:or (
			\[ sh:datatype xsd:date \]
			\[ sh:datatype xsd:dateTime \]
		)
	\] .

In order to help with these design patterns, DASH includes some URIs that can be used in conjunction with `sh:or`.

The URI `dash:DateOrDateTime` is defined to be an `rdf:List` consisting of two `sh:datatype` constraints, for `xsd:date` and `xsd:dateTime`, respectively.

The following example is equivalent to the shape definition from above.

ex:DateOrDateTimeShape
	a sh:NodeShape ;
	sh:property \[
		sh:path ex:timeStamp ;
		sh:or dash:DateOrDateTime ;
	\] .

The URI `dash:StringOrLangString` is similar to [`dash:DateOrDateTime`](https://datashapes.org/dash#DateOrDateTime), only for `xsd:string` or `rdf:langString`. This can be used to represent that a property can either take plain strings or strings with a language tag.

The resource `dash:None` is an instance of `sh:NodeShape` that can never be satisfied by any focus node.

The DASH namespace includes support for the recurring design pattern of resource that for parent-child relationships, so that the life cycle of the children depends on the parents. An example for this is represented below:

ex:DatabaseShape
	a sh:NodeShape ;
	sh:targetClass ex:Database ;
	sh:property \[
		sh:path ex:column ;
		sh:class ex:Column ;
		dash:composite true ;
	\] .

In this example, instances of the class `ex:Database` may have values for a property `ex:column`, which must be instances of `ex:Column`. The property is also marked with `dash:composite true` which indicates that whenever a database gets deleted, then all columns should be deleted, too. This information can be queried by user interface tools and other algorithms to perform cascading deletes, but also for other use cases such as tree visualizations. (TopBraid supports this property as of version 5.2.1 both in Composer and the web products.) Note that `dash:composite` does not include any constraint validation semantics, i.e. it is purely an "annotation" property.

If the relationship points in the inverse direction, e.g. in the well-known cases of `skos:broader` or `rdfs:subClassOf`, then `dash:composite` can be applied to a property constraint that includes an inverse path, using something like `sh:path [ sh:inversePath skos:broader ]`.

The DASH namespace includes executable validators for all SHACL Core Constraint Components. For example, it defines the SPARQL queries and JavaScript code that can be used to validate `sh:minCount`. This means that the DASH namespace can be used as the base of a SPARQL-based or JavaScript-based SHACL implementation. The [Topbraid SHACL API](https://github.com/TopQuadrant/shacl) is based on these validators. Details of these validators can be found in the DASH RDF files.

DASH includes a declarative RDF data model to represent suggestions that can be used by tools to repair SHACL constraint violations. The framework uses SPARQL to describe updates that need to be applied to a graph in order to fix a given constraint violation. See the separate document on the **[DASH Suggestions Vocabulary](https://datashapes.org/suggestions.html)**.

DASH includes a collection of classes and properties to represent test cases that verify that a given executable process still produces the same results as originally intended. See the separate document on **[DASH Test Cases](https://datashapes.org/testcases.html)**.

SHACL shape definitions can be used to drive user interfaces, esp display and edit forms. We are showing examples of recommended form layouts that mirror the definitions of properties in data shapes, and introduce extensions to the SHACL vocabulary from the DASH namespace that further assist in such form definitions. See the separate document on **[Form Generation using SHACL and DASH](https://datashapes.org/forms.html)**.

Reification is a mechanism to make RDF statements about other RDF statements. This document introduces a SHACL constraint component based on the property `dash:reifiableBy` that can be used to instruct processors about the shape that reified statements should conform to. `dash:reifiableBy` links a SHACL property shape with a SHACL node shape that may be used to drive user input or to validate reified statements. See the separate document on **[Reification Support for SHACL](https://datashapes.org/reification.html)**.

\[sparql11-query\]

[SPARQL 1.1 Query Language](https://www.w3.org/TR/sparql11-query/). Steven Harris; Andy Seaborne. W3C. 21 March 2013. W3C Recommendation. URL: [https://www.w3.org/TR/sparql11-query/](https://www.w3.org/TR/sparql11-query/)

\[shacl\]

[Shapes Constraint Language (SHACL)](https://www.w3.org/TR/shacl/). Holger Knublauch; Dimitris Kontokostas. W3C. 20 July 2017. W3C Recommendation. URL: [https://www.w3.org/TR/shacl/](https://www.w3.org/TR/shacl
from rdflib.URIRef import URIRef
from rdflib.Literal import Literal
from rdflib.BNode import BNode
from rdflib.Namespace import Namespace
from rdflib.constants import TYPE, VALUE

# Import RDFLib's default TripleStore implementation
from rdflib.TripleStore import TripleStore

# Create a namespace object
POSTCON = Namespace("http://burningbird.net/postcon/elements/1.0/")

store = TripleStore(  )

store.prefix_mapping("pstcn", "http://http://burningbird.net/postcon/elements/1.0/")
 
# Create top-level resource
monsters = URIRef(POSTCON["monsters1.htm"])

# Add type statement
store.add((monsters, TYPE, POSTCON["Document"]))

# Create bnode and add as statement
presentation = BNode(  );
store.add((monsters, POSTCON["presentation"],presentation))

# Create second bnode, add
requires = BNode(  );
store.add((presentation, POSTCON["requires"], requires))

# add two end nodes
type = Literal("stylesheet")
store.add((requires, POSTCON["type"],type))

value = Literal("http://burningbird.net/de.css")
store.add((requires, VALUE, value))

# Iterate over triples in store and print them out
for s, p, o in store:
    print s, p, o

# Serialize the store as RDF/XML to the file subgraph.rdf
store.save("subgraph.rdf")
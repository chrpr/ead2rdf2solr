import xml.etree.cElementTree as ET
import rdflib
import os
import glob
import sys
import codecs
import re

def gettext(elem):
	text = elem.text or ""
	#print text
	for subelem in elem:
		text = text.strip() + " " + gettext(subelem)
		if subelem.tail:
			text = text + subelem.tail.strip() + " "
	return text.strip() + " "

def generate_rdf(root, path=None):
	'''
	...actually, I think I want a "parse EAD" that creates an EAD Object within python.
	The question is, is the object the parent of many sub-objects, or does it instead have internal data structures that 
	 correspond to it's subobjects?
	 I think it's the latter, right?
	 So maybe it's really the constructor method for the object?
	 (Note to self, ask Shawn questions about OO Pythong... :)
	 Then it'll have a "serialize" method that generates All the RDF to file
	 (And another "From RDF" constructor?)
	 as well as a to_4store method that builds all requisite sparql queries.
	 Yeah, that's totally what I want. Here's some rough notes on how that should look in Python land:
	 http://en.wikibooks.org/wiki/Python_Programming/Object-oriented_programming

	 So... First off, I'm going to copy this current file (ead2rdf.py) over to [need a name...]... 
	 Probably going to try to spread these files out, so will call this ead.py
	 Can't really have 2 __init__s, so we'll use either *args or probably *kwargs
	 This will let us know whether we're instantiating an EAD object_set from a pile-o-turtle, JSON or from EAD files themselves...

	 Or, alternately, I can have "class methods" or "factory methods":
	 http://stackoverflow.com/questions/682504/what-is-a-clean-pythonic-way-to-have-multiple-constructors-in-python

	 Okay, so that's what I'll do. My __init__ will be to generate the EAD monkey from an EAD file.
	 Then I'll have separate factory methods that create these same objects from an RDF serialization or from a sparql query.
	 This way I'll be able to reuse these same classes in the to-SOLR code base.

	 I'll then want to have similar classes for:
		* MARC records?
		* EAD-Components? (which will get called by the EAD class constructor...)
		* "Authority" objects (including sub-types) - Corporate, Family, Person, Event, Topic
			- This is where the code-base will start to get bloody interesting.
			- Will need to manage input from files vs. using fuzzy-wuzzy & lookup code itself, right?

	I need to start working on a serious code-map for how this will all come together, as right now it's a scattered collection of random scripts. 

	*** I think that during generation, I'll want to make a list of my "objects" (store in a YAML file, probly) 
	and their URIs so that I know what I need to generate SORL entries for ***

	'''

	if path is None:
		path = [root.tag]

	#I think I want to dig through these at parent level....
	eadid = None
	for parent in root:
		#print root.tag.replace('{urn:isbn:1-931666-22-9}','')
		#print parent.tag.replace('{urn:isbn:1-931666-22-9}','')
		if parent.tag.replace('{urn:isbn:1-931666-22-9}','') == 'eadheader':
			'''
			I Think the only thing I care about here is the eadid...
			Interstingly, Gadget seems to think there are 5 of these bad boys missing: 
			eadid	1681	1675		8	
			Yet current chunk of code doesn't print any files that are missing them
			(except for a viaf file that don't belong where it is)
			Ah, scratch that: reworked code & found my 5 screwups:
			AIA.065-ead.xml| 
			FILM .013-ead.xml| 
			PHOTOS.023.001-ead.xml| 
			TAM.166-ead.xml| 
			TAM.608-ead.xml| 
			'''
			for child in parent:
				if child.tag.replace('{urn:isbn:1-931666-22-9}','') == 'eadid':
					eadid = gettext(child)
	return eadid
				#for grandchild in child:
				#	print parent.tag.replace('{urn:isbn:1-931666-22-9}','') + "|" + child.tag.replace('{urn:isbn:1-931666-22-9}','') + "|" + grandchild.tag.replace('{urn:isbn:1-931666-22-9}','')

#iterate through files
path = ''
for f in glob.glob( os.path.join(path, '*.xml') ):
    #print f
    innerli = []
    #print "current file is: " + infile
    tree = ET.ElementTree(file=f)
    #print '{0} -> {1}'.format(file, tree.getroot())
    if generate_rdf(tree.getroot()) == " ": 
    	print '{0}|{1}'.format(f, generate_rdf(tree.getroot()))
   
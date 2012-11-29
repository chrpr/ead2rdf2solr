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
	#actually, I think I want a "parse EAD" that creates an EAD Object within python.
	#The question is, is the object the parent of many sub-objects, or does it instead have internal data structures that 
	# correspond to it's subobjects?
	# I think it's the latter, right?
	# So maybe it's really the constructor method for the object?
	# (Note to self, ask Shawn questions about OO Pythong... :)
	# Then it'll have a "serialize" method that generates All the RDF to file
	# (And another "From RDF" constructor?)
	# as well as a to_4store method that builds all requisite sparql queries.

	if path is None:
		path = [root.tag]

	#I think I want to dig through these at parent level....
	eadid = None
	for parent in root:
		#print root.tag.replace('{urn:isbn:1-931666-22-9}','')
		#print parent.tag.replace('{urn:isbn:1-931666-22-9}','')
		if parent.tag.replace('{urn:isbn:1-931666-22-9}','') == 'eadheader':
			#I Think the only thing I care about here is the eadid...
			#Interstingly, Gadget seems to think there are 5 of these bad boys missing: 
			#eadid	1681	1675		8	
			#Yet current chunk of code doesn't print any files that are missing them
			#(except for a viaf file that don't belong where it is)
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
   
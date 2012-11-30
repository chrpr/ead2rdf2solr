import xml.etree.cElementTree as ET
import rdflib

# This moves to "utils"
def gettext(elem):
	text = elem.text or ""
	#print text
	for subelem in elem:
		text = text.strip() + " " + gettext(subelem)
		if subelem.tail:
			text = text + subelem.tail.strip() + " "
	return text.strip() + " "

class Ead(object):

	"""
	Defines EAD record objects.
	Also manages related Component objects
	Contains 3 constuctors: 
		- __init__, which generates from EAD files
		- factory method to generate from RDF
		- factory method to generate from SPARQL queries
	Contains output methods for:
		- Import to 4store via SPARQL
		- Writing RDF to file
		- Writing SOLR Index entries
	"""

	def __init__(self, ead, fn):
		"""Generates an EAD object from ElementTree-parsed EAD file; fn to set ID if no eadid element"""
		''' TODO: Get these via xpaths, or by looping. Maybe a combination of each?'''
		print fn
		namespace = "{urn:isbn:1-931666-22-9}"
		self.metadata = {}

		#print ead.getroot()
		#print ead.getroot().find('{urn:isbn:1-931666-22-9}eadheader/{urn:isbn:1-931666-22-9}eadid')
		#for child in ead.getroot():
		#	print child.tag
		#self.identifier = gettext(ead.find(n + 'eadheader/' + n + 'eadid'))
		restrict = ead.find('{0}archdesc/{0}accessrestrict'.format(namespace))
		if restrict:
			count = 0
			self.metadata['Restrictions'] = gettext(ead.find('{0}archdesc/{0}accessrestrict'.format(namespace)))
			for child in restrict:
				if child.tag.replace(namespace, '') == "p":
					count += 1
					#print child.tag.replace(namespace, '') + ": " + gettext(child).rstrip().encode('utf-8') + " " + str(count) + " " + fn if count > 2 else None
					if count > 2: print child.tag.replace(namespace, '') + ": " + gettext(child).rstrip().encode('utf-8') + " " + str(count) + " " + fn

				#else:
					#print child.tag.replace(namespace, '') + ": " + gettext(child).encode('utf-8')
		_id = ead.find('{0}eadheader/{0}eadid'.format(namespace))
		print gettext(_id)
		self.metadata['Identifier'] = gettext(_id) if gettext(_id) != " " else fn.replace("-ead.xml", "").replace(".", "_").lower()

		self.metadata['Title'] = gettext(ead.find('{0}archdesc/{0}did/{0}unittitle'.format(namespace)))


'''
# All of the below is old code. Probably kill this & start over, but will leave it here as reference for now...
def generate_rdf(root, path=None):
	

	if path is None:
		path = [root.tag]

	#I think I want to dig through these at parent level....
	eadid = None
	for parent in root:
		#print root.tag.replace('{urn:isbn:1-931666-22-9}','')
		#print parent.tag.replace('{urn:isbn:1-931666-22-9}','')
		if parent.tag.replace('{urn:isbn:1-931666-22-9}','') == 'eadheader':

			for child in parent:
				if child.tag.replace('{urn:isbn:1-931666-22-9}','') == 'eadid':
					eadid = gettext(child)
	return eadid
				#for grandchild in child:
				#	print parent.tag.replace('{urn:isbn:1-931666-22-9}','') + "|" + child.tag.replace('{urn:isbn:1-931666-22-9}','') + "|" + grandchild.tag.replace('{urn:isbn:1-931666-22-9}','')

#This is actually what goes into cmdline/ead2rdf.py
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
'''   
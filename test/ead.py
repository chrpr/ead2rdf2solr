#import xml.etree.cElementTree as ET
from lxml import etree
import rdflib
import re

# This moves to "utils"
def gettext(elem, ignore=[], newline=[]):
	text = elem.text or ""
	text = text.rstrip()
	#print elem.tag + "|" + str(newline)
	#print text
	#TODO: This is still a little whacky. Got's to work out how to handle this better....
	for subelem in elem:
		if subelem.tag not in ignore: text = text + " " + gettext(subelem, ignore, newline)
		if subelem.tag in newline: 
			#print text
			text = "\n" + text.lstrip() + "\n"
		if subelem.tail:
			text = text + subelem.tail.strip()
	return text

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
		- Stretch goal: Writing XML for Primo imput?
	"""

	def __init__(self, ead, fn):
		"""Generates an EAD object from ElementTree-parsed EAD file; fn to set ID if no eadid element"""
		''' TODO: Get these via xpaths, or by looping. Maybe a combination of each?'''
		print fn
		namespace = "{urn:isbn:1-931666-22-9}"
		'''
		Refactoring this to use lxml...
		Play with:
		>>> r = doc.xpath('/t:foo/b:bar',
...               namespaces={'t': 'http://codespeak.net/ns/test1',
...                           'b': 'http://codespeak.net/ns/test2'})
		'''
		self.metadata = {}

		#print ead.getroot()
		#print ead.getroot().find('{urn:isbn:1-931666-22-9}eadheader/{urn:isbn:1-931666-22-9}eadid')
		#for child in ead.getroot():
		#	print child.tag
		#self.identifier = gettext(ead.find(n + 'eadheader/' + n + 'eadid'))

		#First, get identifier
		#_id = ead.find('{0}eadheader/{0}eadid'.format(namespace))
		# okay, so after installing lxml and switching over, it actually makes very little difference.
		# Will leave lxml as my tool of choice, but keep using the findall & find methods for compatability with ElementTree...
		_id = ead.xpath('n:eadheader/n:eadid', namespaces={'n': 'urn:isbn:1-931666-22-9'})
		#print len(_id)
		#print gettext(_id)
		self.metadata['Identifier'] = gettext(_id[0]) if gettext(_id[0]) != " " else fn.replace("-ead.xml", "").replace(".", "_").lower()
		#print self.metadata['Identifier']

		#Now, start iteration...
		#So, I feel like there's gotta be a better way to do this. Dict of named functions? Lamdas??
		archdesc = ead.find('{0}archdesc'.format(namespace))
		self.metadata['Type'] = archdesc.get("level")

		for element in archdesc:
			tag = element.tag.replace(namespace, '')
			if tag == "accessrestrict":
				self.metadata['Restrictions'] = []
				for i in element.findall('{0}p'.format(namespace)):
					self.metadata['Restrictions'].append(gettext(i))
			if tag == "arrangement":
				#self.metadata['Arrangement'] = [gettext(element, ignore=[namespace+"head"], newline=[namespace+"item", namespace+"p"])]
				self.metadata['Arrangement'] = [gettext(element, ignore=[namespace+"head"], newline=[namespace+"item"])]

				'''
				Have modded the "gettext" method so it will optionally take a list of elements to strip. 
				Not sure if that approach is preferable here, or if collecting <p> & <list><item> tags 
				in separate instances of "Arrangement" is better approach. Latter is *closer* to keeping formating....
				I could also mod gettext so that <p> tags manifest as having a linebreak after them....
				Hah, this is kinda disgusting, but it actually now takes newline & ignore lists...
				Seems to be better than the approach below:
				self.metadata['Arrangement'] = []
				for i in element.findall('{0}list/{0}item'.format(namespace)):
					self.metadata['Arrangement'].append(gettext(i))
				for i in element.findall('{0}p'.format(namespace)):
					self.metadata['Arrangement'].append(gettext(i))
				'''
			if tag == "bibliography":
				self.metadata['Bibliographic Reference'] = []
				for i in element.findall('{0}bibref'.format(namespace)):
					self.metadata['Bibliographic Reference'].append(gettext(i, ignore=[namespace+"head"]))
			if tag == "bioghist":
				self.metadata['Biographical/Historical Note'] = [gettext(element)]
			if tag == "controlaccess":
				controldict = { 
			   			'corpname': { 'ingest': 'Local Corporate Name', 'local': 'Local Corporate Name',
			   							'nad': 'Local Corporate Name', 'naf': 'LC Corporate Name' },
						'genreform': { 'aat': 'Art & Arch Thesaurus Genre', 'lcsh': 'LC Genre',
										'local': 'Local Genre Term' },
						'geogname': { 'lcsh': 'LC Geographic Name', 'local': 'Local Geographic Name' },
						'persname': { 'ingest': 'Local Personal Name', 'local': 'Local Personal Name', 
										'nad': 'Local Personal Name', 'naf': 'LC Personal Name' },
						'subject': { 'aat': 'Art & Arch Thesaurus Subject', 'lcsh': 'LC Subject', 
										'local': 'Local Subject' },
						'famname': { 'local': 'Family Name', 'ingest': 'Family Name' },
						'occupation': { 'lcsh': 'Occupation' },
						'title': { 'lcsh': 'Title' }
				}
				for ca in element:
					t = ca.tag.replace(namespace, '')
					s = ca.get('source')
					text = re.sub(r' \|[A-Za-z] ', ' -- ', gettext(ca))
					if s == 'lcsh':
						self.metadata["FAST Heading"] = text.split(' -- ')
					self.metadata[controldict[t][s]] = text
			if tag == 'dao':
				href = element.get('{http://www.w3.org/1999/xlink}href')
				self.metadata["Related Web Archive"] = gettext(element) + ": " + href
			if tag == "relatedmaterial":
				if element.xpath('//n:extref', namespaces={'n': 'urn:isbn:1-931666-22-9'}): 
					extref = element.xpath('//n:extref', namespaces={'n': 'urn:isbn:1-931666-22-9'})[0]
					href = extref.get('{http://www.w3.org/1999/xlink}href') if '{http://www.w3.org/1999/xlink}href' in extref else ""
				else:
					href = ""
				self.metadata["Related Mateirals"] = gettext(element, ignore=[namespace+"head"], newline=[namespace+"item", namespace+"extref"]) + " " + href
				#root.xpath("//article[@type='news']")
			if tag == 'scopecontent':
				self.metadata["Scope Note"] = gettext(element, ignore=[namespace+"head"])
			if tag == 'separatedmaterial':
				self.metadata["Separated Materials Note"] = gettext(element, ignore=[namespace+"head"])
			if tag == 'userestrict':
				if 'Restrictions' not in self.metadata: self.metadata['Restrictions'] = []
				self.metadata['Restrictions'].append(gettext(element, ignore=[namespace+"head"]))

 


		''' Working block from here to end of ' ' '
		Replacing with a "for element in" that's going to go chunk by chunk
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

tags = {'accessrestrict' : getTextFromMany(parent, "p"),
		'1' : sqr,
		#4 : sqr,
		#9 : sqr,
		#2 : even,
		#3 : prime,
		#5 : prime,
		#7 : prime,
}

def getTextFromMany(element, child):
    print "You typed zero.\n"

def sqr():
    print "n is a perfect square\n"

def even():
    print "n is an even number\n"

def prime():
    print "n is a prime number\n"

    '''   

#import xml.etree.cElementTree as ET
from lxml import etree
import rdflib
import re
from component import Component
from rdflib import Graph, URIRef, Namespace, Literal


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

fieldrenamings = {
	'abstract': 'dct:abstract',
	'langmaterial': 'arch:langnote',
	'origination': { 'corpname': 'arch:corpcreator', 'persname': 'arch:perscreator' },
	'physdesc': 'dc:description',
	'physloc': 'arch:location',
	'unitdate': 'dc:date',
	'normal': 'arch:datenormal',
	'materialspec': 'arch:materialspec',
	'accessrestrict': 'arch:restrict',
	'arrangement': 'arch:arrange',
	'bibliography': 'arch:bibref',
	'bioghist': 'arch:bioghist',
	'controlaccess': { 
			'corpname': { 'ingest': 'arch:localcorp', 'local': 'arch:localcorp',
						'nad': 'arch:localcorp', 'naf': 'arch:lccorpname' },
			'genreform': { 'aat': 'arch:aat', 'lcsh': 'arch:lcgenre',
							'local': 'arch:localgenre' },
			'geogname': { 'lcsh': 'arch:lcgeo', 'local': 'arch:localgeo' },
			'persname': { 'ingest': 'arch:localpers', 'local': 'arch:localpers', 
							'nad': 'arch:localpers', 'naf': 'arch:lcpers' },
			'subject': { 'aat': 'arch:aatsub', 'lcsh': 'arch:lcsh', 
							'local': 'arch:localsub' },
			'famname': { 'local': 'arch:family', 'ingest': 'arch:family' },
			'occupation': { 'lcsh': 'arch:occupation' },
			'title': { 'lcsh': 'arch:lctitle' }
		},
	'lcsh': 'arch:fast',
	'dao': 'arch:webarch',
	'relatedmaterial': 'arch:related',
	'scopecontent': 'arch:scope',
	'separatedmaterial': 'arch:sepmaterial',
	'userestrict': 'arch:restrict'
}

def procdid(xfrag):
	namespace = "{urn:isbn:1-931666-22-9}"
	md = {}
	#print "FragTag" + gettext(xfrag).encode('utf-8')
	for subelem in xfrag:
		#print "Subelem" + str(subelem)
		tag = subelem.tag.replace(namespace, '')
		#print "Tag" + tag
		if tag == "abstract": md[fieldrenamings[tag]] = gettext(subelem)
		if tag == "langmaterial":
			md[fieldrenamings[tag]] = gettext(subelem)
		if tag == "origination":
			for child in subelem:
				chitag = child.tag.replace(namespace, '')
				if chitag == "corpname": md[fieldrenamings[tag][chitag]] = gettext(child)
				if chitag == "persname": md[fieldrenamings[tag][chitag]] = gettext(child)
		if tag == "physdesc": md[fieldrenamings[tag]] = gettext(subelem)
		if tag == "physloc": md[fieldrenamings[tag]] = gettext(subelem)
		if tag == "unitdate":
			md[fieldrenamings[tag]] = gettext(subelem)
			#print subelem.attrib
			#if '{http://www.w3.org/1999/xlink}normal' in subelem.attrib:
			if'normal' in subelem.attrib:
				md[fieldrenamings['normal']] = subelem.get('normal')
		if tag == "materialspec": md[fieldrenamings[tag]] = gettext(subelem)

	
	return md

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
		#print fn
		namespace = "{urn:isbn:1-931666-22-9}"
		'''
		Refactoring this to use lxml...
		Play with:
		>>> r = doc.xpath('/t:foo/b:bar',
...               namespaces={'t': 'http://codespeak.net/ns/test1',
...                           'b': 'http://codespeak.net/ns/test2'})
		'''
		self.metadata = {}
		self.headinglist = []
		self.headrootlist = []
		# currently self.components is only *immediate* children, not ancestors. Components will have components will have components, though....
		self.components = []
		#self.metadata["File Name"] = fn
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
		self.metadata['dc:identifier'] = gettext(_id[0]) if gettext(_id[0]) != "" else fn.replace("-ead.xml", "").replace(".", "_").lower()
		#print self.metadata['Identifier']

		#Now, start iteration...
		#So, I feel like there's gotta be a better way to do this. Dict of named functions? Lamdas??
		archdesc = ead.find('{0}archdesc'.format(namespace))
		self.metadata['dc:type'] = archdesc.get("level")
		self.metadata['dct:title'] = gettext(ead.find('{0}archdesc/{0}did/{0}unittitle'.format(namespace)))
		self.metadata['arch:findingaid'] = "http://dlib.nyu.edu/findingaids/html/tamwag/" + self.metadata['dc:identifier']

		for element in archdesc:
			tag = element.tag.replace(namespace, '')
			#if tag == "did"

			if tag == "accessrestrict":
				self.metadata[fieldrenamings[tag]] = []
				for i in element.findall('{0}p'.format(namespace)):
					self.metadata[fieldrenamings[tag]].append(gettext(i))
			if tag == "arrangement":
				#self.metadata['Arrangement'] = [gettext(element, ignore=[namespace+"head"], newline=[namespace+"item", namespace+"p"])]
				self.metadata[fieldrenamings[tag]] = [gettext(element, ignore=[namespace+"head"], newline=[namespace+"item"])]

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
				self.metadata[fieldrenamings[tag]] = []
				for i in element.findall('{0}bibref'.format(namespace)):
					self.metadata[fieldrenamings[tag]].append(gettext(i, ignore=[namespace+"head"]))
			if tag == "bioghist":
				self.metadata[fieldrenamings[tag]] = [gettext(element)]
			if tag == "controlaccess":
				for ca in element:
					t = ca.tag.replace(namespace, '')
					s = ca.get('source')
					text = re.sub(r' \|[A-Za-z] ', ' -- ', gettext(ca))
					if s == 'lcsh':
						self.metadata[fieldrenamings[s]] = text.split(' -- ')
					self.headinglist.append(text)
					headroot = text.split(' -- ')[0].rstrip(".")
					if headroot not in self.headrootlist: self.headrootlist.append(headroot)
					#need to redo this so it utilizes "field renamings"
					self.metadata[fieldrenamings[tag][t][s]] = text
			if tag == 'dao':
				href = element.get('{http://www.w3.org/1999/xlink}href')
				self.metadata[fieldrenamings[tag]] = gettext(element) + ": " + href
			if tag == 'did':
				didmd = procdid(element)
				#print "Monkey" + str(didmd)
				self.metadata.update(didmd)
			if tag == "relatedmaterial":
				if element.xpath('//n:extref', namespaces={'n': 'urn:isbn:1-931666-22-9'}): 
					extref = element.xpath('//n:extref', namespaces={'n': 'urn:isbn:1-931666-22-9'})[0]
					href = extref.get('{http://www.w3.org/1999/xlink}href') if '{http://www.w3.org/1999/xlink}href' in extref else ""
				else:
					href = ""
				self.metadata[fieldrenamings[tag]] = gettext(element, ignore=[namespace+"head"], newline=[namespace+"item", namespace+"extref"]) + " " + href
				#root.xpath("//article[@type='news']")
			if tag == 'scopecontent':
				self.metadata[fieldrenamings[tag]] = gettext(element, ignore=[namespace+"head"])
			if tag == 'separatedmaterial':
				self.metadata[fieldrenamings[tag]] = gettext(element, ignore=[namespace+"head"])
			if tag == 'userestrict':
				if fieldrenamings[tag] not in self.metadata: self.metadata[fieldrenamings[tag]] = []
				self.metadata[fieldrenamings[tag]].append(gettext(element, ignore=[namespace+"head"]))

			if tag == 'dsc':
				for c in element:
					component = Component(c, self)
					# TODO Add this to field renamings!
					self.metadata['arch:hasComponent'] = [component.metadata['dct:title'], component.metadata['dc:identifier']]
					self.components.append(component)

	def makeGraph(self):
		"""Generates an internal RDF Graph of the EAD Object"""
		''' TODO: Should this be private?
		Also, currently using Graph rather than ConjunectiveGraph because I want to persist my graph IDs:
		https://rdflib.readthedocs.org/en/latest/graphs_bnodes.html
		But it's possible that I want to do establish the identifiers at time of 4store persist or serialization?
		Otherwise I'm naming this thing each time I graph an EAD instance, which is *not* my goal, no?
		'''
		self.graph = rdflib.Graph(identifier="http://chrpr.com/data/ead.rdf")
		uri = URIRef("http://chrpr.com/data/" + str(self.metadata["dc:identifier"]) + ".rdf")
		namespaces = {
			"dc": Namespace("http://purl.org/dc/elements/1.1/"),
			"dct": Namespace("http://purl.org/dc/terms/"),
			"arch": Namespace("http://chrpr.com/arch/")
		}
		curies = { "dc": "DC", "dct": "DCTERMS", "arch": "ARCH" }
		self.graph.bind("dc", "http://purl.org/dc/elements/1.1/")
		self.graph.bind("dct", "http://purl.org/dc/terms/")
		self.graph.bind("arch", "http://chrpr.com/arch/")
		for k, v, in self.metadata.iteritems():
			#ns = curies[k.split(":")[0]]
			#p = ns[k.split(":")[1]]
			#p = curies[k.split(":")[0]][k.split(":")[1]]
			p = namespaces[k.split(":")[0]][k.split(":")[1]]
			#print p
			self.graph.add([uri, p, Literal(v, lang='en') ])
			#print len(self.graph)
		#print self.graph.serialize(format="turtle")
		''' So, something like this:
		g = Graph(identifier="http://chrpr.com/data/ead.rdf")
		>>> for k, v in ead.metadata.iteritems():
...     p = URIRef("http://chrpr.com/arch" + k)
...     g.add([uri, p, Literal(v, lang='en')])

		... g.namespace_manager.reset()
		  File "<stdin>", line 5
		    g.namespace_manager.reset()
		    ^
		SyntaxError: invalid syntax
		>>> g.namespace_manager
		<rdflib.namespace.NamespaceManager object at 0x273b950>
		>>> g.namespace_manager.reset()
		>>> g.namespace_manager.bind("arch", "http://chrpr.com/arch#")
		>>> g.namespace_manager.bind("dct", "http://chrpr.com/dct#")
		>>> g.namespace_manager.bind("dc", "http://chrpr.com/dc#")
		>>> of2 = open('archturtle2.ttl', 'w')
		>>> g.serialize(format="turtle", destination=of2)

		'''
	def output(self, format="turtle"):
		if not hasattr(self, "graph"):
			self.makeGraph()

		of = "rdf/" + self.metadata["dc:identifier"] + ".ttl"
		self.graph.serialize(format=format, destination = of)

		#self.graph.serialize(format=format, destination = "rdf/cheese.ttl")
		print of
		#self.graph.serialize(format=format, distination = "rdf/monkey.ttl")
		#print "No graph exists"
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

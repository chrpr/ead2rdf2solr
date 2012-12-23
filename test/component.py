#import xml.etree.cElementTree as ET
from lxml import etree
import rdflib
import re
import sunburnt
from utils import *
from configs import *
from rdflib import Graph, URIRef, Namespace, Literal
from HTTP4Store import HTTP4Store


class Component(object):

	"""
	Defines record for EAD component part objects.
	Contains 3 constuctors: 
		- __init__, which generates from an XML fragment, an Ead object, and an optional parent Component Object
		- factory method to generate from RDF
		- factory method to generate from SPARQL queries
	Contains output methods for:
		- Import to 4store via SPARQL
		- Writing RDF to file
		- Writing SOLR Index entries
		- Stretch goal: Writing XML for Primo imput?
	"""

	def __init__(self,  xfrag, eadob, *args):
		"""Generates a component object from an xml fragment, an EAD object & option parent component"""
		#print fn
		namespace = "{urn:isbn:1-931666-22-9}"
		'''
		Refactoring this to use lxml...
		Play with:
		>>> r = doc.xpath('/t:foo/b:bar',
...               namespaces={'t': 'http://codespeak.net/ns/test1',
...                           'b': 'http://codespeak.net/ns/test2'})
		'''
		self.metadata = {
			'arch:aat': [],	'arch:aatsub': [], 'arch:arrange': [], 'arch:bibref': [], 'arch:bioghist': [],
			'arch:family': [], 'arch:fast': [], 'arch:lccorpname': [], 'arch:lcgenre': [], 'arch:lcgeo': [], 
			'arch:lcpers': [],	'arch:lcsh': [],'arch:lctitle': [],	'arch:localcorp': [], 'arch:localgenre': [], 
			'arch:localgeo': [], 'arch:localpers': [], 'arch:localsub': [], 'arch:occupation': [],
			'arch:related': [],	'arch:restrict': [], 'arch:scope': [],'arch:sepmaterial': [], 'arch:webarch': [],
			'arch:hasComponent': []
		}
		self.headinglist = []
		self.headrootlist = []
		self.components = []
		#print ead.getroot()
		#print ead.getroot().find('{urn:isbn:1-931666-22-9}eadheader/{urn:isbn:1-931666-22-9}eadid')
		#for child in ead.getroot():
		#	print child.tag
		#self.identifier = gettext(ead.find(n + 'eadheader/' + n + 'eadid'))

		#First, get identifier
		#_id = ead.find('{0}eadheader/{0}eadid'.format(namespace))
		# okay, so after installing lxml and switching over, it actually makes very little difference.
		# Will leave lxml as my tool of choice, but keep using the findall & find methods for compatability with ElementTree...
		self.metadata['dc:identifier'] = [eadob.metadata['dc:identifier'][0] + '-' + xfrag.get('id')]
		self.metadata['dc:type'] = [xfrag.get("level")]
		self.metadata['dct:title'] = [gettext(xfrag.find('{0}did/{0}unittitle'.format(namespace)))]
		self.metadata['arch:findingaid'] = [eadob.metadata['arch:findingaid'][0]]
		self.metadata['arch:inCollection'] = [eadob.metadata['dc:identifier'][0], eadob.metadata['dct:title'][0]]
		#self.metadata['arch:inCollection'] = [eadob.metadata['dc:identifier'][0], eadob.metadata['dct:title'][0]]
		#don't want titles in these , right? Wait... These should all be ids, but then I'll... Ugh. Pain in ass! Monkey-fucker!
		#Actually, it's okay, because above example "inCollection" is actually 2 elements, not an element with 2 values...
		#Works for unique elements like these (inColleciton, hasParent), but *not* for repeatables like arch:hasComponent

		if args:
			self.metadata['arch:hasParent'] = [args[0].metadata['dc:identifier'][0], args[0].metadata['dct:title'][0]]


		for element in xfrag:
			tag = element.tag.replace(namespace, '')

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
				self.metadata[fieldrenamings[tag]].append(gettext(element))
			if tag == "controlaccess":
				for ca in element:
					t = ca.tag.replace(namespace, '')
					s = ca.get('source')
					text = re.sub(r' \|[A-Za-z] ', ' -- ', gettext(ca))
					if s == 'lcsh':
						self.metadata[fieldrenamings[s]].extend(text.split(' -- '))
					self.headinglist.append(text)
					headroot = text.split(' -- ')[0].rstrip(".")
					if headroot not in self.headrootlist: self.headrootlist.append(headroot)
					#need to redo this so it utilizes "field renamings"
					self.metadata[fieldrenamings[tag][t][s]].append(text)
			if tag == 'dao':
				href = element.get('{http://www.w3.org/1999/xlink}href')
				self.metadata[fieldrenamings[tag]].append(gettext(element) + ": " + href)
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
				self.metadata[fieldrenamings[tag]].append(gettext(element, ignore=[namespace+"head"], newline=[namespace+"item", namespace+"extref"]) + " " + href)
				#root.xpath("//article[@type='news']")
			if tag == 'scopecontent':
				self.metadata[fieldrenamings[tag]].append(gettext(element, ignore=[namespace+"head"]))
			if tag == 'separatedmaterial':
				self.metadata[fieldrenamings[tag]].append(gettext(element, ignore=[namespace+"head"]))
			if tag == 'userestrict':
				self.metadata[fieldrenamings[tag]].append(gettext(element, ignore=[namespace+"head"]))
			if tag == 'c' and 'level' in element.attrib:
					component = Component(element, eadob, self)
					# TODO Add this to field renamings!
					self.metadata['arch:hasComponent'].append(component.metadata['dc:identifier'][0])
					self.components.append(component)

	def makeSolr(self):
		"""Sends SOLR Updates based on current schema"""
		s = sunburnt.SolrInterface('http://localhost:8983/solr')
		record = {}
		#recstring = ''
		for sf in solrfields.itervalues():
			if sf != 'TODO':
				record[sf] = []
		for k, v in self.metadata.iteritems():
			#if k == "arch:perscreator": 
			if solrfields[k] != 'TODO':
				#print type(solrfields[k])
				for val in v: 
					if len(val) > 0: record[solrfields[k]].append(val)
					#else: record[solrfields[k]] = val
		authors = self.metadata['arch:corpcreator'] + self.metadata['arch:perscreator']
		if len(authors) > 0: record['author_display'] = "; ".join(authors)
		record['title_display'] = self.metadata['dct:title']
		record['type_facet'] = "Finding Aid Component / Part"

		#if this finds dupes, try the next version:
		#if len(self.metadata['dct:title']) > 0: record['title_display'] = self.metadata['dct:title'].join("; ")
		for k, v in record.items():
			if len(v) == 0:
				del record[k]


		#print record
		#for k, v in record.iteritems():
		#	print "{0}: {1}".format(k, v)
		s.add(record)
		s.commit()
		#s.commit()
		#print record
		for c in self.components:
			c.makeSolr()
		'''
		import solr

		# create a connection to a solr server
		s = solr.SolrConnection('http://example.org:8083/solr')

		# add a document to the index
		doc = dict(
		    id=1,
		    title='Lucene in Action',
		    author=['Erik Hatcher', 'Otis Gospodnetic'],
		    )
		s.add(doc, commit=True)

		# do a search
		response = s.query('title:lucene')
		for hit in response.results:
		    print hit['title']
    	'''

	def makeGraph(self):
		"""Generates an internal RDF Graph of the Component Object"""
		''' TODO: Should this be private?
		Also, currently using Graph rather than ConjunectiveGraph because I want to persist my graph IDs:
		https://rdflib.readthedocs.org/en/latest/graphs_bnodes.html
		But it's possible that I want to do establish the identifiers at time of 4store persist or serialization?
		Otherwise I'm naming this thing each time I graph an EAD instance, which is *not* my goal, no?
		'''
		self.graph = rdflib.Graph(identifier="http://chrpr.com/data/ead.rdf")
		uri = URIRef("http://chrpr.com/data/" + str(self.metadata["dc:identifier"][0]) + ".rdf")
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
			p = namespaces[k.split(":")[0]][k.split(":")[1]]
			#ns = curies[k.split(":")[0]]
			#p = ns[k.split(":")[1]]
			#p = curies[k.split(":")[0]][k.split(":")[1]]
			if len(v) > 0:
				for data in v:
					self.graph.add([uri, p, Literal(data, lang='en') ])
			#print len(self.graph)
		#print self.graph.serialize(format="turtle")

	def output(self, format="turtle"):
		if not hasattr(self, "graph"):
			self.makeGraph()

		of = "rdf/" + str(self.metadata["dc:identifier"][0]) + ".ttl"
		#of2 = "rdf/" + self.metadata['arch:inCollection'][0] + "-long.ttl"

		self.graph.serialize(format=format, destination = of)

		for c in self.components:
			c.output()

	def fourstore(self):
		if not hasattr(self, "graph"):
			self.makeGraph()
		turtle = self.graph.serialize(format="turtle")
		store = HTTP4Store('http://localhost:8080')
		#print turtle
		r =  store.append_graph("http://chrpr.net/data/ead", turtle, "turtle")
		for c in self.components:
			c.fourstore()


#import xml.etree.cElementTree as ET
from lxml import etree
import rdflib
import re
import sunburnt
from component import Component
from entity import Entity
from utils import *
from configs import *
from rdflib import Graph, URIRef, Namespace, Literal
from HTTP4Store import HTTP4Store

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
		namespace = "{urn:isbn:1-931666-22-9}"

		self.metadata = {
			'arch:aat': [],	'arch:aatsub': [], 'arch:arrange': [], 'arch:bibref': [], 'arch:bioghist': [],
			'arch:family': [], 'arch:fast': [], 'arch:lccorpname': [], 'arch:lcgenre': [], 'arch:lcgeo': [], 
			'arch:lcpers': [],	'arch:lcsh': [],'arch:lctitle': [],	'arch:localcorp': [], 'arch:localgenre': [], 
			'arch:localgeo': [], 'arch:localpers': [], 'arch:localsub': [], 'arch:occupation': [],
			'arch:related': [],	'arch:restrict': [], 'arch:scope': [],'arch:sepmaterial': [], 'arch:webarch': [],
			'arch:hasComponent': []
		}
		#This is the set of entities related to the object.
		#Should be fine if they're dupes, as the top level processing will tweak them.
		self.entities = []
		self.headinglist = []
		self.headrootlist = []
		if components == True: self.components = []

		_id = ead.xpath('n:eadheader/n:eadid', namespaces={'n': 'urn:isbn:1-931666-22-9'})
		self.metadata['dc:identifier'] = [gettext(_id[0]) if gettext(_id[0]) != "" else fn.replace("-ead.xml", "").replace(".", "_").lower()]
		archdesc = ead.find('{0}archdesc'.format(namespace))
		self.metadata['dc:type'] = [archdesc.get("level")]
		self.metadata['dct:title'] = [gettext(ead.find('{0}archdesc/{0}did/{0}unittitle'.format(namespace)))]
		self.metadata['arch:findingaid'] = ["http://dlib.nyu.edu/findingaids/html/tamwag/" + self.metadata['dc:identifier'][0]]

		for element in archdesc:
			tag = element.tag.replace(namespace, '')
			if tag == "accessrestrict":
				self.metadata[fieldrenamings[tag]] = []
				for i in element.findall('{0}p'.format(namespace)):
					self.metadata[fieldrenamings[tag]].append(gettext(i))
			if tag == "arrangement":
				self.metadata[fieldrenamings[tag]] = [gettext(element, ignore=[namespace+"head"], newline=[namespace+"item"])]
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
					#20130202 -- adding entity processing
					#also need to revisit the headinglist processing below...
					entity = Entity(t, gettext(ca), s)
					if hasattr(entity, 'metadata'):
						entity.collections.append(self.metadata["dc:identifier"][0])
						self.entities.append(entity)
					text = re.sub(r' \|[A-Za-z] ', ' -- ', gettext(ca))
					##TODO: 20130202: Do I really want to limit this to lcsh?
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
				didmd, origentities = procdid(element)
				for e in origentities:
						if hasattr(e, 'metadata'):
							e.collections.append(self.metadata["dc:identifier"][0])
							self.entities.append(e)
				self.metadata.update(didmd)
			if tag == "relatedmaterial":
				if element.xpath('//n:extref', namespaces={'n': 'urn:isbn:1-931666-22-9'}): 
					extref = element.xpath('//n:extref', namespaces={'n': 'urn:isbn:1-931666-22-9'})[0]
					href = extref.get('{http://www.w3.org/1999/xlink}href') if '{http://www.w3.org/1999/xlink}href' in extref else ""
				else:
					href = ""
				self.metadata[fieldrenamings[tag]].append(gettext(element, ignore=[namespace+"head"], newline=[namespace+"item", namespace+"extref"]) + " " + href)
			if tag == 'scopecontent':
				self.metadata[fieldrenamings[tag]].append(gettext(element, ignore=[namespace+"head"]))
			if tag == 'separatedmaterial':
				self.metadata[fieldrenamings[tag]].append(gettext(element, ignore=[namespace+"head"]))
			if tag == 'userestrict':
				self.metadata[fieldrenamings[tag]].append(gettext(element, ignore=[namespace+"head"]))
			
			if tag == 'dsc' and components == True:
				for c in element:
					component = Component(c, self)
					# TODO Add this to field renamings!
					self.metadata['arch:hasComponent'].append(component.metadata['dc:identifier'][0])
					self.components.append(component)
			

	def __solrRecord__(self):
		record = {}
		# solrfields imported from configs.py
		for sf in solrfields.itervalues():
			if sf != 'TODO':
				#Initiate all arrays:
				record[sf] = []

		for k, v in self.metadata.iteritems():
			#if k == "arch:perscreator": 
			if solrfields[k] != 'TODO':
				for val in v: 
					if len(val) > 0: 
						if k == "arch:hasComponent": record[solrfields[k]].append("http://localhost:3000/catalog/" + val)
						else: record[solrfields[k]].append(val)
		record['entities_display'] = []
		for entity in self.entities:
			#print entity.metadata["id"]
			record['entities_display'].append(u'http://localhost:3000/catalog/' + entity.metadata['id'])
		authors = self.metadata['arch:corpcreator'] + self.metadata['arch:perscreator']
		if len(authors) > 0: record['author_display'] = "; ".join(authors)
		record['title_display'] = self.metadata['dct:title']
		record['type_facet'] = 'Archival Finding Aid'

		#if this finds dupes, try the next version:
		#if len(self.metadata['dct:title']) > 0: record['title_display'] = self.metadata['dct:title'].join("; ")
		for k, v in record.items():
			if len(v) == 0:
				del record[k]
		return record

	def makeSolr(self):
		"""Sends SOLR Updates based on current schema"""
		s = sunburnt.SolrInterface('http://localhost:8983/solr')
		record = self.__solrRecord__
		s.add(record)
		s.commit()
		if components == True:
			for c in self.components:
				print c.metadata["dc:identifier"]
				c.makeSolr()


	def makeGraph(self):
		"""Generates an internal RDF Graph of the EAD Object"""
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

		of = "rdf/" + self.metadata["dc:identifier"][0] + ".ttl"
		of2 = "rdf/" + self.metadata["dc:identifier"][0] + "-long.ttl"
		self.graph.serialize(format=format, destination = of)
		#self.graph.serialize(format=format)
		if components == True:
			for c in self.components:
				c.output()
		#full = open(of2, 'w')
		#full.write(fullturt)
		#full.close()
	

	def fourstore(self):
		if not hasattr(self, "graph"):
			self.makeGraph()
		turtle = self.graph.serialize(format="turtle")
		store = HTTP4Store('http://localhost:8080')
		#print turtle
		r =  store.append_graph("http://chrpr.net/data/ead", turtle, "turtle")
		if components == True:
			for c in self.components:
				c.fourstore()


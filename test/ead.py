#import xml.etree.cElementTree as ET
from lxml import etree
import rdflib
import re
import sunburnt
from component import Component
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
		self.metadata['dc:identifier'] = [gettext(_id[0]) if gettext(_id[0]) != "" else fn.replace("-ead.xml", "").replace(".", "_").lower()]
		#print self.metadata['Identifier']

		#Now, start iteration...
		#So, I feel like there's gotta be a better way to do this. Dict of named functions? Lamdas??
		archdesc = ead.find('{0}archdesc'.format(namespace))
		self.metadata['dc:type'] = [archdesc.get("level")]
		self.metadata['dct:title'] = [gettext(ead.find('{0}archdesc/{0}did/{0}unittitle'.format(namespace)))]
		self.metadata['arch:findingaid'] = ["http://dlib.nyu.edu/findingaids/html/tamwag/" + self.metadata['dc:identifier'][0]]

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

			if tag == 'dsc':
				for c in element:
					component = Component(c, self)
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
				#Initiate all arrays:
				record[sf] = []
				'''
				This block also no longer needed (20121220):
				if type(sf) == list:
					for f in sf: record[f]  = []
				if type(sf) == str: record[sf] = []
				'''
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
		record['type_facet'] = "Archival Finding Aid"
		#if this finds dupes, try the next version:
		#if len(self.metadata['dct:title']) > 0: record['title_display'] = self.metadata['dct:title'].join("; ")
		for k, v in record.items():
			if len(v) == 0:
				del record[k]
			'''
			update 20121220: redoing this chunk of code....
			The only "list based" mappings in the whole thing were:
				'dct:title': ['title_display', 'title_t'],
				'arch:corpcreator': ['author_display', 'author_t'],
				'arch:perscreator': ['author_display', 'author_t'],
			So, instead of the having lists, let's just treat author_display & title_display as special cases....	
			
			Okay, Got's a lot of problems here:
			Notably, author_display is *not* multi-val in blacklight's solr. 
			So, I either need to *make* it multi-val & prob break the app logic...
			or I need to combine them or only take one....
		
			#This, I can get rid of...
			if k == 'arch:perscreator' or k == 'arch:corpcreator': 
				#print "pre: " + str(v)
				v = ["; ".join(v)]
				#print "post: "+ str(v)
			#This is temporary, holding while I finish mappings.
			if solrfields[k] != 'TODO':
				#print type(solrfields[k])
				for val in v: 
					if type(solrfields[k]) == list:
						for f in solrfields[k]:
							#print f
							#print record[f]
							#Why the fuck do I have this if len(record[f]) == 0? 
							# Isn't that basically saying only write the value if it hasn't already been written?
							# Ah, right, it's because my only list versions are display fields. 
							#Let's actually wipe that whole thing...
							if len(record[f]) == 0: record[f].append(val)
							#else: record[f] = val
					else: 
						if len(val) >= 1: record[solrfields[k]].append(val)
						#else: record[solrfields[k]] = val
		#print record
		'''
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
		for c in self.components:
			c.fourstore()


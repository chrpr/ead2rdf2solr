import re
import codecs
import sunburnt
import rdflib
from configs import *
from utils import *
from types import *
from rdflib import Graph, URIRef, Namespace, Literal
from HTTP4Store import HTTP4Store

#monkey = codecs.open('monkey.txt', 'a', encoding='utf-8')

#lookups = codecs.open('lookups.txt', 'a', encoding='utf-8')

if analyze == True:
	heads = codecs.open('headstrings2.txt', 'a', encoding='utf-8')
	heads2 = codecs.open('headscleaned2.txt', 'a', encoding='utf-8')
	pers = codecs.open('persnames2.txt', 'a', encoding='utf-8')
	corp = codecs.open('corpnames2.txt', 'a', encoding='utf-8')
	geo = codecs.open('geognames2.txt', 'a', encoding='utf-8')
	top = codecs.open('topics2.txt', 'a', encoding='utf-8')
	facets = codecs.open('facets2.txt', 'a', encoding='utf-8')

class Entity(object):
	"""
	Defines Entity record objects.
	***TODO: Update docstrings!!! ***
	Contains 3 constuctors: 
		- __init__, which generates from EAD files
			Thought init took: 	self, type, text, obj_dict="None", *args
			But prob don't need dict or args, instead adding:
			 * source (which I'm going to move to "vocab")
			 * Source tag (TODO: which I'll maybe 
			 	associate with "reverse property" creatorOf, subjectOf)

		- factory method to generate from RDF (Maybe)
		- factory method to generate from SPARQL queries (Maybe)
	Contains an "enrichment" method?
		- How's this actually going to work? Viaf, Fast & id.loc are easy
			because they work off the heading objects themselves.
			DBPedia's way harder, though, because of current fuzzmatch.py structure...
	Contains output methods for:
		- Import to 4store via SPARQL
		- Writing RDF to file
		- Writing SOLR Index entries
		- Stretch goal: Writing XML for Primo imput?
	"""

	def __init__(self, type, text, vocab):
		"""
		Generates a candidate entity object from an access point
		Pre-processes text & checks to see if entity exists
		"""
		if analyze == True: heads.write(type + "|" + text + "\n")
		catext = text.split("--")[0]

		if analyze == True: heads2.write(catext + "\n")
		headlist = catext.split("|")
		## 20130202: Code pulled from ead.py:
		## TODO: Refine this:
		self.headings = [re.sub(r' \|[A-Za-z] ', ' -- ', text)]
		self.collections = []

		## Wait, maybe I don't even need this?
		if type != "genreform" and type != "famname" and type != "occupation" and type != "title":
			root = headlist[0]
			subs = headlist[1:]
			subfields = []
			for sf in subs:
				subfields.append([sf[0:1], sf[2:]])
			
			self.metadata = {}

			if type == "persname":
				# TamWag persnames have no subfields (except |v, which is already stripped)
				# This set of patterns grabs regular & ca. dates, but not b. & d. 
				self.metadata['type'] = "person"
				self.label = catext
				if re.search('(b\. [0-9])', catext):
					self.metadata['bdate'] = re.search('([0-9]{4})', catext).group(0).rstrip()
					self.label = re.sub('b\. [0-9]{4}', '', self.label)
				elif re.search('(d\. [0-9])', catext):
					self.metadata['ddate'] = re.search('([0-9]{4})', catext).group(0).lstrip()
					self.label = re.sub('d\. [0-9]{4}', '', self.label)
				elif re.search('([0-9]{4}-)', catext):
					self.metadata['bdate'] = re.search('([0-9]{4}-)', catext).group(0).rstrip('-')
					if re.search('(-[0-9]{4})', catext): self.metadata['ddate'] = re.search('(-[0-9]{4})', catext).group(0).lstrip('-')
					self.label = re.sub('[0-9]{4}-[0-9]{4}', '', self.label)
					self.label = re.sub('[0-9]{4}-', '', self.label)
			 
				if re.search('(\(.*\))', self.label):
					self.metadata['fullname'] = re.sub('(,.*\()', ', ', self.label).rstrip('), .')
					self.label = re.sub('(\(.*\))', '', self.label)
				#Strip periods that aren't following middle initials:
				self.label = re.sub('(?<! [A-Z])\.', '', self.label)
				#Strip trailing right whitespace and commas:
				self.metadata['heading'] = catext
				self.metadata['label'] = self.label.rstrip(', ')
				self.metadata['id'] = self.label.rstrip(', ').replace(' ', '_').replace(".,'", '')
				self.metadata['lookup'] = [self.metadata['label']]
				if 'fullname' in self.metadata: self.metadata["lookup"].append(self.metadata["fullname"])

			if type == "corpname":
				self.metadata['type'] = "corporation"
				self.label = root.rstrip()
				self.metadata["lookup"] = [self.label]
				for pair in subfields:
					k = pair[0]
					v = pair [1]
					if k == "d" or k == "y": 
						self.label += " " + v.replace('(', '').rstrip(" :).")
						if 'tempfacet' not in self.metadata: self.metadata['tempfacet'] = [v.replace('(', '').rstrip(" :).")]
						else: self.metadata['tempfacet'].append(v.replace('(', '').rstrip(" :)."))
						if self.label not in self.metadata["lookup"]: self.metadata["lookup"].append(self.label)
					if k == "c": 
						self.label += ", " + v.replace('(', '').rstrip(" :).")
						if 'geofacet' not in self.metadata: self.metadata['geofacet'] = [v.replace('(', '').rstrip(" :).")]
						else: self.metadata['geofacet'].append(v.replace('(', '').rstrip(" :)."))
						if self.label not in self.metadata["lookup"]: self.metadata["lookup"].append(self.label)
					if k == "x":
						if 'topicfacet' not in self.metadata: self.metadata['topicfacet'] = [v.replace('(', '').rstrip(" :).")]
						else: self.metadata['topicfacet'].append(v.replace('(', '').rstrip(" :)."))
						if self.label not in self.metadata["lookup"]: self.metadata["lookup"].append(self.label)
				self.metadata['label'] = self.label.rstrip(', ')
				self.metadata['id'] = self.label.rstrip(', ').replace(' ', '_').replace('.', '')
				'''
				Alright, this next block's a little weird:
				First off, I need to generalize it so there's a list in configs.py that is maybe relevant to your data patterns.
				Hard coding NY and New York, NY in here doesn't make sense...

				Also, right now, where I've got a parenthetical AND New York, NY, I don't get a version in lookup that strips both...
				'''
				if re.search('(\(.*\))', self.label):
					noparens = re.sub('(\(.*\) )', '', self.label)
					self.metadata['lookup'].append(noparens)
					if "New York, N.Y." in noparens:
						self.metadata['lookup'].append(re.sub('New York, N.Y.', '', noparens).rstrip(", "))
					if "N.Y." in noparens:
						self.metadata['lookup'].append(re.sub('N.Y.', '', noparens).rstrip(", "))
				if "New York, N.Y." in self.label:
					self.metadata['lookup'].append(re.sub('New York, N.Y.', '', self.label).rstrip(", "))
				if "N.Y." in self.label:
					self.metadata['lookup'].append(re.sub('N.Y.', '', self.label).rstrip(", "))

			if type == "subject":
				self.metadata['type'] = "topic"
				self.label = root.rstrip()
				self.metadata["lookup"] = [self.label]
				for pair in subfields:
					k = pair[0]
					v = pair [1]
					if k == 'y': 
						#why's this commented again?
						#self.label += " " + v.replace('(', '').rstr	ip(' :).'')
						if 'tempfacet' not in self.metadata: self.metadata['tempfacet'] = [v.replace('()', '').rstrip(" :).")]
						else: self.metadata['tempfacet'].append(v.replace('()', '').rstrip(':).'))
						if self.label not in self.metadata['lookup']: self.metadata['lookup'].append(self.label)
						# regex checks if value has anything other than straight dates, numbers.
						if  re.search('([^0-9-.])', v) and 'century' not in v:
							self.label += " " + v.replace('()','').rstrip(' .')
							self.metadata['lookup'].append(self.label)
							self.metadata['lookup'].append(v)						
					if k == 'z':
						if 'geofacet' not in self.metadata: self.metadata['geofacet'] = [v.replace('()', '').rstrip(" :).")]
						else: self.metadata['geofacet'].append(v.replace('()', '').rstrip(" :)."))
					if k == 'x':
						if 'topicfacet' not in self.metadata: self.metadata['topicfacet'] = [v.replace('()', '').rstrip(" :).")]
						else: self.metadata['topicfacet'].append(v.replace('()', '').rstrip(" :)."))
						if re.search('([0-9]{4})', v):
							self.label += " " + v
							self.metadata['lookup'].append(self.label + v)
							self.metadata['lookup'].append(v)
				self.metadata['label'] = self.label.rstrip(', ')
				self.metadata['id'] = self.label.rstrip(', ').replace(' ', '_').replace('.', '')

			if type == "geogname":
				self.metadata['type'] = "place"
				self.label = root.rstrip()
				self.metadata["lookup"] = [self.label]
				for pair in subfields:
					k = pair[0]
					v = pair [1]
					if k == 'y': 
						#self.label += " " + v.replace('(', '').rstr	ip(' :).'')
						if 'tempfacet' not in self.metadata: self.metadata['tempfacet'] = [v.replace('()', '').rstrip(" :).")]
						else: self.metadata['tempfacet'].append(v.replace('()', '').rstrip(':).'))
						if self.label not in self.metadata['lookup']: self.metadata['lookup'].append(self.label)
						# regex checks if value has anything other than straight dates, numbers.
						if  re.search('([^0-9-.])', v) and 'century' not in v:
							self.label += " " + v.replace('()','').rstrip(' .')
							self.metadata['lookup'].append(self.label)
							self.metadata['lookup'].append(v)
					if k == 'z':
						if 'geofacet' not in self.metadata: self.metadata['geofacet'] = [v.replace('()', '').rstrip(" :).")]
						else: self.metadata['geofacet'].append(v.replace('()', '').rstrip(" :)."))
					if k == 'x':
						if 'topicfacet' not in self.metadata: self.metadata['topicfacet'] = [v.replace('()', '').rstrip(" :).")]
						else: self.metadata['topicfacet'].append(v.replace('()', '').rstrip(" :)."))
						if re.search('([0-9]{4})', v):
							self.label += " " + v
							self.metadata['lookup'].append(self.label)
							self.metadata['lookup'].append(v)
				self.metadata['label'] = self.label.rstrip(', ')
				self.metadata['id'] = self.label.rstrip(', ').replace(' ', '_').replace('.', '')
				if "(Spain)" in self.label:
					self.metadata['lookup'].append(re.sub('\(Spain\)', '', self.label).rstrip(", "))
			#printing out all the metadatas to screen.
			#if 'type' in self.metadata and self.metadata['type'] == "place":
			#TODO: THIS GOES AWAY SOON
			
			#print catext.encode('utf-8')
			#for k, v, in self.metadata.iteritems():
				#print k + " is a " + type(v)
				#if type(v) == "str":
				#print "{0}: {1}".format(k, v).encode('utf-8')
				#monkey.write("{0}: {1}".format(k, v).encode('utf-8'))
				#print k
				#print v

			#for lookup in self.metadata['lookup']:
				#lookups.write("{0}|{1}".format(self.metadata['id'].encode('utf-8'), u"WTF"))
				#lookups.write(self.metadata['id'] + "|" + lookup)
			if analyze == True: 
				self.root = root.rstrip()
				facets.write("root|" + root.rstrip() + "\n")
				for facet in subfields:
					if facet[0] != 'v':
						facets.write(facet[0] + "|" + facet[1].rstrip() + "\n")
				if type == "persname":
					pers.write(catext + "\n")
				if type == "corpname":
					corp.write(catext + "\n")
				if type == "geogname":
					geo.write(catext + "\n")
				if type == "subject":
					top.write(catext + "\n")

	def makeSolr(self):
		from utils import *
		"""Sends SOLR Updates based on current schema"""
		s = sunburnt.SolrInterface('http://localhost:8983/solr')
		record = {}
		record['id'] = self.metadata['id']
		record['title_display'] = self.metadata['label']
		record['title_t'] = self.metadata['label']
		record['format'] = self.metadata['type']
		record['title_alt_display'] = []
		record['alttitle_t'] = []
		record['indexer_t'] = []
		record['collections_display'] = []
		record['headings_display'] = []
		record['subject_topic_facet'] = []
		record['subject_geo_facet'] = []
		record['subject_era_facet'] = []

		if 'fullname' in self.metadata: 
			record['title_alt_display'].append(self.metadata['fullname'])
			record['alttitle_t'].append(self.metadata['fullname'])
		if 'heading' in self.metadata: 
			record['title_alt_display'].append(self.metadata['heading'])
			record['alttitle_t'].append(self.metadata['heading'])

		if 'bdate' in self.metadata: record['indexer_t'].append(self.metadata['bdate'])
		if 'ddate' in self.metadata: record['indexer_t'].append(self.metadata['ddate'])
		
		for lookup in self.metadata['lookup']:
			record['indexer_t'].append(lookup)
		
		if 'topic' in self.metadata:
			for topic in self.metadata['topicfacet']:
				record['subject_topic_facet'].append(topic)
		if 'geo' in self.metadata: 
			for geo in self.metadata['geofacet']:
				record['subject_geo_facet'].append(geo)
		if 'temporal' in self.metadata:
			for temporal in self.metadata['tempfacet']:
				record['subject_era_facet'].append(temporal)

		for collection in self.collections:
			record['collections_display'].append("http://localhost:3000/catalog/" + collection)
		for heading in self.headings:
			record['headings_display'].append(heading)

		sameArray = sameAsObj('http://chrpr.com/data/' + self.metadata['id'].encode('utf-8') + '.rdf')
		record['dbpedia_display'] = []
		record['abstract_t'] = []

		for uri in sameArray:
			#print "  -" + uri.encode('utf-8')
			record['dbpedia_display'].append(uri)
			abstracts = dbpField(uri.encode('utf-8'), 'http://dbpedia.org/ontology/abstract')
			for abstract in abstracts:
				#print "      Abstract:" + abstract.encode('utf-8')
				record['abstract_t'].append(abstract)

		#ugh, so there's gotta be a better way...
		#Since I initialized all these fields, I have to kill empties
		for k, v in record.items():
			if len(v) == 0:
				del record[k]

		s.add(record)
		s.commit()

	def makeGraph(self):
		"""Generates an internal RDF Graph of the EAD Object"""
		''' TODO: Should this be private?
		Also, currently using Graph rather than ConjunectiveGraph because I want to persist my graph IDs:
		https://rdflib.readthedocs.org/en/latest/graphs_bnodes.html
		But it's possible that I want to do establish the identifiers at time of 4store persist or serialization?
		Otherwise I'm naming this thing each time I graph an EAD instance, which is *not* my goal, no?
		'''
		self.graph = rdflib.Graph(identifier="http://chrpr.com/data/entity.rdf")
		uri = URIRef("http://chrpr.com/data/" + str(self.metadata['id'].encode('utf-8')) + ".rdf")
		namespaces = {
			"dc": Namespace("http://purl.org/dc/elements/1.1/"),
			"dct": Namespace("http://purl.org/dc/terms/"),
			"arch": Namespace("http://chrpr.com/arch/")
		}
		curies = { "dc": "DC", "dct": "DCTERMS", "arch": "ARCH" }
		self.graph.bind("dc", "http://purl.org/dc/elements/1.1/")
		self.graph.bind("dct", "http://purl.org/dc/terms/")
		self.graph.bind("arch", "http://chrpr.com/arch/")
		'''
		for k, v, in self.metadata.iteritems():
			p = namespaces[k.split(":")[0]][k.split(":")[1]]
			if len(v) > 0:
				for data in v:
					self.graph.add([uri, p, Literal(data, lang='en') ])
		'''
		self.graph.add([uri, namespaces['dc']['identifier'], Literal(self.metadata['id'], lang='en')])
		self.graph.add([uri, namespaces['dct']['title'], Literal(self.metadata['label'], lang='en')])
		self.graph.add([uri, namespaces['dct']['type'], Literal(self.metadata['type'], lang='en')])
		if 'fullname' in self.metadata: self.graph.add([uri, namespaces['dct']['alternative'], Literal(self.metadata['fullname'], lang='en')])
		if 'heading' in self.metadata: self.graph.add([uri, namespaces['arch']['heading'], Literal(self.metadata['heading'], lang='en')])
		if 'bdate' in self.metadata: self.graph.add([uri, namespaces['arch']['bdate'], Literal(self.metadata['bdate'], lang='en')])
		if 'ddate' in self.metadata: self.graph.add([uri, namespaces['arch']['ddate'], Literal(self.metadata['ddate'], lang='en')])
		#if 'fullname' in self.metadata: self.graph.add([uri, namespaces['dct']['alternative'], Literal(self.metadata['id'], lang='en')])
		for lookup in self.metadata['lookup']:
			self.graph.add([uri, namespaces['arch']['lookup'], Literal(self.metadata['lookup'], lang='en')])
		if 'topic' in self.metadata:
			for topic in self.metadata:
				self.graph.add([uri, namespaces['dct']['subject'], Literal(self.metadata['topic'], lang='en')])
		if 'geo' in self.metadata:
			for geo in self.metadata:
				self.graph.add([uri, namespaces['dct']['spatial'], Literal(self.metadata['geo'], lang='en')])
		if 'temporal' in self.metadata:
			for topic in self.metadata:
				self.graph.add([uri, namespaces['dct']['temporal'], Literal(self.metadata['temporal'], lang='en')])
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
		r =  store.append_graph("http://chrpr.net/data/entity", turtle, "turtle")



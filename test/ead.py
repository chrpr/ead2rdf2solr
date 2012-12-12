#import xml.etree.cElementTree as ET
from lxml import etree
import rdflib
import re
import sunburnt
from component import Component
from rdflib import Graph, URIRef, Namespace, Literal
from HTTP4Store import HTTP4Store

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

solrfields = {
	'dc:identifier': 'id',
	'dc:type': 'format',
	'dct:title': ['title_display', 'title_t'],
	'arch:findingaid': 'url_suppl_display',
	'dct:abstract': 'TODO',
	'arch:langnote': 'TODO',
	'arch:corpcreator': ['author_display', 'author_t'],
	'arch:perscreator': ['author_display', 'author_t'],
	'dc:description': 'TODO',
	'arch:location': 'TODO',
	'dc:date': 'TODO',
	'arch:datenormal': 'TODO', #was pub_date, but breaks validation?
	'arch:materialspec': 'TODO',
	'arch:restrict': 'TODO',
	'arch:arrange': 'TODO',
	'arch:bibref': 'TODO',
	'arch:bioghist': 'TODO',
	'arch:localcorp': 'subject_topic_facet', 
	'arch:lccorpname': 'subject_topic_facet',
	'arch:aat': 'subject_topic_facet', 
	'arch:lcgenre': 'subject_topic_facet',
	'arch:localgenre': 'subject_topic_facet',
	'arch:lcgeo': 'subject_geo_facet', 
	'arch:localgeo': 'subject_geo_facet',
	'arch:localpers': 'subject_topic_facet',
	'arch:lcpers': 'subject_topic_facet',
	'arch:aatsub': 'subject_topic_facet',
	'arch:lcsh': 'subject_topic_facet', 
	'arch:localsub': 'subject_topic_facet',
	'arch:family': 'TODO',
	'arch:occupation': 'TODO',
	'arch:lctitle': 'TODO',
	'arch:fast': 'subject_topic_facet',
	'arch:webarch': 'url_suppl_display',
	'arch:related': 'TODO',
	'arch:scope': 'TODO',
	'arch:sepmaterial': 'TODO',
	'arch:restrict': 'TODO',
	'arch:hasComponent': 'TODO',
	'arch:inCollection': 'TODO',
	'arch:hasParent': 'TODO'
}

def procdid(xfrag):
	namespace = "{urn:isbn:1-931666-22-9}"
	md = {
		'dct:abstract': [], 'arch:langnote': [], 'arch:corpcreator': [], 'arch:perscreator': [],
		'dc:description': [], 'arch:location': [], 'dc:date': [], 'arch:datenormal': [],
		'arch:materialspec': [],
	}

	#print "FragTag" + gettext(xfrag).encode('utf-8')
	for subelem in xfrag:
		#print "Subelem" + str(subelem)
		tag = subelem.tag.replace(namespace, '')
		#print "Tag" + tag
		if tag == "abstract": md[fieldrenamings[tag]].append(gettext(subelem))
		if tag == "langmaterial":
			md[fieldrenamings[tag]].append(gettext(subelem))
		if tag == "origination":
			for child in subelem:
				chitag = child.tag.replace(namespace, '')
				if chitag == "corpname": md[fieldrenamings[tag][chitag]].append(gettext(child))
				if chitag == "persname": md[fieldrenamings[tag][chitag]].append(gettext(child))
		if tag == "physdesc": md[fieldrenamings[tag]].append(gettext(subelem))
		if tag == "physloc": md[fieldrenamings[tag]].append(gettext(subelem))
		if tag == "unitdate":
			md[fieldrenamings[tag]].append(gettext(subelem))
			#print subelem.attrib
			#if '{http://www.w3.org/1999/xlink}normal' in subelem.attrib:
			if'normal' in subelem.attrib:
				md[fieldrenamings['normal']].append(subelem.get('normal'))
		if tag == "materialspec": md[fieldrenamings[tag]].append(gettext(subelem))

	
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
					self.metadata['arch:hasComponent'].append(component.metadata['arch:inCollection'][0] + '-' + component.metadata['dc:identifier'][0])
					self.components.append(component)

	def makeSolr(self):
		"""Sends SOLR Updates based on current schema"""
		s = sunburnt.SolrInterface('http://localhost:8983/solr')
		record = {}
		#recstring = ''
		for sf in solrfields.itervalues():
			if sf != 'TODO':
				if type(sf) == list:
					for f in sf: record[f]  = []
				if type(sf) == str: record[sf] = []
		for k, v in self.metadata.iteritems():
			#if k == "arch:perscreator": 
			'''
			Okay, Got's a lot of problems here:
			Notably, author_display is *not* multi-val in blacklight's solr. 
			So, I either need to *make* it multi-val & prob break the app logic...
			or I need to combine them or only take one....
			'''

			if k == 'arch:perscreator' or k == 'arch:corpcreator': 
				#print "pre: " + str(v)
				v = ["; ".join(v)]
				#print "post: "+ str(v)
			if solrfields[k] != 'TODO':
				#print type(solrfields[k])
				for val in v: 
					if type(solrfields[k]) == list:
						for f in solrfields[k]:
							#print f
							#print record[f]
							if len(record[f]) == 0: record[f].append(val)
							#else: record[f] = val
					else: 
						if len(val) >= 1: record[solrfields[k]].append(val)
						#else: record[solrfields[k]] = val
		#print record
		for k, v in record.iteritems():
			print "{0}: {1}".format(k, v)
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


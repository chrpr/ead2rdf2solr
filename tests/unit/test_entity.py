import unittest
from lxml import etree
from entity import Entity
from utils import gettext
from rdflib.compare import graph_diff
from rdflib import Graph

class EntityTestCase(unittest.TestCase):

	def setUp(self):
		namespace = "{urn:isbn:1-931666-22-9}"
		fixture = "tests/fixtures/entity-fragment.xml"
		fragment = etree.parse(fixture)
		c = fragment.xpath('/n:controlaccess/*', namespaces={'n': 'urn:isbn:1-931666-22-9'})[0]
		tag = c.tag.replace(namespace, '')
		text = gettext(c)
		vocab = c.get('source')
		self.entity = Entity(tag, text, vocab, MockOperations())

	def test_solr_field_map(self):
		actual = self.entity.__solrRecord__()
		expected = {'alttitle_t' : ['Clinton, Bill, 1946-'],
		            'format': 'person',
		            'title_alt_display': ['Clinton, Bill, 1946-'],
		            'dbpedia_display': ['http://testing.com/data/Clinton,_Bill.rdf'], 
		            'indexer_t': ['1946', 'Clinton, Bill'], 
		            'headings_display': ['Clinton, Bill, 1946-'], 
		            'title_display': 'Clinton, Bill', 
		            'title_t': 'Clinton, Bill', 
		            'id': 'Clinton,_Bill'}
		for k, v in actual.iteritems():
			self.assertEquals(v, expected[k])
		self.assertEquals(len(actual), len(expected))

	def test_graph(self):
		self.entity.makeGraph()
		actual = self.entity.graph
		expected = Graph(identifier="http://chrpr.com/data/entity.rdf")
		with open("tests/fixtures/entity.n3", 'r') as f:
			expected.parse(format='n3', data=f.read())
		(in_both, in_first, in_second) = graph_diff(expected, actual)
		for triple in in_first:
			print "in_first: " + str(triple)
		for triple in in_second:
			print "in_second: " + str(triple)
		self.assertEqual(actual, expected)
		self.assertEqual(len(in_first), 0)
		self.assertEqual(len(in_second), 0)

class MockOperations(object):
	# A mock of the FourstoreOperations to allow unit testing
	def __init__(self, endpoint = 'http://localhost:8080'):
		pass

	"""
	Encapsulates the resolution of a URI into an array of URIs that are owl:sameAs the input URI
	data URIs are converted to resource URIs in the result
	"""
	def sameAsObj(self, uri):
		return [uri.replace('chrpr', 'testing')]

	"""
	Persists a graph to 4Store
	"""
	def store(self, graph):
		turtle = graph.serialize(format="turtle")
		#print turtle
		pass

	def dbpField(self, sub, prop):
		return []

if __name__ == '__main__':
	unittest.main()

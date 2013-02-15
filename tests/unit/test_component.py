import unittest
from lxml import etree
from component import Component
import configs
from rdflib.compare import graph_diff
from rdflib import Graph

class ComponentTestCase(unittest.TestCase):

	def setUp(self):
		namespace = "{urn:isbn:1-931666-22-9}"
		fixture = "tests/fixtures/component-fragment.xml"
		fragment = etree.parse(fixture)
		self.c = fragment.xpath('/n:dsc/n:c', namespaces={'n': 'urn:isbn:1-931666-22-9'})[0]
		self.component = Component(self.c, MockEad())

	def test_solr_field_map(self):
		actual = self.component.__solrRecord__()
		expected = {'type_facet': 'Finding Aid Component / Part', 
		            'format': ['series'], 
		            'haspart_t': ['http://localhost:3000/catalog/foo-ref18', 
		            'http://localhost:3000/catalog/foo-ref19'], 
		            'ispartof_t': ['http://localhost:3000/catalog/foo'], 
		            'url_suppl_display': ['foo'], 
		            'title_t': ['Series I. Personal'], 
		            'title_display': ['Series I. Personal'], 
		            'date_t': ['1964-2001'], 
		            'id': ['foo-ref13']}
		for k, v in actual.iteritems():
			self.assertEquals(v, expected[k])
		self.assertEquals(len(actual), len(expected))
		subC = self.c.xpath('n:c', namespaces={'n': 'urn:isbn:1-931666-22-9'})[0]
		component = Component(subC, MockEad())
		actual = component.__solrRecord__()
		expected = {'type_facet': 'Finding Aid Component / Part', 
		            'format': ['file'], 
		            'ispartof_t': ['http://localhost:3000/catalog/foo'], 
		            'url_suppl_display': ['foo'], 
		            'title_t': ['Black and Tan Massacre'], 
		            'title_display': ['Black and Tan Massacre'], 
		            'date_t': ['Mar 4, 1985'], 
		            'id': ['foo-ref18']}
		for k, v in actual.iteritems():
			self.assertEquals(v, expected[k])
		self.assertEquals(len(actual), len(expected))

	def test_graph(self):
		self.component.makeGraph()
		actual = self.component.graph
		# MockEad data returns "foo" as the identifier
		# Component puts its triples in the ead graph 
		expected = Graph(identifier="http://chrpr.com/data/ead.rdf")
		with open("tests/fixtures/component.n3", 'r') as f:
			expected.parse(format='n3', data=f.read())
		(in_both, in_first, in_second) = graph_diff(expected, actual)
		for triple in in_first:
			print "in_first: " + str(triple)
		for triple in in_second:
			print "in_second: " + str(triple)
		self.assertEqual(actual, expected)
		self.assertEqual(len(in_first), 0)
		self.assertEqual(len(in_second), 0)


class MockEad(object):
	def __init__(self):
		metadata = {}
		metadata['dc:identifier'] = ["foo"]
		metadata['arch:findingaid'] = ["foo"]
		self.metadata = metadata

if __name__ == '__main__':
	unittest.main()

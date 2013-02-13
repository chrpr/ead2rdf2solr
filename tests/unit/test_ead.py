import unittest
from lxml import etree
from ead import Ead
import configs

class EadTestCase(unittest.TestCase):

	def setUp(self):
		fixture = "tests/fixtures/AIA.009-ead.xml"
		self.ead = Ead(etree.parse(fixture), fixture)

	def test_solr_field_map(self):
		#with self.assertRaises(ValueError):
		#    random.sample(self.seq, 20)
		#for element in random.sample(self.seq, 5):
		#    self.assertTrue(element in self.seq)
		field_map = self.ead.__solrRecord__()
		# 'language_t': ['Majority of materials are in English; some in Spanish, French']
		self.assertEqual(field_map['language_t'], ['Majority of materials are in English; some in Spanish, French'])
		# this field is an assigned constant, not parsed
		self.assertEqual(field_map['type_facet'], 'Archival Finding Aid')
		#print field_map
	def test_components(self):
		if (configs.components == True):
			self.assertTrue(self.ead.components.length() > 0)
		else:
			self.assertFalse('components' in self.ead.__dict__)

if __name__ == '__main__':
	unittest.main()
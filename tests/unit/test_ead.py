import unittest
from lxml import etree
from ead import Ead
import configs
from rdflib.compare import graph_diff
from rdflib import Graph

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
		expected = [
		  u'http://localhost:3000/catalog/Harrison,_George',
		  u'http://localhost:3000/catalog/Clinton,_Bill',
		  u'http://localhost:3000/catalog/Cox,_Thomas_J.',
		  u'http://localhost:3000/catalog/Durkan,_Frank', 
		  u'http://localhost:3000/catalog/International_Brotherhood_of_Teamsters_Local_807_(New_York,_NY)_', 
		  u'http://localhost:3000/catalog/International_Brotherhood_of_Teamsters', 
		  u'http://localhost:3000/catalog/Irish_Northern_Aid_Committee', 
		  u'http://localhost:3000/catalog/Irish_Republican_Army', 
		  u'http://localhost:3000/catalog/McAliskey,_Bernadette_Devlin', 
		  u"http://localhost:3000/catalog/O'Dwyer,_Paul", 
		  u'http://localhost:3000/catalog/Republican_Sinn_Fe\u0301in', 
		  u'http://localhost:3000/catalog/Sinn_Fein', 
		  u'http://localhost:3000/catalog/Veterans_of_the_Abraham_Lincoln_Brigade', 
		  u'http://localhost:3000/catalog/Anti-communist_movements', 
		  u'http://localhost:3000/catalog/Human_rights_activists', 
		  u'http://localhost:3000/catalog/Human_rights', 
		  u'http://localhost:3000/catalog/Hunger_strikes', 
		  u'http://localhost:3000/catalog/Irish_Americans', 
		  u'http://localhost:3000/catalog/Political_campaigns', 
		  u'http://localhost:3000/catalog/Political_campaigns', 
		  u'http://localhost:3000/catalog/Trials_(Political_crimes_and_offenses)']
		self.assertEqual(field_map['entities_display'] , expected)
		expected = ['1925-2003 (bulk 1970-2000)']
		self.assertEqual(field_map['date_t'] , expected)
		expected = ['aia_009']
		self.assertEqual(field_map['id'] , expected)
		expected = [
		 'Clinton, Bill, 1946-', 
		 'Cox, Thomas J., 1906-', 
		 'McAliskey, Bernadette Devlin, 1947-', 
		 "O'Dwyer, Paul, 1907-", 
		 'Anti-communist movements', 
		 'United States.', 'Human rights activists.', 
		 'Human rights.', 
		 'Hunger strikes', 
		 'Northern Ireland.', 
		 'Irish Americans', 
		 'New York (State)', 
		 'New York', 
		 'Political activities.', 
		 'Political campaigns', 
		 'New York (State)', 
		 'New York.', 
		 'Political campaigns.', 
		 'Trials (Political crimes and offenses)', 
		 'United States.', 
		 'Black-and-white photographs.', 
		 'Buttons (information artifacts).', 
		 'Clippings (information artifacts).', 
		 'Color photographs.', 
		 'Correspondence.', 
		 'Fliers (printed matter)', 
		 'Newsletters.', 
		 'Pamphlets.', 
		 'T-shirts.', 
		 'Durkan, Frank, 1930-2006', 
		 'International Brotherhood of Teamsters.', 
		 'Irish Northern Aid Committee.', 
		 'Irish Republican Army.', 
		 u'Republican Sinn Fe\u0301in.', 
		 'Sinn Fein.', 
		 'Veterans of the Abraham Lincoln Brigade.', 
		 'Anti-communist movements -- United States.', 
		 'Human rights activists.', 
		 'Human rights.', 
		 'Hunger strikes -- Northern Ireland.', 
		 'Irish Americans -- New York (State) -- New York -- Political activities.', 
		 'Political campaigns -- New York (State) -- New York.', 
		 'Political campaigns.', 
		 'Trials (Political crimes and offenses) -- United States.', 
		 'International Brotherhood of Teamsters. Local 807 (New York, N.Y.) .']
		self.assertEqual(field_map['subject_topic_facet'] , expected)
		# this field is an assigned constant, not parsed
		self.assertEqual(field_map['type_facet'], 'Archival Finding Aid')
		#print field_map
		
	def test_components(self):
		if (configs.components == True):
			self.assertTrue(len(self.ead.components) > 0)
		else:
			self.assertFalse('components' in self.ead.__dict__)

	def test_graph(self):
		self.ead.makeGraph()
		actual = self.ead.graph
		expected = Graph(identifier="http://chrpr.com/data/ead.rdf")
		with open("tests/fixtures/ead.n3", 'r') as f:
			expected.parse(format='n3', data=f.read())
		(in_both, in_first, in_second) = graph_diff(expected, actual)
		for triple in in_first:
			print "in_first: " + str(triple)
		for triple in in_second:
			print "in_second: " + str(triple)
		self.assertEqual(actual, expected)
		self.assertEqual(len(in_first), 0)
		self.assertEqual(len(in_second), 0)

if __name__ == '__main__':
	unittest.main()
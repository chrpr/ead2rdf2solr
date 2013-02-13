import unittest
from lxml import etree
from component import Component
import configs

class ComponentTestCase(unittest.TestCase):

	def setUp(self):
		namespace = "{urn:isbn:1-931666-22-9}"
		fixture = "tests/fixtures/component-fragment.xml"
		fragment = etree.parse(fixture)
		c = fragment.xpath('/n:dsc/n:c', namespaces={'n': 'urn:isbn:1-931666-22-9'})[0]
		self.component = Component(c, MockEad())

	def test_solr_field_map(self):
		pass
class MockEad(object):
	def __init__(self):
		metadata = {}
		metadata['dc:identifier'] = ["foo"]
		metadata['arch:findingaid'] = ["foo"]
		self.metadata = metadata

if __name__ == '__main__':
	unittest.main()

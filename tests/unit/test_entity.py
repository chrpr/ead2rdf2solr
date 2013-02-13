import unittest
from lxml import etree
from entity import Entity
from utils import gettext
class EntityTestCase(unittest.TestCase):

	def setUp(self):
		namespace = "{urn:isbn:1-931666-22-9}"
		fixture = "tests/fixtures/entity-fragment.xml"
		fragment = etree.parse(fixture)
		c = fragment.xpath('/n:controlaccess/*', namespaces={'n': 'urn:isbn:1-931666-22-9'})[0]
		tag = c.tag.replace(namespace, '')
		text = gettext(c)
		vocab = c.get('source')
		self.entity = Entity(tag, text, vocab)

	def test_something(self):
		pass

if __name__ == '__main__':
	unittest.main()

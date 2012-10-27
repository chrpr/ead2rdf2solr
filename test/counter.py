import glob
import os

path = ''

## {{{ http://code.activestate.com/recipes/65127/ (r3)
from xml.sax.handler import ContentHandler
import xml.sax
class countHandler(ContentHandler):
    def __init__(self):
        self.tags={}

    def __getitem__(self, name):
     	return self.tags[name]

    def startElement(self, name, attr):
        if not self.tags.has_key(name):
            self.tags[name] = 0
        self.tags[name] += 1

for f in glob.glob( os.path.join(path, '*.xml') ):
	parser = xml.sax.make_parser()
	handler = countHandler()
	parser.setContentHandler(handler)
	parser.parse(f)
	#print str(f) + ": " + handler.tags
	#print '{0} -> {1}'.format(f, handler.tags)
	print '{0} -> {1}'.format(f, handler['corpname'])    

## end of http://code.activestate.com/recipes/65127/ }}}

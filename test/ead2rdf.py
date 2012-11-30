from lxml import etree
import os
import glob
import sys
import codecs
import re
from ead import Ead

#iterate through files
path = ''
for f in glob.glob( os.path.join(path, '*.xml') ):
    #print f
    #innerli = []
    #print "current file is: " + infile
    #tree = ET.ElementTree(file=f)
    #print '{0} -> {1}'.format(file, tree.getroot())
    #if generate_rdf(tree.getroot()) == " ": 
    #	print '{0}|{1}'.format(f, generate_rdf(tree.getroot()))
    root = etree.parse(f)
    ead = Ead(root, f)
    #print f
    if f == "ALBA.PHOTO.015-ead.xml":
        #print 'Title: {0}; ID: {1}; Access Restrictions: {2}'.format(ead.title.encode('utf-8'), ead.identifier.encode('utf-8'), ead.restrictions.encode('utf-8'))
        for k, v in ead.metadata.iteritems():
            #print type(v)
            if type(v) == unicode or type(v) == str: 
                print "  -{0}: {1}".format(k, v.encode('utf-8')) 
            elif type(v) == list:
                for e in v:
                    print "  -{0}: {1}".format(k, e.encode('utf-8'))
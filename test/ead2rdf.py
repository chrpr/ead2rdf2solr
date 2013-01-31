from lxml import etree
import os
import glob
import sys
import codecs
import re
from ead import Ead
from time import localtime, strftime

scriptstart = strftime("%a, %d %b %Y %H:%M:%S +0000", localtime())

def printComponents(components):
    for component in components:
        if 'arch:hasParent' in component.metadata.keys():
            print f + "|" + component.metadata['dc:identifier'].encode('utf-8') + ": " + component.metadata['dct:title'].encode('utf-8') + "|hasParent|" + component.metadata['arch:hasParent']
        else:
            print f + "|" + component.metadata['dc:identifier'].encode('utf-8') + ": " + component.metadata['dct:title'].encode('utf-8') + "|hasParent|Top Level"
        if component.components: printComponents(component.components)
#iterate through files
#this should actually take the path from the command line!
path = ''
count = 0
for f in glob.glob( os.path.join(path, '*.xml') ):
    if count <= 300:
        #count += 1
        #print f
        #innerli = []
        #print "current file is: " + infile
        #tree = ET.ElementTree(file=f)
        #print '{0} -> {1}'.format(file, tree.getroot())
        #if generate_rdf(tree.getroot()) == " ": 
        #	print '{0}|{1}'.format(f, generate_rdf(tree.getroot()))
        time = strftime("%a, %d %b %Y %H:%M:%S +0000", localtime())
        print  'Starttime: {0}: {1}'.format(f, time)

        root = etree.parse(f)
        ead = Ead(root, f)
        #print f
        #if f == "ALBA.PHOTO.015-ead.xml":
        #print 'Title: {0}; ID: {1}; Access Restrictions: {2}'.format(ead.title.encode('utf-8'), ead.identifier.encode('utf-8'), ead.restrictions.encode('utf-8'))
        '''
        for k in ead.metadata:
            print k

        for k, v in ead.metadata.iteritems():
            #print type(v)
            if type(v) == unicode or type(v) == str: 
                print "  -{0}: {1}".format(k, v.encode('utf-8')) 
            elif type(v) == list:
                for e in v:
                    print "  -{0}: {1}".format(k, e.encode('utf-8'))

        for heading in ead.headinglist:
            print f + "|head|" + heading.encode('utf-8')

        for headroot in ead.headrootlist:
            print f + "|root|" + headroot.encode('utf-8')
        '''
        #printComponents(ead.components)
        #ead.output()
        #ead.fourstore()
        ead.makeSolr()
        time = strftime("%a, %d %b %Y %H:%M:%S +0000", localtime())
        print  'EndTime: {0}: {1}'.format(f, time)


scriptend = strftime("%a, %d %b %Y %H:%M:%S +0000", localtime())

print "Total Time:"
print "Start: " + scriptstart
print "End: " + scriptend


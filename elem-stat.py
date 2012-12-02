from lxml import etree
import os
import glob
import sys
import codecs
import re
from ead import Ead

def proc_children(root, ptag):

    namespace = "{urn:isbn:1-931666-22-9}"



    for element in root:
        #new_path = path[:]
        tag = element.tag.replace(namespace, '')
        #text = child.text.strip()
        if tag == 'did':
            for subelem in element:
                subtag = subelem.tag.replace(namespace, '')
                if subtag == "origination":
                    for subsub in subelem:
                       print ptag + "|"+ tag + "|" + subtag + "|" + subsub.tag.replace(namespace, '')
                #print subelem.tag.replace(namespace, '')
        proc_children(element, tag)


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
    #print type(root.getroot())
    #ead = Ead(root, f)
    proc_children(root.getroot(), "root")
    #print f
    #if f == "ALBA.PHOTO.015-ead.xml":

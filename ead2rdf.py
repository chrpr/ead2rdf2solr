from lxml import etree
import os
import glob
import sys
import codecs
import re
from utils import *
from ead import Ead
from time import localtime, strftime
from optparse import OptionParser

def printComponents(components):
    for component in components:
        if 'arch:hasParent' in component.metadata.keys():
            print f + "|" + component.metadata['dc:identifier'].encode('utf-8') + ": " + component.metadata['dct:title'].encode('utf-8') + "|hasParent|" + component.metadata['arch:hasParent']
        else:
            print f + "|" + component.metadata['dc:identifier'].encode('utf-8') + ": " + component.metadata['dct:title'].encode('utf-8') + "|hasParent|Top Level"
        if component.components: printComponents(component.components)
        
def main(opts):
    
    lookups = codecs.open(opts.lookups, 'w', encoding='utf-8')
    
    #iterate thr.ough files
    #Or the config file
    entitySet = {}
    count = 0
    for f in glob.glob( os.path.join(opts.sourcedir, '*.xml') ):
        
        if opts.limit and count == opts.limit:
            break
        
        #print f
        #innerli = []
        #print "current file is: " + infile
        #tree = ET.ElementTree(file=f)
        #print '{0} -> {1}'.format(file, tree.getroot())
        #if generate_rdf(tree.getroot()) == " ": 
        #	print '{0}|{1}'.format(f, generate_rdf(tree.getroot()))
        time = strftime("%a, %d %b %Y %H:%M:%S +0000", localtime())
        print  'Starttime: {0}: {1}'.format(f, time)

        try:
            root = etree.parse(f)
            ead = Ead(root, f)
            for e in ead.entities:
                #print dir(e)
                key = e.metadata["id"]
    
                if key not in entitySet:
                    entitySet[key] = e
                #pri.nt key + " added to entitySet."
                else:
                    #print "You already have a " + key
                    if e.collections[0] not in entitySet[key].collections: 
                        entitySet[key].collections.extend(e.collections)
                    if e.headings[0] not in entitySet[key].headings: 
                        entitySet[key].headings.extend(e.headings)
                #print entitySet[key].collections
                #print entitySet[key].headings
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
            #ead.makeSolr()
        except Exception, e:
            print "Error processing %s: %s" % (f, e)
            
        time = strftime("%a, %d %b %Y %H:%M:%S +0000", localtime())
        print  'EndTime: {0}: {1}'.format(f, time)
        
        count += 1
    
    fuzzmatch = codecs.open(opts.fuzzmatch, 'r', encoding='utf-8')
    dbmatches = {}
    for line in fuzzmatch:
        split = line.split('|')
        ratiodict = {'dbid': split[1], 'dblabel': split[2], 'label': split[3]}
        if split[0] not in dbmatches:
            dbmatches[split[0]] = [ratiodict]
        else:
            dbmatches[split[0]].append(ratiodict)
    
    for eid, entity in entitySet.iteritems():
        entity.makeSolr()
        print eid
        '''
        #This block of code moves to makeSolr() for the entity....
        sameArray = sameAs('http://chrpr.com/data/' + eid.encode('utf-8') + '.rdf')
        for uri in sameArray:
            print "  -" + uri.encode('utf-8')
            abstracts = dbpField(uri.encode('utf-8'), 'http://dbpedia.org/ontology/abstract')
            for abstract in abstracts:
                print "      Abstract:" + abstract.encode('utf-8')
        '''
        '''
        if eid in dbmatches:
            candidates = dbmatches[eid]
            toprat = 0
            bestmatch = ""
            for candidate in candidates:
                ratio = fuzzer(candidate['label'], candidate['dblabel'])
                if ratio > toprat:
                    toprat = ratio
                    bestid = candidate['dbid']
                    bestmatch = (eid.encode('utf-8') + "|" + candidate['dbid'].encode('utf-8') + 
                    "|" + candidate['dblabel'].encode('utf-8') + "|" + 
                    candidate['label'].encode('utf-8') + "|" + 
                    str(ratio))
            #print bestmatch 
            #print bestid
            #load4store("dbpedia", bestid)
            #load4store("relations", [eid, 'owl', 'sameas', bestid])
            load4store([eid, 'owl', 'sameas', bestid])
            '''
    
    
        #entity.makeGraph()
        #entity.fourstore()
        #for lookup in entity.metadata['lookup']:
        #    lookups.write(eid + '|' + lookup + '\n')
    
        #    lookups.write('{0}|{1}'.format(eid, lookup.decode('utf-8')))
        #print catext.encode('utf-8')
        #for k, v, in entity.metadata.iteritems():
            #print k + " is a " + type(v)
            #if type(v) == "str":
            #print "{0}: {1}".format(k, v)
        #print "Collections: " + "; ".join(entity.collections).encode('utf-8')
        #print "Headings: " + "; ".join(entity.headings).encode('utf-8')
    
    #dbpmatch(entitySet)
    
    
if __name__ == '__main__':

    op = OptionParser()
    op.add_option('--sourcedir', dest='sourcedir', action='store',
        help='load from this directory path', default='')
    op.add_option('--limit', dest='limit', action='store', type=int,
        help='only process this many', default=None)
    op.add_option('--fuzzmatch', dest='fuzzmatch', action='store',
        help='path to fuzzmatch input', default='fuzzmatch.txt')
    op.add_option('--lookups', dest='lookups', action='store',
        help='path to lookups output', default='lookups.txt')
    opts, args = op.parse_args()
    
    if not os.path.exists(opts.fuzzmatch):
        raise Exception("file not found: %s" % opts.fuzzmatch)

    scriptstart = strftime("%a, %d %b %Y %H:%M:%S +0000", localtime())
    
    main(opts)
    
    scriptend = strftime("%a, %d %b %Y %H:%M:%S +0000", localtime())

    print "Total Time:"
    print "Start: " + scriptstart
    print "End: " + scriptend


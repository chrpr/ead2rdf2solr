import xml.etree.cElementTree as ET
import os
import glob
from collections import Counter
from operator import itemgetter
import sys
import codecs
import re

# Starting to hack on a bit of Eric's work...
from btframework.augment import lucky_viaf_template, lucky_idlc_template, EAD_AUGMENTATIONS

uri_matches = codecs.open('fast_matches.txt', 'w', encoding='utf-8')
#old_matches = open('old_matches.txt')
#old_matches = codecs.open('old_matches.txt', 'r', 'utf-8')
old_uris = {}

#for line in old_matches:
    #print line
 #   l = line.split("|")
    # or is it better to do this as d[str(l[0:5])] = l[5]?...
    # d[str(l[0:4])] = {l[4]: l[5]}
    # Better still, use "|".join(l[0:5])
    # d[str(l[0:5])] = l[5]
#    old_uris["|".join(l[0:5])] = l[5] 

#matrix2 = open('matrix2.txt', 'w')
#totals = open('totals.txt', 'w')

#if len(sys.argv) > 1:
lookup = sys.argv
#else: 
#    lookup = ""

path = ''
li = []
li2 = []
#TODO:
#  - Track sources of access points, then run them through a counter...
#  - Possible that "aat" stuff is completely useless...
sources = []
d = {}
subs = []
#usubs = []

def print_path(root, path=None):

    if path is None:
        path = [root.tag]

    for child in root:
        #text = child.text.strip()
        text = child.text
        new_path = path[:]
        tag = child.tag.replace('{urn:isbn:1-931666-22-9}','')


        #print tag
        #if 'Reference' in current_element.attrib:

        if tag == 'controlaccess':
            #actually, this is fully the wrong way to go about this...
            # What I want to do is get all the raw text, (see other note about more modular code...)
            for subchild in child:
                if subchild.tag.replace('{urn:isbn:1-931666-22-9}','') in [
                        'persname', 'subject', 'corpname', 'genreform', 'geogname', 'famname'
                    ]:
                    #li2.append(f + "|" + '/{0}'.format('/'.join(new_path).replace('{urn:isbn:1-931666-22-9}','')) + 
                        #"/" + tag + "|" + subchild.tag.replace('{urn:isbn:1-931666-22-9}','') + "|" + subchild.text)
                    #tmp = re.findall('[A-Za-z]+',subchild.text)
                    item = {
                        u'id': subchild.text,
                        #b = re.compile('[a-z]+')
                        #u'label': subchild.text.rstrip('.'),
                        u'label': subchild.text.split('|')[0].rstrip('.'),
                        u'type': 'Object',
                    }

                    ''' So this loop will pull together the main facet cluseters.
                    Then I can run fast lookup on main heading based on tag set & on each 
                    subfield based on indicator code.
                    Will need to slightly vary output data so:
                    TAM.129-ead.xml|persname|naf|Hall, Gus -- $$v Portraits|viafFromHeuristic|http://viaf.org/viaf/253268226
                    becomes:
                    TAM.129-ead.xml|persname-heading|naf|Hall, Gus -- $$v Portraits|fastFromHeuristic|http://fast.org/viaf/253268226
                    TAM.129-ead.xml|persname-sub-v|naf|Hall, Gus -- $$v Portraits|fastFromHeuristic|http://fast.org/viaf/253268226
                    Or something similar. Maybe add extra column for "heading" and "sub-v" bits...
                    '''

                    if u"|" in subchild.text:
                        fl = subchild.text.split('|')[1:]
                        #print subchild.text
                        item[u'facets'] = {}
                        for delim in fl:
                            #print delim
                            #print delim[0:1]
                            item[u'facets'][delim[0:1] + 'sub'] = delim[2:]
                            #print item['facets']
                        #print item[u'facets'].keys()
                        subs.extend(item[u'facets'].keys())
                        #usubs = Set(subs)

                    print item[u'label'].encode('utf-8')
                    if u'facets' in item:
                        print item[u'facets']
                    '''
                    #more of eric's stuff goes here...
                    code = subchild.tag.replace('{urn:isbn:1-931666-22-9}','')
                    for (acode, aparams, afunc, key) in EAD_AUGMENTATIONS:
                        #if code == acode: print >> sys.stderr, (item, aparams)
                        #if code == acode and all(( item.get(p) for p in aparams )):
                        #modifying this to drop the item.get(p) thing (for now)
                        #But I like how that's actually working, keeping param names
                        # synched in & outside of function...
                        TODO: 
                            -Parse out dates in persname...
                            -Strip subdivisions (And deal with some of them?)
                            Maybe not necessary to parse out dates from names. Lookup seems to work without it. 
                            Then can do this to track:
                        bash-3.2$ awk ' BEGIN { FS = "|" ; OFS = "|" } { if ($NF == "None") { print "missing" } 
                            else { print "found" } } ' uri_matches.txt | sort | uniq -c
                        123 found
                        210 missing
                        Now that I'm stripping the right hand stuff... Let's see how much my hit-rate goes up.
                        Pretty significantly:
                        bash-3.2$ awk ' BEGIN { FS = "|" ; OFS = "|" } { if ($NF == "None") { print "missing" } 
                            else { print "found" } } ' uri_matches.txt | sort | uniq -c
                        162 found
                        171 missing
                        
                        k = "|".join([f, subchild.tag.replace('{urn:isbn:1-931666-22-9}',''), subchild.attrib["source"], subchild.text.replace("|", "$$"), key  ])
                        if code == acode and all(( item.get(p) for p in aparams )) and ((key[:4] in lookup) or (len(lookup) == 1)) and k not in old_uris:
                            #Meets the criteria for this augmentation
                            val = afunc(item)
                            if afunc(item) == "":
                                val = "None"
                            print subchild.text.encode('utf-8')  + "|"  + str(val)
                            #time to pimp out this uri_match file...
                            #uri_matches.write(subchild.text + "|" + str(val) + "\n")
                            uri_matches.write(
                                                f + "|" + 
                                                subchild.tag.replace('{urn:isbn:1-931666-22-9}','') + "|" + 
                                                subchild.attrib["source"] + "|" + 
                                                subchild.text.replace("|", "$$") + "|" + key + "|" +
                                                str(val) + "\n")
                            
                            #print "boob"
                            #if val is not None: item[key] = val

                    '''
            #accesstype = child    
            '''
            print f + "|" + '/{0}'.format('/'.join(new_path).replace('{urn:isbn:1-931666-22-9}','')) + \
                "/" + tag + "|" + child.text
            '''
        #new_path.append(child.tag)
        #print new_path
        usubs = set(subs)
        #print usubs
        if text:
            text = child.text.strip()
            #print '/{0}, {1}'.format('/'.join(new_path), text)
            #print '/{0}'.format('/'.join(new_path).replace('{urn:isbn:1-931666-22-9}',''))
            #f.write('/{0}\n'.format('/'.join(new_path).replace('{urn:isbn:1-931666-22-9}','')))
            #li.append('/{0}'.format('/'.join(new_path).replace('{urn:isbn:1-931666-22-9}','')))
            #innerli.append('/{0}'.format('/'.join(new_path).replace('{urn:isbn:1-931666-22-9}','')))


        print_path(child, new_path)

#print_path(root)

#iterate through files
for f in glob.glob( os.path.join(path, '*.xml') ):
    print f
    innerli = []
    #print "current file is: " + infile
    tree = ET.ElementTree(file=f)
    #print '{0} -> {1}'.format(file, tree.getroot())
    print_path(tree.getroot())

uri_matches.close()

usubs = set(subs)
print usubs
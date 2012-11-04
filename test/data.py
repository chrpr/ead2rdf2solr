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


"""
Some file info:
PHOTOS.151-ead.xml')
Biggest: PHOTOS.223-ead.xml
"""

levels = codecs.open('c-levels.txt', 'w', encoding='utf-8')
strings = codecs.open('strings.txt', 'w', encoding='utf-8')
title_markup = codecs.open('markup.txt', 'w', encoding='utf-8')
uri_matches = codecs.open('uri_matches.txt', 'w', encoding='utf-8')
#old_matches = open('old_matches.txt')
old_matches = codecs.open('old_matches.txt', 'r', 'utf-8')
old_uris = {}

for line in old_matches:
    #print line
    l = line.split("|")
    # or is it better to do this as d[str(l[0:5])] = l[5]?...
    # d[str(l[0:4])] = {l[4]: l[5]}
    # Better still, use "|".join(l[0:5])
    # d[str(l[0:5])] = l[5]
    #print ["|".join(l[0:6])]
    old_uris["|".join(l[0:6])] = l[6] 

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
cid = 0
nocid = 0

"""
recursive method assembles the full path of each terminal node
also strips out that ridiculous default namespace
I guess I'll want to redo this to build a full list of all possible elements across all files
Then cast that into a "set" so that dups are gone & use that as my index & header row.
At the same time, I'll build a dictionary (of dictionaries?) that has following format
{filename1:{element2:count, element2:count, element3:count}, 
filename2:{element1:count, element2:count}, etc:{etc...}}
Then I'll use the "set" to print my values matrix...
"""
def print_path(root, path=None):

    if path is None:
        path = [root.tag]

    for child in root:
        #text = child.text.strip()
        text = child.text
        new_path = path[:]
        if child.tag.replace('{urn:isbn:1-931666-22-9}','') == 'unittitle':
            #for subchild in child:
            #    title_markup.write(subchild.tag.replace('{urn:isbn:1-931666-22-9}','') + "\n")
            elli = [elem.tag for elem in child.iter()]
            for item in elli:
                title_markup.writelines(["%s, " % item.replace('{urn:isbn:1-931666-22-9}','')])
            title_markup.write("\n")
        # Get rid of "id" calls from here...
        if child.tag.replace('{urn:isbn:1-931666-22-9}','') == 'c' and 'level' in child.attrib:
            if 'otherlevel' in child.attrib:
                new_path.append(child.tag + ":" + child.attrib["id"] + ":" + child.attrib["level"] + 
                    ":" + child.attrib["otherlevel"])
            else: 
                new_path.append(child.tag + ":" + child.attrib["id"] + ":" + child.attrib["level"])
        else:
            new_path.append(child.tag)
        tag = child.tag.replace('{urn:isbn:1-931666-22-9}','')
        #print tag
        #if 'Reference' in current_element.attrib:
        if tag == 'c':
            idtext = child.attrib["id"]
            if 'id' in child.attrib:
                global cid 
                cid += 1
            else: 
                global nocid 
                nocid += 1
            if 'level' in child.attrib:
            #if child.attrib["level"] == 'otherlevel':
                li.append('/{0}'.format('/'.join(new_path).replace('{urn:isbn:1-931666-22-9}','')) + "/" + 
                    tag + ":" + child.attrib["level"] )
            #print child.tag, child.attrib
            else:
                li.append('/{0}'.format('/'.join(new_path).replace('{urn:isbn:1-931666-22-9}','')) + "/" + tag )
        #else:
        if tag == 'unittitle' and child.text:
            # This bit could use a re-write. I'm losing "tail" text. 
            # I should actually build a subroutine that strips tags & gets all text. 
            # http://www.velocityreviews.com/forums/t342725-elementtree-how-to-get-the-whole-content-of-a-tag.html
            '''
            li2.append(f + "|" + '/{0}'.format('/'.join(new_path).replace('{urn:isbn:1-931666-22-9}',''))  + 
                "|" + str(child.text.decode('utf-8')))
            li2.append(f + "|" + '/{0}'.format('/'.join(new_path).replace('{urn:isbn:1-931666-22-9}',''))  + 
                "|" + "".join( [ child.text ] + [ e.text for e in child.iter() ] ))
            '''
            ut = f + "|" + '/{0}'.format('/'.join(new_path).replace('{urn:isbn:1-931666-22-9}','')) + "|"
            t = ''
            for e in child.iter():
                if e.text:
                    t += e.text.strip() + " "
            if t == '':
                print idtext
            li2.append(ut + t.lstrip())
            '''
            li2.append(f + "|" + '/{0}'.format('/'.join(new_path).replace('{urn:isbn:1-931666-22-9}','')) + 
                "|" )+ " ".join([ e.text.strip() for e in child.iter() ] ).lstrip())
            li2.append(f + "|" + '/{0}'.format('/'.join(new_path).replace('{urn:isbn:1-931666-22-9}','')) + 
                "|" + child.text)
            '''

        elif tag == 'controlaccess':
            #actually, this is fully the wrong way to go about this...
            # What I want to do is get all the raw text, (see other note about more modular code...)
            for subchild in child:
                if subchild.tag.replace('{urn:isbn:1-931666-22-9}','') in [
                        'persname', 'subject', 'corpname', 'genreform', 'geogname', 'famname'
                    ]:
                    li2.append(f + "|" + '/{0}'.format('/'.join(new_path).replace('{urn:isbn:1-931666-22-9}','')) + 
                        "/" + tag + "|" + subchild.tag.replace('{urn:isbn:1-931666-22-9}','') + "|" + subchild.text)
                    #tmp = re.findall('[A-Za-z]+',subchild.text)
                    items = []
                    items.append({
                        u'id': subchild.text,
                        #b = re.compile('[a-z]+')
                        #u'label': subchild.text.rstrip('.'),
                        u'label': subchild.text.split('|')[0].rstrip('.'),
                        u'type': 'Object',
                        u'level': 'Heading',
                        u'code' : subchild.tag.replace('{urn:isbn:1-931666-22-9}','')

                     })
                    if u"|" in subchild.text:
                        fl = subchild.text.split('|')[1:]
                        #print subchild.text
                        #item[u'facets'] = {}
                        for delim in fl:
                            items.append({
                                u'id': subchild.text + delim[0:1],
                                u'label': delim[2:],
                                u'type': 'Object',
                                u'level': 'sub',
                                u'code': 'sub' + delim[0:1]
                            })
                            #print delim
                            #print delim[0:1]
                            #item[u'facets'][delim[0:1] + 'sub'] = delim[2:]
                            #print item['facets']
                        #print item[u'facets'].keys()
                        #subs.extend(item[u'facets'].keys())
                        #usubs = Set(subs)

                    #print item[u'label'].encode('utf-8')
                    #if u'facets' in item:
                    #    print item[u'facets']
                    #more of eric's stuff goes here...
                    #print items
                    #interesting: so, passing an item that had a dictionary in it broke the augement.py code.
                    # stripping it into main "item" fixed the problem. 
                    # So, what I really need is an "items" list, and an extra processing loop...
                    #if u'facets' in items[0]:
                    #    print facets
                    #    facets = items[0].pop(u'facets')
                    #    for key, val in facets.iteritems():
                        # TODO: 
                        #    - THis is the next step. Add a bunch of additional "items"
                        #    - Make "code" an attribute of the item itself
                        #    - modify the lookup loop below
                    #        items.append({
                    #            u'id': subchild.text + key,
                     #           u'label': val,
                     #           u'type': 'Object',
                     #           u'level': 'sub',
                     #           u'code': 'key'

                     #       })
                    for item in items:
                        print item
                        for (acode, aparams, afunc, key) in EAD_AUGMENTATIONS:
                            #if code == acode: print >> sys.stderr, (item, aparams)
                            #if code == acode and all(( item.get(p) for p in aparams )):
                            #modifying this to drop the item.get(p) thing (for now)
                            #But I like how that's actually working, keeping param names
                            # synched in & outside of function...
                            '''TODO: 
                                -Parse out dates in persname...
                                -strip subdivisions (And deal with some of them?)
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
                            '''
                            # This shit here is *crazy* wonky... I'll need to trick this out so it's clear whether I'm 
                            # cranking on "subfields" or main headings...
                            #k = "|".join([f, subchild.tag.replace('{urn:isbn:1-931666-22-9}',''), subchild.attrib["source"], item['level'], subchild.text.replace("|", "$$"), key  ])
                            k = "|".join([f, item['code'], subchild.attrib["source"], item['level'], subchild.text.replace("|", "$$"), key  ])

                            #Huh: This still doesn't seem to be working. See gap in midst of :
                            # file:///media/Storage/EAD%20for%20Corey/EAD%20for%20Corey/WAG.038-ead.xml
                            ## TODO: Fix this shit, find gaps, re-run code to fill gaps at some point? Also, will there be gaps on id.loc or in viaf?
                            ## TODO: Tighten up Viaf Matching & rerun that as well
                            
                            if item['code'] == acode and all(( item.get(p) for p in aparams )) and ((key[:4] in lookup) or (len(lookup) == 1)) and k not in old_uris:
                                #Meets the criteria for this augmentation
                                val = afunc(item)
                                if afunc(item) == "":
                                    val = "None"
                                print subchild.text.encode('utf-8')  + "|"  + str(val)
                                #time to pimp out this uri_match file...
                                #uri_matches.write(subchild.text + "|" + str(val) + "\n")
                                uri_matches.write(
                                                f + "|" + item['code'] + "|" + 
                                                subchild.attrib["source"] + "|" + item['level'] + "|" +
                                                subchild.text.replace("|", "$$") + "|" + key + "|" +
                                                str(val) + "\n")
                            
                                #print "boob"
                                #if val is not None: item[key] = val


            #accesstype = child    
            '''
            print f + "|" + '/{0}'.format('/'.join(new_path).replace('{urn:isbn:1-931666-22-9}','')) + \
                "/" + tag + "|" + child.text
            '''
        #new_path.append(child.tag)
        #print new_path
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

#s = (sorted(set(li)))
#print s
counter = Counter(li)
#print Counter(li)

for k, v in counter.items():
    #print k + "|" + str(v)
    levels.write(k + "|" + str(v) + "\n")

for i in li2:
    #i.decode('utf-8')
    #i.unicode(i, 'utf-8')
    strings.write(i + "\n")

"""
    d[f] = counter


#print len(li)
s = (sorted(set(li)))
totaler = Counter(li)
#print len(s)

#print s
#print d

templ = list(s)

matrix1.write("filename|" + '|'.join(templ[0:250]) + "\n")    
matrix2.write("filename|" + '|'.join(templ[250:]) + "\n")    

#sorted(d.items(), key=lambda x: x[1])
totaler = sorted(totaler.items(), key=lambda x: x[1])
for v in totaler:
#for key in sorted(totaler.items(), key=itemgetter(1)):
    #outstr += "|" + str(counts.get(i, 0))
    #tstr = key + "|" + totaler.get(key, 0)
    tstr = v[0] + "|" + str(v[1])
    totals.write(tstr + "\n")

for key, value in d.items():
    #colcount +=1
    outstr1 = key
    outstr2 = key
    counts = value
    colcount = 0
    for i in s:
        colcount += 1
        #outstr += "|" + str(counts.get(i, 0))
        if colcount <= 250:
            outstr1 += "|" + str(counts.get(i, 0))
        else:
            outstr2 += "|" + str(counts.get(i, 0))
    matrix1.write(outstr1 + "\n")    
    matrix2.write(outstr2 + "\n")

print len(sorted(s))
matrix1.close()
matrix2.close()
totals.close()"""
print "C's with IDs: " + str(cid)
print "C's without: " + str(nocid)
levels.close()
strings.close()
title_markup.close()
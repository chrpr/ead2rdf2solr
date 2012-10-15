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

#matrix2 = open('matrix2.txt', 'w')
#totals = open('totals.txt', 'w')
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
{filename1:{element2:count, element2:count, element3:count}, filename2:{element1:count, element2:count}, etc:{etc...}}
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
                new_path.append(child.tag + ":" + child.attrib["id"] + ":" + child.attrib["level"] + ":" + child.attrib["otherlevel"])
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
                li.append('/{0}'.format('/'.join(new_path).replace('{urn:isbn:1-931666-22-9}','')) + "/" + tag + ":" + child.attrib["level"] )
            #print child.tag, child.attrib
            else:
                li.append('/{0}'.format('/'.join(new_path).replace('{urn:isbn:1-931666-22-9}','')) + "/" + tag )
        #else:
        if tag == 'unittitle' and child.text:
            # This bit could use a re-write. I'm losing "tail" text. 
            # I should actually build a subroutine that strips tags & gets all text. 
            # See: http://www.velocityreviews.com/forums/t342725-elementtree-how-to-get-the-whole-content-of-a-tag.html

#            li2.append(f + "|" + '/{0}'.format('/'.join(new_path).replace('{urn:isbn:1-931666-22-9}',''))  + "|" + str(child.text.decode('utf-8')))
#            li2.append(f + "|" + '/{0}'.format('/'.join(new_path).replace('{urn:isbn:1-931666-22-9}',''))  + "|" + "".join( [ child.text ] + [ e.text for e in child.iter() ] ))
            ut = f + "|" + '/{0}'.format('/'.join(new_path).replace('{urn:isbn:1-931666-22-9}','')) + "|"
            t = ''
            for e in child.iter():
                if e.text:
                    t += e.text.strip() + " "
            if t == '':
                print idtext
            li2.append(ut + t.lstrip())
            #li2.append(f + "|" + '/{0}'.format('/'.join(new_path).replace('{urn:isbn:1-931666-22-9}',''))  + "|" )+ " ".join([ e.text.strip() for e in child.iter() ] ).lstrip())
            #li2.append(f + "|" + '/{0}'.format('/'.join(new_path).replace('{urn:isbn:1-931666-22-9}',''))  + "|" + child.text)


        elif tag == 'controlaccess':
            #actually, this is fully the wrong way to go about this...
            # What I want to do is get all the raw text, (see other note about more modular code...)
            for subchild in child:
                if subchild.tag.replace('{urn:isbn:1-931666-22-9}','') in ['persname', 'subject', 'corpname', 'genreform', 'geogname', 'famname']:
                    li2.append(f + "|" + '/{0}'.format('/'.join(new_path).replace('{urn:isbn:1-931666-22-9}','')) + "/" + tag + "|" + subchild.tag.replace('{urn:isbn:1-931666-22-9}','') + "|" + subchild.text)
                    #tmp = re.findall('[A-Za-z]+',subchild.text)
                    item = {
                        u'id': subchild.text,
                        #b = re.compile('[a-z]+')
                        #u'label': subchild.text.rstrip('.'),
                        u'label': subchild.text.split('|')[0].rstrip('.'),
                        u'type': 'Object',
                     }
                    #more of eric's stuff goes here...
                    code = subchild.tag.replace('{urn:isbn:1-931666-22-9}','')
                    for (acode, aparams, afunc, key) in EAD_AUGMENTATIONS:
                        #if code == acode: print >> sys.stderr, (item, aparams)
                        #if code == acode and all(( item.get(p) for p in aparams )):
                        #modifying this to drop the item.get(p) thing (for now)
                        #But I like how that's actually working, keeping param names synched in & outside of function...
                        '''TODO: 
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
                        '''
                        if code == acode and all(( item.get(p) for p in aparams )):
                            #Meets the criteria for this augmentation
                            val = afunc(item)
                            print subchild.text.encode('utf-8')  + "|"  + str(val)
                            #time to pimp out this uri_match file...
                            #uri_matches.write(subchild.text + "|" + str(val) + "\n")
                            uri_matches.write(
                                                f + "|" + 
                                                subchild.tag.replace('{urn:isbn:1-931666-22-9}','') + "|" + 
                                                subchild.attrib["source"] + "|" + 
                                                subchild.text.replace("|", "$$") + "|" + 
                                                str(val) + "\n")

                            #print "boob"
                            #if val is not None: item[key] = val


            #accesstype = child    
            #print f + "|" + '/{0}'.format('/'.join(new_path).replace('{urn:isbn:1-931666-22-9}','')) + "/" + tag + "|" + child.text
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
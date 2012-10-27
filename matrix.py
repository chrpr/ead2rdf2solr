import xml.etree.cElementTree as ET
import os
import glob
from collections import Counter
from operator import itemgetter
import sys

"""
Some file info:
PHOTOS.151-ead.xml')
Biggest: PHOTOS.223-ead.xml
"""

matrix1 = open('matrix1.txt', 'w')
matrix2 = open('matrix2.txt', 'w')
totals = open('totals.txt', 'w')
path = ''
li = []
d = {}

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
        if child.tag.replace('{urn:isbn:1-931666-22-9}','') == 'c' and 'level' in child.attrib:
            if 'otherlevel' in child.attrib:
                new_path.append(child.tag + ":" + child.attrib["level"] + ":" + child.attrib["otherlevel"])
            else: 
                new_path.append(child.tag + ":" + child.attrib["level"])
        else:
            new_path.append(child.tag)
        #print new_path
        if text:
            text = child.text.strip()
            #print '/{0}, {1}'.format('/'.join(new_path), text)
            #print '/{0}'.format('/'.join(new_path).replace('{urn:isbn:1-931666-22-9}',''))
            #f.write('/{0}\n'.format('/'.join(new_path).replace('{urn:isbn:1-931666-22-9}','')))
            li.append('/{0}'.format('/'.join(new_path).replace('{urn:isbn:1-931666-22-9}','')))
            innerli.append('/{0}'.format('/'.join(new_path).replace('{urn:isbn:1-931666-22-9}','')))


        print_path(child, new_path)

#print_path(root)

#iterate through files
for f in glob.glob( os.path.join(path, '*.xml') ):
    innerli = []
    #print "current file is: " + infile
    tree = ET.ElementTree(file=f)
    #print '{0} -> {1}'.format(file, tree.getroot())
    print_path(tree.getroot())
    counter = Counter(innerli)
    print Counter(innerli)

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
totals.close()
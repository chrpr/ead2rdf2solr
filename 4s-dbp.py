import codecs
import urllib
import time
from urllib import urlopen
from pprint import pprint
from HTTP4Store import HTTP4Store

import xml.etree.cElementTree as ET


matches = codecs.open('/home/charper/store/dbpedia/fuzzmatch.txt', 'r', 'utf-8')
#matches = codecs.open('/home/charper/store/dbpedia/dbp-data.txt', 'w', 'utf-8')
store = HTTP4Store('http://localhost:8080')

r = store.add_graph("http://example.org/dbpedia", "", "xml")
pprint(r)
count = 0
deduper = []	

for line in matches:
	m = line.split("|")[0].rstrip()
	count += 1
	if m not in deduper:
		#m = m + ".rdf"
		deduper.append(m)
		m = m.replace("resource", "data").encode('utf-8')
		print m
		#url = urlopen("http://id.loc.gov/authorities/subjects/sh85137025.rdf")
		url = urlopen(m)
		raw = url.read().decode('utf-8')
		#xml = ET.fromstring(raw)
		#r = store.del_graph("http://example.org/idlc")
		r =  store.append_graph("http://example.org/dbpedia", raw.encode('utf-8'), "xml")
		print str(count) + ": " + str(r.status)
		time.sleep(2)



#r =  store.append_graph("http://example.org/idlc", raw, "xml")
#print r.status
#time.sleep(2)
#r = e.del_graph("http://example.org/relsext")

#url = "http://id.loc.gov/authorities/subjects/sh85137025.rdf"
#xml = ET.parse(urllib.urlopen(url))
#url = urlopen("http://id.loc.gov/authorities/subjects/sh85137025.rdf")
#raw = url.read().decode('utf-8')
#xml = ET.fromstring(raw)
#print(xml)
#print(xml.findall("a"))        




#xml = ET.ElementTree(urllib.urlopen(url))
#print "Root: " + str(xml.getroot())
#for child in xml.getroot():
#	print child.tag
#tree = ET.ElementTree(file=f)
#print type(raw)
#print dir(raw)

#print xml.Element("root")
#print ET.tostring(xml)

#print xml

#r = store.del_graph("http://example.org/idlc")
#print r.status


#r =  store.append_graph("http://example.org/idlc", raw, "xml")
#print r.status
#time.sleep(2)
#r = e.del_graph("http://example.org/relsext")


q = """LOAD <http://id.loc.gov/authorities/subjects/sh85137025.rdf>
INTO GRAPH <http://example.org/idlc>
"""

#pprint(store.sparql(q))

#for line in matches:
#	count += 1
	#r =  store.append_graph("http://example.org/idlc", line, "xml")

#		out.write(ET.tostring(rec) + '\n')

	
#	print str(count) + ": " + str(r.status)
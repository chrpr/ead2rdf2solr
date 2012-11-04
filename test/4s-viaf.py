import codecs
from HTTP4Store import HTTP4Store

viaf = codecs.open('/media/Storage/viaf-matches-clusters-rdf.xml', 'r', 'utf-8')

store = HTTP4Store('http://localhost:8080')

r = store.add_graph("http://example.org/viaf", "", "xml")
count = 0	

for line in viaf:
	count += 1
	r =  store.append_graph("http://example.org/viaf", line, "xml")
	print str(count) + ": " + str(r.status)



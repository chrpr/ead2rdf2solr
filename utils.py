from configs import *
from entity import Entity
import codecs
from itertools import *
import rdflib
import urllib
import StringIO
from urllib import urlopen
from nltk.corpus import stopwords
from time import localtime, strftime
from fuzzywuzzy import fuzz
import string
from HTTP4Store import HTTP4Store
from rdflib import Graph, URIRef, Namespace, Literal

def gettext(elem, ignore=[], newline=[]):
	text = elem.text or ""
	text = text.rstrip()
	#print elem.tag + "|" + str(newline)
	#print text
	#TODO: This is still a little whacky. Got's to work out how to handle this better....
	for subelem in elem:
		if subelem.tag not in ignore: text = text + " " + gettext(subelem, ignore, newline)
		if subelem.tag in newline: 
			#print text
			text = "\n" + text.lstrip() + "\n"
		if subelem.tail:
			text = text + subelem.tail.strip()
	return text

def procdid(xfrag):
	namespace = "{urn:isbn:1-931666-22-9}"
	md = {
		'dct:abstract': [], 'arch:langnote': [], 'dc:language': [], 'arch:corpcreator': [], 'arch:perscreator': [],
		'dc:description': [], 'arch:location': [], 'dc:date': [], 'arch:datenormal': [],
		'arch:materialspec': [],
	}
	entities = []


	#print "FragTag" + gettext(xfrag).encode('utf-8')
	for subelem in xfrag:
		#print "Subelem" + str(subelem)
		tag = subelem.tag.replace(namespace, '')
		#print "Tag" + tag
		if tag == "abstract": md[fieldrenamings[tag]].append(gettext(subelem))
		if tag == "langmaterial":
			md[fieldrenamings[tag]].append(gettext(subelem).rstrip())
			for subsub in subelem:
				if subsub.tag.replace(namespace, '') == 'language':
					md['dc:language'].append(subsub.get('langcode'))
		#TODO: This is one piece of entity processing....
		# Fucker -- how to deal with component side?
		if tag == "origination":
			for child in subelem:
				chitag = child.tag.replace(namespace, '')
				chisource = child.get('source')
				#right, so this needs to define an entity & return it,
				#so I need to make sure I parse this from return
				entity = Entity(chitag, gettext(child), chisource)
				entities.append(entity)
				if chitag == "corpname": md[fieldrenamings[tag][chitag]].append(gettext(child))
				if chitag == "persname": md[fieldrenamings[tag][chitag]].append(gettext(child))
		if tag == "physdesc": md[fieldrenamings[tag]].append(gettext(subelem))
		if tag == "physloc": md[fieldrenamings[tag]].append(gettext(subelem))
		if tag == "unitdate":
			md[fieldrenamings[tag]].append(gettext(subelem))
			#print subelem.attrib
			#if '{http://www.w3.org/1999/xlink}normal' in subelem.attrib:
			if'normal' in subelem.attrib:
				md[fieldrenamings['normal']].append(subelem.get('normal'))
		if tag == "materialspec": md[fieldrenamings[tag]].append(gettext(subelem))

	return md, entities

def fuzzer(localstring, dbpstring):
	lwl = localstring.replace('-','').replace(',.', '').split()
	lfwl = [w for w in lwl if not w in stopwords.words('english')]
	dwl = dbpstring.replace('-','').split()
	dfwl = [w for w in dwl if not w in stopwords.words('english')]
	ratio = fuzz.token_sort_ratio(str(lfwl), str(dfwl))
	return ratio

def sameAsObj(uri):
	q = ( "SELECT ?o WHERE { <" + uri + ">"
		"<http://www.w3.org/2002/07/owl#sameas> ?o " + 
		"}" )
	store = HTTP4Store('http://localhost:8080')
	response = store.sparql(q)
	sameAs = []
	for data in response:
		if data[u'o'].replace('/data/', '/resource/') not in sameAs: sameAs.append(data[u'o'].replace('/data/', '/resource/'))
	return sameAs

def dbpField(sub, prop):
	#sub = sub.replace('/data/', '/resource/')
	q = ( "SELECT ?o WHERE { <" + sub + ">"
		"<" + prop + "> ?o " + 
		"FILTER langMatches( lang(?o), \"EN\" )" +
		"}" )
	store = HTTP4Store('http://localhost:8080')
	print q
	response = store.sparql(q)
	propData = []
	for data in response:
		if data[u'o'].rstrip('@EN').strip('"') not in propData: propData.append(data[u'o'].rstrip('@EN').strip('"'))
	return propData	


def load4store(data):
	#def load4store(graph, data):
	#Yeah, probably want to generalize this as above, but for now, f-it...
	store = HTTP4Store('http://localhost:8080')
	''''
	#Is this even necessary?
	if type(data) == unicode:
		#print "URL: " + data.encode('utf-8')
	if type(data) == list:
		#print "Triple: " + " -- ".join(data)
	'''
	urlstr = data[3].replace("/resource/", "/data/").encode('utf-8')
	url = urlopen(urlstr)
	raw = url.read().decode('utf-8')
	r = store.append_graph('http://chrpr.net/dbpedia', raw.encode('utf-8'), 'xml')
	relGraph = rdflib.Graph(identifier="http://chrpr.net/data/relations")
	uri = URIRef("http://chrpr.com/data/" + data[0].encode('utf-8') + ".rdf")
	if data[1] == 'owl' and data[2] == 'sameas':
		namespaces = {
			"owl": Namespace("http://www.w3.org/2002/07/owl#")
		}
		curies = { "owl": "OWL" }
		relGraph.bind("owl", "http://www.w3.org/2002/07/owl#")
		relGraph.add([uri, namespaces['owl']['sameas'], URIRef(urlstr)])
		turtle = relGraph.serialize(format="turtle") 
		r2 = store.append_graph('http://chrpr.net/relations', turtle, 'turtle')	

def dbpmatch(entitySet):
	start = strftime("%a, %d %b %Y %H:%M:%S +0000", localtime())
	path = '/home/charper/store/dbpedia/'
	log = codecs.open('dbp-log.txt', 'a', encoding='utf-8')
	fuzzmatch = codecs.open('fuzzmatch.txt', 'w', encoding='utf-8')
	bestmatch = codecs.open('bestmatch.txt', 'w', encoding='utf-8')


	tokens = {}
	table = string.maketrans("","")

	for eid, entity in entitySet.iteritems():
		headid = eid
		tokens[headid] = []
		for heading in entity.metadata['lookup']:
		    #headid = line.split('|')[0]
		    wl = heading.replace('-','').split()
		    fwl = [w for w in wl if not w in stopwords.words('english')]
		    full = []
		    full.append(heading)
		    full.extend(fwl)
		    # print full
		    # Borrowed from here: http://stackoverflow.com/questions/5486337/stop-words-using-nltk-in-python
		    tokens[headid].append(full)

	    #tokens.append(full)

	#for t in tokens:
	#    print t


	counter = 0
	gcounter = 0
	match = 0
	nomatch = 0
	topfuzz = {}
	#with codecs.open(path + '500000_en.ttl', 'r', encoding='utf-8') as f:
	#fname = path + 'labels_en.ttl'
	fname = path + 'labels_en.ttl'
	with codecs.open(fname, 'r', encoding='utf-8') as f:
	    for next_n_lines in izip_longest(*[f] * 100000,  fillvalue="xxx"):
	        _file = StringIO.StringIO(next_n_lines)
	        #print file.read()
	        g = rdflib.Graph()
	        
	        #for line in next_n_lines:
	            #result = g.parse(next_n_lines, format='n3')
	        #    counter += 1
	            #print str(counter) + "|" + line
	            #while counter <= 1:
	                #result = g.parse(line, format='n3')
	        #        g.add(line)
	        #gcounter += 1
	        #print gcounter
	        #result = g.parse(_file.read(), format='n3')
	        for line in next_n_lines:
	            if line != 'xxx':
	                result = g.parse(data=line, format='n3')

	        #print len(g)
	        for stmt in g:
	            #head = stmt[2].encode('utf-8').translate(table, string.punctuation)
	            head = stmt[2]
	            wl = head.replace('-','').replace(',', '').split()
	            fwl = [w for w in wl if not w in stopwords.words('english')]
	            # Borrowed from here: http://stackoverflow.com/questions/5486337/stop-words-using-nltk-in-python
	            for headid, lookups in tokens.iteritems():
	                for t in lookups:
	                    #head = t[0]
	                    if len(set(fwl).intersection( set(t[1:]) )) > 0:
	                        ratio = fuzz.token_sort_ratio(str(fwl), str(t[1:]))
	                        if ratio > 85:
	                            #print str(stmt[2]) + " matches " + str(t[0]) + " fuzz: " + str(ratio)
	                            #printmatch = str(stmt[0]) + "|" + str(stmt[2]) + "|" + str(t[0]).rstrip() + "|" + str(ratio)
	                            printmatch = headid + "|" + stmt[0] + "|" + stmt[2] + "|" + t[0].rstrip() + "|" + str(ratio)
	                            matchdata = [[stmt[0], stmt[2], str(ratio)]]
	                            if headid not in topfuzz:
	                            	topfuzz[headid] = matchdata
	                            else: topfuzz[headid].append(matchdata)
	                            fuzzmatch.write(printmatch + "\n")
	                            print printmatch.encode('utf-8')
	                            match += 1
	                        else:
	                            nomatch += 1
	                        #print str(fwl) + " matches " + str(t)
	                        #match += 1
	                    else:
	                        nomatch += 1

	            #print stmt[2].encode('utf-8')
	        #for line in next_n_lines:
	        #for stmt in g:
	        #	counter += 1
	        #    print stmt
	        	#print str(gcounter) + "|" + str(counter) + "|" + line.encode('utf-8')
	        	# process next_n_lines

	end = strftime("%a, %d %b %Y %H:%M:%S +0000", localtime())

	store = HTTP4Store('http://localhost:8080')
	for headid, fuzzes in topfuzz.iteritems():
		print headid
		print fuzzes
		highest = 0
		for matched in fuzzes:
			
			#print "--".join(matched)
			
			if matched[2] > highest: 
				lead = matched[0]
				highest = matched[2]
		
		bestmatch.write(headid + "|" + "|" + lead + "|" + str(highest) + "\n")
		urlstr = lead.replace("/resource/", "/data/").encode('utf-8')
		url = urlopen(urlstr)
		raw = url.read().decode('utf-8')
		r = store.append_graph('http://chrpr.net/dbpedia', raw.encode('utf-8'), 'xml')
		relGraph = rdflib.Graph(identifier="http://chrpr.net/data/relations.rdf")
		uri = URIRef("http://chrpr.com/data/" + headid.encode('utf-8') + ".rdf")
		namespaces = {
			"owl": Namespace("http://www.w3.org/2002/07/owl#")
		}
		curies = { "owl": "OWL" }
		relGraph.bind("owl", "http://www.w3.org/2002/07/owl#")
		relGraph.add([uri, namespaces['owl']['sames'], URIRef(urlstr)])
		turtle = relGraph.serialize(format="turtle") 
		r2 = store.append_graph('http://chrpr.net/relations', turtle, 'turtle')

	print '{0} <-> {1}'.format(start, end)
	print 'No Match Count: ' + str(nomatch)
	print 'Match Count: ' + str(match)

	log.write(fname + "\n")
	log.write('{0} <-> {1}'.format(start, end) + "\n")
	log.write('No Match Count: ' + str(nomatch) + "\n")
	log.write('Match Count: ' + str(match) + "\n")
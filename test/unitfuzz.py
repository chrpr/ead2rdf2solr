import xml.etree.cElementTree as ET
import glob
import os
from fuzzywuzzy import fuzz
import codecs

path = ''

fuzzy = codecs.open('fuzz_matches.txt', 'w', encoding='utf-8')
logger = codecs.open('unittitle.log.txt', 'w', encoding='utf-8')
logger.write("filename|matchcount|nomatchcount|uttotal\n")

def gettext(elem):
	text = elem.text or ""
	#print text
	for subelem in elem:
		text = text.strip() + " " + gettext(subelem)
		if subelem.tail:
			text = text + subelem.tail.strip() + " "
	return text.strip() + " "

for f in glob.glob( os.path.join(path, '*.xml') ):
	matchflag = 0
	matchcount = 0
	nomatchcount = 0
	utcount = 0
	access = []
	tree = ET.ElementTree(file=f)
	for parent in tree.getiterator():
		#print "monkey"	
		for child in parent:
			if (parent.tag.replace('{urn:isbn:1-931666-22-9}','') == 'controlaccess' and
					child.tag.replace('{urn:isbn:1-931666-22-9}','') in [
                        'persname', 'subject', 'corpname', 'genreform', 'geogname', 'famname'
                    ]
                ):
				subfields = child.text.split("|")
				access.append([subfields[0], child.tag.replace('{urn:isbn:1-931666-22-9}','')])
			for subchild in child:
				if subchild.tag.replace('{urn:isbn:1-931666-22-9}','') == 'unittitle' and parent.tag.replace('{urn:isbn:1-931666-22-9}','') == 'c':
					ut = gettext(subchild)
					utcount += 1
					#var1 = 4 if var1 is None else var1
					level = "NoLevel" if "level" not in parent.attrib else parent.attrib["level"]
					utpath = (f + "|" + parent.tag.replace('{urn:isbn:1-931666-22-9}','') + "|" + 
						parent.attrib["id"] + "|" + level + "|" + 
						child.tag.replace('{urn:isbn:1-931666-22-9}','') + "|" + 
						subchild.tag.replace('{urn:isbn:1-931666-22-9}','') + "|" + ut)
					#print utpath
					for point in access:
						ratio = fuzz.token_sort_ratio(utpath, point[0])
						if ratio > 35:
							matchflag = 1
							print utpath.encode('utf-8') + "|" + point[1].encode('utf-8') + "|" + point[0].encode('utf-8') + "|" + str(ratio)
							fuzzy.write(utpath + "|" + point[1] + "|" + point[0] + "|" + str(ratio) + "\n")
					if matchflag == 1: matchcount += 1 
					elif matchflag == 0: nomatchcount += 1
	logger.write(f + "|" + str(matchcount) + "|" + str(nomatchcount) + "|" + str(utcount) + "\n")			

        	#work on parent/child tuple
        	#if child.tag.replace('{urn:isbn:1-931666-22-9}','') == 'unittitle':
        	#	print child + "|" + parent
	#parent_map = dict((c, p) for p in tree.getiterator() for c in p)
	#print parent_map


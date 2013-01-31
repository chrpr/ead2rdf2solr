from lxml import etree
import codecs
from utils import *
from configs import *
from entity import Entity
import glob
import os
import re

path = ''
if analyze == True:
	heads = codecs.open('headstrings2.txt', 'w', encoding='utf-8')
	heads2 = codecs.open('headscleaned2.txt', 'w', encoding='utf-8')
	pers = codecs.open('persnames2.txt', 'w', encoding='utf-8')
	corp = codecs.open('corpnames2.txt', 'w', encoding='utf-8')
	geo = codecs.open('geognames2.txt', 'w', encoding='utf-8')
	top = codecs.open('topics2.txt', 'w', encoding='utf-8')
	facets = codecs.open('facets2.txt', 'w', encoding='utf-8')

elements = []


for fn in glob.glob( os.path.join(path, '*.xml') ):
	root = etree.parse(fn)
	namespace = "{urn:isbn:1-931666-22-9}"

	_id = root.xpath('n:eadheader/n:eadid', namespaces={'n': 'urn:isbn:1-931666-22-9'})
	identifier = gettext(_id[0]) if gettext(_id[0]) != "" else fn.replace("-ead.xml", "").replace(".", "_").lower()
	archdesc = root.find('{0}archdesc'.format(namespace))
	for element in archdesc:

		## Nope, this is all wrong, but actually don't need it if I run this out of the ead from here on out, so let's start that shortly....
		## Also, have to redo my dbpedia shite because of, for example:
		## http://en.wikipedia.org/wiki/Vincent_R._Impellitteri

		'''

		This logic has been moved to "entity"

		First off, get rid of everything after the "--". 
		These are generally either a $$v or an unhelpful (and uncoded) persname subdivision.
		Save the rest into a nice "elements" array, and also write the output 

		'''
		tag = element.tag.replace(namespace, '')
		if tag == "controlaccess":
			for ca in element:
				catag = ca.tag.replace(namespace, '')
				catext = gettext(ca)
				#heads.write(catag + "|" + gettext(ca) + "\n")
				#print catag + "|" + gettext(ca).encode('utf-8')
				#catext = gettext(ca).split("--")[0]
				#elements.append(catag + "|" + catext)
				entity = Entity(catag, catext)
		if tag == "did":
			for dider in element:
				didtag = dider.tag.replace(namespace, '')
				if didtag == "origination":
					for name in dider:
						nametag = name.tag.replace(namespace, '')
						nametext = gettext(name)
						#print nametag + "|" + gettext(name).encode('utf-8')
						#heads.write(nametag + "|" + gettext(name) + "\n")
						#nametext = gettext(name).split("--")[0]
						#elements.append(nametag + "|" + nametext)
						entity = Entity(nametag, nametext)


#for element in elements:
#	print element.encode('utf-8')

'''
			for ca in element:
				catag = ca.tag.replace(namespace, '')
				if catag == "persname" or catag == "corpname":
					#print catag
					s = ca.get('source')
					text = re.sub(r' \|[A-Za-z] ', ' -- ', gettext(ca))
					#if s == 'lcsh':
					#	self.metadata[fieldrenamings[s]].extend(text.split(' -- '))
					#self.headinglist.append(text)
					#headroot = text.split(' -- ')[0].rstrip(".")
					#if headroot not in self.headrootlist: self.headrootlist.append(headroot)
					#need to redo this so it utilizes "field renamings"
					stringy = fn + "|" + identifier + "|" + tag + "|" + catag  + "|" + gettext(ca) + "\n"
					names.write(stringy)
					print stringy.encode('utf-8').rstrip()
					#self.metadata[fieldrenamings[tag][t][s]].append(text)
			'''

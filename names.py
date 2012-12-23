from lxml import etree
import codecs
from utils import *
import glob
import os
import re

path = ''
names = codecs.open('names.txt', 'w', encoding='utf-8')


for fn in glob.glob( os.path.join(path, '*.xml') ):
	root = etree.parse(fn)
	namespace = "{urn:isbn:1-931666-22-9}"

	_id = root.xpath('n:eadheader/n:eadid', namespaces={'n': 'urn:isbn:1-931666-22-9'})
	identifier = gettext(_id[0]) if gettext(_id[0]) != "" else fn.replace("-ead.xml", "").replace(".", "_").lower()
	archdesc = root.find('{0}archdesc'.format(namespace))

	for element in archdesc:
		tag = element.tag.replace(namespace, '')
		if tag == "controlaccess" or "origination":
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


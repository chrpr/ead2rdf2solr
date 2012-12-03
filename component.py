#import xml.etree.cElementTree as ET
from lxml import etree
import rdflib
import re

# This moves to "utils"
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

fieldrenamings = {
	'abstract': 'dct:abstract',
	'langmaterial': 'arch:langnote',
	'origination': { 'corpname': 'arch:corpcreator', 'persname': 'arch:perscreator' },
	'physdesc': 'dc:description',
	'physloc': 'arch:location',
	'unitdate': 'dc:date',
	'normal': 'arch:datenormal',
	'materialspec': 'arch:materialspec',
	'accessrestrict': 'arch:restrict',
	'arrangement': 'arch:arrange',
	'bibliography': 'arch:bibref',
	'bioghist': 'arch:bioghist',
	'controlaccess': { 
			'corpname': { 'ingest': 'arch:localcorp', 'local': 'arch:localcorp',
						'nad': 'arch:localcorp', 'naf': 'arch:lccorpname' },
			'genreform': { 'aat': 'arch:aat', 'lcsh': 'arch:lcgenre',
							'local': 'arch:localgenre' },
			'geogname': { 'lcsh': 'arch:lcgeo', 'local': 'arch:localgeo' },
			'persname': { 'ingest': 'arch:localpers', 'local': 'arch:localpers', 
							'nad': 'arch:localpers', 'naf': 'arch:lcpers' },
			'subject': { 'aat': 'arch:aatsub', 'lcsh': 'arch:lcsh', 
							'local': 'arch:localsub' },
			'famname': { 'local': 'arch:family', 'ingest': 'arch:family' },
			'occupation': { 'lcsh': 'arch:occupation' },
			'title': { 'lcsh': 'lctitle' }
		},
	'lcsh': 'arch:fast',
	'dao': 'arch:webarch',
	'relatedmaterial': 'arch:related',
	'scopecontent': 'arch:scope',
	'separatedmaterial': 'arch:sepmaterial',
	'userestrict': 'arch:restrict'
}

def procdid(xfrag):
	namespace = "{urn:isbn:1-931666-22-9}"
	md = {}

	#print "FragTag" + gettext(xfrag).encode('utf-8')
	for subelem in xfrag:
		#print "Subelem" + str(subelem)
		tag = subelem.tag.replace(namespace, '')
		#print "Tag" + tag
		if tag == "abstract": md[fieldrenamings[tag]] = gettext(subelem)
		if tag == "langmaterial":
			md[fieldrenamings[tag]] = gettext(subelem)
		if tag == "origination":
			for child in subelem:
				chitag = child.tag.replace(namespace, '')
				if chitag == "corpname": md[fieldrenamings[tag][chitag]] = gettext(child)
				if chitag == "persname": md[fieldrenamings[tag][chitag]] = gettext(child)
		if tag == "physdesc": md[fieldrenamings[tag]] = gettext(subelem)
		if tag == "physloc": md[fieldrenamings[tag]] = gettext(subelem)
		if tag == "unitdate":
			md[fieldrenamings[tag]] = gettext(subelem)
			#print subelem.attrib
			#if '{http://www.w3.org/1999/xlink}normal' in subelem.attrib:
			if'normal' in subelem.attrib:
				md[fieldrenamings['normal']] = subelem.get('normal')
		if tag == "materialspec": md[fieldrenamings[tag]] = gettext(subelem)

	
	return md

class Component(object):

	"""
	Defines record for EAD component part objects.
	Contains 3 constuctors: 
		- __init__, which generates from an XML fragment, an Ead object, and an optional parent Component Object
		- factory method to generate from RDF
		- factory method to generate from SPARQL queries
	Contains output methods for:
		- Import to 4store via SPARQL
		- Writing RDF to file
		- Writing SOLR Index entries
		- Stretch goal: Writing XML for Primo imput?
	"""

	def __init__(self,  xfrag, eadob, *args):
		"""Generates a component object from an xml fragment, an EAD object & option parent component"""
		#print fn
		namespace = "{urn:isbn:1-931666-22-9}"
		'''
		Refactoring this to use lxml...
		Play with:
		>>> r = doc.xpath('/t:foo/b:bar',
...               namespaces={'t': 'http://codespeak.net/ns/test1',
...                           'b': 'http://codespeak.net/ns/test2'})
		'''
		self.metadata = {}
		self.headinglist = []
		self.headrootlist = []
		#print ead.getroot()
		#print ead.getroot().find('{urn:isbn:1-931666-22-9}eadheader/{urn:isbn:1-931666-22-9}eadid')
		#for child in ead.getroot():
		#	print child.tag
		#self.identifier = gettext(ead.find(n + 'eadheader/' + n + 'eadid'))

		#First, get identifier
		#_id = ead.find('{0}eadheader/{0}eadid'.format(namespace))
		# okay, so after installing lxml and switching over, it actually makes very little difference.
		# Will leave lxml as my tool of choice, but keep using the findall & find methods for compatability with ElementTree...
		self.metadata['dc:identifier'] = xfrag.get('id')
		self.metadata['dc:type'] = xfrag.get("level")
		self.metadata['dct:title'] = gettext(xfrag.find('{0}did/{0}unittitle'.format(namespace)))
		self.metadata['arch:findingaid'] = eadob.metadata['arch:findingaid']
		self.metadata['arch:inCollection'] = eadob.metadata['dct:title']


		for element in xfrag:
			tag = element.tag.replace(namespace, '')

			if tag == "accessrestrict":
				self.metadata[fieldrenamings[tag]] = []
				for i in element.findall('{0}p'.format(namespace)):
					self.metadata[fieldrenamings[tag]].append(gettext(i))
			if tag == "arrangement":
				#self.metadata['Arrangement'] = [gettext(element, ignore=[namespace+"head"], newline=[namespace+"item", namespace+"p"])]
				self.metadata[fieldrenamings[tag]] = [gettext(element, ignore=[namespace+"head"], newline=[namespace+"item"])]

				'''
				Have modded the "gettext" method so it will optionally take a list of elements to strip. 
				Not sure if that approach is preferable here, or if collecting <p> & <list><item> tags 
				in separate instances of "Arrangement" is better approach. Latter is *closer* to keeping formating....
				I could also mod gettext so that <p> tags manifest as having a linebreak after them....
				Hah, this is kinda disgusting, but it actually now takes newline & ignore lists...
				Seems to be better than the approach below:
				self.metadata['Arrangement'] = []
				for i in element.findall('{0}list/{0}item'.format(namespace)):
					self.metadata['Arrangement'].append(gettext(i))
				for i in element.findall('{0}p'.format(namespace)):
					self.metadata['Arrangement'].append(gettext(i))
				'''
			if tag == "bibliography":
				self.metadata[fieldrenamings[tag]] = []
				for i in element.findall('{0}bibref'.format(namespace)):
					self.metadata[fieldrenamings[tag]].append(gettext(i, ignore=[namespace+"head"]))
			if tag == "bioghist":
				self.metadata[fieldrenamings[tag]] = [gettext(element)]
			if tag == "controlaccess":
				for ca in element:
					t = ca.tag.replace(namespace, '')
					s = ca.get('source')
					text = re.sub(r' \|[A-Za-z] ', ' -- ', gettext(ca))
					if s == 'lcsh':
						self.metadata[fieldrenamings[s]] = text.split(' -- ')
					self.headinglist.append(text)
					headroot = text.split(' -- ')[0].rstrip(".")
					if headroot not in self.headrootlist: self.headrootlist.append(headroot)
					#need to redo this so it utilizes "field renamings"
					self.metadata[fieldrenamings[tag][t][s]] = text
			if tag == 'dao':
				href = element.get('{http://www.w3.org/1999/xlink}href')
				self.metadata[fieldrenamings[tag]] = gettext(element) + ": " + href
			if tag == 'did':
				didmd = procdid(element)
				#print "Monkey" + str(didmd)
				self.metadata.update(didmd)
			if tag == "relatedmaterial":
				if element.xpath('//n:extref', namespaces={'n': 'urn:isbn:1-931666-22-9'}): 
					extref = element.xpath('//n:extref', namespaces={'n': 'urn:isbn:1-931666-22-9'})[0]
					href = extref.get('{http://www.w3.org/1999/xlink}href') if '{http://www.w3.org/1999/xlink}href' in extref else ""
				else:
					href = ""
				self.metadata[fieldrenamings[tag]] = gettext(element, ignore=[namespace+"head"], newline=[namespace+"item", namespace+"extref"]) + " " + href
				#root.xpath("//article[@type='news']")
			if tag == 'scopecontent':
				self.metadata[fieldrenamings[tag]] = gettext(element, ignore=[namespace+"head"])
			if tag == 'separatedmaterial':
				self.metadata["Separated Materials Note"] = gettext(element, ignore=[namespace+"head"])
			if tag == 'userestrict':
				if fieldrenamings[tag] not in self.metadata: self.metadata[fieldrenamings[tag]] = []
				self.metadata[fieldrenamings[tag]].append(gettext(element, ignore=[namespace+"head"]))

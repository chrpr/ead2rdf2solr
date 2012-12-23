from configs import *

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

	#print "FragTag" + gettext(xfrag).encode('utf-8')
	for subelem in xfrag:
		#print "Subelem" + str(subelem)
		tag = subelem.tag.replace(namespace, '')
		#print "Tag" + tag
		if tag == "abstract": md[fieldrenamings[tag]].append(gettext(subelem))
		if tag == "langmaterial":
			md[fieldrenamings[tag]].append(gettext(subelem))
			for subsub in subelem:
				if subsub.tag.replace(namespace, '') == 'language':
					md['dc:language'].append(subsub.get('langcode'))
		if tag == "origination":
			for child in subelem:
				chitag = child.tag.replace(namespace, '')
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

	
	return md
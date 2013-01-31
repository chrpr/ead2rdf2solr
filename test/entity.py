import re
import codecs
from utils import *
from types import *

heads = codecs.open('headstrings2.txt', 'a', encoding='utf-8')
heads2 = codecs.open('headscleaned2.txt', 'a', encoding='utf-8')
pers = codecs.open('persnames2.txt', 'a', encoding='utf-8')
corp = codecs.open('corpnames2.txt', 'a', encoding='utf-8')
geo = codecs.open('geognames2.txt', 'a', encoding='utf-8')
top = codecs.open('topics2.txt', 'a', encoding='utf-8')
facets = codecs.open('facets2.txt', 'a', encoding='utf-8')

class Entity(object):
	"""
	Defines Entity record objects.
	***TODO: Update docstrings!!! ***
	Contains 3 constuctors: 
		- __init__, which generates from EAD files
		- factory method to generate from RDF (Maybe)
		- factory method to generate from SPARQL queries (Maybe)
	Contains an "enrichment" method?
		- How's this actually going to work? Viaf, Fast & id.loc are easy
			because they work off the heading objects themselves.
			DBPedia's way harder, though, because of current fuzzmatch.py structure...
	Contains output methods for:
		- Import to 4store via SPARQL
		- Writing RDF to file
		- Writing SOLR Index entries
		- Stretch goal: Writing XML for Primo imput?
	"""

	def __init__(self, type, text, obj_dict="None", *args):
		"""
		Generates a candidate entity object from an access point
		Pre-processes text & checks to see if entity exists
		"""
		#heads2.write(type + "|" + text+ "\n")
		'''
		Move first-cut text processing from headings.py into here, & change the order of things.
		(Currently headings strips everything after the "--", which dumps |v from persname tags
		and removes uncoded subdivisions. Want to preserve the actual strings, though...)
		''' 
		heads.write(type + "|" + text + "\n")
		#print text.encode('utf-8')
		catext = text.split("--")[0]

		heads2.write(catext + "\n")
		headlist = catext.split("|")
		if type != "genreform":
			root = headlist[0]
			subs = headlist[1:]
			subfields = []
			for sf in subs:
				subfields.append([sf[0:1], sf[2:]])
			
			self.metadata = {}
			if type == "persname":
				#print catext
				# TamWag persnames have no subfields (except |v, which is already stripped)
				# This set of patterns grabs regular & ca. dates, but not b. & d. 
				#print catext.encode('utf-8')
				self.metadata['type'] = "person"
				self.label = catext
				if re.search('(b\. [0-9])', catext):
					#print "b"
					#print catext
					self.metadata['bdate'] = re.search('([0-9]{4})', catext).group(0).rstrip
					self.label = re.sub('b\. [0-9]{4}', '', self.label)
					#print self.label
				elif re.search('(d\. [0-9])', catext):
					#print "d"
					#print catext
					#print re.search('(d\. [0-9])', catext).group(0)
					self.metadata['ddate'] = re.search('([0-9]{4})', catext).group(0).lstrip
					self.label = re.sub('d\. [0-9]{4}', '', self.label)

				elif re.search('([0-9]{4}-)', catext):
					#print "range"
					self.metadata['bdate'] = re.search('([0-9]{4}-)', catext).group(0).rstrip('-')
					#if re.search('(-[0-9]{4})', catext):
					if re.search('(-[0-9]{4})', catext): self.metadata['ddate'] = re.search('(-[0-9]{4})', catext).group(0).lstrip('-')
					self.label = re.sub('[0-9]{4}-[0-9]{4}', '', self.label)
					self.label = re.sub('[0-9]{4}-', '', self.label)
				 
				#huh -- so it seems that these don't actually check for the attribute if I cluster all that if/else stuff above
				# but they did before?
				# either way, I should treat this a metadata hash regardless....
				#if self.bdate: print "Born: "# + self.bdate.group(0) 
				#.rstrip('-')
				#if self.ddate: print "Died: " + self.ddate.group(0) 
				#.lstrip('-')

				# Process parenthentical name expansions
				# Is full name or name with initial the "Label"? 
				# Probably need both for dbpedia lookup
				# 20130128 -- actually, I'm going to need multiple dbpedia lookup strings for other 
				# types, so best to generalize this as:
				# self.metadata["lookup"]   
				if re.search('(\(.*\))', self.label):
					self.metadata['fullname'] = re.sub('(,.*\()', ', ', self.label).rstrip('), .').encode('utf-8')
					self.label = re.sub('(\(.*\))', '', self.label)
				#Strip periods that aren't following middle initials:
				self.label = re.sub('(?<! [A-Z])\.', '', self.label)
				#Strip trailing right whitespace and commas:
				self.metadata["heading"] = catext.encode('utf-8')
				self.metadata["label"] = self.label.rstrip(', ').encode('utf-8')
				self.metadata["id"] = self.label.rstrip(', ').replace(' ', '_').encode('utf-8')
				self.metadata["lookup"] = [self.metadata["label"]]
				if "fullname" in self.metadata: self.metadata["lookup"].append(self.metadata["fullname"])
				#print "id: " + self.id.encode('utf-8')
				#print "label: " + self.label.encode('utf-8')
				#this now lives below processing:
				#for k, v, in self.metadata.iteritems():
					#print k + " is a " + type(v)
					#if type(v) == "str":
					#print "{0}: {1}".format(k, v)

			if type == "corpname":
				#print catext.encode('utf-8')
				self.metadata['type'] = "corporation"
				#self.label = catext
				self.label = root.rstrip()
				self.metadata["lookup"] = [self.label]
				for pair in subfields:
					k = pair[0]
					v = pair [1]
					if k == "d" or k == "y": 
						self.label += " " + v.replace('(', '').rstrip(" :).")
						if 'tempfacet' not in self.metadata: self.metadata['tempfacet'] = [v.replace('(', '').rstrip(" :).")]
						else: self.metadata['tempfacet'].append(v.replace('(', '').rstrip(" :)."))
						if self.label not in self.metadata["lookup"]: self.metadata["lookup"].append(self.label)
					if k == "c": 
						self.label += ", " + v.replace('(', '').rstrip(" :).")
						if 'geofacet' not in self.metadata: self.metadata['geofacet'] = [v.replace('(', '').rstrip(" :).")]
						else: self.metadata['geofacet'].append(v.replace('(', '').rstrip(" :)."))
						if self.label not in self.metadata["lookup"]: self.metadata["lookup"].append(self.label)

					if k == "x":
						if 'topicfacet' not in self.metadata: self.metadata['topicfacet'] = [v.replace('(', '').rstrip(" :).")]
						else: self.metadata['topicfacet'].append(v.replace('(', '').rstrip(" :)."))
						if self.label not in self.metadata["lookup"]: self.metadata["lookup"].append(self.label)
				self.metadata['label'] = self.label.rstrip(', ').encode('utf-8')
				self.metadata['id'] = self.label.rstrip(', ').replace(' ', '_').encode('utf-8')
				'''
				Alright, this block's a little weird:
				First off, I need to generalize it so there's a list in configs.py that is maybe relevant to your data patterns.
				Hard coding NY and New York, NY in here doesn't make sense...

				Also, right now, where I've got a parenthetical AND New York, NY, I don't get a version in lookup that strips both...

				'''
				if re.search('(\(.*\))', self.label):
					noparens = re.sub('(\(.*\) )', '', self.label)
					self.metadata['lookup'].append(noparens.encode('utf-8'))
					if "New York, N.Y." in noparens:
						self.metadata['lookup'].append(re.sub('New York, N.Y.', '', noparens).rstrip(", ").encode('utf-8'))
					if "N.Y." in noparens:
						self.metadata['lookup'].append(re.sub('N.Y.', '', noparens).rstrip(", ").encode('utf-8'))

				if "New York, N.Y." in self.label:
					self.metadata['lookup'].append(re.sub('New York, N.Y.', '', self.label).rstrip(", ").encode('utf-8'))
				if "N.Y." in self.label:
					self.metadata['lookup'].append(re.sub('N.Y.', '', self.label).rstrip(", ").encode('utf-8'))

			if type == "subject":
				#print catext.encode('utf-8')
				self.metadata['type'] = "topic"
				#self.label = catext
				self.label = root.rstrip()
				self.metadata["lookup"] = [self.label]
				for pair in subfields:
					k = pair[0]
					v = pair [1]
					#print k
					'''
					okay, so topic subfields:     4  
					      1 d
					      1 g
					      1 t
					    350 v
					   1211 x
					      1 X
					    145 y
					   3909 z
					      2 Z
					Alot of these are super broken, so if it isn't a x, y or z, toss it.
					Though maybe I actually want that $t, $g, $d, which is a misformulated treaty heading:
					Germany. |t Treaties, etc. |g Soviet Union, |d 1939 Aug. 23.
					Which is actually this. Do I want to hardcode that shit? Again, a config file of overrides 'd be nice...
					For now, I'm ignoring...
					But it's worth noting that for dbpedia lookups there's a lot of other places where a manual override would be usefull:
					      1 label: Textile Workers' Strike, Gastonia, N.C., 1929. is actually the Loray Mill Strike in Wiki/Dbpedia
					'''
					if k == 'y': 
						#self.label += " " + v.replace('(', '').rstr	ip(' :).'')
						if 'tempfacet' not in self.metadata: self.metadata['tempfacet'] = [v.replace('()', '').rstrip(" :).")]
						else: self.metadata['tempfacet'].append(v.replace('()', '').rstrip(':).'))
						if self.label not in self.metadata['lookup']: self.metadata['lookup'].append(self.label)
						# regex checks if value has anything other than straight dates, numbers.
						if  re.search('([^0-9-.])', v) and 'century' not in v:
							self.label += " " + v.replace('()','').rstrip(' .')
							self.metadata['lookup'].append(self.label)
							self.metadata['lookup'].append(v)							
							#print v
					if k == 'z':
						if 'geofacet' not in self.metadata: self.metadata['geofacet'] = [v.replace('()', '').rstrip(" :).")]
						else: self.metadata['geofacet'].append(v.replace('()', '').rstrip(" :)."))
					if k == 'x':
						if 'topicfacet' not in self.metadata: self.metadata['topicfacet'] = [v.replace('()', '').rstrip(" :).")]
						else: self.metadata['topicfacet'].append(v.replace('()', '').rstrip(" :)."))
						if re.search('([0-9]{4})', v):
							self.label += " " + v
							self.metadata['lookup'].append(self.label + v)
							self.metadata['lookup'].append(v)



				self.metadata['label'] = self.label.rstrip(', ').encode('utf-8')
				self.metadata['id'] = self.label.rstrip(', ').replace(' ', '_').encode('utf-8')

			if type == "geogname":
				#print catext.encode('utf-8')
				self.metadata['type'] = "place"
				#self.label = catext
				self.label = root.rstrip()
				self.metadata["lookup"] = [self.label]
				for pair in subfields:
					k = pair[0]
					v = pair [1]
					
					if k == 'y': 
						#self.label += " " + v.replace('(', '').rstr	ip(' :).'')
						if 'tempfacet' not in self.metadata: self.metadata['tempfacet'] = [v.replace('()', '').rstrip(" :).")]
						else: self.metadata['tempfacet'].append(v.replace('()', '').rstrip(':).'))
						if self.label not in self.metadata['lookup']: self.metadata['lookup'].append(self.label)
						# regex checks if value has anything other than straight dates, numbers.
						if  re.search('([^0-9-.])', v) and 'century' not in v:
							self.label += " " + v.replace('()','').rstrip(' .')
							self.metadata['lookup'].append(self.label)
							self.metadata['lookup'].append(v)
							#print v
					if k == 'z':
						if 'geofacet' not in self.metadata: self.metadata['geofacet'] = [v.replace('()', '').rstrip(" :).")]
						else: self.metadata['geofacet'].append(v.replace('()', '').rstrip(" :)."))
					if k == 'x':
						if 'topicfacet' not in self.metadata: self.metadata['topicfacet'] = [v.replace('()', '').rstrip(" :).")]
						else: self.metadata['topicfacet'].append(v.replace('()', '').rstrip(" :)."))
						if re.search('([0-9]{4})', v):
							self.label += " " + v
							self.metadata['lookup'].append(self.label)
							self.metadata['lookup'].append(v)



				self.metadata['label'] = self.label.rstrip(', ').encode('utf-8')
				self.metadata['id'] = self.label.rstrip(', ').replace(' ', '_').encode('utf-8')
			
			#printing out all the metadatas to screen.
			#if 'type' in self.metadata and self.metadata['type'] == "place":
		
			print catext.encode('utf-8')
			for k, v, in self.metadata.iteritems():
				#print k + " is a " + type(v)
				#if type(v) == "str":
				print "{0}: {1}".format(k, v)
			
			'''

			20130129: Okay, is the note below meaningful? If not, then...
			Now is where logic *really* get's tricky. I've now got my fields parsed & ready.
			I could push to 4store now.
			Next steps:
				-Track whether a *label* is new. Add a metadata field that has source "record", append (multival)
				- Make sure we've built output correctly, probably by writing these to Turtle first.
				- Add the solr-izers & triplifiers (4store & ttl both)
				- Run all day tomorrow? 
				- Then... incorporate all the lookups -- separate augment routine called once matches found?
					- do lookups against id, viaf, fast, add triples for these
					- (add properties to serialization methods, too....)
					- go through dbpedia labels, get scored matches into 4store
					- REVIEW
					- incoprorate the dbpedia expands to flesh out data points....

				- Rethink *final* data flow questions....

			Okay, this is where business logic gets tricky:
				- first element of headlist is root
				- remaining elements go in a subs dict coded by type:
					but it's not really a dict because elements have to be repeatable!
					so it's really an ordered list of typed things?
					Yep, that's the way to do this:
						- subhead obj w/ type / value pairs
						- Actually, maybe this is just an array of tuples?
			stupid whitespace
			'''
			self.root = root.rstrip()

			facets.write("root|" + root.rstrip() + "\n")
	#		for facet in headlist:
			for facet in subfields:
				if facet[0] != 'v':
					facets.write(facet[0] + "|" + facet[1].rstrip() + "\n")
			if type == "persname":
				pers.write(catext + "\n")
			if type == "corpname":
				corp.write(catext + "\n")
			if type == "geogname":
				geo.write(catext + "\n")
			if type == "subject":
				top.write(catext + "\n")




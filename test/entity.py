import re
import codecs
from configs import *
from utils import *
from types import *

if analyze == True:
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
			Thought init took: 	self, type, text, obj_dict="None", *args
			But prob don't need dict or args, instead adding:
			 * source (which I'm going to move to "vocab")
			 * Source tag (TODO: which I'll maybe 
			 	associate with "reverse property" creatorOf, subjectOf)

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

	def __init__(self, type, text, vocab):
		"""
		Generates a candidate entity object from an access point
		Pre-processes text & checks to see if entity exists
		"""
		if analyze == True: heads.write(type + "|" + text + "\n")
		catext = text.split("--")[0]

		if analyze == True: heads2.write(catext + "\n")
		headlist = catext.split("|")
		## 20130202: Code pulled from ead.py:
		## TODO: Refine this:
		self.headings = [re.sub(r' \|[A-Za-z] ', ' -- ', text)]
		self.collections = []

		## Wait, maybe I don't even need this?
		if type != "genreform" and type != "famname" and type != "occupation" and type != "title":
			root = headlist[0]
			subs = headlist[1:]
			subfields = []
			for sf in subs:
				subfields.append([sf[0:1], sf[2:]])
			
			self.metadata = {}

			if type == "persname":
				# TamWag persnames have no subfields (except |v, which is already stripped)
				# This set of patterns grabs regular & ca. dates, but not b. & d. 
				self.metadata['type'] = "person"
				self.label = catext
				if re.search('(b\. [0-9])', catext):
					self.metadata['bdate'] = re.search('([0-9]{4})', catext).group(0).rstrip()
					self.label = re.sub('b\. [0-9]{4}', '', self.label)
				elif re.search('(d\. [0-9])', catext):
					self.metadata['ddate'] = re.search('([0-9]{4})', catext).group(0).lstrip()
					self.label = re.sub('d\. [0-9]{4}', '', self.label)
				elif re.search('([0-9]{4}-)', catext):
					self.metadata['bdate'] = re.search('([0-9]{4}-)', catext).group(0).rstrip('-')
					if re.search('(-[0-9]{4})', catext): self.metadata['ddate'] = re.search('(-[0-9]{4})', catext).group(0).lstrip('-')
					self.label = re.sub('[0-9]{4}-[0-9]{4}', '', self.label)
					self.label = re.sub('[0-9]{4}-', '', self.label)
			 
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

			if type == "corpname":
				self.metadata['type'] = "corporation"
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
				Alright, this next block's a little weird:
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
				self.metadata['type'] = "topic"
				self.label = root.rstrip()
				self.metadata["lookup"] = [self.label]
				for pair in subfields:
					k = pair[0]
					v = pair [1]
					if k == 'y': 
						#why's this commented again?
						#self.label += " " + v.replace('(', '').rstr	ip(' :).'')
						if 'tempfacet' not in self.metadata: self.metadata['tempfacet'] = [v.replace('()', '').rstrip(" :).")]
						else: self.metadata['tempfacet'].append(v.replace('()', '').rstrip(':).'))
						if self.label not in self.metadata['lookup']: self.metadata['lookup'].append(self.label)
						# regex checks if value has anything other than straight dates, numbers.
						if  re.search('([^0-9-.])', v) and 'century' not in v:
							self.label += " " + v.replace('()','').rstrip(' .')
							self.metadata['lookup'].append(self.label)
							self.metadata['lookup'].append(v)							
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
				self.metadata['type'] = "place"
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
			#TODO: THIS GOES AWAY SOON
			'''
			print catext.encode('utf-8')
			for k, v, in self.metadata.iteritems():
				#print k + " is a " + type(v)
				#if type(v) == "str":
				print "{0}: {1}".format(k, v)
			'''

			if analyze == True: 
				self.root = root.rstrip()
				facets.write("root|" + root.rstrip() + "\n")
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




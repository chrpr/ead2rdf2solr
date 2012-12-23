import re
import codecs
from utils import *

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
		catext = text.split("--")[0]

		heads2.write(text + "\n")
		headlist = text.split("|")
		if type != "genreform":
			root = headlist[0]
			subs = headlist[1:]
			subfields = []
			for sf in subs:
				subfields.append([sf[0:1], sf[2:]])

			#if type == "persname":
				# TamWag persnames have no subfields (except |v, which is already stripped)


			'''
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
				pers.write(text + "\n")
			if type == "corpname":
				corp.write(text + "\n")
			if type == "geogname":
				geo.write(text + "\n")
			if type == "subject":
				top.write(text + "\n")




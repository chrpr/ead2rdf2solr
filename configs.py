analyze = False
components = False

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
			'title': { 'lcsh': 'arch:lctitle' }
		},
	'lcsh': 'arch:fast',
	'dao': 'arch:webarch',
	'relatedmaterial': 'arch:related',
	'scopecontent': 'arch:scope',
	'separatedmaterial': 'arch:sepmaterial',
	'userestrict': 'arch:restrict'
}

solrfields = {
	'dc:identifier': 'id',
	'dc:type': 'format',
	'dct:title': 'title_t', #also hard-coded mapping to title_display
	'arch:findingaid': 'url_suppl_display',
	'dct:abstract': 'abstract_t',
	'arch:langnote': 'language_t',
	'arch:corpcreator': 'author_t', #also hard-coded mapping to author_display
	'arch:perscreator': 'author_t', #also hard-coded mapping to author_display
	'dc:description': 'indexer_t',
	'arch:location': 'location_t',
	'dc:language': 'language_facet',
	'dc:date': 'date_t',
	'arch:datenormal': 'TODO', #was pub_date, but breaks validation?
	'arch:materialspec': 'indexer_t',
	'arch:restrict': 'TODO',
	'arch:arrange': 'TODO',
	'arch:bibref': 'bibref_t',
	'arch:bioghist': 'indexer_t',
	'arch:localcorp': 'subject_topic_facet', 
	'arch:lccorpname': 'subject_topic_facet',
	'arch:aat': 'subject_topic_facet', 
	'arch:lcgenre': 'subject_topic_facet',
	'arch:localgenre': 'subject_topic_facet',
	'arch:lcgeo': 'subject_geo_facet', 
	'arch:localgeo': 'subject_geo_facet',
	'arch:localpers': 'subject_topic_facet',
	'arch:lcpers': 'subject_topic_facet',
	'arch:aatsub': 'subject_topic_facet',
	'arch:lcsh': 'subject_topic_facet', 
	'arch:localsub': 'subject_topic_facet',
	'arch:family': 'TODO',
	'arch:occupation': 'TODO',
	'arch:lctitle': 'TODO',
	'arch:fast': 'subject_topic_facet',
	'arch:webarch': 'url_suppl_display',
	'arch:related': 'related_t',
	'arch:scope': 'indexer_t',
	'arch:sepmaterial': 'related_t',
	'arch:hasComponent': 'haspart_t',
	'arch:inCollection': 'ispartof_t',
	'arch:hasParent': 'ispartof_t'
}
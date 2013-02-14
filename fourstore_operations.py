from HTTP4Store import HTTP4Store

class FourstoreOperations(object):
	def __init__(self, endpoint = 'http://localhost:8080'):
		self.store = HTTP4Store(endpoint)
		self.sameas_query = "SELECT ?o WHERE {{ <{0:s}><http://www.w3.org/2002/07/owl#sameas> ?o }}"
		self.dbp_query = "SELECT ?o WHERE {{ <{0}><{1}> ?o FILTER langMatches( lang(?o), \"EN\" )}}"

	"""
	Encapsulates the resolution of a URI into an array of URIs that are owl:sameAs the input URI
	data URIs are converted to resource URIs in the result
	"""
	def sameAsObj(self, uri):
		q = self.sameas_query.format(uri)
		response = self.store.sparql(q)
		sameAs = []
		for data in response:
			resource = data[u'o'].replace('/data/', '/resource/')
			if resource not in sameAs: sameAs.append(resource)
		return sameAs

	"""
	Persists a graph to 4Store
	"""
	def store(self, graph):
		turtle = graph.serialize(format="turtle")
		#print turtle
		r =  self.store.append_graph("http://chrpr.net/data/entity", turtle, "turtle")

	"""
	Encapsulates the resolution of a property to the English-language value
	"""
	def dbpField(self, sub, prop):
		#sub = sub.replace('/data/', '/resource/')
		q = self.dbp_query.format(sub, prop)
		print q
		response = self.store.sparql(q)
		propData = []
		for data in response:
			prop = data[u'o'].rstrip('@EN').strip('"')
			if prop not in propData: propData.append(prop)
		return propData	


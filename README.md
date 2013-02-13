ead2rdf2solr
=========

A first release of some code that manages a modified BlackLight
SOLR full of dis-aggregated EAD collections & components, including
records for the "Entities" described in either origination or
controlaccess elements of the ead. Enriches these entities with
data from DBPedia, and soon VIAF, id.loc.gov, fast & others. Stores
this heterogeneous data in 4store, then appends at SOLRization stage
using SPARQL. Also contains functionality for generating .ttl files
for use with content negotiation.


Installation
------------

See ```requirements.txt``` for a list of library dependencies.  You
can use this to bootstrap your environment with virtualenv like this
(presuming you already have virtualenv):

```
% git clone https://github.com/chrpr/ead2rdf2solr.git
% virtualenv --no-site-packages ENV
(ENV)% source ENV/bin/activate
(ENV)% pip install -r requirements.txt
```


Usage
--------

Look for usage instructions & some examples here soon. For now,
there's a single command line script (ead2rdf.py) that manages a
variety of transformations. Among the first issues I want to tackle
is getting this into an argument driven format, rather than the
commenting out various chunks for running different sub-processes.


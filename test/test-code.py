import os
import glob

path = ''
#iterate through files
for f in glob.glob( os.path.join(path, '*.xml') ):
	print f
	print path
	print "WTF"
old_matches = open('old_matches.txt')
d = {}

for line in old_matches:
	#print line
    l = line.split("|")
    # or is it better to do this as d[str(l[0:5])] = l[5]?...
    # d[str(l[0:4])] = {l[4]: l[5]}
    # Better still, use "|".join(l[0:5])
    # d[str(l[0:5])] = l[5]
    d["|".join(l[0:5])] = l[5] 
print d
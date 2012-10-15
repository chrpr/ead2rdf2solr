import xml.etree.cElementTree as ET
#from lxml import etree
tree = ET.ElementTree(file='C:\EAD for Corey\EAD for Corey\PHOTOS.223-ead.xml')
f = open('C:\EAD for Corey\PHOTOS.223.out.txt', 'w')
"""
PHOTOS.151-ead.xml')

Biggest: PHOTOS.223-ead.xml

root = tree.getroot()
print root

for elem in tree.iter():


from xml.etree.ElementTree import ElementTree
"""
root = tree.getroot()

def print_abs_path(root, path=None):
    if path is None:
        path = [root.tag]

    for child in root:
        #text = child.text.strip()
        text = child.text
        new_path = path[:]
        new_path.append(child.tag)
        #print new_path
        if text:
            text = child.text.strip()
            #print '/{0}, {1}'.format('/'.join(new_path), text)
            print '/{0}'.format('/'.join(new_path).replace('{urn:isbn:1-931666-22-9}',''))
            f.write('/{0}\n'.format('/'.join(new_path).replace('{urn:isbn:1-931666-22-9}','')))

        print_abs_path(child, new_path)

print_abs_path(root)
f.close()
"""

for Node in tree.xpath('//*'):
    if not Node.getchildren() and Node.text:
        print XMLDoc.getpath(Node), Node.text
        """
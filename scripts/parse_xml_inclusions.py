# Libxml
#The 4Suite XML library for Python <http://4suite.org/> has an option to resolve XIncludes when parsing. 
from lxml import etree


with open("/Users/jgarra/sandbox/nalms-resources/examples/test_config_top.xml", "r") as data:
    tree = etree.parse(data)
    tree.xinclude()
    print(etree.tostring(tree.getroot()))
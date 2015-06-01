Xml Info
========

Library for creating an class structure to interpret information in an XML file.


Summary
-------

I often have a need to interpret and XML file and I want to create a set of
classes to represent the XML objects.  This library aims to be a general use
library for creating a class structure to map on top of the structure of an
XML file.


Glossary
--------

  - **Parsed XML Object**: This is an object returned by xml parsing library
    (xml.dom.minidom) while parsing the XML file.
  - **XML Info Ojbect**: This is an object in your project, subclassed from
    XmlInfoObject, to act as a wrapper to the Parsed XML Object.


Typical Usage
-------------

The primary use of this library is to subclass the XmlInfoObject.  It should
allow you the developer to concentrate on describing the expected structure of
the XML file.

You should override:

 - quick_wrap_xml_element() or wrap_xml_element()
 - quick_wrap_xml_text() or wrap_xml_text()
 - \_\_str\_\_() to describe this info element in the xml_str_path
 - info_name property if you want to retrieve this XmlInfo object from
   its parent by name.  Must be unique withing parent's children.
 - info_path property if you want to retrieve this XmlInfo object from
   the entire document.  Must be unique across all XmlInfo objects for this file
   
   
XML Parsing Procedure
---------------------

 1) Create a class to represent the XML file as a whole, subclassed from
    XmlInfo.  In the \_\_init\_\_(), call self._parse_xml_file(path) to get the
    parsed xml object for the document.  Then, pass this to the parent init
    as xml_node
    
     class MyXmlFile(XmlInfo):
         def __init__(self, path):
             doc_node = self._parse_xml_file(path)
             super(MyXmlFile, self).__init__(xml_node=doc_node)
             
 2) XmlInfo will call .\_discover\_xml\_elements() internally to process each
    of the discovered XML child nodes, which will in turn call the wrap_*()
    methods to give each XmlInfo object a chance to specify how to wrap the
    XML children.
    
    _discover_xml_elements()
    |
    |-- _handle_discovered_child_xml_element()
    |   `-- wrap_xml_element()
    |       `-- quick_wrap_xml_element()
    |
    `-- _handle_discovered_child_xml_text()
        `-- wrap_xml_text()
            `-- quick_wrap_xml_text()
            
  
            
            
            
             
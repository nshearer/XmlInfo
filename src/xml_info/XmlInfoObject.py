from abc import ABCMeta, abstractmethod, abstractproperty
import weakref

import xml.dom.minidom

class UnkownXmlElement(Exception):
    def __init__(self, parent, tag):
        msg = "No object provided to wrap element <%s> under %s"
        msg = msg % (tag, parent.xml_str_path)
        super(UnkownXmlElement, self).__init__(msg)
        

class UnkownXmlText(Exception):
    def __init__(self, parent, text):
        msg = "No object provided to wrap text '%s' under %s" 
        msg = msg % (text.strip(), parent.xml_str_path)
        super(UnkownXmlText, self).__init__(msg)
        

class DuplicateInfoNameError(Exception):
    def __init__(self, parent, name):
        msg = "Two elements have used name '%s' in %s" % (name,
                                                        parent.xml_str_path)
        super(DuplicateInfoNameError, self).__init__(msg)


class MissingXmlAttr(Exception):
    def __init__(self, info_obj, attr_name):
        msg = "Xml Element %s is missing a required element '%s'"
        msg = msg  % (info_obj.xml_str_path, attr_name)
        super(MissingXmlAttr, self).__init__(msg)


class XmlInfoObject(object):
    '''An object that wraps XML information'''
    __metaclass__ = ABCMeta
    
    IGNORE = 'IGNORED'
    
    def __init__(self, xml_node=None, xml_text=None, parent_info_obj=None):
        self._xml_node = xml_node
        self._xml_text = xml_text
        if xml_node is None and xml_text is None:
            raise Exception("Specify xml_node or xml_text")
        if xml_node is not None and xml_text is not None:
            raise Exception("Specify only one of xml_node or xml_text")
        self._info_children = list()
        self.__parent = None
        if parent_info_obj is not None:
            self.__parent = weakref.ref(parent_info_obj)
        if self._xml_node is not None:
            self._discover_xml_elements()
        
        
    @property
    def xml_element(self):
        return self._xml_node
       
       
    @property
    def is_text(self):
        return self._xml_text is not None
    
    
    @property
    def is_element(self):
        return self._xml_node is not None
    
    @property
    def xml_text(self):
        if not self.is_text:
            cname = self.__class__.__name__
            raise Exception('%s.is_text only meant for XML Text' % (cname))
        return self._xml_text
    
    
    @property
    def info_name(self):
        '''Optional name to identify this info object amongst siblings'''
        return None
    
    
    @property
    def info_path(self):
        '''Optional name to identify this info object in document'''
        return None
    
    
    @property
    def xml_str_path(self):
        '''Describe the locating of this parsed XML object within the document'''
        path = list()
        for info_obj in self.xml_info_path:
            path.append(str(info_obj))
        return '.'.join(path)
    
    
    @property
    def parent(self):
        if self.__parent is None:
            return None
        return self.__parent()  # Dereference weakref.  Will be None parent
                                # deleted (should not happen as all children
                                # hang off root under _info_children).
        
    
    @property
    def xml_info_path(self):
        '''List of info objects from root to this info object'''
        path = list(reversed(list(self.rev_xml_info_path)))
        path.append(self)
        return path
        
        
    @property
    def rev_xml_info_path(self):
        '''List of info objects starting with parent to root'''
        parent = self.parent
        while parent is not None:
            yield parent
            parent = parent.parent
    
    
    def __str__(self):
        if self.is_element:
            return '<' + self._xml_node.tagName + '>'
        else:
            return 'text'
    
    
    @property
    def get_root_info(self):
        '''Get highest level info object (info object with no parent)'''
        root = self
        while True:
            if root.parent is None:
                return root
            else:
                root = root.parent
            
    
    # Static method
    def _prase_xml_file(self, path):
        xml_file = xml.dom.minidom.parse(path)
        xml_doc = xml_file.documentElement
        return xml_doc
    
    
    # XML Object discovery
    def _discover_xml_elements(self):
        '''Interpret XML and create SourceSegment objects to represent source'''
        accum_text = None
        
        for child in self.xml_element.childNodes:
            # print child.__class__.__name__, str(child)
            
            # <elements>
            if child.nodeType == child.ELEMENT_NODE:
                # Process any accumulated text
                if accum_text is not None:
                    self._handle_discovered_child_xml_text(accum_text)
                    accum_text = None
                # Process element
                self._handle_discovered_child_xml_element(child.tagName, child)
                
            # Text
            elif child.nodeType == child.TEXT_NODE:
                if accum_text is None:
                    accum_text = child.data
                else:
                    accum_text += child.data
                    
            else:
                print "ERROR: I don't know what an XML %s is" % (child.nodeType)
                    
        # Consume any trailing text
        if accum_text is not None:
            self._handle_discovered_child_xml_text(accum_text)
            accum_text = None
        
        
    def _handle_discovered_child_xml_element(self, tag, element):
        '''Handle any element found in the XML as a child to this XML node
        
        Wrapped elements should be placed into _info_children
        
        @param tag: Name of the element tag
        @param element: Parsed XML Object
        '''
        try:
            info_obj = self.wrap_xml_element(tag, element)
            if info_obj is not None:
                self._info_children.append(info_obj)
        except UnkownXmlElement, e:
            print "WARNING:", str(e)
                    
        
    def _handle_discovered_child_xml_text(self, text):
        '''Handle text discovered as a child to this XML Node
        
        Because text can be split into multiple nodes, _discover_xml_elements()
        accumulates consecutive text nodes and extracts the text, passing
        all text to this method at once.
        
        Wrapped text objects should be placed into _info_children
        
        @param text: Text extracted from child XML Nodes
        ''' 
        try:
            info_obj = self.wrap_xml_text(text)
            if info_obj is not None:
                self._info_children.append(info_obj)
        except UnkownXmlText, e:
            print "WARNING:", str(e)        
        
        
    # -- Parsed XML Object Wrapping into XmlInfo Objects ----------------------
        
    def wrap_xml_element(self, tag, element):
        '''Wrap the element in a SourceSegment object
        
        (Override this if special class initialization is required, else 
        override quick_wrap_xml_element)
        
        @param tag: Tag name (string) of XML element discovered
        @param element: XML element object discovered
        @param db: Section DB to add children to
        '''
        info_class = self.quick_wrap_xml_element(tag, element)
        if info_class is not None and info_class != self.IGNORE:
            return info_class(xml_node=element, parent_info_obj=self)
        elif info_class != self.IGNORE:
            raise UnkownXmlElement(self, tag)


    def quick_wrap_xml_element(self, tag, element):
        '''Return the class to use to wrap XML element
        
        @param tag: Tag name (string) of XML element discovered
        @param element: XML element object discovered
        @return: Class subclassed from SourceSegment or 'IGNORED'
        '''
        return None

        

    def wrap_xml_text(self, text):
        '''Wrap the element in a SourceSegment object
        
        @param text: Text extracted from XML
        '''
        info_class = self.quick_wrap_xml_text(text)
        if info_class is not None and info_class != self.IGNORE:
            return info_class(xml_text=text, parent_info_obj=self)
        elif info_class != self.IGNORE:
            raise UnkownXmlText(self, text)
    
    
    def quick_wrap_xml_text(self, text):
        '''Return the class to use to wrap the given XML text
        
        @param text: Text extracted from XML
        @return: Class subclassed from SourceSegment or 'IGNORED'
        '''
        return None
    
    
    # -- Finding other info objects ------------------------------------------
        
        
    def get_children(self):
        '''Return all child info objects to this one'''
        return self._info_children[:]
    
    
    def get_all_children(self):
        '''Return all children recursively'''
        for child in self.get_children():
            yield child
            for grand_child in child.get_all_children():
                yield grand_child

            
    def get_child(self, name, required=False):
        '''Find a child object by it's .info_name property'''
        for child in self._info_children:
            if child.info_name == name:
                return child
        if required:
            msg = "%s (%s) does not have a child info object named '%s'"
            msg = msg % (self.__class__.__name__,
                        self.xml_str_path,
                        name)
            raise IndexError(msg)
    
    
    def has(self, name):
        '''Check to see if a child object exists with .info_name property'''
        return self.get_child(name, required=False) is not None 
    
    
    def get_info_by_path(self, info_path):
        '''Find an info object by it's info_path property'''
        
        
    # -- Accessing XML Properties ---------------------------------------------
    
    def get_xml_attr(self, name, required=False):
        if self.is_element:
            if self._xml_node.hasAttribute(name):
                return self._xml_node.getAttribute(name)
        if required:
            raise MissingXmlAttr(self, name)
        
    
    

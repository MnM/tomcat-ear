import os, shutil
import zlib
from zipfile import ZipFile
from xml.dom.minidom import parseString

def p_not_empty_text_node(node):
    return not (node.nodeType == node.TEXT_NODE and len(node.data.strip()) == 0)

def text(nodelist):
    return ''.join([node.data
                    for node in filter(p_not_empty_text_node, nodelist)])

def first_text(nodelist, default=None):
    try:
        return text(nodelist[0].childNodes)
    except IndexError as e:
        if default != None:
            return default
        else:
            raise e

def children(node, tagname=None):
    """Ignores text nodes containing only whitespace. If tagname is
    given, this function calls getElementsByTagName on the given node
    instead."""
    if not tagname:
        return filter(p_not_empty_text_node, node.childNodes)
    else:
        return node.getElementsByTagName(tagname)

def text_child1(node, tagname, default=None):
    return first_text(children(node, tagname), default)

def crc32(filename):
    "http://stackoverflow.com/questions/1742866/compute-crc-of-file-in-python"
    prev = 0
    for eachLine in open(filename,"rb"):
        prev = zlib.crc32(eachLine, prev)
    return prev & 0xFFFFFFFF

class ZipMember(object):
    def __init__(self, zipinfo):
        self.assign_zipinfo(zipinfo)

    def assign_zipinfo(self, zipinfo):
        """Method for assigning zipinfo objects after this object has
        been created. Useful for classes inheriting from this."""
        self.filename = zipinfo.filename
        self.basename = os.path.basename(self.filename)
        self.crc = zipinfo.CRC

    def __repr__(self):
        return self.basename

class Ear(object):
    application_xml_path = 'META-INF/application.xml'

    def __init__(self, ear_path):
        self.ear = ZipFile(ear_path)
        bad_files = self.ear.testzip()
        if bad_files:
            raise Exception("EAR is corrupt: %s" % bad_files)

        self.__application = self.__parse_application_xml()
        self.modules = self.__application.modules

        # scan library-dir for libraries
        self.libraries = map(ZipMember,
            filter(lambda x: x.filename.endswith('.jar') and
                   x.filename.startswith(self.__application.library_directory),
                   self.ear.infolist()))

        # check if all the modules are inside the archive and assign the
        # underlying zipfile to the module
        for module in self.modules:
            try:
                module.assign_zipinfo(self.ear.getinfo(module.uri))
            except KeyError:
                raise Exception("%s not found in EAR!" % module.uri)

    def __parse_application_xml(self):
        try:
            f = self.ear.open(self.application_xml_path)
            return ApplicationDescriptor(parseString(f.read()))
        finally:
            f.close()

    def __open_zipmember(self, library):
        return self.ear.open(library.filename)

    def __extract_file(self, path, zipmember, overwrite_callback=None):
        """Overwrites files if they exist. This can be disabled by
        registering an 'overwrite_callback' function and returning
        False."""
        filename = zipmember.basename
        target_path = os.path.join(path, filename)

        if os.path.isfile(target_path) and overwrite_callback != None:
            target_crc = crc32(target_path)
            cb = overwrite_callback(filename, target_crc, zipmember.crc)
            if cb is False:
                return False # skip file because the callback returned False

        if not os.path.exists(path):
            os.makedirs(path) # create target directory if it doesn't exist

        try:
            source = self.__open_zipmember(zipmember)
            target = file(target_path, "wb")
            shutil.copyfileobj(source, target)
        finally:
            source.close()
            target.close()

        return True # indicating success

    def extract_library(self, path, library, overwrite_callback=None):
        return self.__extract_file(path, library, overwrite_callback)

    def extract_module(self, path, module, overwrite_callback=None):
        if not isinstance(module, WebModule):
            raise Exception("Don't know how to handle module.")
        return self.__extract_file(path, module, overwrite_callback)

class ApplicationDescriptor(object):
    def __init__(self, dom):
        self.modules = []
        self.__handleApplication(dom.getElementsByTagName('application')[0])

    def __handleApplication(self, app):
        if app.getAttribute('version') != '6':
            raise Exception("application version needs to be '6'!")

        self.description = text_child1(app, 'description', '')
        self.display_name = text_child1(app, 'display-name', '')
        self.library_directory = text_child1(app, 'library-directory', '')

        deployment_nodes = children(app, 'module')
        if len(deployment_nodes) != 1:
            raise Exception("Too many module tags found. EARs with multiple deployments are currently not supported!")

        self.modules = [self.__handle_module(node)
                        for node in children(deployment_nodes[0])]
        
    def __handle_module(self, module_node):
        otype = WebModule if module_node.nodeName == 'web' else Module
        return otype(module_node)

class Module(ZipMember):
    def __init__(self, module_node):
        self.type = module_node.nodeName
        # TODO: uri

class WebModule(Module):
    # elements: web-uri, context-root
    # attributes: id
    def __init__(self, web_node):
        super(WebModule, self).__init__(web_node)
        self.id = web_node.getAttribute('id')
        self.web_uri = self.uri = text_child1(web_node, 'web-uri')
        self.context_root = text_child1(web_node, 'context-root')

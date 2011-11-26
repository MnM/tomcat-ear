import os, shutil
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

class Ear(object):
    application_xml_path = 'META-INF/application.xml'

    def __init__(self, ear_path):
        self.ear = ZipFile(ear_path)
        bad_files = self.ear.testzip()
        if bad_files:
            raise Exception("EAR is corrupt: %s" % bad_files)

        # TODO: make application private
        self.application = self.__parse_application_xml()
        self.modules = self.application.modules

        # scan library-dir for libraries
        self.libraries = filter(lambda x: x.startswith(self.application.library_directory) and x.endswith('.jar'), self.ear.namelist())

        # check if all the modules are inside the archive
        for module in self.modules:
            if not module.uri in self.ear.namelist():
                raise Exception("%s not found in EAR!" % module.uri)

    def __parse_application_xml(self):
        try:
            f = self.ear.open(self.application_xml_path)
            return ApplicationDescriptor(parseString(f.read()))
        finally:
            f.close()

    def __extract_file(self, path, member, skipExisting=True):
        filename = os.path.basename(member)
        target_path = os.path.join(path, filename)
        if os.path.isfile(target_path) and skipExisting:
            return # skip if it already exists
        if not os.path.exists(path):
            os.makedirs(path) # create target directory if it doesn't exist
        source = self.ear.open(member)
        target = file(target_path, "wb")
        shutil.copyfileobj(source, target)
        source.close()
        target.close()

    def extract_library(self, path, library):
        self.__extract_file(path, library)

    def extract_module(self, path, module):
        if not isinstance(module, WebModule):
            raise Exception("Don't know how to handle module.")
        self.__extract_file(path, module.uri)

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
        if module_node.nodeName == 'web':
            return WebModule(module_node)
        else:
            return Module(module_node)

class Module(object):
    def __init__(self, module_node):
        self.type = module_node.nodeName
        # TODO: uri
    pass

class WebModule(Module):
    # elements: web-uri, context-root
    # attributes: id
    def __init__(self, web_node):
        super(WebModule, self).__init__(web_node)
        self.id = web_node.getAttribute('id')
        self.web_uri = self.uri = text_child1(web_node, 'web-uri')
        self.context_root = text_child1(web_node, 'context-root')

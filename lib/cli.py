import os, sys
from pprint import pformat

from properties import parse_properties
from ear import Ear, WebModule

### begin logging stuff
import logging

#logging.basicConfig(format="%(message)s")
log = logging.getLogger(__name__)

BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)
RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ = "\033[1m"

def colourize(s, colour):
    return COLOR_SEQ % (30 + colour) + s + RESET_SEQ

def debug(s):
    log.debug(colourize(s, BLACK))

def info(s):
    log.info(s)

def error(s, code=1):
    log.error(colourize(s, RED))
    if code:
        exit(code)

### end of logging stuff

def mkpath(*args):
    return os.path.join(*args)

def p_not_empty_nor_jar(s):
    return len(s) and not s.endswith('*.jar')

def resolve_paths(env):
    if not env.has_key('CATALINA_HOME'):
        error("CATALINA_HOME must be set!")

    catalina_home = env.get('CATALINA_HOME')    
    catalina_base = env.get('CATALINA_BASE', catalina_home)
    
    return {'catalina_home': catalina_home,
            'catalina_base': catalina_base,
            'catalina_deploy': env.get('CATALINA_DEPLOY', mkpath(catalina_base, 'webapps')),
            'catalina.properties': mkpath(catalina_base, 'conf', 'catalina.properties'),}

YES = ["y", "yes"]
NO = ["n", "no"]

def prompt(message, validate_input):
    input = None
    while not validate_input(input):
        sys.stdout.write(message + " ")
        try:
            input = raw_input()
        except ValueError:
            pass
    return input

if __name__ == "__main__":
    log.setLevel(logging.INFO)

    if len(sys.argv) != 2:
        error("Script expects an EAR file as it's single argument.")

    ear = Ear(sys.argv[1])
    debug("EAR libraries: " + pformat(ear.libraries))

    path = resolve_paths(os.environ)
    debug("Paths: " + pformat(path))

    # these need to be applied to property files
    env = {'catalina.home': path['catalina_home'],
           'catalina.base': path['catalina_base']}
    
    with open(path['catalina.properties']) as f:
        props = parse_properties(f, env)
    debug(pformat(props))
    
    commonl = props['common.loader']
    sharedl = props['shared.loader']
    serverl = props['server.loader']
    library_paths = filter(p_not_empty_nor_jar,
                           set(list(commonl) + list(sharedl) + list(serverl)))
    debug("Library paths: " + pformat(library_paths))

    ### begin of user input

    print("These are the libraries contained in the EAR file, that need to be deployed:")
    print(pformat(ear.libraries) + "\n")

    # ask the user where he wants to deploy the libraries
    library_path_index = None
    while library_path_index not in range(len(library_paths)):
        print("Where do you want the libraries to be deployed?")
        for index, libpath in zip(range(len(library_paths)), library_paths):
            print("%s -> %s" % (index, colourize(libpath, YELLOW)))
        try:
            library_path_index = int(raw_input())
        except ValueError:
            pass
    library_path = library_paths[library_path_index]

    web_path = path['catalina_deploy']
    print("\nWeb modules will be deployed here: %s\n" % colourize(web_path, YELLOW))
    print("If you want to deploy to a different directory, please set")
    print("the CATALINA_DEPLOY environment variable.\n")
    
    if prompt("Do you want to continue? (yes|no)",
              lambda x: x in YES + NO) in NO:
        error("Exiting, user decided not to continue.")

    # extract all library JARs
    info("Extracting libraries to %s..." % library_path)
    for library in ear.libraries:
        info("\t%s" % library)
        ear.extract_library(library_path, library)

    # extract all WEBs
    info("Extracting WEBs to %s..." % web_path)
    for module in filter(lambda x: isinstance(x, WebModule), ear.modules):
        info("\t%s" % module.uri)
        ear.extract_module(web_path, module)

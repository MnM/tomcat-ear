import os, sys
from pprint import pformat

from colourize import colourize, RED, BLACK, YELLOW
from properties import parse_properties
from ear import Ear, WebModule

### begin logging stuff
import logging

logging.basicConfig(format="%(message)s")
log = logging.getLogger(__name__)

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

def prompt(message, validate_input, convert=str):
    input = None
    while not validate_input(input):
        sys.stdout.write(message + " ")
        try:
            input = convert(raw_input())
        except ValueError:
            pass
    return input

def overwrite_callback(dest, old_crc, new_crc):
    if (old_crc == new_crc):
        return False
    else:
        info("old_crc = %s, new_crc = %s" % (old_crc, new_crc))
        return prompt("File %s already exists and differs, overwrite? (yes|no)" % dest,
                  lambda x: x in YES + NO) in YES

def write_obj(fn, obj, path, overwrite_callback):
    wrote_file = fn(path, obj, overwrite_callback)
    info("\t%s%s" % ("" if wrote_file else "SKIPPED ", obj))

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
    
    print("Possible deployment targets are (read from catalina.properties):")
    for tuple in zip(range(len(library_paths)), library_paths):
        print("\t%s -> %s" % tuple)

    index = prompt("Where do you want the libraries to be deployed?",
                   lambda x: x in range(len(library_paths)),
                   int)
    library_path = library_paths[index]

    # print summary and let user decide whether to continue
    print("\nLibraries will be deployed here: %s" % colourize(library_path, YELLOW))
    web_path = path['catalina_deploy']
    print("Web modules will be deployed here: %s\n" % colourize(web_path, YELLOW))
    print("If you want to deploy the WEB(s) to a different directory, please")
    print("set the CATALINA_DEPLOY environment variable.\n")
    
    if prompt("Do you want to continue? (yes|no)",
              lambda x: x in YES + NO) in NO:
        error("Exiting, user decided not to continue.")

    # extract all library JARs
    info("Extracting libraries to %s..." % library_path)
    for library in ear.libraries:
        write_obj(ear.extract_library, library, library_path, overwrite_callback)

    # extract all WEBs
    info("Extracting WEBs to %s..." % web_path)
    for module in filter(lambda x: isinstance(x, WebModule), ear.modules):
        write_obj(ear.extract_module, module, web_path, overwrite_callback)

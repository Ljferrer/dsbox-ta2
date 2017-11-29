"""
Command Line Interface for running the DSBox TA2 Planner
"""

# Setup path before loading any dsbox.* packages. Or, alternatively
# use ../dsbox-dev-setup.sh to setup PYTHONPATH.
from dsbox_dev_setup import path_setup
path_setup()

import sys
import os
import argparse
from dsbox.planner.controller import Controller, Feature
from dsbox.planner.event_handler import PlannerEventHandler

__all__ = []
__version__ = 0.3
__date__ = '2017-06-27'
__updated__ = '2017-08-27'

DEBUG = 0

def main(argv=None): # IGNORE:C0111
    '''Command line options.
    '''

    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    program_name = os.path.basename(sys.argv[0])
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = '%%(prog)s %s (%s)' % (program_version, program_build_date)
    program_shortdesc = __import__('__main__').__doc__.split("\n")[1]
    program_license = '''%s
USAGE
''' % program_shortdesc

    #try:
    # Setup argument parser
    parser = argparse.ArgumentParser(description=program_license, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-p", "--problem", dest="problem", help="Problem directory")
    parser.add_argument("-l", "--library", dest="library", help="Primitives library directory. [default: %(default)s]", default="library")
    parser.add_argument("-o", "--output", dest="output", help="Output directory. [default: %(default)s]", default="output")
    parser.add_argument("-v", "--verbose", dest="verbose", action="count", help="set verbosity level [default: %(default)s]")
    parser.add_argument('-V', '--version', action='version', version=program_version_message)
    parser.add_argument('-d', '--debug', dest='debug', action='store_true', help='Debug. Do not redirect stderr to file')

    # Process arguments
    args = parser.parse_args()

    problem_directory = args.problem
    if not problem_directory:
        sys.stderr.write(program_name + ": No problem directory specified\n")
        sys.stderr.write("  for help use --help\n")
        exit(1)

    data_directory = problem_directory + os.sep + "data"

    library_directory = args.library
    verbose = args.verbose
    if not args.verbose:
        verbose = 0
    output_directory = args.output

    if verbose > 0:
        print("Verbose mode on")

    debug = args.debug

    controller = Controller(library_directory, debug=debug)
    controller.set_config_simple(data_directory, output_directory)
    controller.load_problem_schema()
    controller.initialize_training_data_from_defaults()
    controller.initialize_planners()
    for result in controller.train(PlannerEventHandler()):
        pass


if __name__ == "__main__":
    if DEBUG:
        sys.argv.append("-v")
        sys.argv.append("-d")
    sys.exit(main())

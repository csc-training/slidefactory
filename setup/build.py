#!/usr/bin/python3
#---------------------------------------------------------------------------#
# Function: Build slidefactory singularity container.                       #
# Help:     ./build.sh --help                                               #
#---------------------------------------------------------------------------#
import argparse
import sys
import os

def run():
    desc = 'Build slidefactory singularity container'
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('output', nargs='?',
            default='slidefactory.sif', metavar='image.sif',
            help='filename for the container image to be built ' \
                    + '(default: %(default)s)')
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
            help='display additional information while running')
    parser.add_argument('-d', '--definition',
            default='slidefactory.def', metavar='image.def',
            help='singularity definition file for the container ' \
                    + '(default: %(default)s)')

    args = parser.parse_args()

    # be noisy?
    if args.verbose:
        print('Image file: {0}'.format(args.output))
        print('Definition: {0}'.format(args.definition))
        print('')

    # check files
    if not os.path.isfile(args.definition):
        print("Definition file '{0}' missing.".format(args.definition))
        return 1
    if os.path.exists(args.output):
        # is the existing container image newer than the definition?
        try:
            time_def = os.path.getmtime(args.definition)
            time_out = os.path.getmtime(args.output)
            if time_def < time_out:
                if args.verbose:
                    print('Nothing to do.')
                return 0
        except Exception:
            if args.verbose:
                print('Warning: unable to determine file modification time')
        # remove existing file?
        yn = input("File '{0}' exists. Overwrite [y/N]? ".format(args.output))
        if yn.lower() in ['y', 'yes']:
            try:
                os.remove(args.output)
            except Exception:
                print("Unable to remove '{0}'. Maybe it is not a file?".format(
                    args.output))
                return 1
        else:
            print('Abort.')
            return 2

    # build command
    cmd = 'sudo singularity build {0} {1}'.format(args.output, args.definition)

    # execute
    if args.verbose:
        print('Building image...')
        print('  ' + cmd)
        print('')
    os.system(cmd)

    # the end.
    return 0

if __name__ == '__main__':
    sys.exit(run())

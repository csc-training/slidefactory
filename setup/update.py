#!/usr/bin/python3
#---------------------------------------------------------------------------#
# Function: Update slidefactory repository (and maybe container)            #
# Help:     ./update.sh --help                                              #
#---------------------------------------------------------------------------#
import argparse
import sys
import os
import tempfile
from contextlib import contextmanager

def get_install_path():
    if 'SLIDEFACTORY' in os.environ:
        return os.path.abspath(
                os.path.join(os.environ['SLIDEFACTORY'], '../..'))
    else:
        path = os.environ.get('HOME', os.path.expanduser('~'))
        if os.path.isdir(os.path.join(path, 'lib/slidefactory')):
            return path
        raise Exception

@contextmanager
def change_dir(path):
    cwd = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(cwd)

def run():
    desc = 'Update slidefactory repository (and maybe container)'
    parser = argparse.ArgumentParser(description=desc)
    parser.set_defaults(image='slidefactory.sif')
    parser.add_argument('--as-container', action='store_true', default=False,
            help=argparse.SUPPRESS)
    parser.add_argument('-c', '--container', action='store_true', default=False,
            help='update also container')
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
            help='display additional information while running')

    args = parser.parse_args()

    # figure out install paths
    try:
        install_prefix = get_install_path()
    except Exception:
        print('Could not find files to update. Please set correct path '
                + 'to the environment variable SLIDEFACTORY.')
        print("If you haven't yet installed slidefactory, please first run:")
        if args.as_container:
            print('  slidefactory.sif --install')
        else:
            print('  python3 setup/install.py')
        return 1
    install_git = os.path.join(install_prefix, 'lib/slidefactory')
    install_sif = os.path.join(install_prefix, 'bin', args.image)

    # check files
    if not os.path.isdir(install_git) or \
            not os.path.isdir(os.path.join(install_git, '.git')):
        print("Invalid git repository path: {0}".format(install_git))
        return 1
    if args.container:
        if not os.path.isfile(install_sif):
            print("Invalid image file: {0}".format(install_sif))
            return 1

    # be noisy?
    if args.verbose:
        print('Repository: {0}'.format(install_git))
        if args.container:
            print('Container:  {0}'.format(install_sif))
        print('')

    # update repository
    cmd = 'git pull'
    if args.verbose:
        print('Updating repository...')
        print('  ' + cmd)
        print('')
    try:
        with change_dir(install_git):
            os.system(cmd)
    except Exception:
        print("Unable to update repository: {0}".format(install_git))

    # update container
    if args.container:
        with tempfile.TemporaryDirectory(prefix='slidefactory-') as tmp:
            sandbox = os.path.join(tmp, 'sandbox')
            # create sandbox from the existing container
            cmd = 'singularity build --sandbox {0} {1}'.format(sandbox,
                                                               install_sif)
            if args.verbose:
                print('Unpacking container...')
                print('  ' + cmd)
            try:
                os.system(cmd)
            except Exception:
                print('Unable to unpack container: {0}'.format(install_sif))
            # update the git repo
            path = os.path.join(sandbox, 'slidefactory')
            cmd = 'git pull'
            if args.verbose:
                print('Updating repository (in container)...')
                print('  ' + cmd)
            try:
                with change_dir(path):
                    os.system(cmd)
            except Exception:
                print("Unable to update the repository in the container.")
            # create a new container from the sandbox
            cmd = 'singularity build --force {0} {1}'.format(install_sif,
                                                             sandbox)
            if args.verbose:
                print('Building container...')
                print('  ' + cmd)
                print('')
            try:
                os.system(cmd)
            except Exception:
                print('Unable to build container: {0}'.format(install_sif))

    print('Updated:')
    print('  {0}'.format(install_git))
    if args.container:
        print('  {0}'.format(install_sif))

    # the end.
    return 0

if __name__ == '__main__':
    sys.exit(run())

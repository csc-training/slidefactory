#!/usr/bin/python3
#---------------------------------------------------------------------------#
# Function: Install slidefactory container and repository                   #
# Help:     ./install.sh --help                                             #
#---------------------------------------------------------------------------#
import argparse
import sys
import os
import shutil
import subprocess

def get_version(image):
    cmd = [image, '--version']
    proc = subprocess.run(cmd, capture_output=True, encoding='utf-8')
    if proc.returncode or not proc.stdout:
        print("Couldn't determine the version of image {0}".format(image))
        sys.exit(3)
    return proc.stdout.strip()

def run():
    desc = 'Install slidefactory container and repository'
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-p', '--prefix',
            default=os.environ.get('HOME', os.path.expanduser('~')),
            help='install files into this path (under bin/ and lib/)' \
                    + ' (default: %(default)s)')
    parser.add_argument('-i', '--image', metavar='SIF',
            default='slidefactory.sif',
            help='container image to install (default: %(default)s)')
    parser.add_argument('-r', '--repository', metavar='URL',
            default='https://github.com/csc-training/slide-template',
            help='URL to the git repository to install (default: %(default)s)')
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
            help='display additional information while running')

    args = parser.parse_args()

    # install paths
    install_git = os.path.join(args.prefix, 'lib/slidefactory')
    install_bin = os.path.join(args.prefix, 'bin')
    install_sif = os.path.join(install_bin, args.image)

    # be noisy?
    if args.verbose:
        print('Image file: {0}'.format(args.image))
        print('Repository: {0}'.format(args.repository))
        print('Install paths:')
        print('  {0}'.format(install_bin))
        print('  {0}'.format(install_git))
        print('')

    # check files
    if not os.path.isfile(args.image):
        print("Image file '{0}' missing.".format(args.definition))
        return 1
    if os.path.exists(install_sif):
        version_sif = get_version(install_sif)
        version_image = get_version(os.path.join('.', args.image))
        if version_image < version_sif:
            print()
            print(("Newer version of the image installed already "
                   "({0} vs. {1}).").format(version_sif, version_image))
            print()
            print(("To update the installed git repository, please run "
                   "'setup/update.py'"))
            return 1
        yn = input("File '{0}' exists already. Remove [y/N]? ".format(
            install_sif))
        if yn.lower() in ['y', 'yes']:
            try:
                os.remove(install_sif)
            except Exception:
                print("Unable to remove '{0}'. Maybe it is not a file?".format(
                    install_sif))
                return 1
        else:
            print('Abort.')
            return 2
    if os.path.exists(install_git):
        yn = input("Path '{0}' exists already. Remove [y/N]? ".format(
            install_git))
        if yn.lower() in ['y', 'yes']:
            try:
                shutil.rmtree(install_git)
            except Exception:
                print("Unable to remove '{0}'.")
                return 1
        else:
            print('Abort.')
            return 2

    # copy image
    cmd = 'cp -i {0} {1}'.format(args.image, install_sif)
    if args.verbose:
        print('Copying image...')
        print('  ' + cmd)
    os.system(cmd)

    # clone git repository
    cmd = 'git clone {0} {1}'.format(args.repository, install_git)
    if args.verbose:
        print('Cloning repository...')
        print('  ' + cmd)
        print('')
    os.system(cmd)

    print('')
    print('Installed:')
    print('  {0}'.format(install_sif))
    print('  {0}'.format(install_git))
    print('')
    print('Please add the following into your .bashrc or similar:')
    print('  export SLIDEFACTORY={0}'.format(install_git))

    # check if bin in PATH
    path = os.environ.get('PATH', '').split(':')
    if not install_bin in path:
        print('')
        print("Please make sure that '{0}' is in your PATH:".format(install_bin))
        print('  export PATH=$PATH:{0}'.format(install_bin))

    # the end.
    return 0

if __name__ == '__main__':
    sys.exit(run())

#!/usr/bin/python3
#---------------------------------------------------------------------------#
# Function: Uninstall slidefactory container and repository                 #
# Help:     ./install.sh --help                                             #
#---------------------------------------------------------------------------#
import argparse
import sys
import os
import shutil

def get_install_path():
    if 'SLIDEFACTORY' in os.environ:
        return os.path.abspath(
                os.path.join(os.environ['SLIDEFACTORY'], '../..'))
    else:
        return os.environ.get('HOME', os.path.expanduser('~'))

def run():
    desc = 'Uninstall slidefactory container and repository'
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-p', '--prefix',
            default=get_install_path(),
            help='uninstall files installed at this path (under bin/ and lib/)'
                    + ' (default: %(default)s)')
    parser.add_argument('-i', '--image', metavar='SIF',
            default='slidefactory.sif',
            help='name of the container image (default: %(default)s)')
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
        print('Uninstall paths:')
        print('  {0}'.format(install_bin))
        print('  {0}'.format(install_git))
        print('')

    # are there files to remove?
    if not os.path.exists(install_sif) and not os.path.exists(install_git):
        print('Nothing to uninstall.')

    print('Removing:')
    print('  {0}'.format(install_sif))
    print('  {0}'.format(install_git))
    yn = input('Proceed [Y/n]? ')
    if yn.lower() not in ['y', 'yes', '']:
        print('Abort.')
        return 2
    try:
        pass
        os.remove(install_sif)
        shutil.rmtree(install_git)
    except Exception:
        print('Unable to remove all files.')
        return 1

    # the end.
    return 0

if __name__ == '__main__':
    sys.exit(run())

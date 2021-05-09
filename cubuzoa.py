import argparse
import common
import importlib
import json
import packaging.specifiers
import pathlib
import re
import shutil
import sys
import toml
dirname = pathlib.Path(__file__).resolve().parent

parser = argparse.ArgumentParser(description='Generate wheels for Linux, macOS and Windows')
subparsers = parser.add_subparsers(dest='command')
provision_parser = subparsers.add_parser('provision', help='download and install the Virtual Machines')
provision_parser.add_argument('--os', default='.*', help='operating system regex, case insensitive')
provision_parser.add_argument('--force', action='store_true', help='install VMs vn if they already exist')

build_parser = subparsers.add_parser('build', help='build a Python project')
build_parser.add_argument('project', help='path to the project directory')
build_parser.add_argument('--wheels', default=None, help='path to the output wheels directory, defaults to [project]/wheels')
build_parser.add_argument('--os', default='.*', help='operating system regex, case insensitive')
build_parser.add_argument('--version', default='>=3.7,<=3.9', help='version specifiers in PEP 440 format')
unprovision_parser = subparsers.add_parser('unprovision', help='stop all the Vagrant machines created by Cubuzoa')
args = parser.parse_args()

if args.command == 'provision':
    (dirname / 'build').mkdir(exist_ok=True)
    args.os = re.compile(args.os, re.IGNORECASE)
    sys.path.insert(0, str(dirname / 'provision'))
    for os_name in (child.stem for child in (dirname / 'provision').iterdir() if child.is_file()):
        if args.os.match(os_name) is not None:
            os_module = importlib.import_module(os_name)
            if hasattr(os_module, 'os_provision') and (not (dirname / 'build' / os_name).exists() or args.force):
                (dirname / 'build' / os_name).mkdir(exist_ok=True)
                os_module.os_provision(common, build=dirname / 'build' / os_name)

if args.command == 'build':
    if not (dirname / 'build').is_dir():
        print(f'run \033[1mpython3 cubuzoa.py provision\033[0m first')
        sys.exit(1)
    args.project = pathlib.Path(args.project).resolve()
    with open(args.project / 'pyproject.toml') as pyproject_file:
        pyproject = toml.load(pyproject_file)
    backend = pyproject['build-system']['build-backend']
    backends = set(child.name for child in (dirname / 'backends').iterdir() if child.is_dir())
    if not backend in backends:
        raise Exception(f'unsupported backend \'{backend}\' (supported backends: {backends})')
    if args.wheels is None:
        args.wheels = args.project / 'wheels'
    else:
        args.wheels = pathlib.Path(args.wheels).resolve()
    (args.wheels).mkdir(exist_ok=True)
    args.os = re.compile(args.os, re.IGNORECASE)
    versions = packaging.specifiers.SpecifierSet(args.version)
    sys.path.insert(0, str(dirname / 'backends' / backend))
    for os_name in (child.stem for child in (dirname / 'backends' / backend).iterdir() if child.is_file()):
        if args.os.match(os_name) is not None:
            os_module = importlib.import_module(os_name)
            if hasattr(os_module, 'os_build'):
                (dirname / 'build' / os_name).mkdir(exist_ok=True)
                os_module.os_build(
                    common,
                    versions=tuple(version for version in common.os_to_configuration[os_name].versions() if versions.contains(version)),
                    project=args.project,
                    wheels=args.wheels,
                    build=dirname / 'build' / os_name)

if args.command == 'unprovision':
    if (dirname / 'build').is_dir():
        for directory in (child for child in (dirname / 'build').iterdir() if child.is_dir()):
            common.vagrant_destroy(directory)
    shutil.rmtree(dirname / 'build', ignore_errors=True)

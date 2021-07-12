import argparse
import common
import importlib
import packaging.specifiers
import pathlib
import re
import shutil
import subprocess
import sys
import toml

dirname = pathlib.Path(__file__).resolve().parent

parser = argparse.ArgumentParser(
    description="Generate wheels for Linux, macOS and Windows", formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
subparsers = parser.add_subparsers(dest="command")
provision_parser = subparsers.add_parser(
    "provision",
    help="download and install the Virtual Machines",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
provision_parser.add_argument("--os", default=".*", help="operating system regex, case insensitive")
provision_parser.add_argument("--force", action="store_true", help="install VMs even if they already exist")

build_parser = subparsers.add_parser(
    "build", help="build a Python project", formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
build_parser.add_argument("project", help="path to the project directory")
build_parser.add_argument(
    "--post", default=None, help="path to a Python script to run post-build, must be in the project directort"
)
build_parser.add_argument(
    "--wheels", default=None, help="path to the output wheels directory, defaults to [project]/wheels"
)
build_parser.add_argument("--os", default=".*", help="operating system regex, case insensitive")
build_parser.add_argument("--version", default=">=3.7,<=3.9", help="version specifiers in PEP 440 format")
unprovision_parser = subparsers.add_parser(
    "unprovision",
    help="destroy the Vagrant machines created by Cubuzoa",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
unprovision_parser.add_argument("--prune", action="store_true", help="delete downloaded Vagrant boxes")
unprovision_parser.add_argument(
    "--clean", action="store_true", help="delete any VirtualBox machine whose name starts with cubuzoa-"
)
args = parser.parse_args()

if args.command == "provision":
    (dirname / "vagrant_private_key").chmod(0o600)
    (dirname / "build").mkdir(exist_ok=True)
    args.os = re.compile(args.os, re.IGNORECASE)
    sys.path.insert(0, str(dirname / "provision"))
    for os_name in sorted(child.stem for child in (dirname / "provision").iterdir() if child.is_file()):
        if args.os.match(os_name) is not None:
            os_module = importlib.import_module(os_name)
            if hasattr(os_module, "os_provision") and (not (dirname / "build" / os_name).exists() or args.force):
                (dirname / "build" / os_name).mkdir(exist_ok=True)
                os_module.os_provision(common, build=dirname / "build" / os_name)

if args.command == "build":
    args.project = pathlib.Path(args.project).resolve()
    if args.post is not None:
        args.post = pathlib.Path(args.post).resolve()
        try:
            args.post = args.post.relative_to(args.project)
        except ValueError:
            common.print_bold(f"the post script '{args.post}' must be in the project directory '{args.project}'")
            sys.exit(1)
    if args.wheels is None:
        args.wheels = args.project / "wheels"
    else:
        args.wheels = pathlib.Path(args.wheels).resolve()
    if not (dirname / "build").is_dir():
        common.print_bold(f"run python3 cubuzoa.py provision first")
        sys.exit(1)
    with open(args.project / "pyproject.toml") as pyproject_file:
        pyproject = toml.load(pyproject_file)
    backend = pyproject["build-system"]["build-backend"]
    backends = set(child.name for child in (dirname / "backend").iterdir() if child.is_dir())
    if not backend in backends:
        raise Exception(f"unsupported backend '{backend}' (supported backends: {backends})")
    (args.wheels).mkdir(exist_ok=True)
    args.os = re.compile(args.os, re.IGNORECASE)
    versions = packaging.specifiers.SpecifierSet(args.version)
    sys.path.insert(0, str(dirname / "backend" / backend))
    for os_name in sorted(child.stem for child in (dirname / "backend" / backend).iterdir() if child.is_file()):
        if args.os.match(os_name) is not None:
            os_module = importlib.import_module(os_name)
            if hasattr(os_module, "os_build"):
                (dirname / "build" / os_name).mkdir(exist_ok=True)
                os_module.os_build(
                    common,
                    versions=tuple(
                        version
                        for version in common.os_to_configuration[os_name].versions()
                        if versions.contains(version)
                    ),
                    project=args.project,
                    wheels=args.wheels,
                    build=dirname / "build" / os_name,
                    post=args.post,
                )

if args.command == "unprovision":
    if (dirname / "build").is_dir():
        for directory in sorted(child for child in (dirname / "build").iterdir() if child.is_dir()):
            common.vagrant_destroy(directory)
    shutil.rmtree(dirname / "build", ignore_errors=True)
    if args.prune:
        for configuration in common.os_to_configuration.values():
            common.vagrant_remove(configuration.box)
    if args.clean:
        machine_pattern = re.compile('^"cubuzoa-.+"\s{([\-a-z0-9]+)}\s*$')
        for line in subprocess.run(
            ("VBoxManage", "list", "vms"), check=True, capture_output=True, encoding="utf-8"
        ).stdout.split("\n"):
            match = machine_pattern.match(line)
            if match is not None:
                subprocess.check_call(("VBoxManage", "unregistervm", match.group(1), "--delete"))

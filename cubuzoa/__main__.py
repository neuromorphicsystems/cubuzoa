import argparse
import importlib
import packaging.specifiers
import pathlib
import re
import shutil
import subprocess
import sys
import toml
from . import common

dirname = pathlib.Path(__file__).resolve().parent

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="python3 -m cubuzoa",
        description="Generate wheels or frozen packages for Linux, macOS and Windows",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command")
    provision_parser = subparsers.add_parser(
        "provision",
        help="download and install the Virtual Machines",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    provision_parser.add_argument(
        "--os", default=".*", help="operating system regex, case insensitive"
    )
    provision_parser.add_argument(
        "--force", action="store_true", help="install VMs even if they already exist"
    )
    provision_parser.add_argument(
        "--build", default=str(dirname.parent / "build"), help="build directory"
    )
    build_parser = subparsers.add_parser(
        "build",
        help="build a Python project",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    build_parser.add_argument("project", help="path to the project directory")
    build_parser.add_argument(
        "--pre",
        default=None,
        help="path to a Python script to run pre-build on the guest machine, must be in the project directory",
    )
    build_parser.add_argument(
        "--post",
        default=None,
        help="path to a Python script to run post-build, must be in the project directory",
    )
    build_parser.add_argument(
        "--output",
        default=None,
        help="path to the output directory, defaults to [project]/wheels for wheels and [project]/build for frozen packages",
    )
    build_parser.add_argument(
        "--os", default=".*", help="operating system regex, case insensitive"
    )
    build_parser.add_argument(
        "--version", default=">=3.7,<=3.9", help="version specifiers in PEP 440 format"
    )
    build_parser.add_argument(
        "--build", default=str(dirname.parent / "build"), help="build directory"
    )
    unprovision_parser = subparsers.add_parser(
        "unprovision",
        help="destroy the Vagrant machines created by Cubuzoa",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    unprovision_parser.add_argument(
        "--prune", action="store_true", help="delete downloaded Vagrant boxes"
    )
    unprovision_parser.add_argument(
        "--clean",
        action="store_true",
        help="delete any VirtualBox machine whose name starts with cubuzoa-",
    )
    unprovision_parser.add_argument(
        "--build", default=str(dirname.parent / "build"), help="build directory"
    )
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "provision":
        (dirname / "vagrant_private_key").chmod(0o600)
        pathlib.Path(args.build).mkdir(exist_ok=True)
        args.os = re.compile(args.os, re.IGNORECASE)
        for os_name in sorted(
            child.stem for child in (dirname / "provision").iterdir() if child.is_file()
        ):
            if args.os.match(os_name) is not None:
                os_module = importlib.import_module(f"cubuzoa.provision.{os_name}")
                if hasattr(os_module, "os_provision") and (
                    not (pathlib.Path(args.build) / os_name).exists() or args.force
                ):
                    # @DEV this should  be delayed until the box is downloaded (if possible)
                    (pathlib.Path(args.build) / os_name).mkdir(exist_ok=True)
                    os_module.os_provision(build=pathlib.Path(args.build) / os_name)  # type: ignore

    if args.command == "build":
        args.project = pathlib.Path(args.project).resolve()
        if args.pre is not None:
            args.pre = pathlib.Path(args.pre).resolve()
            try:
                args.pre = args.pre.relative_to(args.project)
            except ValueError:
                common.print_error(
                    f'the pre script "{args.pre}" must be in the project directory "{args.project}"'
                )
                sys.exit(1)
        if args.post is not None:
            args.post = pathlib.Path(args.post).resolve()
            try:
                args.post = args.post.relative_to(args.project)
            except ValueError:
                common.print_error(
                    f'the post script "{args.post}" must be in the project directory "{args.project}"'
                )
                sys.exit(1)
        if not pathlib.Path(args.build).is_dir():
            common.print_error(f"run python3 cubuzoa.py provision first")
            sys.exit(1)
        with open(args.project / "pyproject.toml") as pyproject_file:
            pyproject = toml.load(pyproject_file)
        backend = pyproject["build-system"]["build-backend"]
        if backend == "setuptools.build_meta":
            backend = "setuptools"
        backends = set(
            child.name for child in (dirname / "backend").iterdir() if child.is_dir()
        )
        if not backend in backends:
            raise Exception(
                f'unsupported backend "{backend}" (supported backends: {backends})'
            )
        if args.output is None:
            if backend == "pyinstaller":
                args.output = args.project / "build"
            else:
                args.output = args.project / "wheels"
        else:
            args.output = pathlib.Path(args.output).resolve()
        args.output.mkdir(exist_ok=True)
        args.os = re.compile(args.os, re.IGNORECASE)
        versions = packaging.specifiers.SpecifierSet(args.version)
        for os_name in sorted(
            child.stem
            for child in (dirname / "backend" / backend).iterdir()
            if child.is_file() and child.suffix == ".py"
        ):
            if args.os.match(os_name) is not None:
                os_module = importlib.import_module(
                    f"cubuzoa.backend.{backend}.{os_name}"
                )
                if hasattr(os_module, "os_build"):
                    (pathlib.Path(args.build) / os_name).mkdir(exist_ok=True)
                    os_module.os_build(  # type: ignore
                        versions=tuple(
                            version
                            for version in common.os_to_configuration[
                                os_name
                            ].versions()
                            if versions.contains(version)
                        ),
                        project=args.project,
                        output=args.output,
                        build=pathlib.Path(args.build) / os_name,
                        pre=args.pre,
                        post=args.post,
                        pyproject=pyproject,
                    )

    if args.command == "unprovision":
        if pathlib.Path(args.build).is_dir():
            for directory in sorted(
                child for child in pathlib.Path(args.build).iterdir() if child.is_dir()
            ):
                common.vagrant_destroy(directory)
        shutil.rmtree(pathlib.Path(args.build), ignore_errors=True)
        if args.prune:
            for configuration in common.os_to_configuration.values():
                common.vagrant_remove(configuration.box)
        if args.clean:
            machine_pattern = re.compile(r'^"cubuzoa-.+"\s{([\-a-z0-9]+)}\s*$')
            for line in subprocess.run(
                ("VBoxManage", "list", "vms"),
                check=True,
                capture_output=True,
                encoding="utf-8",
            ).stdout.split("\n"):
                match = machine_pattern.match(line)
                if match is not None:
                    subprocess.check_call(
                        ("VBoxManage", "unregistervm", match.group(1), "--delete")
                    )

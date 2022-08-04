import datetime
import os
import pathlib
import shutil
import subprocess
import tempfile
import typing
import sys

dirname = pathlib.Path(__file__).resolve().parent


class Configuration:
    def __init__(self, box: str, version_to_name: dict[str, str]):
        self.box = box
        self.version_to_name = version_to_name

    def names(self) -> list[str]:
        return list(self.version_to_name.values())

    def versions(self) -> list[str]:
        return list(self.version_to_name.keys())

    def default_version(self) -> str:
        return next(iter(self.version_to_name.keys()))

    def default_name(self) -> str:
        return next(iter(self.version_to_name.values()))


os_to_configuration: dict[str, Configuration] = {
    "linux": Configuration(
        "ubuntu/focal64",
        {
            "3.10": "/opt/python/cp310-cp310/bin",
            "3.9": "/opt/python/cp39-cp39/bin",
            "3.8": "/opt/python/cp38-cp38/bin",
            "3.7": "/opt/python/cp37-cp37m/bin",
        },
    ),
    "macos": Configuration(
        "amarcireau/macos",
        {
            "3.10": "3.10.6",
            "3.9": "3.9.13",
            "3.8": "3.8.13",
            "3.7": "3.7.13",
        },
    ),
    "windows": Configuration(
        "gusztavvargadr/windows-10",
        {
            "3.10": "3.10.6",
            "3.9": "3.9.13",
            "3.8": "3.8.10",
            "3.7": "3.7.9",
        },
    ),
}


def format_bold(message: str) -> str:
    if os.getenv("ANSI_COLORS_DISABLED") is None:
        return f"\033[1m{message}\033[0m"
    return message


def print_bold(message: str) -> None:
    print(format_bold(message))


def format_info(message: str) -> str:
    return f"📦 {format_bold(message)}"


def print_info(message: str) -> None:
    print(format_info(message))


def format_warning(message: str) -> str:
    return f"⚠️  {format_bold(message)}"


def print_warning(message: str) -> None:
    print(format_warning(message))


def format_error(message: str) -> str:
    return f"❌ {format_bold(message)}"


def print_error(message: str) -> None:
    print(format_error(message))


def versions_to_string(versions: list[str]) -> str:
    if len(versions) == 1:
        return f"{versions.__iter__().__next__()}"
    versions_as_list = sorted(list(versions))
    return f'{", ".join(versions_as_list[:-1])} and {versions_as_list[-1]}'


def box_name(os_name: str) -> str:
    return "cubuzoa-{}-{}".format(
        os_name, datetime.datetime.today().isoformat().split(".")[0]
    )


def vagrant_plugin(plugin: str) -> None:
    plugins_string = subprocess.run(
        ("vagrant", "plugin", "list"), check=True, capture_output=True, encoding="utf-8"
    )
    plugins = set(
        plugin.split(" ")[0] for plugin in plugins_string.stdout[:-1].split("\n")
    )
    if plugin in plugins:
        subprocess.check_call(("vagrant", "plugin", "update", plugin))
    else:
        subprocess.check_call(("vagrant", "plugin", "install", plugin))


def vagrant_add(box: str) -> None:
    boxes_string = subprocess.run(
        ("vagrant", "box", "list"), check=True, capture_output=True, encoding="utf-8"
    )
    boxes = set(box.split(" ")[0] for box in boxes_string.stdout[:-1].split("\n"))
    if box in boxes:
        subprocess.check_call(
            ("vagrant", "box", "update", "--box", box, "--provider", "virtualbox")
        )
    else:
        subprocess.check_call(
            ("vagrant", "box", "add", box, "--provider", "virtualbox")
        )


def vagrant_remove(box: str) -> None:
    boxes_string = subprocess.run(
        ("vagrant", "box", "list"), check=True, capture_output=True, encoding="utf-8"
    )
    boxes = set(box.split(" ")[0] for box in boxes_string.stdout[:-1].split("\n"))
    if box in boxes:
        subprocess.check_call(("vagrant", "box", "remove", box, "--all"))


def vagrant_up(build: pathlib.Path, experimental: typing.Optional[str] = None) -> None:
    if experimental is not None:
        env = dict(os.environ)
        env["VAGRANT_EXPERIMENTAL"] = experimental
    else:
        env = os.environ
    subprocess.check_call(("vagrant", "up"), cwd=build, env=env)


def vagrant_run(build: pathlib.Path, command: str) -> None:
    subprocess.check_call(("vagrant", "ssh", "--", command), cwd=build)


def vagrant_destroy(build: pathlib.Path) -> None:
    if (
        build.exists()
        and subprocess.run(
            ("vagrant", "status"), check=False, capture_output=True, cwd=build
        ).returncode
        == 0
    ):
        subprocess.call(("vagrant", "destroy", "-f"), cwd=build)
    shutil.rmtree(build / ".vagrant", ignore_errors=True)


def vboxmanage(build: pathlib.Path, command: str, *args: str) -> None:
    with open(
        build / ".vagrant" / "machines" / "default" / "virtualbox" / "id"
    ) as uuid_file:
        uuid = uuid_file.read()
    subprocess.check_call(("VBoxManage", *command, uuid, *args), cwd=build)


def rsync(
    build: pathlib.Path, host_path: pathlib.Path, guest_path: str, host_to_guest: bool
) -> None:
    port = int(
        subprocess.run(
            ("vagrant", "port", "--guest", "22"),
            cwd=build,
            check=True,
            capture_output=True,
            encoding="utf-8",
        ).stdout
    )
    private_key = dirname / "vagrant_private_key"
    ssh = f"ssh -o LogLevel=ERROR -o StrictHostKeyChecking=no -o UserKnownHostsFile={os.devnull} -i {private_key} -p {port}"
    if host_to_guest:
        subprocess.check_call(
            (
                "rsync",
                "-az",
                "--filter=:- .gitignore",
                "--exclude=.git",
                "-e",
                ssh,
                f"{host_path}{os.sep}",
                f"vagrant@127.0.0.1:{guest_path}",
            )
        )
    else:
        subprocess.check_call(
            (
                "rsync",
                "-az",
                "-e",
                ssh,
                f"vagrant@127.0.0.1:{guest_path}{os.sep}",
                f"{host_path}",
            )
        )


def linux_docker_run(build: pathlib.Path, command: str) -> None:
    vagrant_run(
        build,
        " ".join(
            (
                "sudo /usr/bin/docker run",
                "--rm",
                "-e BASH_ENV=/root/.profile",
                "-v ~/project:/project",
                "-v ~/wheels:/wheels",
                "-v ~/build:/build",
                "manylinux",
                f"/bin/bash -c $'{command}'",
            )
        ),
    )


def rsync_windows_utilities(build: pathlib.Path) -> None:
    with tempfile.TemporaryDirectory() as temporary_directory:
        with open(pathlib.Path(temporary_directory) / "echo.py", "wb") as echo_file:
            base = format_info("{}")
            echo_file.write(
                "\n".join(
                    (
                        "import sys",
                        "if len(sys.argv) > 1:",
                        "    sys.stdout.reconfigure(encoding='utf-8')",
                        f"    print('{base}'.format(' '.join(sys.argv[1:])))",
                    )
                ).encode("utf-8")
            )
        rsync(
            build,
            host_path=pathlib.Path(temporary_directory),
            guest_path="utilities",
            host_to_guest=True,
        )


def pip_wheel(target: str) -> str:
    return f"-m pip wheel . -w {target} --no-deps"


def pip_install(wheel: str) -> str:
    return f"-m pip install --force-reinstall {wheel}"


def pip_uninstall(wheel: str) -> str:
    return f"-m pip uninstall -y {wheel}"


def pip_install_pyproject(pyproject: dict[str, typing.Any], guest: str) -> str:
    if guest == "macos":
        return pip_install(
            " ".join(
                '"{}"'.format(package.replace(" ", ""))
                for package in pyproject["build-system"]["requires"]
            )
        )
    elif guest == "linux":
        return pip_install(
            " ".join(
                '"{}"'.format(package.replace(" ", "").replace("'", "\\'"))
                for package in pyproject["build-system"]["requires"]
            )
        )
    return pip_install(
        " ".join(
            package.replace(" ", "")
            for package in pyproject["build-system"]["requires"]
        )
    )


def pyinstaller(
    project: pathlib.Path,
    target: str,
    pyproject: dict[str, typing.Any],
    version: str,
    suffix: str,
    guest: str,
) -> str:
    extra_arguments = ""
    if (
        "onefile" in pyproject["tool"]["pyinstaller"]
        and pyproject["tool"]["pyinstaller"]["onefile"] == True
    ):
        extra_arguments += " --onefile"
    if (
        "windowed" in pyproject["tool"]["pyinstaller"]
        and pyproject["tool"]["pyinstaller"]["windowed"] == True
    ):
        extra_arguments += " --windowed"
    if "data" in pyproject["tool"]["pyinstaller"]:
        for destination, sources in pyproject["tool"]["pyinstaller"]["data"].items():
            for source in sources:
                absolute_source_path = (
                    project / pathlib.PurePosixPath(source)
                ).resolve()
                try:
                    source_path = absolute_source_path.relative_to(project)
                except ValueError:
                    print_error(
                        f"the data file '{absolute_source_path}' must be in the project directory '{project}'"
                    )
                    sys.exit(1)
                extra_arguments += " --add-data {}{}{}".format(
                    pathlib.PureWindowsPath(source_path)
                    if guest == "windows"
                    else source_path.as_posix(),
                    ";" if guest == "windows" else ":",
                    destination,
                )
    if "exclude_modules" in pyproject["tool"]["pyinstaller"]:
        extra_arguments += " ".join(
            f" --exclude-module {module}"
            for module in pyproject["tool"]["pyinstaller"]["exclude_modules"]
        )
    if guest == "macos":
        extra_arguments += " --upx-dir /usr/local/bin"
    print(
        "-m PyInstaller{} --distpath {} -n {}-cp{}-{} {}".format(
            extra_arguments,
            target,
            pyproject["tool"]["pyinstaller"]["name"],
            version.replace(".", ""),
            suffix,
            " ".join(pyproject["tool"]["pyinstaller"]["scriptnames"]),
        )
    )
    return "-m PyInstaller{} --distpath {} -n {}-cp{}-{} {}".format(
        extra_arguments,
        target,
        pyproject["tool"]["pyinstaller"]["name"],
        version.replace(".", ""),
        suffix,
        " ".join(pyproject["tool"]["pyinstaller"]["scriptnames"]),
    )

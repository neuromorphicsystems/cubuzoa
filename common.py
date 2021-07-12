import datetime
import os
import pathlib
import shutil
import subprocess
import tempfile

dirname = pathlib.Path(__file__).resolve().parent


class Configuration:
    def __init__(self, box, version_to_name):
        self.box = box
        self.version_to_name = version_to_name

    def names(self):
        return self.version_to_name.values()

    def versions(self):
        return self.version_to_name.keys()

    def default_version(self):
        return next(iter(self.version_to_name.keys()))

    def default_name(self):
        return next(iter(self.version_to_name.values()))


os_to_configuration = {
    "linux": Configuration(
        "ubuntu/focal64",
        {
            "3.9": "/opt/python/cp39-cp39/bin",
            "3.8": "/opt/python/cp38-cp38/bin",
            "3.7": "/opt/python/cp37-cp37m/bin",
        },
    ),
    "macos": Configuration(
        "amarcireau/macos",
        {
            "3.9": "3.9.4",
            "3.8": "3.8.9",
            "3.7": "3.7.10",
        },
    ),
    "windows": Configuration(
        "gusztavvargadr/windows-10",
        {
            "3.9": "3.9.4",
            "3.8": "3.8.9",
            "3.7": "3.7.9",
        },
    ),
}


def format_bold(message):
    if os.getenv("ANSI_COLORS_DISABLED") is None:
        return f"\033[1m{message}\033[0m"
    return message


def print_bold(message):
    print(format_bold(message))


def format_info(message):
    return f"📦 {format_bold(message)}"


def print_info(message):
    print(format_info(message))


def versions_to_string(versions):
    if len(versions) == 1:
        return f"{versions.__iter__().__next__()}"
    versions_as_list = sorted(list(versions))
    return f'{", ".join(versions_as_list[:-1])} and {versions_as_list[-1]}'


def box_name(os_name):
    return "cubuzoa-{}-{}".format(os_name, datetime.datetime.today().isoformat().split(".")[0])


def vagrant_plugin(plugin):
    plugins_string = subprocess.run(("vagrant", "plugin", "list"), check=True, capture_output=True, encoding="utf-8")
    plugins = set(plugin.split(" ")[0] for plugin in plugins_string.stdout[:-1].split("\n"))
    if plugin in plugins:
        subprocess.check_call(("vagrant", "plugin", "update", plugin))
    else:
        subprocess.check_call(("vagrant", "plugin", "install", plugin))


def vagrant_add(box):
    boxes_string = subprocess.run(("vagrant", "box", "list"), check=True, capture_output=True, encoding="utf-8")
    boxes = set(box.split(" ")[0] for box in boxes_string.stdout[:-1].split("\n"))
    if box in boxes:
        subprocess.check_call(("vagrant", "box", "update", "--box", box, "--provider", "virtualbox"))
    else:
        subprocess.check_call(("vagrant", "box", "add", box, "--provider", "virtualbox"))


def vagrant_remove(box):
    boxes_string = subprocess.run(("vagrant", "box", "list"), check=True, capture_output=True, encoding="utf-8")
    boxes = set(box.split(" ")[0] for box in boxes_string.stdout[:-1].split("\n"))
    if box in boxes:
        subprocess.check_call(("vagrant", "box", "remove", box, "--all"))


def vagrant_up(build, experimental=None):
    if experimental is not None:
        env = dict(os.environ)
        env["VAGRANT_EXPERIMENTAL"] = experimental
    else:
        env = os.environ
    subprocess.check_call(("vagrant", "up"), cwd=build, env=env)


def vagrant_run(build, command):
    subprocess.check_call(("vagrant", "ssh", "--", command), cwd=build)


def vagrant_destroy(build):
    if subprocess.run(("vagrant", "status"), check=False, capture_output=True, cwd=build).returncode == 0:
        subprocess.call(("vagrant", "destroy", "-f"), cwd=build)
    shutil.rmtree(build / ".vagrant", ignore_errors=True)


def vboxmanage(build, command, *args):
    with open(build / ".vagrant" / "machines" / "default" / "virtualbox" / "id") as uuid_file:
        uuid = uuid_file.read()
    subprocess.check_call(("VBoxManage", *command, uuid, *args), cwd=build)


def rsync(build, host_path, guest_path, host_to_guest):
    port = int(
        subprocess.run(
            ("vagrant", "port", "--guest", "22"), cwd=build, check=True, capture_output=True, encoding="utf-8"
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
        subprocess.check_call(("rsync", "-az", "-e", ssh, f"vagrant@127.0.0.1:{guest_path}{os.sep}", f"{host_path}"))


def linux_docker_run(build, command):
    vagrant_run(
        build,
        " ".join(
            (
                "sudo /usr/bin/docker run",
                "--rm",
                "-e BASH_ENV=/root/.profile",
                "-v ~/project:/project",
                "-v ~/wheels:/wheels",
                "manylinux",
                f"/bin/bash -c $'{command}'",
            )
        ),
    )


def rsync_windows_utilities(build):
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
        rsync(build, host_path=temporary_directory, guest_path="utilities", host_to_guest=True)


def pip_wheel(target):
    return f"-m pip wheel . -w {target} --no-deps --use-feature=in-tree-build"


def pip_install(wheel):
    return f"-m pip install --force-reinstall {wheel}"


def pip_uninstall(wheel):
    return f"-m pip uninstall -y {wheel}"

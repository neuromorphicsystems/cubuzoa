from os import name
import pathlib
import typing


def os_build(
    common,
    versions: tuple[str, ...],
    project: pathlib.Path,
    output: pathlib.Path,
    build: pathlib.Path,
    post: pathlib.Path,
    pyproject: dict[str, typing.Any],
):
    common.print_info(f"Copying project files to Linux")
    common.vagrant_run(build, "sudo rm -rf project; sudo rm -rf build; mkdir build")
    common.rsync(build, host_path=project, guest_path="project", host_to_guest=True)
    if len(versions) > 1 or len(versions) == 1 and versions[0] != "3.8":
        common.print_warning(
            "Only Python 3.8 is supported by PyInstaller on Linux (see https://github.com/pypa/manylinux/issues/1149)"
        )
    if len(versions) >= 1:
        common.print_info(f"Building with Python 3.8 on Linux")
        common.linux_docker_run(
            build,
            " && ".join(
                (
                    "source /opt/rh/rh-python38/enable",
                    "python3 {}".format(common.pip_install_pyproject(pyproject, "linux")),
                    "python3 {}".format(
                        common.pyinstaller(
                            project=project,
                            target="/build",
                            pyproject=pyproject,
                            version="3.8",
                            suffix="manylinux",
                            guest="linux",
                        )
                    ),
                    *(
                        ()
                        if post is None
                        else (
                            "printf \\'{}\\n\\'".format(common.format_info(f"Running {post.as_posix()}")),
                            "python3 {}".format(post.as_posix()),
                        )
                    ),
                )
            ),
        )
        common.rsync(build, host_path=output, guest_path="build/", host_to_guest=False)

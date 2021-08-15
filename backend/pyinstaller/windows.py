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
    common.print_info(f"Copying project files to Windows")
    common.rsync_windows_utilities(build)
    common.vagrant_run(build, "rmdir /s /q project 2>nul & rmdir /s /q build 2>nul & mkdir build")
    common.rsync(build, host_path=project, guest_path="project", host_to_guest=True)
    for version in versions:
        for suffix, version_string, python in (
            ("win", version, '"C:\\Program Files\\Python{}\\python.exe"'.format(version.replace(".", ""))),
            (
                "win32",
                f"{version} (32 bits)",
                '"C:\\Program Files (x86)\\Python{}-32\\python.exe"'.format(version.replace(".", "")),
            ),
        ):
            common.print_info(f"Building with Python {version_string} on Windows")
            common.vagrant_run(
                build,
                " && ".join(
                    (
                        "echo off",
                        "cd project",
                        "{} {}".format(python, common.pip_install_pyproject(pyproject, "windows")),
                        "{} {}".format(
                            python,
                            common.pyinstaller(
                                project=project,
                                target="..\\build",
                                pyproject=pyproject,
                                version=version,
                                suffix=suffix,
                                guest="windows",
                            ),
                        ),
                        *(
                            ()
                            if post is None
                            else (
                                "{} ..\\utilities\\echo.py {}".format(python, f"Running {post.as_posix()}"),
                                "{} {}".format(python, post.as_posix()),
                            )
                        ),
                    )
                ),
            )
            common.rsync(build, host_path=output, guest_path="build", host_to_guest=False)

from cubuzoa import common
import pathlib
import typing


def os_build(
    versions: tuple[str, ...],
    project: pathlib.Path,
    output: pathlib.Path,
    build: pathlib.Path,
    pre: pathlib.Path,
    post: pathlib.Path,
    pyproject: dict[str, typing.Any],
):
    common.print_info(f"Copying project files to Windows")
    common.rsync_windows_utilities(build)
    common.vagrant_run(
        build, "rmdir /s /q project 2>nul & rmdir /s /q wheels 2>nul & mkdir wheels"
    )
    common.rsync(build, host_path=project, guest_path="project", host_to_guest=True)
    for version in versions:
        for version_string, python in (
            (
                version,
                '"C:\\Program Files\\Python{}\\python.exe"'.format(
                    version.replace(".", "")
                ),
            ),
            (
                f"{version} (32 bits)",
                '"C:\\Program Files (x86)\\Python{}-32\\python.exe"'.format(
                    version.replace(".", "")
                ),
            ),
        ):
            common.print_info(f"Building for Python {version_string} on Windows")
            common.vagrant_run(
                build,
                " && ".join(
                    (
                        "echo off",
                        "rmdir /s /q new-wheels 2>nul & rmdir /s /q new-wheels 2>nul & mkdir new-wheels",
                        "cd project",
                        *(
                            ()
                            if pre is None
                            else (
                                "{} ..\\utilities\\echo.py {}".format(
                                    python, f"Running {pre.as_posix()}"
                                ),
                                "{} {}".format(python, pre.as_posix()),
                            )
                        ),
                        "{} {}".format(python, common.pip_wheel("..\\new-wheels")),
                        *(
                            ()
                            if post is None
                            else (
                                "for %w in (..\\new-wheels\\*.whl) do {} {}".format(
                                    python, common.pip_install("%w")
                                ),
                                "{} ..\\utilities\\echo.py {}".format(
                                    python, f"Running {post.as_posix()}"
                                ),
                                "{} {}".format(python, post.as_posix()),
                                "for %w in (..\\new-wheels\\*.whl) do {} {}".format(
                                    python, common.pip_uninstall("%w")
                                ),
                            )
                        ),
                        "move /y ..\\new-wheels\\*.whl ..\\wheels\\",
                    )
                ),
            )
            common.rsync(
                build, host_path=output, guest_path="wheels", host_to_guest=False
            )

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
    common.print_info(f"Copying project files to macOS")
    common.vagrant_run(build, "rm -rf project; rm -rf wheels; mkdir wheels")
    common.rsync(build, host_path=project, guest_path="project", host_to_guest=True)
    for version in versions:
        common.print_info(f"Building for Python {version} on macOS")
        common.vagrant_run(
            build,
            " && ".join(
                (
                    "rm -rf new-wheels",
                    "mkdir new-wheels",
                    "cd project",
                    *(
                        ()
                        if pre is None
                        else (
                            "printf '{}\n'".format(
                                common.format_info(f"Running {pre.as_posix()}")
                            ),
                            "/usr/local/bin/pyenv exec python3 {}".format(
                                pre.as_posix()
                            ),
                        )
                    ),
                    "/usr/local/bin/pyenv local {}".format(
                        common.os_to_configuration["macos"].version_to_name[version]
                    ),
                    "/usr/local/bin/pyenv exec python3 {}".format(
                        common.pip_wheel("../new-wheels")
                    ),
                    *(
                        ()
                        if post is None
                        else (
                            ";".join(
                                (
                                    "for wheel in ../new-wheels/*.whl",
                                    "    do /usr/local/bin/pyenv exec python3 {}".format(
                                        common.pip_install("$wheel")
                                    ),
                                    "done",
                                )
                            ),
                            "printf '{}\n'".format(
                                common.format_info(f"Running {post.as_posix()}")
                            ),
                            "/usr/local/bin/pyenv exec python3 {}".format(
                                post.as_posix()
                            ),
                            ";".join(
                                (
                                    "for wheel in ../new-wheels/*.whl",
                                    "    do /usr/local/bin/pyenv exec python3 {}".format(
                                        common.pip_uninstall("$wheel")
                                    ),
                                    "done",
                                )
                            ),
                        )
                    ),
                    "mv ../new-wheels/* ../wheels/",
                )
            ),
        )
        common.rsync(build, host_path=output, guest_path="wheels/", host_to_guest=False)

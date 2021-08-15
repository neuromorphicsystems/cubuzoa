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
    common.vagrant_run(build, "sudo rm -rf project; sudo rm -rf wheels; mkdir wheels")
    common.rsync(build, host_path=project, guest_path="project", host_to_guest=True)
    for version in versions:
        python_path = common.os_to_configuration["linux"].version_to_name[version]
        common.print_info(f"Building for Python {version} on Linux")
        common.linux_docker_run(
            build,
            " && ".join(
                (
                    "mkdir ../unaudited-wheels",
                    "mkdir ../new-wheels",
                    " ".join(
                        (
                            "{}/maturin".format(common.os_to_configuration["linux"].default_name()),
                            "build",
                            "--interpreter",
                            f"{python_path}/python3",
                            "--release",
                            "--strip",
                            "--no-sdist",
                            "--out",
                            "../new-wheels",
                        )
                    ),
                    *(
                        ()
                        if post is None
                        else (
                            ";".join(
                                (
                                    "for wheel in /new-wheels/*.whl",
                                    "    do {}/python {}".format(python_path, common.pip_install("$wheel")),
                                    "done",
                                )
                            ),
                            "printf \\'{}\\n\\'".format(common.format_info(f"Running {post.as_posix()}")),
                            "{}/python {}".format(python_path, post.as_posix()),
                            ";".join(
                                (
                                    "for wheel in /new-wheels/*.whl",
                                    "    do {}/python {}".format(python_path, common.pip_uninstall("$wheel")),
                                    "done",
                                )
                            ),
                        ),
                    ),
                    "mv ../new-wheels/* /wheels/",
                )
            ),
        )
        common.rsync(build, host_path=output, guest_path="wheels/", host_to_guest=False)

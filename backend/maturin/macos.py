def os_build(common, versions, project, wheels, build, post):
    common.print_info(f"Copying project files to macOS")
    common.vagrant_run(build, "rm -rf project; rm -rf wheels; mkdir wheels")
    common.rsync(build, host_path=project, guest_path="project", host_to_guest=True)
    for version in versions:
        python_version = common.os_to_configuration["macos"].version_to_name[version]
        common.print_info(f"Building for Python {version} on macOS")
        common.vagrant_run(
            build,
            " && ".join(
                (
                    "rm -rf new-wheels",
                    "mkdir new-wheels",
                    "cd project",
                    " ".join(
                        (
                            "/Users/vagrant/.pyenv/versions/{}/bin/maturin".format(
                                common.os_to_configuration["macos"].default_name()
                            ),
                            "build",
                            "--interpreter",
                            f"/Users/vagrant/.pyenv/versions/{python_version}/bin/python3",
                            "--release",
                            "--strip",
                            "--no-sdist",
                            "--out",
                            "../new-wheels",
                        )
                    ),
                    f"/usr/local/bin/pyenv local {python_version}",
                    *(
                        ()
                        if post is None
                        else (
                            ";".join(
                                (
                                    "for wheel in ../new-wheels/*.whl",
                                    "    do /usr/local/bin/pyenv exec python3 {}".format(common.pip_install("$wheel")),
                                    "done",
                                )
                            ),
                            "printf '{}\n'".format(common.format_info(f"Running {post.as_posix()}")),
                            "/usr/local/bin/pyenv exec python3 {}".format(post.as_posix()),
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
        common.rsync(build, host_path=wheels, guest_path="wheels/", host_to_guest=False)

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
    common.vagrant_run(build, "rmdir /s /q project 2>nul & rmdir /s /q wheels 2>nul & mkdir wheels")
    common.rsync(build, host_path=project, guest_path="project", host_to_guest=True)
    maturin = '"C:\\Program Files\\Python{}\\Scripts\\maturin.exe"'.format(
        common.os_to_configuration["windows"].default_version().replace(".", "")
    )
    for version in versions:
        for version_string, python, target in (
            (
                version,
                '"C:\\Program Files\\Python{}\\python.exe"'.format(version.replace(".", "")),
                "x86_64-pc-windows-msvc",
            ),
            (
                f"{version} (32 bits)",
                '"C:\\Program Files (x86)\\Python{}-32\\python.exe"'.format(version.replace(".", "")),
                "i686-pc-windows-msvc",
            ),
        ):
            common.print_info(f"Building for Python {version_string} on Windows")
            common.vagrant_run(build, "rmdir /s /q new-wheels 2>nul & rmdir /s /q new-wheels 2>nul & mkdir new-wheels")
            common.vagrant_run(
                build,
                " && ".join(
                    (
                        "echo off",
                        "rmdir /s /q new-wheels 2>nul & rmdir /s /q new-wheels 2>nul & mkdir new-wheels",
                        "cd project",
                        " ".join(
                            (
                                maturin,
                                "build",
                                "--interpreter",
                                python,
                                "--release",
                                "--strip",
                                "--target",
                                target,
                                "--no-sdist",
                                "--out",
                                "..\\new-wheels",
                            )
                        ),
                        *(
                            ()
                            if post is None
                            else (
                                "for %w in (..\\new-wheels\\*.whl) do {} {}".format(python, common.pip_install("%w")),
                                "{} ..\\utilities\\echo.py {}".format(python, f"Running {post.as_posix()}"),
                                "{} {}".format(python, post.as_posix()),
                                "for %w in (..\\new-wheels\\*.whl) do {} {}".format(python, common.pip_uninstall("%w")),
                            )
                        ),
                        "move /y ..\\new-wheels\\*.whl ..\\wheels\\",
                    )
                ),
            )
            common.rsync(build, host_path=output, guest_path="wheels", host_to_guest=False)

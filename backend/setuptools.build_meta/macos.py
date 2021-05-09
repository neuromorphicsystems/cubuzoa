def os_build(common, versions, project, wheels, build):
    common.info(f'Copying project files to macOS')
    common.vagrant_run(build, 'rm -rf project; rm -rf wheels; mkdir wheels')
    common.rsync(build, host_path=project, guest_path='project', host_to_guest=True)
    for version in versions:
        common.info(f'Building for Python {version} on macOS')
        common.vagrant_run(build, ' && '.join((
            'cd project',
            '/usr/local/bin/pyenv local {}'.format(common.os_to_configuration['macos'].version_to_name[version]),
            '/usr/local/bin/pyenv exec python3 {}'.format(common.pip_wheel('../wheels')),
        )))
        common.rsync(build, host_path=wheels, guest_path='wheels/', host_to_guest=False)

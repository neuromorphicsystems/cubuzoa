def os_build(common, versions, project, wheels, build):
    common.info(f'Copying project files to macOS')
    common.vagrant_run(build, 'rm -rf project; rm -rf wheels; mkdir wheels')
    common.rsync(build, host_path=project, guest_path='project', host_to_guest=True)
    for version in versions:
        common.info(f'Building for Python {version} on macOS')
        common.vagrant_run(build, ' '.join((
            'cd project',
            '&&',
            '/Users/vagrant/.pyenv/versions/{}/bin/maturin'.format(
                common.os_to_configuration['macos'].default_name()),
            'build',
            '--interpreter',
            '/Users/vagrant/.pyenv/versions/{}/bin/python3'.format(
                common.os_to_configuration['macos'].version_to_name[version]),
            '--release',
            '--strip',
            '--no-sdist',
            '--out',
            '../wheels')))
        common.rsync(build, host_path=wheels, guest_path='wheels/', host_to_guest=False)

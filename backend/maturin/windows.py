def os_build(common, versions, project, wheels, build):
    common.info(f'Copying project files to Windows')
    common.vagrant_run(build, 'rmdir /s /q project 2>nul & rmdir /s /q wheels 2>nul &')
    common.rsync(build, host_path=project, guest_path='project', host_to_guest=True)
    maturin = '"C:\\Program Files\\Python{}\\Scripts\\maturin.exe"'.format(
        common.os_to_configuration['windows'].default_version().replace('.', ''))
    for version in versions:
        common.info(f'Building for Python {version} on Windows')
        common.vagrant_run(build, ' '.join((
            'cd project',
            '&&',
            maturin,
            'build',
            '--interpreter',
            '"C:\\Program Files\\Python{}\\Python.exe"'.format(version.replace('.', '')),
            '--release',
            '--strip',
            '--target',
            'x86_64-pc-windows-msvc',
            '--no-sdist',
            '--out',
            '..\\wheels')))
        common.rsync(build, host_path=wheels, guest_path='wheels', host_to_guest=False)
        common.info(f'Building for Python {version} (32 bits) on Windows')
        common.vagrant_run(build, ' '.join((
            'cd project',
            '&&',
            maturin,
            'build',
            '--interpreter',
            '"C:\\Program Files (x86)\\Python{}-32\\Python.exe"'.format(version.replace('.', '')),
            '--release',
            '--strip',
            '--target',
            'i686-pc-windows-msvc',
            '--no-sdist',
            '--out',
            '..\\wheels')))
        common.rsync(build, host_path=wheels, guest_path='wheels', host_to_guest=False)

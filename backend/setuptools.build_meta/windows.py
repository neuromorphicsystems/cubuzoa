def os_build(common, versions, project, wheels, build):
    common.info(f'Copying project files to Windows')
    common.vagrant_run(build, 'rmdir /s /q project 2>nul & rmdir /s /q wheels 2>nul &')
    common.rsync(build, host_path=project, guest_path='project', host_to_guest=True)
    for version in versions:
        common.info(f'Building for Python {version} on Windows')
        common.vagrant_run(build, 'cd project && "C:\\Program Files\\Python{}\\python.exe" {}'.format(
            version.replace('.', ''),
            common.pip_wheel('..\\wheels')))
        common.rsync(build, host_path=wheels, guest_path='wheels', host_to_guest=False)
        common.info(f'Building for Python {version} (32 bits) on Windows')
        common.vagrant_run(build, 'cd project && "C:\\Program Files (x86)\\Python{}-32\\python.exe" {}'.format(
            version.replace('.', ''),
            common.pip_wheel('..\\wheels')))
        common.rsync(build, host_path=wheels, guest_path='wheels', host_to_guest=False)

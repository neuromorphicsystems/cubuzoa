def os_build(common, versions, project, wheels, build):
    common.info(f'Copying project files to Linux')
    common.vagrant_run(build, 'sudo rm -rf project; sudo rm -rf wheels')
    common.rsync(build, host_path=project, guest_path='project', host_to_guest=True)
    for version in versions:
        common.info(f'Building for Python {version} on Linux')
        common.linux_docker_run(build, '{} {}'.format(
            common.os_to_configuration['linux'].version_to_name[version],
            common.pip_wheel('/wheels')))
        common.rsync(build, host_path=wheels, guest_path='wheels/', host_to_guest=False)

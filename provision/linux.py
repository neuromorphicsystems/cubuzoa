def os_provision(common, build):
    configuration = common.os_to_configuration['linux']
    common.info(f'Installing Linux with Python versions {common.versions_to_string(configuration.versions())}')
    common.vagrant_destroy(build)
    common.vagrant_add(configuration.box)
    with open(build / 'Dockerfile', 'w') as dockerfile:
        dockerfile.write('\n'.join((
            'FROM quay.io/pypa/manylinux2014_x86_64',
            'ENV USER root',
            'ENV PATH {}:$PATH'.format(':'.join(configuration.names())),
            'RUN mkdir /project',
            'RUN mkdir /wheels',
            'WORKDIR /project',
        )))
    with open(build / 'Vagrantfile', 'w') as vagrantfile:
        vagrantfile.write('\n'.join((
            '$provision = <<-\'SCRIPT\'',
            '    printf \'Installing docker\\n\'',
            '    export DEBIAN_FRONTEND=noninteractive',
            '    apt-get update -qq -o=Dpkg::Use-Pty=0 > /dev/null',
            '    apt-get install -qq -o=Dpkg::Use-Pty=0 docker.io > /dev/null 2>&1',
            '    usermod -aG docker vagrant',
            '    printf \'Downloading manylinux\\n\'',
            '    docker build manylinux -t manylinux -q --rm',
            'SCRIPT',
            'Vagrant.configure("2") do |config|',
            '    config.vm.box = "{}"'.format(configuration.box),
            '    config.vm.synced_folder ".", "/vagrant", disabled: true',
            '    config.vm.provision "file", source: "{}", destination: "manylinux/Dockerfile"'.format(build / 'Dockerfile'),
            '    config.vm.provision "shell", inline: $provision',
            '    config.vm.provider "virtualbox" do |v|',
            '        v.name = "{}"'.format(common.box_name('linux')),
            '        v.check_guest_additions = false',
            '    end',
            '    config.ssh.insert_key = false',
            'end',
        )))
    common.vagrant_up(build)

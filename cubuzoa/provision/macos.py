from cubuzoa import common
import pathlib


def os_provision(build: pathlib.Path):
    configuration = common.os_to_configuration["macos"]
    common.print_info(
        f"Installing macOS with Python {common.versions_to_string(configuration.versions())}"
    )
    common.vagrant_destroy(build)
    common.vagrant_add(configuration.box)
    build.mkdir(exist_ok=True)
    with open(build / "Vagrantfile", "w") as vagrantfile:
        vagrantfile.write(
            "\n".join(
                (
                    "$provision = <<-'SCRIPT'",
                    "brew update",
                    "brew install pyenv",
                    *(
                        "\n".join(
                            (
                                'PYTHON_CONFIGURE_OPTS="--enable-framework" pyenv install {}'.format(
                                    name
                                ),
                                "pyenv local {}".format(name),
                                "pyenv exec python3 -m pip install --upgrade pip",
                            )
                        )
                        for name in configuration.names()
                    ),
                    "brew install rustup-init",
                    "rustup-init -y",
                    "source $HOME/.cargo/env",
                    "rustup target add aarch64-apple-darwin x86_64-apple-darwin",
                    "brew install upx",
                    *(
                        "\n".join(
                            (
                                "pyenv local {}".format(name),
                                "pyenv exec python3 -m pip install pyinstaller",
                            )
                        )
                        for name in configuration.names()
                    ),
                    "pyenv local {}".format(configuration.default_name()),
                    "pyenv exec python3 -m pip install maturin",
                    "SCRIPT",
                    'Vagrant.configure("2") do |config|',
                    '    config.vm.box = "{}"'.format(configuration.box),
                    '    config.vm.synced_folder ".", "/vagrant", disabled: true',
                    '    config.vm.provision "shell", inline: $provision, privileged: false',
                    '    config.vm.provider "virtualbox" do |v|',
                    '        v.name = "{}"'.format(common.box_name("macos")),
                    "        v.check_guest_additions = false",
                    "    end",
                    "    config.ssh.insert_key = false",
                    '    config.trigger.after :"VagrantPlugins::ProviderVirtualBox::Action::Import", type: :action do |t|',
                    "        t.ruby do |env, machine|",
                    "            FileUtils.cp(",
                    '                machine.box.directory.join("include").join("macOS.nvram").to_s,',
                    '                machine.provider.driver.execute_command(["showvminfo", machine.id, "--machinereadable"]).',
                    "                    split(/\n/).",
                    "                    map {|line| line.partition(/=/)}.",
                    '                    select {|partition| partition.first == "BIOS NVRAM File"}.',
                    "                    last.",
                    "                    last[1..-2]",
                    "            )",
                    "        end",
                    "    end",
                    "end",
                )
            )
        )
    common.vagrant_up(build, experimental="typed_triggers")

from cubuzoa import common
import pathlib


def os_provision(build: pathlib.Path):
    configuration = common.os_to_configuration["windows"]
    common.print_info(
        f"Installing Windows with Python {common.versions_to_string(configuration.versions())}"
    )
    common.vagrant_destroy(build)
    common.vagrant_add(configuration.box)
    build.mkdir(exist_ok=True)
    with open(build / "Vagrantfile", "w") as vagrantfile:
        vagrantfile.write(
            "\n".join(
                (
                    "$provision = <<-'SCRIPT'",
                    "function Install-Python($version, $suffix) {",
                    'Write-Output "Installing python $version$suffix"',
                    "Invoke-WebRequest `",
                    '    -URI "https://www.python.org/ftp/python/$version/python-$version$suffix.exe" `',
                    '    -OutFile "C:\\Users\\vagrant\\python-$version$suffix.exe" `',
                    "    -UseBasicParsing",
                    '& "C:\\Users\\vagrant\\python-$version$suffix.exe" /quiet `',
                    "    InstallAllUsers=1 `",
                    "    PrependPath=1 `",
                    "    Include_test=0",
                    "}",
                    "function Upgrade-pip($directory) {",
                    '    Write-Output "Upgradigng pip for $directory"',
                    '    & "$directory\\python.exe" -m pip install --upgrade pip --no-warn-script-location',
                    "}",
                    *(
                        "Install-Python {} '-amd64'".format(name)
                        for name in configuration.names()
                    ),
                    *(
                        "Install-Python {} ''".format(name)
                        for name in configuration.names()
                    ),
                    *(
                        "Upgrade-pip C:\\Program` Files\\Python{}".format(
                            version.replace(".", "")
                        )
                        for version in configuration.versions()
                    ),
                    *(
                        "Upgrade-pip C:\\Program` Files` `(x86`)\\Python{}-32".format(
                            version.replace(".", "")
                        )
                        for version in configuration.versions()
                    ),
                    "choco install visualstudio2019buildtools -y",
                    "choco install visualstudio2019-workload-vctools -y",
                    "choco install upx -y",
                    "Invoke-WebRequest `",
                    '    -URI "https://win.rustup.rs/x86_64" `',
                    '    -OutFile "C:\\Users\\vagrant\\rustup-init.exe" `',
                    "    -UseBasicParsing",
                    "C:\\Users\\vagrant\\rustup-init.exe -y",
                    "C:\\Users\\vagrant\\.cargo\\bin\\rustup.exe target add i686-pc-windows-msvc",
                    '& "C:\\Program Files\\Python{}\\Scripts\\pip3.exe" install maturin'.format(
                        configuration.default_version().replace(".", "")
                    ),
                    *(
                        '& "C:\\Program Files\\Python{}\\Scripts\\pip3.exe" install pyinstaller setuptools wheel'.format(
                            version.replace(".", "")
                        )
                        for version in configuration.versions()
                    ),
                    *(
                        '& "C:\\Program Files (x86)\\Python{}-32\\Scripts\\pip3.exe" install pyinstaller setuptools wheel'.format(
                            version.replace(".", "")
                        )
                        for version in configuration.versions()
                    ),
                    "choco install rsync -y",
                    "SCRIPT",
                    'Vagrant.configure("2") do |config|',
                    '    config.vm.box = "{}"'.format(configuration.box),
                    '    config.vm.synced_folder ".", "/vagrant", disabled: true',
                    '    config.vm.provision "shell", inline: $provision',
                    '    config.vm.provider "virtualbox" do |v|',
                    '        v.name = "{}"'.format(common.box_name("windows")),
                    "        v.check_guest_additions = false",
                    "    end",
                    "    config.ssh.insert_key = false",
                    "end",
                )
            )
        )
    common.vagrant_up(build)

![banner](banner.png)

Cubuzoa is a script that builds Python wheels for Linux, macOS and Windows on a single host operating system by spawning VirtualBox machines.

Tested on the following host operating systems:
- Ubuntu 20.04
- macOS Big Sur 11.3.1

A full installation requires about `75 GB` of free disk space for the following resources:
- Linux Vagrant box (`0.5 GB`)
- macOS Vagrant box (`11 GB`)
- Windows Vagrant box (`16 GB`)
- Linux VirtualBox machine (`2.9 GB`)
- macOS VirtualBox machine (`22 GB`)
- Window VirtualBox machine (`22 GB`)

Partial installations are supported, reducing disk usage accordingly. Cubuzoa provides an uninstallation script to delete all used resources.

# Dependencies

Cubuzoa requires VirtualBox with its Extension Pack (https://www.virtualbox.org/wiki/Downloads) and Vagrant (https://www.vagrantup.com/downloads). They can be downloaded from the command line with:

- __Ubuntu__
  ```sh
  sudo apt install virtualbox virtualbox-ext-pack
  curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -
  sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
  sudo apt update
  sudo apt install vagrant
  ```
- __macOS__
  ```sh
  brew install --cask virtualbox virtualbox-extension-pack
  brew tap hashicorp/tap
  brew install hashicorp/tap/vagrant
  ```
- __Windows__
  ```sh
  choco install virtualbox --params "/ExtensionPack"
  choco install vagrant
  ```

# Usage

1. Download and start the VirtualBox machines
  ```sh
  python3 cubuzoa.py provision
  ```

2. Build wheels for a Python project
  ```sh
  python3 cubuzoa.py build /path/to/python/project
  ```

3. Stop the machines and delete all downloaded resources
  ```sh
  python3 cubuzoa.py unprovision --prune
  ```

Step 2 can be repeated any number of times with different projects.

# Documentation

## Provision

`cubuzoa.py provision [-h] [--os OS] [--force]`

Optional arguments:
- `-h`, `--help` show this help message and exit
- `--os OS` operating system regex, case insensitive (defaults to `.*`)
- `--force` install VMs even if they already exist

## Build

`cubuzoa.py build [-h] [--wheels WHEELS] [--os OS] [--version VERSION] [--skip-sdist] project`

Positional arguments:
- `project` path to the project directory

Optional arguments:
- `-h`, `--help` show this help message and exit
- `--wheels WHEELS` path to the output wheels directory, defaults to `[project]/wheels`
- `--os OS` operating system regex, case insensitive (defaults to `.*`)
- `--version VERSION` version specifiers in PEP 440 format (defaults to `>=3.7,<=3.9`, see https://www.python.org/dev/peps/pep-0440/#version-specifiers)
- `--skip-sdist` do not create a source distribution

## Unprovision

`cubuzoa.py unprovision [-h] [--prune] [--clean]`

Optional arguments:
- `-h`, `--help` show this help message and exit
- `--prune` delete downloaded Vagrant boxes
- `--clean` delete any VirtualBox machine whose name starts with `cubuzoa-`

# Example Python projects using Cubuzoa

- https://github.com/neuromorphicsystems/event_stream

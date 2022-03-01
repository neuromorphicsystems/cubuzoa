![banner](banner.png)

Cubuzoa builds Python wheels for Linux, macOS, and Windows on a single host operating system by spawning VirtualBox machines.

- [Host OS requirements](#host-os-requirements)
- [Python versions](#python-versions)
- [Backends](#backends)
- [Dependencies](#dependencies)
- [Usage](#usage)
- [Documentation](#documentation)
  - [Provision](#provision)
  - [Build](#build)
  - [Unprovision](#unprovision)
- [Example Python projects that use Cubuzoa](#example-python-projects-that-use-cubuzoa)
- [Contribute](#contribute)

# Host OS requirements

Cubuzoa should work on any operating system supported by Virtual Box. It has been tested on the following **host** operating systems so far:

-   Ubuntu 20.04
-   macOS Big Sur 11.3.1

A complete installation requires about `75 GB` of free disk space for the following resources:

-   Linux Vagrant box (`0.5 GB`)
-   macOS Vagrant box (`11 GB`)
-   Windows Vagrant box (`16 GB`)
-   Linux VirtualBox machine (`2.9 GB`)
-   macOS VirtualBox machine (`22 GB`)
-   Window VirtualBox machine (`22 GB`)

# Python versions

Cubuzoa compiles wheels and frozen packages for:
- Python 3.7
- Python 3.8
- Python 3.9

Linux guest builds rely on Manylinux 2014 x86-64 (https://github.com/pypa/manylinux).

Windows guest builds create both 32-bits and 64-bits versions.

# Backends

The build backend is automatically determined by parsing `pyproject.toml` in the target project directory. The following build backends are supported:

-   `"setuptools.build_meta"` (https://setuptools.readthedocs.io/en/latest/build_meta.html)
-   `"maturin"` (https://github.com/PyO3/maturin)
-   `"pyinstaller"` (https://www.pyinstaller.org)

# Dependencies

Cubuzoa requires VirtualBox with its Extension Pack (https://www.virtualbox.org/wiki/Downloads) and Vagrant (https://www.vagrantup.com/downloads). You can download them from the command line with the following commands:

-   **Ubuntu**
    ```sh
    sudo apt install virtualbox virtualbox-ext-pack
    curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -
    sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
    sudo apt update
    sudo apt install vagrant
    ```
-   **macOS**
    ```sh
    brew install --cask virtualbox virtualbox-extension-pack
    brew tap hashicorp/tap
    brew install hashicorp/tap/vagrant
    ```
-   **Windows**
    ```sh
    choco install virtualbox --params "/ExtensionPack"
    choco install vagrant
    ```

# Usage

1. Clone this repository and install Python dependencies

```
git clone https://github.com/neuromorphicsystems/cubuzoa.git
cd cubuzoa
pip3 install -r requirements.txt
```

2. Download and start the VirtualBox machines

```sh
python3 -m cubuzoa provision
```

3. Build wheels or frozen packages for a Python project

```sh
python3 -m cubuzoa build /path/to/python/project
```

4. Stop the machines and delete all downloaded resources

```sh
python3 -m cubuzoa unprovision --prune
```

You may repeat step 3 any number of times with different projects.

# Documentation

## Provision

`python3 -m cubuzoa provision [-h] [--os OS] [--force]`

Optional arguments:

-   `-h`, `--help` show this help message and exit
-   `--os OS` operating system regex filter, case insensitive (defaults to `.*`)
-   `--force` install VMs even if they already exist

## Build

`python3 -m cubuzoa build [-h] [--wheels WHEELS] [--os OS] [--version VERSION] [--skip-sdist] project`

Positional arguments:

-   `project` path to the project directory

Optional arguments:

-   `-h`, `--help` show this help message and exit
-   `--wheels WHEELS` path to the output wheels directory, defaults to `[project]/wheels`
-   `--os OS` operating system regex, case insensitive (defaults to `.*`)
-   `--version VERSION` version specifiers in PEP 440 format (defaults to `>=3.7,<=3.9`, see https://www.python.org/dev/peps/pep-0440/#version-specifiers)
-   `--skip-sdist` do not create a source distribution

## Unprovision

`python3 -m cubuzoa unprovision [-h] [--prune] [--clean]`

Optional arguments:

-   `-h`, `--help` show this help message and exit
-   `--prune` delete downloaded Vagrant boxes
-   `--clean` delete any VirtualBox machine whose name starts with `cubuzoa-`

# Example Python projects that use Cubuzoa

-   https://github.com/neuromorphicsystems/event_stream (setuptools)
-   https://github.com/neuromorphicsystems/aedat (maturin)

# Contribute

Run `black .` to format the source code (see https://github.com/psf/black).
Run `pyright .` to check types (see https://github.com/microsoft/pyright).

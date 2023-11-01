# brafar-python

## About

This is an implementation of the brafar-python tool for Python introductory programming assignments.

## Setup

### Operation System

The package is currently supported/tested on the following operating systems:
* Ubuntu
* MacOS

### Install Python packages
The package is currently supported/tested on the following Python versions:
* python3
```shell
sudo apt-get install python3 python3-pip
```
* zss
```shell
pip3 install zss
```
* timeout_decorator
```shell
pip3 install timeout_decorator
```

* fastcache
```shell
pip3 install fastcache
```
* numpy
```shell
pip3 install numpy
```
### Docker environment

As an alternate to setting up the Python packages manually, the same environment can be obtained by building a docker image based on ```Dockerfile```.
```
docker build -t brafar-python .
```

## Running brafar-python

Brafar-python tool is invoked using the command line interface offered by ```brafar-python/run.py```. For example, the below command runs brafar-python on the target buggy program of ```question_1``` in the ```./example``` directory, with 100% sampling rate of correct programs.
```
python3 brafar-python/run.py ./example -q question_1 -s 100 -o output/patches
```

### Command line arguments
* ```-d``` flag specifies the path of data directory.
* ```-q``` flag specifies the question (folder) name within data directory.
* ```-s``` flag specifies the sampling rate.
* ```-o``` flag specifies the output directory.

### Output
After the completion of a run by brafar-python tool, the generated repaired code will be output in the question directory and one patch file in unified diff format for the provided source code will be generated in the output directory.

# LSpy


## Description
Loosely implementation of the UNIX [ls](https://linuxcommand.org/lc3_man_pages/ls1.html) command in Python.

## Requirements
Python 3.8 or higher.

## Usage 
```sh
lspy [-h] [--long] [--all] [--sort] [--recursive] [files [files ...]]
```
### Avaible options:
#### - positional arguments:
- files: file paths
#### - optional arguments:
- -l: use a long listing format
- -a: do not ignore entries starting with .
- -S: sort by file size
- -R: list subdirectories recursively
### Example run
#### - script:
```sh
python lspy.py -al ./
```

#### - installed module:

```sh
# install module
pip install .

lspy -al ./
```

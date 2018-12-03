# StubDB
## Description
Extract valid interface signals from an interface specification, create a list of global declarations, RTE function calls and update the interface database for testing, and update the stubs by inserting the global declarations and RTE function calls in their respective modules. RTE read/write functions not found in the RTE API list of the stub will have their corresponding function calls commented out to avoid compile errors.

## Requirements
Aside from the libraries listed in the requirements.txt file, I used the following:
*  [Python 3.7](https://www.python.org/downloads/release/python-370/)

### What's in `requirements.txt`?
*  pandas 0.23.4
*  xlrd 1.1.0
*  openpyxl 2.5.9
*  numpy 1.15.3

## Usage
### Before anything else..
*  By default, stub files should be place in the `Stubs` folder of the script directory
```
   ./Stubs
      |- A.c
      |- B.c
      |- C.c
      :
      |- Z.c
```

### Command line syntax
This package uses 2 Python scripts:
*  `PrepareData.py` - extracts valid interface signals from the interface specification, create a list of global declarations, RTE function calls and update the interface database for testing
```
py PrepareData.py <interface specification in Excel>
```
*  `UpdateStubs.py` - updates the stubs by inserting the global declarations or RTE function calls in their respective modules, by using `declarations` and `functions`, respectively
```
py UpdateStubs.py <declarations/functions> [-s <stub folder path>]
```

## What's next?
*  Code optimization
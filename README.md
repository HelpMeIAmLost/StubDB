# StubDB
## Description
Extract valid interface signals from an interface specification, create a list of global declarations, RTE function calls and update the interface database for testing, and update the stubs by inserting the global declarations and RTE function calls in their respective modules.

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
*  DBC files should be in the following folder structure relative to the script folder (DBC file names could be different:
```
   ./DBC
      |- <variant 1>
         |- FILE1_<var 1>.dbc
         |- FILE2_<var 1>.dbc
         |- FILE3_<var 1>.dbc
         |- FILE4_<var 1>.dbc
      |- <variant 2>
         |- FILE1_<var 2>.dbc
         |- FILE2_<var 2>.dbc
         |- FILE3_<var 2>.dbc
         |- FILE4_<var 2>.dbc
      :
      |- <variant n>
         |- FILE1_<var n>.dbc
         |- FILE2_<var n>.dbc
         |- FILE3_<var n>.dbc
         |- FILE4_<var n>.dbc
```

### Command line syntax
This package uses 2 Python scripts:
*  `PrepareData.py` - extracts valid interface signals from the interface specification, create a list of global declarations, RTE function calls and update the interface database for testing
```
py PrepareData.py <interface specification in Excel>
```
*  `UpdateStubs.py` - updates the stubs by inserting the global declarations and RTE function calls in their respective modules
```
py UpdateStubs.py <declarations/functions> [-s <stub folder path>]
```

## What's next?
*  Code optimization
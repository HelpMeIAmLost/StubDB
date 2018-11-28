from common_util import *
from StringUtils import *
from pathlib import Path

import os
import re
import sys
import argparse
import numpy as np
import linecache


# #             Sheet name , Use cols
# #             [0]        , [1]
# inputData0 =
# inputData1 =

dataHandler = {'declarations': ['GlobalDeclarationsList.xlsx', 'Global Declarations', 'A:B', OFF],
               'functions': ['ForMCUAppMethod.xlsx', 'Function Calls', 'A:B', OFF]}


def filter_data(args):
    # From util.py
    data_frame = read_excel_file(dataHandler[args.section][0], dataHandler[args.section][1:4])

    for root, dirs, files in os.walk(Path(args.stubs_folder)):
        for file in files:
            if file.endswith('.c'):
                module_name = file[:-2].lower()
                data_frame['TargetModule'] = data_frame.TargetModule.astype(str).str.lower()
                filtered_data = data_frame[data_frame['TargetModule'] == module_name]

                if len(filtered_data.head(1)) == 0:
                    print('No global declarations and RTE read/write calls for {}'.format(file[:-2]))
                else:
                    if args.section == 'declarations':
                        string = '<< Start of include and declaration area >>'
                        column_name = 'Declarations'
                        skip_count = 2
                        spaces = ''
                    else:
                        string = '<< Start of runnable implementation >>'
                        column_name = 'Function_Name'
                        skip_count = 3
                        spaces = '  '

                    if module_name == 'acc_main':
                        skip_count += 3
                    filename = os.path.join(root, file)
                    success = insert_lines_of_code(filename, filtered_data[column_name], string, skip_count, spaces)
                    if success:
                        if args.section == 'declarations':
                            print('Finished inserting global declarations for {}'.format(file[:-2]))
                        else:
                            print('Finished inserting RTE read and write function calls for {}'.format(file[:-2]))
                    else:
                        if args.section == 'declarations':
                            print('Failed to insert global declarations for {}'.format(file[:-2]))
                        else:
                            print('Failed to insert RTE read and write function calls for {}'.format(file[:-2]))


debug = True
# Read arguments
parser = argparse.ArgumentParser()
if debug:
    parser.add_argument('-d', dest='section', help='for debugging', default='declarations')
else:
    parser.add_argument('section', help='part of the stubs to update', choices=['declarations', 'functions'])
parser.add_argument('-s', dest='stubs_folder', help='stubs folder', default='Stubs/')
# parser.add_argument('-i', dest='input_file', help='input file', default='GlobalDeclarations.xlsx')
args = parser.parse_args()

filter_data(args)

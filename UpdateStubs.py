from common_util import *
from StringUtils import *
from pathlib import Path

import os
import argparse

data_handler = {'declarations': ['GlobalDeclarationsList.xlsx', 'Global Declarations', 'A:B', OFF],
               'functions': ['RTEFunctionCalls.xlsx', 'RTE Function Calls', 'A:B', OFF]}


def filter_data(args):
    # From util.py
    data_frame = read_excel_file(data_handler[args.section][0], data_handler[args.section][1:4])

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
                        column_name = 'FunctionCalls'
                        skip_count = 3
                        spaces = '  '

                    if module_name == 'acc_main':
                        skip_count += 3
                    filename = os.path.join(root, file)
                    success = insert_lines_of_code(args.section, filename, filtered_data[column_name], string, skip_count, spaces)
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
    parser.add_argument('-d', dest='section', help='for debugging', default='functions')
else:
    parser.add_argument('section', help='part of the stubs to update', choices=['declarations', 'functions'])
parser.add_argument('-s', dest='stubs_folder', help='stubs folder', default='Stubs/')
args = parser.parse_args()

if not os.path.exists(args.stubs_folder):
    print('{} not found!'.format(args.stubs_folder))
    print('Please make sure {} is in the script folder!'.format(args.stubs_folder))
elif not os.path.exists(data_handler[args.section][0]):
    print('{} not found!'.format(data_handler[args.section][0]))
    print('Please run the PrepareData script first!')
else:
    filter_data(args)

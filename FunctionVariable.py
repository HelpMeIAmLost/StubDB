from common_util import *
from StringUtils import *
from pathlib import Path

import sys
import pandas as pd
import numpy as np


#             Sheet name , Use cols , Skip rows
#             [0]        , [1]      , [2]
data_range = ['IF Information', 'A:M', OFF]
module = {'CAN_VP': ['CANRx_', 'IPCRx_'],
          'CTL': ['Ctl_'],
          'Others': ['Feat_']}
CAN_VP = {'CAN', 'VP'}
CTL = {'EGI','TCU_CVT','TCU_Shift','VDC'}
skip_list = {'RTE', 'FWBSW', 'NVMBSW', 'CONST', 'FMWF',
       'Ground', 'SWBSW', 'SSM', 'Input_Getway', 
       'RTE_Gateway', 'FMWR1'}

unwantedString = {'nan', '-', '', 'パラ', 'OFF', 'ON'}

inout_col = 1
source_modname_col = 2
signal_name_col = 9
module_signal_col = 11
fixed_array_size_col = 12
# The following data frame columns are for this script only
target_module_col = 13
fixed_source_signame_col = 14
source_module_signal_col = 15


def getModPosKey(df, row, col):
    index = df.iat[row, col]
    if index in CAN_VP:
        return 'CAN_VP'
    elif index in CTL:
        return 'CTL'
    else:
        return 'Others'


def create_function_name(df, row, posKey, posVal, varName, name, insideVarName ):
    
    Arr = str(df.iat[row, fixed_array_size_col])
    state = df.iat[row, inout_col]
    string = name + module[posKey][posVal] + varName
    
    if state == "IN":
        if Arr == 'nan' or Arr == '1':
            string = string + '( &' + insideVarName + ' );'
            return string
        else:
            string = string + '_Arr' + Arr + '( ' + insideVarName + ' );'
            return string
    else:
        if Arr == 'nan' or Arr == '1':
            string = string + '( ' + insideVarName + ' );'
            return string
        else:
            string = string + '_Arr' + Arr + '( ' + insideVarName + ' );'
            return string


def create_data(args, df):
    INDefault = "Rte_Read_RP_"
    OUTDefault = "Rte_Write_PP_"
    # ------------------------------
    # Data Manipulation
    function_call_list = []
    target_module_list = []
    for row in range(df.shape[0]):
        # Skip modules in skip_list
        if df.iat[row, source_modname_col] in skip_list:
            continue
        target_module = df.iat[row, target_module_col]
        signal_name = df.iat[row, signal_name_col]
        module_signal = df.iat[row, module_signal_col]
        fixed_source_signame = df.iat[row, fixed_source_signame_col]
        source_module_signal = df.iat[row, source_module_signal_col]
        state = df.iat[row, inout_col]
        inputFrom = df.iat[row, source_modname_col]
        if state == "IN":
            # CAN and VP -------------------------------------------------------
            # INDefault    + posKey  + module_signal         + module_signal
            # Rte_Read_RP_ + CANRx_  + CUS_CustomChange_ACCL + (uint8 *data)

            # CTL and Feat -----------------------------------------------------
            # INDefaule    + posKey  + source_module_signal + module_signal
            # Rte_Read_RP_ + Feat_   + FS_DetFailCode_0     + (uint8 *data)

            # Check if the input signal is from CAN or VP
            posKey = getModPosKey(df, row, source_modname_col)
            if posKey == 'CAN_VP':
                if signal_name != '':
                    if inputFrom == "CAN":  # CAN
                        function_call_list.append(create_function_name(
                            df, row, posKey, 0, module_signal, INDefault, module_signal))
                        target_module_list.append(target_module)
                    else:  # VP
                        function_call_list.append(create_function_name(
                            df, row, posKey, 1, module_signal, INDefault, module_signal))
                        target_module_list.append(target_module)
            elif posKey == 'CTL':
                if fixed_source_signame != '':
                    function_call_list.append(create_function_name(
                        df, row, posKey, 0, source_module_signal, INDefault, module_signal))
                    target_module_list.append(target_module)
                else:
                    print('1 {}: {}'.format(target_module, signal_name))
            else:
                if fixed_source_signame != '':
                    function_call_list.append(create_function_name(
                        df, row, posKey, 0, source_module_signal, INDefault, module_signal))
                    target_module_list.append(target_module)
                else:
                    print('2 {}: {}'.format(target_module, signal_name))
        else:
            # CAN and VP -------------------------------------------------------
            # INDefault     + posKey  + Module  + signal_name           + module_signal
            # Rte_Write_PP_ + Feat_   + CUS_    + CustomCont_AUTO_DRIVE + (boolean data)
            posKey = getModPosKey(df, row, target_module_col)
            if signal_name != '':
                function_call_list.append(create_function_name(
                    df, row, posKey, 0, module_signal, OUTDefault, module_signal))
                target_module_list.append(target_module)
            else:
                print('4 {}: {}'.format(target_module, signal_name))

    df = pd.DataFrame({'TargetModule': target_module_list, 'FunctionCalls': function_call_list})
    df.sort_values(by=['TargetModule', 'FunctionCalls'], ascending=True, inplace=True)
    df.drop_duplicates(keep='last', inplace=True)

    write_to_excel(df, 'RTEFunctionCalls.xlsx', 'RTE Function Calls')
    

def filter_data(args):
    target_module = 'target_module'
    source_signame = 'source_signame'
    fixed_source_signame = 'fixed_source_signame'
    source_module_signal = 'source_module_signal'
    fixed_array_size = 'fixed_array_size'

    data_frame = read_excel_file(args.input_file, data_range)
    # Create a new column named module containing the original target_model_name column
    data_frame[target_module] = data_frame['target_model_name']
    # Convert target_model_name text to lowercase
    data_frame['target_model_name'] = data_frame.target_model_name.astype(str).str.lower()

    # Remove () and other unwanted text in the source_modname column
    data_frame['source_modname'] = reg_replace(data_frame, 'source_modname', r'[\(\)]', '')
    for i in unwantedString:
        data_frame['source_modname'] = replace(data_frame, 'source_modname', i, '')

    # Create a new column with just the signal name
    data_frame[fixed_source_signame] = reg_replace(
        data_frame, source_signame, r'\[(.*){1,3}\]\[(.*){1,3}\]|\[(.*){1,3}\]', '')
    data_frame[fixed_source_signame] = reg_replace(
        data_frame, fixed_source_signame, r'^(\d+)|([\u4e00-\u9fff]+)|([\u3040-\u309Fー]+)|([\u30A0-\u30FF]+)|(-)$', '')
    # Remove unwanted text in the new column fixed_source_signame
    for i in unwantedString:
        data_frame[fixed_source_signame] = replace(data_frame, fixed_source_signame, i, '')

    data_frame[source_module_signal] = data_frame['source_modname'] + '_' + data_frame[fixed_source_signame]

    # Remove [] from fixed_array_size column and convert column values to string
    data_frame[fixed_array_size] = reg_replace(data_frame, fixed_array_size, r'[\[\]]', '')
    data_frame[fixed_array_size] = data_frame[fixed_array_size].astype(str)

    create_data(args, data_frame)


debug = True
# Read arguments
parser = argparse.ArgumentParser()
if debug:
    parser.add_argument('-i', dest='input_file', help='Excel file containing list of interface signals to be processed',
                        default='InterfaceList.xlsx')
else:
    parser.add_argument('input', help='Excel file containing the range of data to be processed')
parser.add_argument('-s', dest='stubs_folder', help='stubs folder', default='Stubs/')
args = parser.parse_args()

if not os.path.exists(args.input_file):
    print('{} not found!'.format(args.input_file))
else:
    print('Creating a list of RTE read and write function calls..')
    filter_data(args)
    print('Done!')

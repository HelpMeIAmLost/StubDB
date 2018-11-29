from common_util import *
from StringUtils import *
from sqlite3 import Error

import sys
import numpy as np
import argparse
import sqlite3

# Column header indices
target_module_col = 0
in_out_col = 1
source_module_col = 2
source_signal_col = 3
raw_target_signal_col = 4
raw_data_type_col = 5
destination_module_col = 6
destination_signal_col = 7
fixed_data_type_col = 8
fixed_target_signal_col = 9
raw_array_size_col = 10
module_signal_col = 11
fixed_array_size_col = 12
module_signal_array_col = 13


def create_data_list(cdl_data_frame, cdl_conn):
    """ create multiple data lists for all interface, internal and external signals, I/O pairing, global declarations,
    and function calls

    :param cdl_data_frame: data frame from the interface specification
    :param cdl_conn: connection to interface.db for updating its tables
    :return: None
    """
    signal_name = 'signal_name'
    data_type = 'data_type'
    array_size = 'array_size'
    fixed_array_size = 'fixed_array_size'
    module_signal = 'module_signal'
    # module_signal_array = 'module_signal_array'
    # source_input_signame = 'SigName(CAN/LIN/MDL)'

    print('Validating interface signal information from the input file')
    print('{} rows found'.format(len(cdl_data_frame.index)))
    # Rename column headers
    cdl_data_frame.rename(columns={'対象モデル': 'target_model_name'}, inplace=True)
    cdl_data_frame.rename(columns={'SigName(MDL)': 'model_signal_name'}, inplace=True)
    cdl_data_frame.rename(columns={'入力元': 'source_modname'}, inplace=True)
    cdl_data_frame.rename(columns={'SigName(CAN/LIN/MDL)': 'source_signame'}, inplace=True)
    cdl_data_frame.rename(columns={'型[配列サイズ]': 'raw_data_type'}, inplace=True)
    cdl_data_frame.rename(columns={'出力先': 'destination_modname'}, inplace=True)
    cdl_data_frame.rename(columns={'SigName(CAN/LIN/MDL).1': 'destination_signame'}, inplace=True)
    # Create column data_type from raw_data_type column and remove unwanted strings, arrays and values
    cdl_data_frame[data_type] = reg_replace(
        cdl_data_frame, 'raw_data_type', r'\[(.*){1,3}\]\[(.*){1,3}\]|\[(.*){1,3}\]', '')
    # Replace incorrect data type by 'float32'
    replace_string = {'UINT8', 'single', 'single ', 'Single'}
    for i in replace_string:
        cdl_data_frame[data_type] = replace(cdl_data_frame, data_type, i, 'float32')
    # Replace incorrect data type by 'uint8'
    replace_string = {'int8', 'unit8', 'uchar8', 'int'}
    for i in replace_string:
        cdl_data_frame[data_type] = replace(cdl_data_frame, data_type, i, 'uint8')

    # Input_Carpara -> Input_CarPara
    cdl_data_frame['source_modname'] = replace(cdl_data_frame, 'source_modname', 'Input_Carpara', 'Input_CarPara')
    # FC_common -> FC_Common
    cdl_data_frame['source_modname'] = replace(cdl_data_frame, 'source_modname', 'FC_common', 'FC_Common')
    # f_fail_Detect_State -> f_Fail_Detect_State
    cdl_data_frame['source_signame'] = replace(cdl_data_frame, 'source_signame', 'f_fail_Detect_State', 'f_Fail_Detect_State')
    cdl_data_frame['model_signal_name'] = replace(cdl_data_frame, 'model_signal_name', 'f_fail_Detect_State', 'f_Fail_Detect_State')
    # Gdel -> GDel
    cdl_data_frame['destination_signame'] = replace(cdl_data_frame, 'destination_signame', 'Gdel', 'GDel')
    # LCT_Yaw_Rad -> LCT_Yaw_rad
    cdl_data_frame['source_signame'] = replace(cdl_data_frame, 'source_signame', 'LCT_Yaw_Rad', 'LCT_Yaw_rad')
    # VspdCan -> VSpdCan
    cdl_data_frame['model_signal_name'] = replace(cdl_data_frame, 'model_signal_name', 'VspdCan', 'VSpdCan')
    # TOLLGATEWarn -> TollgateWarn
    cdl_data_frame['model_signal_name'] = replace(cdl_data_frame, 'model_signal_name', 'TOLLGATEWarn', 'TollgateWarn')
    # Unnecessary text
    # HALTフラグ -> np.nan
    cdl_data_frame['source_signame'] = replace(cdl_data_frame, 'source_signame', 'HALTフラグ', np.nan)
    # FSモデルに出力追加の予定 -> np.nan
    cdl_data_frame['source_signame'] = replace(cdl_data_frame, 'source_signame', 'FSモデルに出力追加の予定', np.nan)
    # 車種パラに追加予定-> np.nan
    cdl_data_frame['source_signame'] = replace(cdl_data_frame, 'source_signame', '車種パラに追加予定', np.nan)
    print('Removed \'HALTフラグ\', \'FSモデルに出力追加の予定\' and \'車種パラに追加予定\' in source signal name')

    # Extract just the signal name from model_signal_name and remove [] and ()
    cdl_data_frame[signal_name] = reg_replace(
        cdl_data_frame, 'model_signal_name', r'\[(.*){1,3}\]\[(.*){1,3}\]|\[(.*){1,3}\]', '')
    cdl_data_frame[signal_name] = reg_replace(
        cdl_data_frame, signal_name, r'\((.*){1,3}\)', '')
    
    # Remove CONST input signals
    invalid1 = cdl_data_frame['source_modname'] == 'CONST'
    cdl_data_frame = cdl_data_frame.drop(cdl_data_frame[invalid1].index)
    print('Removed rows with CONST input. {} rows remain'.format(len(cdl_data_frame.index)))

    invalid1 = cdl_data_frame['raw_data_type'] == '-'
    invalid2 = cdl_data_frame['raw_data_type'] == 'ー'
    invalid3 = cdl_data_frame['raw_data_type'] == '―'
    invalid4 = pd.isna(cdl_data_frame['raw_data_type'])
    invalid5 = cdl_data_frame['raw_data_type'] == '[2]'
    cdl_data_frame = cdl_data_frame.drop(cdl_data_frame[(invalid1 | invalid2 | invalid3 | invalid4 | invalid5)].index)
    print('Removed rows with \'-\', \'ー\' or no data type described. {} rows remain'.format(
        len(cdl_data_frame.index)))
    # Remove invalid signals for input
    invalid1 = cdl_data_frame['IN/OUT'] == 'IN'
    invalid2 = cdl_data_frame['source_modname'] == '-'
    invalid3 = cdl_data_frame['source_modname'] == 'ー'
    invalid4 = cdl_data_frame['source_modname'] == '―'
    invalid5 = pd.isna(cdl_data_frame['source_modname'])
    cdl_data_frame = cdl_data_frame.drop(cdl_data_frame[invalid1 & (invalid2 | invalid3 | invalid4 | invalid5)].index)
    print('Removed rows with \'-\', \'ー\' or no source module described. {} rows remain'.format(
        len(cdl_data_frame.index)))
    invalid1 = cdl_data_frame['IN/OUT'] == 'IN'
    invalid2 = cdl_data_frame['source_signame'] == '-'
    invalid3 = cdl_data_frame['source_signame'] == 'ー'
    invalid4 = cdl_data_frame['source_signame'] == '―'
    invalid5 = pd.isna(cdl_data_frame['source_signame'])
    invalid6 = cdl_data_frame.source_signame.str.find(',') != -1
    cdl_data_frame = cdl_data_frame.drop(cdl_data_frame[invalid1 &
                                                        (invalid2 | invalid3 | invalid4 | invalid5 | invalid6)].index)
    print('Removed rows with \'-\', \'ー\' or no source signal name described. {} rows remain'.format(
        len(cdl_data_frame.index)))
    # Remove invalid signals for output
    invalid1 = cdl_data_frame['IN/OUT'] == 'OUT'
    invalid2 = cdl_data_frame['destination_modname'] == '-'
    invalid3 = cdl_data_frame['destination_modname'] == 'ー'
    invalid4 = cdl_data_frame['destination_modname'] == '―'
    invalid5 = pd.isna(cdl_data_frame['destination_modname'])
    invalid6 = cdl_data_frame.destination_modname.str.find(',') != -1
    cdl_data_frame = cdl_data_frame.drop(cdl_data_frame[invalid1 &
                                                        (invalid2 | invalid3 | invalid4 | invalid5 | invalid6)].index)
    print('Removed rows with \'-\', \'ー\' or no destination module described. {} rows remain'.format(
        len(cdl_data_frame.index)))
    invalid1 = cdl_data_frame['IN/OUT'] == 'OUT'
    invalid2 = cdl_data_frame['destination_signame'] == '-'
    invalid3 = cdl_data_frame['destination_signame'] == 'ー'
    invalid4 = cdl_data_frame['destination_signame'] == '―'
    invalid5 = pd.isna(cdl_data_frame['destination_signame'])
    invalid6 = cdl_data_frame.destination_signame.str.find(',') != -1
    cdl_data_frame = cdl_data_frame.drop(cdl_data_frame[invalid1 &
                                                        (invalid2 | invalid3 | invalid4 | invalid5 | invalid6)].index)
    print('Removed rows with \'-\', \'ー\' or no destination signal name described. {} rows remain'.format(
        len(cdl_data_frame.index)))

    # Extract array size from raw_data_type
    cdl_data_frame[array_size] = reg_replace(
        cdl_data_frame, 'raw_data_type', r'^\w*\d{0,2}[^\[]|(\[\D+\]|\[\D+\]\[\D+\])', '')
        
    # Create global signal name for declarations in stubs
    cdl_data_frame[module_signal] = cdl_data_frame['target_model_name'] + '_' + cdl_data_frame[signal_name]

    # Fix the array size of the signals
    array_size_list = {}
    temp_inout_o = ''
    temp_module_o = ''
    temp_module_signal_o = ''
    temp_array_size_o = ''
    signal_count = 0
    signal_count_o = 0
    acquired = False
    first_pass = True
    cdl_data_frame.sort_values(['target_model_name', 'IN/OUT', module_signal], inplace=True)
    for row in range(cdl_data_frame.shape[0]):
        temp_inout = cdl_data_frame.iat[row, in_out_col]
        if temp_inout == 'IN':
            temp_module = cdl_data_frame.iat[row, source_module_col]
        else:
            temp_module = cdl_data_frame.iat[row, destination_module_col]
        temp_module_signal = cdl_data_frame.iat[row, module_signal_col]
        temp_array_size = cdl_data_frame.iat[row, raw_array_size_col]
        if not first_pass:
            # Input, from same source, to same signal
            if temp_inout == temp_inout_o and temp_module == temp_module_o and \
                    temp_module_signal == temp_module_signal_o:
                # Map/table
                if temp_array_size.find('][') != -1:
                    if not acquired:
                        array_size_list[temp_module_signal] = temp_array_size
                        acquired = True
                    else:
                        # acquired = False
                        pass
                else:
                    if temp_array_size != '':
                        signal_count += 1
                    else:
                        pass
            else:
                if temp_module_signal_o not in array_size_list \
                        or (array_size_list[temp_module_signal_o].find('][') == -1
                            and signal_count_o + 1 > int(array_size_list[temp_module_signal_o][1:-1])):
                    array_size_list[temp_module_signal_o] = '[{}]'.format(signal_count_o + 1) \
                        if temp_array_size_o == '' or int(temp_array_size_o[1:2]) < signal_count_o + 1 \
                        else temp_array_size_o
                else:
                    pass
                signal_count = 0
                acquired = False
        else:
            first_pass = False
        temp_inout_o = temp_inout
        temp_module_o = temp_module
        temp_module_signal_o = temp_module_signal
        temp_array_size_o = temp_array_size
        signal_count_o = signal_count
    # For the last entry in array_size_list
    if temp_module_signal_o not in array_size_list \
            or (array_size_list[temp_module_signal_o].find('][') == -1
                and signal_count_o + 1 > int(array_size_list[temp_module_signal_o][1:-1])):
        array_size_list[temp_module_signal_o] = '[{}]'.format(signal_count_o + 1) \
            if temp_array_size_o == '' or int(temp_array_size_o[1:2]) < signal_count_o + 1 \
            else temp_array_size_o

    # Update the array size of each module signal
    cdl_data_frame[fixed_array_size] = cdl_data_frame[array_size]
    for row in range(cdl_data_frame.shape[0]):
        cdl_data_frame.iat[row, fixed_array_size_col] = array_size_list[cdl_data_frame.iat[row, module_signal_col]]
    # Save the updated interface list to an Excel file
    write_to_excel(cdl_data_frame, 'InterfaceList.xlsx', 'IF Information')

    # For global declarations
    declarations_module_list = []
    declarations_list = []
    for row in range(cdl_data_frame.shape[0]):
        declarations_module_list.append(cdl_data_frame.iat[row, target_module_col])
        declarations_list.append('{} {}{};'.format(
            cdl_data_frame.iat[row, fixed_data_type_col], 
            cdl_data_frame.iat[row, module_signal_col], 
            cdl_data_frame.iat[row, fixed_array_size_col] 
            if cdl_data_frame.iat[row, fixed_array_size_col] != '[1]' else '')
        )
    declarations_data_frame = pd.DataFrame({'TargetModule': declarations_module_list,
                                            'Declarations': declarations_list})
    declarations_data_frame.drop_duplicates(inplace=True)
    write_to_excel(declarations_data_frame, 'GlobalDeclarationsList.xlsx', 'Global Declarations')

    # Start updating interface.db
    # For IOList.xlsx
    source_module = []
    source_signal = []
    destination_module = []
    destination_signal = []
    # For ExternalSignals.xlsx
    ext_name = []
    ext_node = []
    ext_id = []
    ext_ch = []
    ext_byte = []
    ext_bit = []
    ext_factor = []
    ext_min = []
    ext_max = []
    ext_cycle_ms = []

    # interface DB -> internal_signals table
    sql_internal_signal = '''INSERT INTO internal_signals (module, name, address, link, data_type, data_size, array_size, cycle_ms
                        ) VALUES (?,?,?,?,?,?,?,?);'''
    data_size = {'boolean': 1, 'uint8': 1, 'uint16': 2, 'uint32': 4, 'float32': 4}
    print('Updating internal_signals table of interface database')
    for row in range(cdl_data_frame.shape[0]):
        # Append to internal_signals table
        internal_signal_data = (
            cdl_data_frame.iat[row, target_module_col],
            cdl_data_frame.iat[row, raw_target_signal_col],
            0,
            cdl_data_frame.iat[row, module_signal_col],
            cdl_data_frame.iat[row, fixed_data_type_col],
            data_size[cdl_data_frame.iat[row, fixed_data_type_col]],
            cdl_data_frame.iat[row, fixed_array_size_col],
            0
        )
        execute_sql(cdl_conn, sql_internal_signal, internal_signal_data)

        # For IOList.xlsx
        # Check if the model signal is an array/map/table but is not described in the signal's name
        if str(cdl_data_frame.iat[row, raw_target_signal_col]).find('[') == -1 \
                and cdl_data_frame.iat[row, raw_array_size_col] != '':
            model_signal = cdl_data_frame.iat[row, raw_target_signal_col] + cdl_data_frame.iat[row, raw_array_size_col]
        else:
            model_signal = cdl_data_frame.iat[row, raw_target_signal_col]
        source_module.append(cdl_data_frame.iat[row, source_module_col]
                             if cdl_data_frame.iat[row, in_out_col] == 'IN'
                             else cdl_data_frame.iat[row, target_module_col])
        source_signal.append(cdl_data_frame.iat[row, source_signal_col]
                             if cdl_data_frame.iat[row, in_out_col] == 'IN'
                             else model_signal)
        destination_module.append(cdl_data_frame.iat[row, target_module_col]
                                  if cdl_data_frame.iat[row, in_out_col] == 'IN'
                                  else cdl_data_frame.iat[row, destination_module_col])
        destination_signal.append(model_signal
                                  if cdl_data_frame.iat[row, in_out_col] == 'IN'
                                  else cdl_data_frame.iat[row, destination_signal_col])
        # else:
        #     signals = str(cdl_data_frame.iat[row, source_signal_col]).split(', ')
        #     # signals
        #     for index in range(len(signals)):
        #         source_module.append(cdl_data_frame.iat[row, source_module_col])
        #         source_signal.append(signals[index])
        #         destination_module.append(cdl_data_frame.iat[row, target_module_col])
        #         destination_signal.append(cdl_data_frame.iat[row, fixed_target_signal_col] + '[{}]'.format(index))

        # For external signals
        if cdl_data_frame.iat[row, in_out_col] == 'IN':
            if cdl_data_frame.iat[row, source_module_col] == 'CAN' \
                    or cdl_data_frame.iat[row, source_module_col] == 'VP':
                try:
                    under_loc = str(cdl_data_frame.iat[row, source_signal_col]).find('_')
                    if under_loc != -1:
                        test_id = int(cdl_data_frame.iat[row, source_signal_col][under_loc-3:under_loc], 16)
                        ext_name.append(cdl_data_frame.iat[row, source_signal_col])
                        ext_node.append(cdl_data_frame.iat[row, source_module_col]
                                        if cdl_data_frame.iat[row, source_module_col] != 'DebugCAN' else 'DBG')
                        ext_id.append(test_id)
                        ext_ch.append(0)
                        ext_byte.append(int(cdl_data_frame.iat[row, source_signal_col][under_loc+1:under_loc+2]))
                        ext_bit.append(int(cdl_data_frame.iat[row, source_signal_col][under_loc+3:under_loc+4]))
                        ext_factor.append(0)
                        ext_min.append(0)
                        ext_max.append(0)
                        ext_cycle_ms.append(0)
                except ValueError:
                    pass
        else:
            if cdl_data_frame.iat[row, destination_module_col] == 'CAN' \
                   or cdl_data_frame.iat[row, destination_module_col] == 'VP' \
                   or cdl_data_frame.iat[row, destination_module_col] == 'DebugCAN':
                try:
                    under_loc = str(cdl_data_frame.iat[row, destination_signal_col]).find('_')
                    if under_loc != -1:
                        test_id = int(cdl_data_frame.iat[row, destination_signal_col][under_loc - 3:under_loc], 16)
                        ext_name.append(cdl_data_frame.iat[row, destination_signal_col])
                        ext_node.append(cdl_data_frame.iat[row, destination_module_col]
                                        if cdl_data_frame.iat[row, destination_module_col] != 'DebugCAN' else 'DBG')
                        ext_id.append(test_id)
                        ext_ch.append(0)
                        ext_byte.append(int(cdl_data_frame.iat[row, destination_signal_col][under_loc+1:under_loc+2]))
                        ext_bit.append(int(cdl_data_frame.iat[row, destination_signal_col][under_loc+3:under_loc+4]))
                        ext_factor.append(0)
                        ext_min.append(0)
                        ext_max.append(0)
                        ext_cycle_ms.append(0)
                except ValueError:
                    pass

    # For io_pairing table, duplicates need to be removed
    # interface DB -> io_pairing table
    sql_io_pairing = '''INSERT INTO io_pairing (source_module, source_signal, destination_module, destination_signal)
                    VALUES (?,?,?,?);'''
    # print('Creating Excel file for input/output pairings')
    cdl_data_frame = pd.DataFrame({'source_module': source_module, 'source_signal': source_signal,
                                   'destination_module': destination_module, 'destination_signal': destination_signal})
    cdl_data_frame.drop_duplicates(inplace=True)
    # write_to_excel(cdl_data_frame, 'IOList.xlsx', 'IO Pairing')
    # Append to io_pairing table
    print('Updating io_pairing table of interface database')
    for row in range(cdl_data_frame.shape[0]):
        io_pairing_data = (
            cdl_data_frame.iat[row, 0],
            cdl_data_frame.iat[row, 1],
            cdl_data_frame.iat[row, 2],
            cdl_data_frame.iat[row, 3]
        )
        execute_sql(cdl_conn, sql_io_pairing, io_pairing_data)

    # For external signals
    # interface DB -> external_signals table
    sql_external_signal = '''INSERT INTO external_signals (name, node, id, ch, byte, bit, factor, min, max, cycle_ms)
                        VALUES (?,?,?,?,?,?,?,?,?,?);'''
    # name TEXT PRIMARY KEY NOT NULL,
    # node TEXT NOT NULL,
    # id INTEGER NOT NULL,
    # ch INTEGER NOT NULL,
    # byte INTEGER NOT NULL,
    # bit INTEGER NOT NULL,
    # factor BLOB,
    # min BLOB,
    # max BLOB,
    # cycle_ms INTEGER
    # print('Creating Excel file of all APP external signals (CAN, IPC)')
    cdl_data_frame = pd.DataFrame({'SignalName':  ext_name, 'Node': ext_node,
                               'CAN_ID': ext_id, 'CAN_Ch': ext_ch,
                               'ByteNum': ext_byte, 'BitNum': ext_bit,
                               'Factor': ext_factor, 'MinValue': ext_min,
                               'MaxValue': ext_max, 'Cycle_ms': ext_cycle_ms}
                              )
    cdl_data_frame.drop_duplicates(inplace=True)
    # write_to_excel(cdl_data_frame, 'ExternalSignals.xlsx', 'External')
    print('Updating external_signals table of interface database')
    for row in range(cdl_data_frame.shape[0]):
        external_signal_data = (
            cdl_data_frame.iat[row, target_module_col],
            cdl_data_frame.iat[row, in_out_col],
            int(cdl_data_frame.iat[row, source_module_col]),
            int(cdl_data_frame.iat[row, source_signal_col]),
            int(cdl_data_frame.iat[row, raw_target_signal_col]),
            int(cdl_data_frame.iat[row, raw_data_type_col]),
            int(cdl_data_frame.iat[row, destination_module_col]),
            int(cdl_data_frame.iat[row, destination_signal_col]),
            int(cdl_data_frame.iat[row, fixed_data_type_col]),
            int(cdl_data_frame.iat[row, fixed_target_signal_col])
        )
        execute_sql(cdl_conn, sql_external_signal, external_signal_data)


debug = True
parser = argparse.ArgumentParser()
if debug:
    parser.add_argument('-i', dest='input_file', default='【SASB連-2018-21】外部IF定義書_暫定版.xlsx')
else:
    parser.add_argument('input_file', help='IF specification file')
args = parser.parse_args()

if not os.path.exists(args.input_file):
    print('{} not found!'.format(args.input_file))
else:
    #             Sheet name , Use cols                , Skip rows
    #             [0]        , [1]                     , [2]
    input_data = ['Interface', 'A, B, D, E, I, J, K, L', 12]

    # create a database connection
    conn = create_connection("interface.db")
    if conn is not None:
        # Drop tables first, if they exist
        sql_statement = '''DROP TABLE IF EXISTS internal_signals;'''
        execute_sql(conn, sql_statement)
        sql_statement = ''' DROP TABLE IF EXISTS external_signals; '''
        execute_sql(conn, sql_statement)
        sql_statement = ''' DROP TABLE IF EXISTS io_pairing; '''
        execute_sql(conn, sql_statement)

        # For the address, convert hex to int (int("0xdeadbeef", 0))
        # APP
        sql_statement = '''CREATE TABLE IF NOT EXISTS internal_signals (
            module text NOT NULL, 
            name text NOT NULL, 
            address integer NOT NULL, 
            link text PRIMARY KEY NOT NULL, 
            data_type text, 
            data_size integer, 
            array_size text, 
            cycle_ms integer
        );'''
        execute_sql(conn, sql_statement)

        # CAN, IPC, etc.
        sql_statement = '''CREATE TABLE IF NOT EXISTS external_signals (
                                            name TEXT PRIMARY KEY NOT NULL,
                                            node TEXT NOT NULL,
                                            id INTEGER NOT NULL,
                                            ch INTEGER NOT NULL,
                                            byte INTEGER NOT NULL,
                                            bit INTEGER NOT NULL,
                                            factor BLOB,
                                            min BLOB,
                                            max BLOB,
                                            cycle_ms INTEGER
                                        );'''
        execute_sql(conn, sql_statement)

        # Input-output pairing
        sql_statement = '''CREATE TABLE IF NOT EXISTS io_pairing (
            id integer NOT NULL PRIMARY KEY,
            source_module text NOT NULL, 
            source_signal text NOT NULL, 
            destination_module text NOT NULL, 
            destination_signal text NOT NULL 
        );'''
        execute_sql(conn, sql_statement)
    else:
        print("Error! cannot create the database connection.")

    # filename = args.input_file
    print('Creating data frame from {}'.format(args.input_file))
    data_frame = read_excel_file(args.input_file, input_data)
    create_data_list(data_frame, conn)

    commit_disconnect_database(conn)

    print('Done preparing interface I/O data for testing')
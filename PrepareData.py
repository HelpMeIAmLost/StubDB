from common_util import *
from StringUtils import *

import numpy as np
import argparse

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
# The following data frame columns are for function calls only
fixed_source_signame_col = 13
source_module_signal_col = 14

#             Sheet name , Use cols , Skip rows
#             [0]        , [1]      , [2]
data_range = ['IF Information', 'A:M', OFF]
module = {'CAN_VP': ['CANRx_', 'IPCRx_'],
          'CTL': ['Ctl_'],
          'Others': ['Feat_']}
CAN_VP = {'CAN', 'VP'}
CTL = {'EGI', 'TCU_CVT', 'TCU_Shift', 'VDC'}
skip_list = {'RTE', 'FWBSW', 'NVMBSW', 'CONST', 'FMWF',
             'Ground', 'SWBSW', 'SSM', 'Input_Getway',
             'RTE_Gateway', 'FMWR1'}

unwantedString = {'nan', '-', '', 'パラ', 'OFF', 'ON'}


def getModPosKey(df, row, col):
    index = df.iat[row, col]
    if index in CAN_VP:
        return 'CAN_VP'
    elif index in CTL:
        return 'CTL'
    else:
        return 'Others'


def create_function_name(df, row, posKey, posVal, varName, name, insideVarName):
    # Check if the signal is a map/table
    if str(df.iat[row, fixed_array_size_col]).find('][') != -1:
        array_size = '-1'
    else:
        array_size = str(df.iat[row, fixed_array_size_col]).replace('[', '')
        array_size = array_size.replace(']', '')
    state = df.iat[row, in_out_col]
    string = name + module[posKey][posVal] + varName

    if state == "IN":
        if array_size == 'nan' or array_size == '1':
            string = string + '( &' + insideVarName + ' );'
            return string
        elif array_size == '-1':
            string = string + '( ' + insideVarName + ' );'
            return string
        else:
            string = string + '_Arr' + array_size + '( ' + insideVarName + ' );'
            return string
    else:
        if array_size == 'nan' or array_size == '1':
            string = string + '( ' + insideVarName + ' );'
            return string
        else:
            string = string + '_Arr' + array_size + '( ' + insideVarName + ' );'
            return string


def create_function_calls(cdl_data_frame):
    # Data Manipulation
    function_call_list = []
    target_module_list = []
    # target_module = 'target_module'
    source_signame = 'source_signame'
    fixed_source_signame = 'fixed_source_signame'
    source_module_signal = 'source_module_signal'
    # Function call creation
    rte_read = "Rte_Read_RP_"
    rte_write = "Rte_Write_PP_"

    print('Creating a list of RTE functions calls per module..')
    function_call_data_frame = cdl_data_frame
    # # Convert target_model_name text to lowercase
    # function_call_data_frame['target_model_name'] = function_call_data_frame.target_model_name.astype(str).str.lower()

    # Remove () and other unwanted text in the source_modname column
    function_call_data_frame['source_modname'] = reg_replace(function_call_data_frame, 'source_modname', r'[\(\)]', '')
    for i in unwantedString:
        function_call_data_frame['source_modname'] = replace(function_call_data_frame, 'source_modname', i, '')

    # Create a new column with just the signal name
    function_call_data_frame[fixed_source_signame] = reg_replace(
        function_call_data_frame, source_signame, r'\[(.*){1,3}\]\[(.*){1,3}\]|\[(.*){1,3}\]', '')
    function_call_data_frame[fixed_source_signame] = reg_replace(
        function_call_data_frame, fixed_source_signame, r'^(\d+)|([\u4e00-\u9fff]+)|([\u3040-\u309Fー]+)|([\u30A0-\u30FF]+)|(-)$', '')
    # Remove unwanted text in the new column fixed_source_signame
    for i in unwantedString:
        function_call_data_frame[fixed_source_signame] = replace(function_call_data_frame, fixed_source_signame, i, '')

    function_call_data_frame[source_module_signal] = function_call_data_frame['source_modname'] + '_' + \
        function_call_data_frame[fixed_source_signame]

    for row in range(function_call_data_frame.shape[0]):
        # Skip modules in skip_list
        if function_call_data_frame.iat[row, source_module_col] in skip_list:
            continue
        target_module = function_call_data_frame.iat[row, target_module_col]
        state = function_call_data_frame.iat[row, in_out_col]
        input_from = function_call_data_frame.iat[row, source_module_col]
        signal_name = function_call_data_frame.iat[row, fixed_target_signal_col]
        module_signal = function_call_data_frame.iat[row, module_signal_col]
        fixed_source_signame = function_call_data_frame.iat[row, fixed_source_signame_col]
        source_module_signal = function_call_data_frame.iat[row, source_module_signal_col]
        if state == "IN":
            # CAN and VP -------------------------------------------------------
            # rte_read     + posKey  + module_signal         + module_signal
            # Rte_Read_RP_ + CANRx_  + CUS_CustomChange_ACCL + (uint8 *data)

            # CTL and Feat -----------------------------------------------------
            # rte_read     + posKey  + source_module_signal + module_signal
            # Rte_Read_RP_ + Feat_   + FS_DetFailCode_0     + (uint8 *data)

            # Check if the input signal is from CAN or VP
            posKey = getModPosKey(function_call_data_frame, row, source_module_col)
            if posKey == 'CAN_VP':
                if signal_name != '':
                    if input_from == "CAN":  # CAN
                        function_call_list.append(create_function_name(
                            function_call_data_frame, row, posKey, 0, module_signal, rte_read, module_signal))
                        target_module_list.append(target_module)
                    else:  # VP
                        function_call_list.append(create_function_name(
                            function_call_data_frame, row, posKey, 1, module_signal, rte_read, module_signal))
                        target_module_list.append(target_module)
            elif posKey == 'CTL':
                if fixed_source_signame != '':
                    function_call_list.append(create_function_name(
                        function_call_data_frame, row, posKey, 0, source_module_signal, rte_read, module_signal))
                    target_module_list.append(target_module)
                else:
                    print('1 {}: {}'.format(target_module, signal_name))
            else:
                if fixed_source_signame != '':
                    function_call_list.append(create_function_name(
                        function_call_data_frame, row, posKey, 0, source_module_signal, rte_read, module_signal))
                    target_module_list.append(target_module)
                else:
                    print('2 {}: {}'.format(target_module, signal_name))
        else:
            # CAN and VP -------------------------------------------------------
            # rte_write     + posKey  + Module  + signal_name           + module_signal
            # Rte_Write_PP_ + Feat_   + CUS_    + CustomCont_AUTO_DRIVE + (boolean data)
            posKey = getModPosKey(function_call_data_frame, row, target_module_col)
            if signal_name != '':
                function_call_list.append(create_function_name(
                    function_call_data_frame, row, posKey, 0, module_signal, rte_write, module_signal))
                target_module_list.append(target_module)
            else:
                print('4 {}: {}'.format(target_module, signal_name))

    function_call_data_frame = pd.DataFrame({'TargetModule': target_module_list, 'FunctionCalls': function_call_list})
    function_call_data_frame.sort_values(by=['TargetModule', 'FunctionCalls'], ascending=True, inplace=True)
    function_call_data_frame.drop_duplicates(keep='last', inplace=True)

    write_to_excel(function_call_data_frame, 'RTEFunctionCalls.xlsx', 'RTE Function Calls')
    print('Done!')


def create_global_declarations(cdl_data_frame):
    # For global declarations
    declarations_module_list = []
    declarations_list = []

    print('Creating a list of global declarations per module..')
    global_declarations_data_frame = cdl_data_frame
    for row in range(global_declarations_data_frame.shape[0]):
        declarations_module_list.append(global_declarations_data_frame.iat[row, target_module_col])
        declarations_list.append('{} {}{};'.format(
            global_declarations_data_frame.iat[row, fixed_data_type_col],
            global_declarations_data_frame.iat[row, module_signal_col],
            global_declarations_data_frame.iat[row, fixed_array_size_col]
            if global_declarations_data_frame.iat[row, fixed_array_size_col] != '[1]' else '')
        )
    declarations_data_frame = pd.DataFrame({'TargetModule': declarations_module_list,
                                            'Declarations': declarations_list})
    declarations_data_frame.drop_duplicates(inplace=True)
    write_to_excel(declarations_data_frame, 'GlobalDeclarationsList.xlsx', 'Global Declarations')
    print('Done!')


def create_interface_database(cdl_data_frame):
    # create a database connection
    conn = create_connection("interface.db")
    if conn is not None:
        print('Updating the interface database..')
        interface_data_frame = cdl_data_frame
        # Drop tables first, if they exist
        sql_statement = '''DROP TABLE IF EXISTS internal_signals;'''
        execute_sql(conn, sql_statement)
        sql_statement = ''' DROP TABLE IF EXISTS external_signals; '''
        execute_sql(conn, sql_statement)
        sql_statement = ''' DROP TABLE IF EXISTS io_pairing; '''
        execute_sql(conn, sql_statement)

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
        for row in range(interface_data_frame.shape[0]):
            # Append to internal_signals table
            internal_signal_data = (
                interface_data_frame.iat[row, target_module_col],
                interface_data_frame.iat[row, raw_target_signal_col],
                0,
                interface_data_frame.iat[row, module_signal_col],
                interface_data_frame.iat[row, fixed_data_type_col],
                data_size[interface_data_frame.iat[row, fixed_data_type_col]],
                interface_data_frame.iat[row, fixed_array_size_col],
                0
            )
            execute_sql(conn, sql_internal_signal, internal_signal_data)

            # For IOList.xlsx
            # Check if the model signal is an array/map/table but is not described in the signal's name
            if str(interface_data_frame.iat[row, raw_target_signal_col]).find('[') == -1 \
                    and interface_data_frame.iat[row, raw_array_size_col] != '':
                model_signal = interface_data_frame.iat[row, raw_target_signal_col] + \
                               interface_data_frame.iat[row, raw_array_size_col]
            else:
                model_signal = interface_data_frame.iat[row, raw_target_signal_col]
            source_module.append(interface_data_frame.iat[row, source_module_col]
                                 if interface_data_frame.iat[row, in_out_col] == 'IN'
                                 else interface_data_frame.iat[row, target_module_col])
            source_signal.append(interface_data_frame.iat[row, source_signal_col]
                                 if interface_data_frame.iat[row, in_out_col] == 'IN'
                                 else model_signal)
            destination_module.append(interface_data_frame.iat[row, target_module_col]
                                      if interface_data_frame.iat[row, in_out_col] == 'IN'
                                      else interface_data_frame.iat[row, destination_module_col])
            destination_signal.append(model_signal if interface_data_frame.iat[row, in_out_col] == 'IN'
                                      else interface_data_frame.iat[row, destination_signal_col])

            # For external signals
            if interface_data_frame.iat[row, in_out_col] == 'IN':
                if interface_data_frame.iat[row, source_module_col] == 'CAN' \
                        or interface_data_frame.iat[row, source_module_col] == 'VP':
                    try:
                        under_loc = str(interface_data_frame.iat[row, source_signal_col]).find('_')

                        if under_loc != -1:
                            test_id = int(interface_data_frame.iat[row, source_signal_col][under_loc - 3:under_loc], 16)
                            ext_name.append(interface_data_frame.iat[row, source_signal_col])
                            ext_node.append(interface_data_frame.iat[row, source_module_col]
                                            if interface_data_frame.iat[row, source_module_col] != 'DebugCAN' else 'DBG')
                            ext_id.append(test_id)
                            ext_ch.append(0)
                            ext_byte.append(int(interface_data_frame.iat[row, source_signal_col][under_loc + 1:under_loc + 2]))
                            ext_bit.append(int(interface_data_frame.iat[row, source_signal_col][under_loc + 3:under_loc + 4]))
                            ext_factor.append(0)
                            ext_min.append(0)
                            ext_max.append(0)
                            ext_cycle_ms.append(0)

                    except ValueError:
                        pass
            else:
                if interface_data_frame.iat[row, destination_module_col] == 'CAN' \
                    or interface_data_frame.iat[row, destination_module_col] == 'VP' \
                        or interface_data_frame.iat[row, destination_module_col] == 'DebugCAN':
                    try:
                        under_loc = str(interface_data_frame.iat[row, destination_signal_col]).find('_')

                        if under_loc != -1:
                            test_id = int(interface_data_frame.iat[row, destination_signal_col][under_loc - 3:under_loc], 16)
                            ext_name.append(interface_data_frame.iat[row, destination_signal_col])
                            ext_node.append(interface_data_frame.iat[row, destination_module_col]
                                            if interface_data_frame.iat[row, destination_module_col] != 'DebugCAN'
                                            else 'DBG')
                            ext_id.append(test_id)
                            ext_ch.append(0)
                            ext_byte.append(int(interface_data_frame.iat[row, destination_signal_col]
                                                [under_loc + 1:under_loc + 2]))
                            ext_bit.append(int(interface_data_frame.iat[row, destination_signal_col]
                                               [under_loc + 3:under_loc + 4]))
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
        interface_data_frame = pd.DataFrame({'source_module': source_module, 'source_signal': source_signal,
                                             'destination_module': destination_module,
                                             'destination_signal': destination_signal})
        interface_data_frame.drop_duplicates(inplace=True)
        # Append to io_pairing table
        print('Updating io_pairing table of interface database')
        for row in range(interface_data_frame.shape[0]):
            io_pairing_data = (
                interface_data_frame.iat[row, 0],
                interface_data_frame.iat[row, 1],
                interface_data_frame.iat[row, 2],
                interface_data_frame.iat[row, 3]
            )
            execute_sql(conn, sql_io_pairing, io_pairing_data)

        # For external signals
        # interface DB -> external_signals table
        sql_external_signal = '''INSERT INTO external_signals (name, node, id, ch, byte, bit, factor, min, max, cycle_ms)
                            VALUES (?,?,?,?,?,?,?,?,?,?);'''
        print('Updating external_signals table of interface database')
        interface_data_frame = pd.DataFrame({'SignalName': ext_name, 'Node': ext_node,
                                             'CAN_ID': ext_id, 'CAN_Ch': ext_ch,
                                             'ByteNum': ext_byte, 'BitNum': ext_bit,
                                             'Factor': ext_factor, 'MinValue': ext_min,
                                             'MaxValue': ext_max, 'Cycle_ms': ext_cycle_ms}
                                            )
        interface_data_frame.drop_duplicates(inplace=True)
        for row in range(interface_data_frame.shape[0]):
            external_signal_data = (
                interface_data_frame.iat[row, target_module_col],
                interface_data_frame.iat[row, in_out_col],
                int(interface_data_frame.iat[row, source_module_col]),
                int(interface_data_frame.iat[row, source_signal_col]),
                int(interface_data_frame.iat[row, raw_target_signal_col]),
                int(interface_data_frame.iat[row, raw_data_type_col]),
                int(interface_data_frame.iat[row, destination_module_col]),
                int(interface_data_frame.iat[row, destination_signal_col]),
                int(interface_data_frame.iat[row, fixed_data_type_col]),
                int(interface_data_frame.iat[row, fixed_target_signal_col])
            )
            execute_sql(conn, sql_external_signal, external_signal_data)

        # Commit changes to database and disconnect from it
        commit_disconnect_database(conn)
        print('Done!')
    else:
        print("Error! Cannot create the database connection.")


def create_data_list(input_file):
    """ create multiple data lists for all interface, internal and external signals, I/O pairing, global declarations,
    and function calls

    :return: None
    """
    #             Sheet name , Use cols                , Skip rows
    #             [0]        , [1]                     , [2]
    input_data = ['Interface', 'A, B, D, E, I, J, K, L', 12]

    signal_name = 'signal_name'
    data_type = 'data_type'
    array_size = 'array_size'
    fixed_array_size = 'fixed_array_size'
    module_signal = 'module_signal'

    print('Creating data frame from {}'.format(input_file))
    cdl_data_frame = read_excel_file(input_file, input_data)
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
    print('Done processing interface signal information')

    ### Start trial here
    create_function_calls(cdl_data_frame)
    create_global_declarations(cdl_data_frame)
    create_interface_database(cdl_data_frame)
    ### End trial here
    print('Done preparing interface I/O data for testing')


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
    create_data_list(args.input_file)

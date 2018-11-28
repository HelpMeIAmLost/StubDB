import os


def reg_replace(data_frame, from_column, regex, str_replace):
    return data_frame[from_column].astype(str).replace(regex, str_replace, regex=True)


def drop(data_frame, from_column, str_drop):
    return data_frame.drop(data_frame[(data_frame[from_column] == str_drop)].index)


def replace(data_frame, from_column, str_before, str_replace):
    return data_frame[from_column].replace(str_before, str_replace)


def insert_lines_of_code(filename, data_frame, string, skip_count, spaces):
    """ inserts declarations global variables to the stubs

    :param filename: filename of the stub
    :param data_frame: filtered data frame for the current module
    :param string: a line in the stub that indicates the declarations section of the file
    :param skip_count: number of lines to skip from the section header's identifying string
    :param spaces:
    :return: return True if updating the file is a success, otherwise, return False
    """
    line_number = find_section_header(filename, string, skip_count)

    if line_number > 0:
        line_number = line_number + skip_count
        os.rename(filename, '{}.tmp'.format(filename))
        current_line = 1
        with open('{}.tmp'.format(filename), 'r') as fi:
            with open(filename, 'w') as fo:
                for line in fi:
                    fo.write(line)
                    current_line += 1

                    if current_line == line_number:
                        data = data_frame.tolist()
                        for row in data:
                            fo.write('{}{}\n'.format(spaces, row))
            fo.close()
        fi.close()
        os.remove('{}.tmp'.format(filename))
        return True
    elif line_number == -1:
        print('Declarations section of {} is not empty'.format(filename))
        return False
    else:
        print('Section header in {} not found'.format(filename))
        return False


def find_section_header(filename, string, skip_count):
    line_number = 1
    insertion_point = skip_count + 1
    insertion_point_start = False
    with open(filename, 'r') as f:
        for line in f:
            if line.find(string) != -1 and not insertion_point_start:
                insertion_point_start = True

            if not insertion_point_start:
                line_number = line_number + 1
            else:
                insertion_point -= 1
                if insertion_point == 0:
                    if line.strip() != '':
                        line_number = -1
                        break
                    else:
                        break
                # nLine = line.strip()
                # if bool(re.match(string, nLine)):
                #     break
                # else:
                #     line_number = line_number + 1
    f.close()
    return line_number

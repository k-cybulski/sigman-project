"""
This file contains functions allowing the import and export of data.
"""

import csv
import os.path
import pickle

import numpy as np
from QtSigman import DefaultColors
import sigman as sm 

def save_composite_data(file_name, composite_data):
    """Saves the given `Composite_data` in a pickle file."""
    with open(file_name, 'wb') as pickle_file:
        pickle.dump(composite_data, pickle_file)

def load_composite_data(file_name):
    """Loads `Composite_data` from a given pickle file."""
    with open(file_name, 'rb') as pickle_file:
        return pickle.load(pickle_file)

def _import_dat(file_name):
    """Imports two tables of coordinates from a .dat file."""
    x = []
    y = []
    with open(file_name) as csv_file:
        reader = csv.reader(csv_file, delimiter=' ')
        for row in reader:              
            x.append(float(row[0]))
            # Some .dat files have two spaces instead of one, in which case
            # row[1] is empty
            if row[1]=="": 
                y.append(float(row[2]))
            else:
                y.append(float(row[1]))
    return x, y


def _import_wave_dat(file_name, wave_type, offset=0):
    """Imports a waveform of constant frequency from a .dat file and
    returns a corresponding `Wave`."""
    x, y = _import_dat(file_name)
    sample_rate = len(x)/(x[-1]-x[0])
    return sm.Wave(y, sample_rate, 
                      wave_type=wave_type, 
                      offset=offset)
    
def _import_point_dat(file_name, point_type):
    """Imports coordinates from a .dat file and returns a corresponding
    `Points` instance."""
    x, y = _import_dat(file_name)    
    return sm.Points(x, y, 
                          point_type = point_type)

def import_wave(file_name, wave_type, offset=0):
    """Imports a `Wave` instance from a given file."""
    extension = os.path.splitext(file_name)[1][1:]
    if extension == 'dat':
        import_func = _import_wave_dat
    else:
        raise ValueError("Invalid file format")
    return import_func(
        file_name, 
        wave_type=wave_type, 
        offset=offset)

def import_points(file_name, point_type):
    """Imports a `Points` instance from a given file."""
    extension = os.path.splitext(file_name)[1][1:]
    if extension == 'dat':
        import_func = _import_point_dat
    else:
        raise ValueError("Invalid file format")
    return import_func(
        file_name,
        point_type = point_type)

def _export_dat(data_x, data_y, filename):
    """Writes two coordinate tables in a .dat file"""
    with open(filename, 'w', newline='') as csv_file:#fix extra line in file create on windows
        writer = csv.writer(csv_file, delimiter=' ')
        for x, y in zip(data_x, data_y):
            writer.writerow([x,y])

def _export_line_dat(file_name, wave):
    """Exports `Wave` to a .dat file."""
    data_x, data_y = wave.generate_coordinate_tables()
    _export_dat(data_x,data_y,file_name)

def _export_point_dat(file_name, points):
    """Exports `Points` to a .dat file."""
    _export_dat(points.data_x, points.data_y, file_name)

def export_wave(file_name, wave):
    """Exports `Wave` into a file with the format depending on
    the extension.
    """
    extension = os.path.splitext(file_name)[1][1:]
    if extension == 'dat':
        export_func = _export_line_dat
    else:
        raise ValueError("Invalid file format")
    export_func(file_name, wave)

def export_points(file_name, points):
    """Exports `Points` into a file with the format depending on
    the extension.
    """
    extension = os.path.splitext(file_name)[1][1:]
    if extension == 'dat':
        export_func = _export_point_dat
    else:
        raise ValueError("Invalid file format")
    export_func(file_name, points)

def export(file_name, object):
    """Exports `Points` or `Wave` into a file with the format depending
    on the extension.
    """
    if isinstance(object, sm.Points):
        export_points(file_name, object)
    elif isinstance(object, sm.Wave):
        export_wave(file_name, object)

def _estimate_points_offset(reference_points,align_points,
                            cross_correlation=False):
    """Estimates the offset between two sets of points that describe
    the same data. Returns the time in seconds that the align_points
    need to be moved by.
    
    align_points must be longer than reference_points
    """
    align_data = align_points.data_y
    reference_data = reference_points.data_y
    if not cross_correlation:
        differences = []
        difference = 0
        if (len(reference_data)>len(align_data)):
            for i in range(0,len(reference_data)-len(align_data)):
                difference = 0
                for j in range (0,len(align_data)):
                     difference = difference + abs((reference_data[i+j]-align_data[j]))     
                differences.append(difference)

            offset = (np.argmin(differences))
        else:
            for i in range(0,len(align_data)-len(reference_data)):
                difference = 0
                for j in range (0,len(align_data)):
                     if (i+j>= len(reference_data)):
                         break
                     difference = difference + abs((reference_data[i+j]-align_data[j]))     
                differences.append(difference)

            offset = (np.argmin(differences))
    else:
        if len(align_data) < len(reference_data):
            raise ValueError("Points to align must have more data than refrence.")
        index_offset = np.argmin(np.correlate(align_points.data_y,
                                              reference_points.data_y))
        offset = align_points.data_x[index_offset] - reference_points.data_x[0]
        # We need to account for the fact align_points and reference_points
        # are off by 2x the time of the first value in align_points
        offset -= align_points.data_x[0]*2
    time_offset = align_points.data_x[0] - reference_points.data_x[offset]
    return time_offset

def _hr_from_r(time):
    HR = [0] * (len(time) - 1)
    for i in range(len(time) - 1):
        HR[i] = round(60 / (time[i+1] - time[i]))
    return HR

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def import_modelflow_data(file_name, reference_points, reference_points_type):
    """Imports and aligns Finapres Modeflow data to already existing 
    points.
    
    Args:
        base_data - sm.Points to align to
        base_data_type - can be 'sbp', 'dbp' or 'r'
    """
    if reference_points_type not in ['sbp', 'dbp', 'r']:
        raise ValueError("Invlaid reference data type")
    x = []
    y = None
    names = None
    # Data retrieval
    with open(file_name) as f:
        if '.A00' in file_name:
            data_section = False
            for line in f:
                if not data_section and "END preamble" in line:
                    data_section = True 
                    continue
                if data_section:
                    data = line.split()
                    if len(data) > 2:
                        if names is None:
                            # trim " characters
                            names = [name[1:-1] for name in data[1:]]
                            continue
                        try:
                            x.append(float(data[0]))
                            if y is None:
                                y = [[float(str_)] for str_ in data[1:]]
                            else:
                                for i in range(1, len(data)):
                                    y[i-1].append(float(data[i]))
                        except ValueError: # If values are strings
                            continue
        else:
           i = 0
           for line in f:
               i = i + 1
               if i == 8:
                   pom = line.split(';')
                   if '\n' in pom:
                       del pom[pom.index('\n')]
                   pom[0] = 'HR'
                   names = pom
               if i > 8:
                   pom = line.split(';') 
                   if '\n' in pom:
                       del pom[pom.index('\n')]
                   if len(pom) > 2:
                       if is_number(pom[0]):
                           x.append(float(pom[0]))  
                           if y is None:
                                 y = [[0 for k in range(1)] for j in range(len(pom))]
                                 for k in range(1, len(pom)):
                                     if (is_number(pom[k])):
                                         y[k][0]=(float(pom[k]))   
                                     else:
                                         y[k][0] = 0
                           else:
                               for k in range(1, len(pom)):
                                    if (is_number(pom[k])):
                                         y[k].append(float(pom[k]))   
                                    else:
                                         y[k].append (0)
           y[0] =  _hr_from_r(x)         
    # Alignment and object initialization
    # modelflow_data[0] -> fiSYS -> SBP
    # modelflow_data[1] -> fiDIA -> DBP
    # modelflow_data[6] -> HR -> can be calculated from R
    points_list = []
    hr_points = None
    offset = 0
    for y_vals, name in zip(y, names):
        points = sm.Points(x, y_vals, name)
        points_list.append(points)
        if offset == 0:
            if reference_points_type == 'sbp' and name =='fiSYS':
                offset = _estimate_points_offset(points, reference_points)
            elif reference_points_type == 'dbp' and name == 'fiDIA':
                offset = _estimate_points_offset(points, reference_points)
            elif reference_points_type == 'r' and name == 'HR':
                hr_from_r = _hr_from_r(reference_points.data_x)
                hr_points = sm.Points(reference_points.data_x, hr_from_r,
                                      'HRfromR')
                offset = _estimate_points_offset(points, hr_points)
            

    for points in points_list:
        points.move_in_time(offset)
    
    if hr_points is not None:
        points_list.append(hr_points)
        names.append('HRfromR')


    return points_list, names


def import_signal_from_signal_express_file (file_name):
    """Import wave from signal express export Ascci file. First parse the head of the file next read all wave data.
    """
    x = []
    y = []
    names = []
    dt = 0
    with open(file_name,encoding="CP1250") as f:
        i = 1
        for line in f:
            if (i == 1):
                if 'channel names:' not in line:
                    break;
            if (i == 2):
                pom = line.split ('	')
                for name in pom:
                    names.append (name[(name.rfind('-')+2):].replace('\n',''))
            if (i == 6):
                dt = float(line.replace (',','.'))
            if (i > 7):
                signals_value = line.split ('	')
                nr = 0
                if len(y) == 0:
                    y = [[0 for k in range(1)] for j in range(len(pom))]
                for value in signals_value:
                    if (i == 8):
                        y[nr][0]=(float(value.replace (',','.')))
                    else:
                        y[nr].append(float(value.replace (',','.')))
                    nr = nr + 1
            i= i + 1
    setOfWaves = []
    for i in range(len(names)):
                wave = sm.Wave(y[i], dt, names[i], 0) #TODO: move to fm
                wave.offset = 0
                wave.type = names[i]
                #TODO: Check whether the name is already taken
                setOfWaves.append((wave, names[i],
                                   DefaultColors.getColor(names[i]), -1))
    return setOfWaves
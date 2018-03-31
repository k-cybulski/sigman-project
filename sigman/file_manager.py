"""
This file contains functions allowing the import and export of data.
"""

import csv
import os.path
import pickle

import numpy as np

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

def _export_dat(data_x,data_y,filename):
    """Writes two coordinate tables in a .dat file"""
    with open(filename, 'w') as csv_file:
        writer = csv.writer(csv_file, delimiter=' ')
        for x, y in zip(data_x, data_y):
            writer.writerow([x,y])

def _export_line_dat(file_name, wave):
    """Exports `Wave` to a .dat file."""
    data_x, data_y = wave.generate_coordinate_tables()
    _export_dat(data_x,data_y,file_name)

def _export_point_dat(file_name, points):
    """Exports `Points` to a .dat file."""
    _export_dat(file_name, points.data_x, points.data_y)

def export_line(file_name, wave):
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

def _estimate_points_offset(align_points, reference_points,
                            cross_correlation=False):
    """Estimates the offset between two sets of points that describe
    the same data. Returns the time in seconds that the align_points
    need to be moved by.
    
    align_points must be longer than reference_points
    """
    if len(align_points) < len(reference_points):
        raise ValueError("Points to align must have more data than refrence.")
    if not cross_correlation:
        align_data = align_points.data_y
        reference_data = reference_points.data_y
        differences = []
        difference = 0
        for i in range(0, len(align_data) - len(reference_data)):
            difference = 0
            for j in range (0, len(reference_data)):
                 difference += abs(align_data[i+j] - reference_data[j])     
            differences.append(difference)
        offset = np.argmin(differences)
        offset = align_points.data_x[offset] - reference_points.data_x[0]
    else:
        index_offset = np.argmin(np.correlate(align_points.data_y,
                                              reference_points.data_y))
        offset = align_points.data_x[index_offset] - reference_points.data_x[0]
        # We need to account for the fact align_points and reference_points
        # are off by 2x the time of the first value in align_points
        offset -= align_points.data_x[0]*2

    return -offset

def _hr_from_r(time):
    HR = [0] * (len(time) - 1)
    for i in range(len(time) - 1):
        HR[i] = round(60 / (time[i+1] - time[i]))
    return HR

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
                                      'wyznaczoneHRzR')
                offset = _estimate_points_offset(points, hr_points)

    for points in points_list:
        points.move_in_time(offset)
    
    if hr_points is not None:
        points_list.append(hr_points)
        names.append('wyznaczoneHRzR')

    return points_list, names

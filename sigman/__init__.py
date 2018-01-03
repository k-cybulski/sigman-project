"""
sigman
======
Library for digital signal processing. It operates on two basic types of 
data: signal waveforms and points that describe events in time (i.e. QRS
complexes on an ECG signal).

This file defines the following classes:
    Wave            - signal waveform
    Points          - sorted collection of points
    Parameter       - parameter calculated in chosen time ranges
    Composite_data  - class containing a set of Wave, Points and 
                      Parameter classes allowing for an analysis of 
                      multiple types of data simultaneously.
"""
# TODO: Documentation should be PEP-257 compliant
from math import isclose

import numpy as np

class Wave():
    """
    Class describing a signal waveform. 
    
    It may be offset in time and not begin at t=0. In such a case all 
    references to its value at a certain time will include such an 
    offset. For example if the Wave is offset by -0.5s and a request is
    made for its value at 0s, the value returned would be 0.5s after the
    beginning of the waveform.
    
    Attributes:
        Wave.data               - list of values of the signal
        Wave.complete_length    - length of the signal in seconds
        Wave.sample_length      - length of a sample in seconds
        Wave.sample_rate        - samlping rate in Hz
        Wave.wave_type          - string describing the type of data, 
                                  i.e. 'ecg' or 'bp'
        Wave.offset             - time offset

    """
    def __init__(self, data, complete_length, wave_type, offset=0):
        """Initializes a Wave object given its values, complete length 
        and type of data.
        """
        self.sample_length = complete_length/len(data)
        self.sample_rate = 1/self.sample_length        
        self.complete_length = complete_length 
        self.type = wave_type 
        self.data = np.array(data) 
        self.offset = offset

    @classmethod
    def copy(cls, wave):
        """It returns a new Wave exactly like the given one."""
        return cls(wave.data, wave.complete_length,
                   wave_type=wave.type, offset=wave.offset)

    def __len__(self):
        """Returns the number of samples."""
        return len(self.data)

    def sample_at(self, time):
        """Returns the index of the sample at a given time."""
        index = round((time-self.offset) / self.sample_length)
        if index == len(self):
            index -= 1
        if index < 0 or index > len(self):
            raise ValueError('Point at %s is outside the range of Wave'
                             % time)
        return int(index)
    
    def value_at(self, time):
        """Returns the value of the waveform at a given time calculated
        using linear approximation of surrounding values.
        """
        approx_index = (time-self.offset) / self.sample_length
        interp_index = int(approx_index)
        if interp_index < 0 or interp_index >= len(self)-1:
            raise ValueError('Point at %s is outside the range of Wave'
                             % time)
        approx_value = np.interp(
            approx_index, [interp_index, interp_index+1], 
            [self.data[interp_index],  self.data[interp_index+1]])
        return self.data[self.sample_at(time)]
    
    def data_slice(self, begin_time, end_time, 
                   value_every=0, value_count=None):
        """

        """
        begin_i = self.sample_at(begin_time)
        end_i = self.sample_at(end_time)
        if value_count is not None:
            value_every = (end_time-begin_time)/value_count
        if value_every == 0 or isclose(self.sample_length, value_every):
           return self.data[begin_i:end_i]
        wanted_values = np.arange(begin_time, end_time, value_every)
        coord_x, coord_y = self.generate_coordinate_tables(
            begin_time = begin_time, end_time = end_time, 
            begin_x = begin_time)
        interpolated_table = np.interp(wanted_values, coord_x, coord_y)
        return interpolated_table

    def replace_slice(self, begin_time, end_time, wave):
        if not isclose(self.sample_length,
                       wave.sample_length, rel_tol=0.0001):
            # TRANSLATE THIS
            raise ValueError('Fragment do wklejenia ma częstotliwość danych '
                             'niezgodną z częstotliwością danych całości')
        if end_time - begin_time > wave.complete_length:
            # TRANSLATE THIS
            raise ValueError('Dany Wave krótszy niż zakres czasu danych '
                             'do zastąpienia')
        begin_i = self.sample_at(begin_time)
        end_i = self.sample_at(end_time)
        for j in range(end_i-begin_i):
            self.data[begin_i+j]=wave.data[j]
    
    def generate_coordinate_tables(self, begin_time=0, end_time=None,
                                   begin_x=0):
        data = self.data_slice(begin_time, end_time)
        output_x = []
        output_y = []
        for i in range(len(data)):
            output_x.append(begin_x+i * self.sample_length)
            output_y.append(data[i])
        output_x = np.array(output_x)
        output_y = np.array(output_y)
        return output_x, output_y

class EmptyPointsError(Exception):
    pass

class Points():
    def __init__(self, data_x, data_y, point_type):
        if len(data_x) > 0:
            temp_data_x, temp_data_y = zip(*sorted(zip(data_x,data_y)))
            self.data_x = np.array(temp_data_x) 
            self.data_y = np.array(temp_data_y) 
            self.type = point_type 
        else:
            raise EmptyPointsError
    
    @classmethod
    def copy(cls, points):
        return cls(points.data_x, points.data_y,
                   point_type = points.type)

    def __len__(self):
        return len(self.data_x)

    def slice_range(self, begin_time, end_time):
        begin_i = np.searchsorted(self.data_x, begin_time)
        end_i = np.searchsorted(self.data_x, end_time)
        if begin_i != end_i:
            return range(begin_i, end_i)
        else:
            return None

    def data_slice(self, begin_time, end_time, left_offset=0):
        temp_range = self.slice_range(begin_time, end_time)
        if temp_range is None:
            return None
        begin_i = temp_range[0] - left_offset
        if begin_i < 0:
            begin_i = 0
        end_i = temp_range[-1]+1
        return self.data_x[begin_i:end_i], self.data_y[begin_i:end_i]

    def delete_slice(self, begin_time, end_time):
        temp_range = self.slice_range(begin_time, end_time)
        self.data_x = np.delete(self.data_x, temp_range)
        self.data_y = np.delete(self.data_y, temp_range)
        return temp_range[0]

    def replace_slice(self, begin_time, end_time, points):
        begin_i = self.delete_slice(begin_time, end_time)
        j = 0
        while (j < len(points) and 
                points.data_x[j] < end_time-begin_time):
            np.insert(self.data_x, begin_i+j, points.data_x[j]+begin_time)
            np.insert(self.data_y, begin_i+j, points.data_y[j])
    
    def add_point(self, x, y):
        i = np.searchsorted(self.data_x, x)
        self.data_x=np.insert(self.data_x, i, x)
        self.data_y=np.insert(self.data_y, i, y)
        
    def add_points(self, points, begin_time=0):
        for x, y in zip(points.data_x, points.data_y):
            self.add_point(x+begin_time, y)

    def delete_point(self, x, y=None):
        if y is not None:
            closest_id = self.closest_point_id(x, y)
        else:
            closest_id = np.argmin(np.abs(self.data_x - x))
        self.data_x = np.delete(self.data_x, closest_id)
        self.data_y = np.delete(self.data_y, closest_id)
    
    def move_point(self, x1, y1, x2, y2):
        closest_id = self.closest_point_id(x1, y1)
        if not (isclose(self.data_x[closest_id], x1) and
                isclose(self.data_y[closest_id], y1)):
            # TRAANSLATE THIS
            raise ValueError('Nie ma punktu o takich x1 i y1')
        self.data_x = np.delete(self.data_x, closest_id)
        self.data_y = np.delete(self.data_y, closest_id)
        i = np.searchsorted(self.data_x, x2)
        self.data_x=np.insert(self.data_x, i, x2)
        self.data_y=np.insert(self.data_y, i, y2)

    def closest_point_id(self, x, y):
        points = np.vstack((self.data_x, self.data_y))
        point = np.array([[x,y]])
        comparison_distances = np.sum((points - point)**2, axis=1)
        return np.argmin(comparison_distances) 

    def align_to_line(self, wave):
        for i in range(len(self)):
            self.data_y[i] = wave.value_at(self.data_x[i])

    def move_in_time(self, time):
        for i in range(len(self)):
            self.data_x[i] += time

class Parameter():
    def __init__(self, parameter_type):
        self.type = parameter_type
        self.begin_times = np.array([])
        self.end_times = np.array([])
        self.values = np.array([])

    @classmethod
    def copy(cls, parameter):
        out = cls(parameter.type)
        out.begin_times = np.copy(parameter.begin_times)
        out.end_times = np.copy(parameter.end_times)
        out.values = np.copy(parameter.values)
        return out

    def __len__(self):
        return len(self.begin_times)

    def add_value(self, begin_time, end_time, value):
        if len(self)==0: 
            self.begin_times = np.append(self.begin_times, begin_time)
            self.end_times = np.append(self.end_times, end_time)
            self.values = np.append(self.values, value)
        else:
            i = np.searchsorted(self.begin_times, begin_time)
            self.begin_times = np.insert(self.begin_times, i, begin_time)
            self.end_times = np.insert(self.end_times, i, end_time)
            self.values = np.insert(self.values, i, value)

    def contained_in(self, time):
        contained_indices = []
        for index, begin_time, end_time in zip(range(len(self)),self.begin_times,
                                        self.end_times):
            if time >= begin_time and time <= end_time:
                contained_indices.append(index)
            elif time > begin_time:
                break
        return contained_indices

    def value_at(self, time):
        parameter_indices = self.contained_in(time)
        if len(parameter_indices) == 0:
            return None
        else:
            return np.average(self.values[parameter_indices])

    def generate_parameter_line_tuples(self, begin_time=None, end_time=None):
        line_tuples = []
        for param_begin_time, param_end_time, value in zip(self.begin_times,
                                                           self.end_times,
                                                           self.values):
            if begin_time is not None and param_end_time < begin_time:
                continue
            if end_time is not None and param_begin_time > end_time:
                break
            temp_begin_time = max(begin_time, param_begin_time)
            temp_end_time = min(end_time, param_end_time)
            line_tuples.append(((temp_begin_time, temp_end_time),(value, value)))
        return line_tuples

class Composite_data:
    def __init__(self, waves=None, points=None, parameters=None):
        self.waves = {}
        self.points = {}
        self.parameters = {}
        if waves is not None: 
            self.waves = waves
        if points is not None: 
            self.points = points
        if parameters is not None:
            self.parameters = parameters

    def calculate_complete_time_span(self):
        begin_time = None
        end_time = None
        for key, wave in self.waves.items():
            if begin_time is None:
                begin_time = wave.offset
            else:
                begin_time = min(wave.offset, begin_time)
            if end_time is None:
                end_time = wave.offset + wave.complete_length
            else:
                end_time = max(wave.offset + wave.complete_length,
                               end_time)
        for key, points in self.points.items():
            if begin_time is None:
                begin_time = points.data_x[0]
            else:
                begin_time = min(points.data_x[0], begin_time)
            if end_time is None:
                end_time = points.data_x[-1]
            else:
                end_time = max(points.data_x[-1],
                               end_time)
        if begin_time and end_time is None:
            begin_time = 0
        return begin_time, end_time

    def calculate_time_range(self, required_waves):
        begin_time = None
        end_time = None
        for required_wave in required_waves:
            wave = self.waves[required_wave]
            if begin_time is None:
                begin_time = wave.offset
            else:
                begin_time = max(wave.offset, begin_time)
            if end_time is None:
                end_time = wave.offset + wave.complete_length
            else:
                end_time = min(wave.offset + wave.complete_length,
                               end_time)
        return begin_time, end_time

    def add_wave(self, wave, dict_type, replace=False):
        if dict_type is None:
            dict_type = wave.type
            if dict_type is None:
                # TRANSLATE THIS
                raise ValueError('Etykieta (dictionary key; tutaj dict_type) '
                                 'linii danych nie może być pusta')
        if dict_type in self.waves and not replace:
            # TRANSLATE THIS
            raise ValueError('Etykieta %s w waves jest już zajęta.' 
                             % dict_type)
        self.waves[dict_type] = wave

    def delete_wave(self, dict_type):
        self.waves.pop(dict_type)

    def add_points(self, points, dict_type, join=False):
        if dict_type is None:
            dict_type = points.type
        if dict_type in self.points:
            if join:
                self.points[dict_type].add_points(points)
            else:
                # TRANSLATE THIS
                raise ValueError('Etykieta %s w points jest już zajęta.'
                                 % dict_type)
        else:
            self.points[dict_type] = points

    def delete_points(self, dict_type):
        self.points.pop(dict_type)

    def add_parameter(self, parameter, dict_type, replace=False):
        if dict_type is None:
            dict_type = parameter.type
            if dict_type is None:
                # TRANSLATE THIS
                raise ValueError('Etykieta (dictionary key; tutaj dict_type) '
                                 'parametru nie może być pusta')
        if dict_type in self.parameters and not replace:
            # TRANSLATE THIS
            raise ValueError('Etykieta %s w parameters już zajęta.' 
                             % dict_type)
        self.parameters[dict_type] = parameter

    def delete_parameter(self, dict_type):
        self.parameters.pop(dict_type)

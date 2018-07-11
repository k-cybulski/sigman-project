"""
sigman
======
Digital signal processing library. It operates on two basic types of 
data: signal waveforms and points that describe events in time (i.e. R
points within QRS complexes on an ECG signal).

This file defines the following classes:
    Wave            - signal waveform
    Points          - sorted collection of points
    Parameter       - parameter calculated in chosen time ranges
    Composite_data  - class containing a set of Wave, Points and 
                      Parameter objects allowing for simultaneous
                      analysis of multiple types of data.
"""
# TODO: Documentation should be PEP-257 compliant
from math import isclose

import numpy as np

class Wave:
    """Class describing a signal waveform. 
    
    It may be offset in time and not begin at t=0. In such a case all
    methods that reference its value at a given time will take that
    into consideration. For example if the `Wave` is offset by -0.5s and
    `value_at(5)` is called, the returned value would be 5.5s into the
    waveform.
    
    Attributes:
        Wave.data               - numpy array of values of the signal
        Wave.complete_length    - length of the signal in seconds
        Wave.sample_length      - length of a sample in seconds
        Wave.sample_rate        - sampling rate in Hz
        Wave.type               - string describing the type of data, 
                                  e.g. 'ecg' or 'bp'
        Wave.offset             - time offset
    """

    def __init__(self, data, sample_rate, wave_type, offset=0):
        """Initializes a Wave object.
        
        Arguments:
            data            - list of values of the signal
            sample_rate     - sample rate of the signal in Hz
            type            - string describing the type of data,
                              e.g. 'ecg' or 'bp'
        """
        if sample_rate <= 0:
            raise ValueError(("Sample rate must be greater than 0, is "
                              "{}").format(sample_rate))
        self.sample_rate = sample_rate
        self.sample_length = 1/sample_rate
        self.complete_length = len(data) * self.sample_length
        self.type = wave_type 
        self.data = np.array(data) 
        self.offset = offset

    @classmethod
    def fromWave(cls, wave):
        """Returns a new `Wave` exactly like the one given."""
        return cls(wave.data, wave.sample_rate,
                   wave_type=wave.type, offset=wave.offset)

    def copy(self):
        """Returns a copy of this `Wave` instance."""
        return Wave.fromWave(self)

    def __len__(self):
        """Returns the total number of samples."""
        return len(self.data)

    def __getitem__(self, key):
        return self.data[key]

    def sample_at(self, time):
        """Returns the index of the sample at a given time in seconds."""
        index = int((time-self.offset) / self.sample_length)
        if index == len(self):
            index -= 1
        if index < 0 or index > len(self):
            raise ValueError('Point at %s is outside the range of Wave'
                             % time)
        return int(index)
    
    def value_at(self, time):
        """Returns the value of the waveform at a given time in seconds 
        calculated using linear interpolation of surrounding samples.
        """
        approx_index = (time-self.offset) / self.sample_length
        interp_index = int(approx_index)
        if time == self.complete_length: # correction for last value
            return self[-1]
        if interp_index < 0 or interp_index > len(self):
            raise ValueError('Point at %s is outside the range of Wave'
                             % time)
        approx_value = np.interp(
            approx_index, [interp_index, interp_index+1], 
            [self.data[interp_index],  self.data[interp_index+1]])
        return approx_value
    
    def data_slice(self, begin_time, end_time, 
                   value_every=0, value_count=None):
        """Returns a numpy array of values from a time range.

        The returned values may have a different sampling rate than
        the `Wave` instance if `value_every` or `value_count` are
        set.

        If `value_every` is set and not equal to `self.sample_rate`, 
        the output array values will be the result of linear 
        interpolation like with `Wave.value_at`.

        Arguments:
            begin_time  - beginning of the time range
            end_time    - end of the time range
            value_every - time between values (i.e. frequency) of the
                          returned array
            value_count - number of values to return. If `value_every` 
                          is also set, `value_count` supersedes it.
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
        """Replaces the values of this `Wave` instance in a given time 
        range with those of a given `Wave`.

        The given `Wave` must have the same sample_rate as the base
        instance.

        Arguments:
            begin_time - beginning of the time range
            end_time   - end of the time range
            wave       - the given `Wave`
        """

        if not isclose(self.sample_length,
                       wave.sample_length, rel_tol=0.0001):
            raise ValueError('Wave to replace has incompatible sample_rate')
        if end_time - begin_time > wave.complete_length:
            raise ValueError('Given Wave shorter than the time wanted range')
        begin_i = self.sample_at(begin_time)
        end_i = self.sample_at(end_time)
        for j in range(end_i-begin_i):
            self.data[begin_i+j]=wave.data[j]
    
    def generate_coordinate_tables(self, begin_time=0, end_time=None,
                                   begin_x=0):
        """Returns points of the waveform in the form of two arrays - 
        x and y values.

        Useful for visualization.

        Arguments:
            begin_time - the beginning of the time range
            end_time   - the end of the time range
            begin_x    - x value of the first point in the output array
        """
        # TODO: Rethink this; arguments seem shady
        if end_time is None:
            end_time = self.complete_length
        data = self.data_slice(begin_time, end_time)
        output_x = []
        output_y = []
        for i in range(len(data)):
            output_x.append(begin_x+i * self.sample_length)
            output_y.append(data[i])
        output_x = np.array(output_x)
        output_y = np.array(output_y)
        return output_x, output_y

# TODO: Unnecessary
class EmptyPointsError(Exception):
    """Raised when an empty Points class is initialized."""

class Points:
    """Class describing points, i.e. events in time with a value.

    The points are kept in the form of two arrays, of x and y values,
    sorted by x.

    Attributes:
        Points.data_x - numpy array of x coordinates
        Points.data_y - numpy array of y coordinates
        Points.type   - type of points, e.g. 'r' or 'sbp'
    """
    # TODO: rename data_x and data_y into x and y (?may be less clear)
    def __init__(self, data_x, data_y, point_type):
        """Initializes a `Points` instance.

        Arguments:
            data_x - list of x coordinates of points
            data_y - list of y coordinates of points
            point_type - type of points, e.g. 'r' or 'sbp'
        """
        if len(data_x) > 0:
            temp_data_x, temp_data_y = zip(*sorted(zip(data_x,data_y)))
            self.data_x = np.array(temp_data_x) 
            self.data_y = np.array(temp_data_y) 
            self.type = point_type 
        else:
            raise EmptyPointsError
    
    @classmethod
    def fromPoints(cls, points):
        """Initializes a new `Points` with the same data and type as
        the given one."""
        return cls(points.data_x, points.data_y,
                   point_type=points.type)

    def copy(self):
        """Returns a copy of this `Points` instance."""
        return Points.fromPoints(self)

    def __len__(self):
        """Returns number of points contained in this instance."""
        return len(self.data_x)

    def __getitem__(self, key):
        x = self.data_x[key]
        y = self.data_y[key]
        if isinstance(key, slice):
            points = list(zip(*(x,y)))
        else:
            points = (x, y)
        return points

    def slice_range(self, begin_time, end_time):
        """Returns a list of indices of points from a given time range.

        Arguments:
            begin_time - beginning of the time range
            end_time   - end of the time range
        """
        begin_i = np.searchsorted(self.data_x, begin_time)
        end_i = np.searchsorted(self.data_x, end_time)
        if begin_i != end_i:
            return range(begin_i, end_i)
        else:
            return None

    def data_slice(self, begin_time, end_time, left_offset=0):
        """Returns two lists of x and y coordinates of points in a
        given time range.

        Arguments:
            begin_time  - beginning of the time range
            end_time    - end of the time range
            left_offset - number of points to the left of the time
                          range, i.e. with smaller x, to include in the
                          output
        """
        temp_range = self.slice_range(begin_time, end_time)
        if temp_range is None:
            return None
        begin_i = temp_range[0] - left_offset
        if begin_i < 0:
            begin_i = 0
        end_i = temp_range[-1]+1
        return self.data_x[begin_i:end_i], self.data_y[begin_i:end_i]

    def delete_slice(self, begin_time, end_time):
        """Deletes points contained in this instance from a time
        range and returns a list of the indices of removed points.

        Arguments:
            begin_time  - beginning of the time range
            end_time    - end of the time range
        """
        temp_range = self.slice_range(begin_time, end_time)
        self.data_x = np.delete(self.data_x, temp_range)
        self.data_y = np.delete(self.data_y, temp_range)
        return temp_range[0]

    def replace_slice(self, begin_time, end_time, points):
        """Replaces points within a time range with those from a
        different `Points` instance.

        Arguments:
            begin_time  - beginning of the time range
            end_time    - end of the time range
            points      - `Points` instance with which to replace this
                          instance's points
        """
        begin_i = self.delete_slice(begin_time, end_time)
        j = 0
        while (j < len(points) and 
                points.data_x[j] < end_time-begin_time):
            np.insert(self.data_x, begin_i+j, points.data_x[j]+begin_time)
            np.insert(self.data_y, begin_i+j, points.data_y[j])
    
    def add_point(self, x, y):
        """Adds a point with a given x and y coordinates to this
        `Points` instance.
        """
        i = np.searchsorted(self.data_x, x)
        self.data_x=np.insert(self.data_x, i, x)
        self.data_y=np.insert(self.data_y, i, y)
        
    def add_points(self, points, begin_time=0):
        """Adds points from a given `Points` instance to this instance."""
        for x, y in zip(points.data_x, points.data_y):
            self.add_point(x+begin_time, y)

    def delete_point(self, x, y=None):
        """Deletes a point closest to the given x and y coordinates.
        If y is not given, then only the x axis is considered.
        """
        if y is not None:
            closest_id = self.closest_point_id(x, y)
        else:
            closest_id = np.argmin(np.abs(self.data_x - x))
        self.data_x = np.delete(self.data_x, closest_id)
        self.data_y = np.delete(self.data_y, closest_id)
    
    def move_point(self, x1, y1, x2, y2):
        """Moves a point with the given x and y coordinates to a
        new position.
        """
        closest_id = self.closest_point_id(x1, y1)
        if not (isclose(self.data_x[closest_id], x1) and
                isclose(self.data_y[closest_id], y1)):
            raise ValueError(('A point with the given x1 and y1 coordinates'
                              'does not exist: {}, {}').format(x1, y1))
        self.data_x = np.delete(self.data_x, closest_id)
        self.data_y = np.delete(self.data_y, closest_id)
        i = np.searchsorted(self.data_x, x2)
        self.data_x=np.insert(self.data_x, i, x2)
        self.data_y=np.insert(self.data_y, i, y2)

    def closest_point_id(self, x, y):
        """Returns the index of the closest point to the point with
        given x and y coordinates.
        """
        points = np.vstack((self.data_x, self.data_y))
        point = np.array([[x,y]])
        comparison_distances = np.sum((points - point)**2, axis=1)
        return np.argmin(comparison_distances) 

    def align_to_line(self, wave):
        """Aligns all points' y values to the value of a `Wave` at the
        same x.
        """
        for i in range(len(self)):
            self.data_y[i] = wave.value_at(self.data_x[i])

    def offset(self, time):
        """Offsets all points' x coordinates."""
        for i in range(len(self)):
            self.data_x[i] += time
    
    def move_in_time(self, time):
        # DEPRECATED
        self.offset(time)

class Parameter:
    """Class denoting a parameter calculated over time ranges.

    Attributes:
        Parameter.type          - string describing the type of the
                                  parameter, e.g. 'hr'
        Parameter.begin_times   - numpy array of the beginnings of time
                                  ranges over which the parameter was
                                  calculated
        Parameter.end_times     - numpy array of the endings of time
                                  ranges over which the parameter was
                                  calculated
        Parameter.values        - numpy array of the calculated values
                                  of the parameter, corresponding to the
                                  above time ranges
    """
    # The architecture of the Parameter class should probably be reconsidered
    def __init__(self, parameter_type):
        self.type = parameter_type
        self.begin_times = np.array([])
        self.end_times = np.array([])
        self.values = np.array([])

    @classmethod
    def fromParameter(cls, parameter):
        out = cls(parameter.type)
        out.begin_times = np.copy(parameter.begin_times)
        out.end_times = np.copy(parameter.end_times)
        out.values = np.copy(parameter.values)
        return out

    def copy(self):
        return Parameter.fromParameter(self)

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
    """Class denoting a collection of data that can be easily
    analyzed together.

    It contains three `dict`s, each containing a different type of data.
    """
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
        """Calculates the entire time range in which the 
        `Composite_data` contains any data.
        """
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
        """Calculates the timme range in which the required `Wave`
        instances' data overlaps.
        """
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
        """Adds a `Wave` to the `Composite_data`."""
        if dict_type is None:
            dict_type = wave.type
            if dict_type is None:
                raise ValueError(('dict_type may not be None if `type` of '
                                  'instance is None'))
        if dict_type in self.waves and not replace:
            raise ValueError(('Key {} in waves dict is already taken').format(
                dict_type))
        self.waves[dict_type] = wave

    def delete_wave(self, dict_type):
        """Deletes a `Wave` with the given dict key from the
        `Composite_data`."""
        self.waves.pop(dict_type)

    def add_points(self, points, dict_type, join=False):
        """Adds a `Points` to the `Composite_data`."""
        if dict_type is None:
            dict_type = points.type
            if dict_type is None:
                raise ValueError(('dict_type may not be None if `type` of '
                                  'instance is None'))
        if dict_type in self.points:
            if join:
                self.points[dict_type].add_points(points)
            else:
                raise ValueError(('Key {} in points dict is already taken'
                                 ).format(dict_type))
        else:
            self.points[dict_type] = points

    def delete_points(self, dict_type):
        """Deletes a `Points` with the given dict key from the
        `Composite_data`."""
        self.points.pop(dict_type)

    def add_parameter(self, parameter, dict_type, replace=False):
        """Adds a `Parameter` to the `Composite_data`."""
        if dict_type is None:
            dict_type = parameter.type
            if dict_type is None:
                raise ValueError(('dict_type may not be None if `type` of '
                                  'instance is None'))
        if dict_type in self.parameters and not replace:
            raise ValueError(('Key {} in parameters dict is already taken'
                             ).format(dict_type))
        self.parameters[dict_type] = parameter

    def delete_parameter(self, dict_type):
        """Deletes a `Parameter` from the `Composite_data`."""
        self.parameters.pop(dict_type)

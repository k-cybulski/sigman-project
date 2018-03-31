"""
This module contains functions allowing the use of external procedures
from the `procedures` directory.

There are three types of procedures:
    modify - these procedures modify a signal waveform. They take a
             `Wave` instance as an argument.
    points - these procedures find events and label them as points.
             They take dicts of `Wave` and `Points` instances as
             arguments.
    parameter - these procedures calculate parameters over time based
                on dicts of `Wave` and `Point` instances.

Procedures also take additional arguments in the form of a `dict` of
`<argument name>:<argument string>` pairs.

Each procedure module must contain these attributes:
    <string> procedure_type - type of procedure as described above.
    <string> description - description of what the procedure does.
    <string> author - author of the procedure.
    <dict> arguments - `dict` of arguments and what they do.
    <dict> default_arguments - `dict` of default arguments.
    <function> validate_arguments - function that validates whether
                                    given arguments are correct.
    <function> procedure - procedure itself.
    <function> execute - function called externally that validates
                         and interprets arguments and executes
                         `procedure`.

`points` and `parameter` procedures must also contain:
    <string> output_type - type of data returned, e.g. `r` for an
                           R-finding procedure or `hr` for a heart rate
                           calculating procedure.
    <list of strings> required_waves - required types of waves.
    <list of strings> required_points - required types of points.

Depending on their type procedures must take in specific arguments and
return specific results:
    `modify`
        procedure(<Wave> wave,
                  <float> begin_time, <float> end_time,
                  <dict> arguments)
        Procedure must return a modified table of values of the given
        `Wave` corresponding to the given time range.
    `points`
        procedure(<dict> waves, <dict> points,
                  <float> begin_time, <float> end_time,
                  <dict> arguments)
        Procedure must return two lists of x and y values of points.
    `paramteter`
        procedure(<dict> waves, <dict> points,
                  <float> begin_time, <float> end_time,
                  <dict> arguments)
        Procedure must return the value of the parameter in the given
        time range.

Sample usage:
    butterworth = analyzer.import_procedure("modify_filter_butterworth")
    arguments = butterworth.default_arguments
    arguments['N'] = 3
    arguments['Wn'] = 30
    filtered_wave = analyzer.modify_wave(composite_data.waves['bp'], 60, 70, butterworth, arguments)
    complete_data.waves['bp'].replace_slice(60, 70, filtered_wave)
"""

import importlib

import sigman as sm

class InvalidArgumentError(Exception):
    """Raised when the procedure receives an invalid argument."""

class InvalidProcedureError(Exception):
    """Raised when a procedure doesn't fulfill API requirements."""

def validate_procedure_compatibility(procedure_module):
    """Returns a boolean whether a given module fulfills API 
    requirements and an error message string, if it doesn't.
    
    The error message string is an empty string if the module
    does fulfill requirements.
    """
    
    if 'procedure_type' not in procedure_module.__dict__:
        return False, ('`procedure_type` has not been declared in the module')
    procedure_type = procedure_module.procedure_type
    if procedure_type not in ['modify', 'points', 'parameter']:
        error_message = "`procedure_type` "+procedure_type+" is incorrect."
        return False, error_message

    # TODO: Also check if the attributes are of correct type
    required_attributes = [
        "description",
        "author",
        "arguments",
        "default_arguments",
        "validate_arguments",
        "procedure",
        "execute"]
    if procedure_type in ['points', 'parameter']:
        required_attributes.extend([
            "required_waves",
            "required_points",
            "output_type"])
    
    for attribute in required_attributes:
        if attribute not in procedure_module.__dict__:
            error_message = "atrybut "+attribute+(" nie został "
                "zadeklarowany w module procedury")
            return False, error_message
    return True, ""
    
def import_procedure(name):
    """Zwraca moduł procedury o danej nazwie z folderu procedures."""
    procedure = importlib.import_module("procedures."+name)
    valid, error_message = validate_procedure_compatibility(procedure)
    if not valid:
        raise InvalidProcedureError(error_message)
    return procedure

def modify_wave(wave, begin_time, end_time, 
                procedure, arguments, 
                wave_type=None):
    """Runs a `modify` procedure and returns a Wave corresponding to its output."""
    if wave_type is None:
        wave_type = wave.type
    modified_data = procedure.execute(wave, begin_time, end_time, arguments)
    return sm.Wave(modified_data, end_time-begin_time, wave_type)
    
def find_points(waves, points, begin_time, end_time, 
                procedure, arguments):
    """Runs a `points` procedure and returns a `Points` instance
    corresponding to its output.
    """
    if (procedure.required_waves
        and not all(wave in waves for wave in procedure.required_waves)):
        raise ValueError('Not all waves from {} provided.'.format(
            procedure.required_waves))
    if (procedure.required_points
        and not all(points_ in points for points_ in procedure.required_points)):
        raise ValueError('Not all points from {} provided.'.format(
            procedure.required_points))
    found_points_x, found_points_y = procedure.execute(
        waves, points,
        begin_time, end_time, 
        arguments)
    return sm.Points(found_points_x, found_points_y, procedure.output_type)

def calculate_parameter(waves, points, time_tuples,
                        procedure, arguments):
    """Runs a `parameter` procedure in given time ranges and returns 
    a `Parameter`."""
    if (procedure.required_waves
        and not all(wave in waves for wave in procedure.required_waves)):
        raise ValueError('Not all waves from {} provided.'.format(
            procedure.required_waves))
    if (procedure.required_points
        and not all(points_ in points for points_ in procedure.required_points)):
        raise ValueError('Not all points from {} provided.'.format(
            procedure.required_points))
    parameter = sm.Parameter(procedure.output_type)
    for begin_time, end_time in time_tuples:
        value = procedure.execute(
            waves, points,
            begin_time, end_time,
            arguments)
        parameter.add_value(begin_time, end_time, value)
    return parameter

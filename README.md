# sigman-project
The goal of this project is the creation of a free and open multichannel digital signal analysis library **sigman** as well as a GUI application **QtSigman** to work along with it.

## Installation
### Requirements
* [Python 3](https://www.python.org/about/) - entirety
* [NumPy](http://www.numpy.org/) - basic data handling
* [SciPy](https://scipy.org/) - advanced analysis tools
* [matplotlib](http://matplotlib.org/) - plot visualization
* [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - GUI

### Linux
#### Ubuntu
```
git clone "https://github.com/k-cybulski/sigman-project.git"
sudo apt install python3-pip
pip3 install PyQt5 numpy scipy matplotlib XlsxWriter
```

## Usage
### QtSigman
Run `run_qtsigman.py`.

### sigman
Below examples assume importing `sigman` as `sm`, `sigman.file_manager` as `fm` and `sigman.visualizer` as `vis`.

#### sigman.Wave
The most basic type of data in the sigman library is a signal waveform `sigman.Wave`. Its most important attributes are a list of values `Wave.data` and length in seconds `Wave.complete_length`. From these sample rate `Wave.sample_rate` as well as sample length `Wave.sample_length` are calculated. Type of the signal `Wave.type` (e.g. `ecg` or `bp`) will also be useful for further analysis.

`sigman.Wave` example containing the values of the sine function from 0 to 4pi in a 10 second range.
```python
import sigman as sm
import numpy as np
sine = np.sin(np.linspace(0, 4*np.pi))
sine_wave = sm.Wave(sine, 10, 'sine')
```

`sigman.Wave` objects may be imported from files with the function `file_manager.import_wave`.
```python
from sigman import file_manager as fm
ecg = fm.import_wave('example_data/EKG.dat', 'ecg')
```

In the event of a signal being offset with respect to others the variable `Wave.offset` allows the user to move the waveform in time.

The most basic method of retrieving data from `sigman.Wave` is `Wave.data_slice` which returns a numpy array of values from a given time range. Further documentation in `sigman/__init__.py`. Examples:
```python
>>> ecg.data_slice(5, 5.025) # 25 milisecond waveform slice
array([ 0.10659864,  0.10404629,  0.1673287 ,  0.1688633 ,  0.04704312])
>>> ecg.data_slice(5, 8, value_every=1) # 3 second waveform slice with values separated by 1 second each
array([ 0.10659864, -0.52108215,  0.95624742])
>>> ecg.data_slice(5, 25, value_count=5) # a slice of 5 values in a range of 20 seconds
array([ 0.10659864,  0.35472794, -0.61547362, -0.75704451, -0.59674523])
```

#### sigman.Points
Points that describe events in time with a given value, like blood pressure peaks `sbp` on a `bp` signal, are described by the `sigman.Points` class. It contains two lists `Points.data_x` and `Points.data_y` sorted with respect to `data_x`, as well as the type of points like `sbp` or `r`.

Example initialization of `sigman.Points`.
```python
import sigman as sm
data_x = [1, 4, 7]
data_y = [3, -2, 4]
points = sm.Points(data_x, data_y, 'example')
```

`sigman.Points` may be imported from files
```python
from sigman import file_manager as fm
r = fm.import_points('example_data/R.dat', 'r')
```
or found using procedures, which will be described later on.

There is a `Points.data_slice` method similar to `sigman.Wave`.
```python
>>> r.data_slice(20,23)
(array([ 20.61868,  21.49193,  22.3552 ]), array([ 4.07120371,  3.76066208,  3.69650602]))
```

#### sigman.Parameter
A class containing values of a parameter, like heart rate, calculated in a set of time ranges. It contains a list of values `Parameter.values` as well as information as to when each time range starts `Parameter.begin_times` and ends `Parameter.end_times`. `sigman.Parameter` may only be initialized using procedures.

#### sigman.Composite_data
A class containing multiple data objects described above. It may contain any number of `sigman.Wave`, `sigman.Points` and `sigman.Parameter` objects in its three `dict` attributes. It hence allows to easily use procedures which require multiple data channels, like a procedure calculating dicrotic notch location based on `sbp` points as well as `bp` and `ecg` waveforms. These three `dict` are:
* `Composite_data.waves`
* `Composite_data.points`
* `Composite_data.parameters`

Data objects may be added when initializing or afterwards.
```python
import sigman as sm
from sigman import file_manager as fm

ecg = fm.import_wave('example_data/EKG.dat', 'ecg')
composite_data = sm.Composite_data(waves={'ecg':ecg}) # when initializing

bp = fm.import_wave('example_data/BP.dat', 'bp')
composite_data.add_wave(bp, 'bp') # afterwards
r = fm.import_points('example_data/R.dat', 'r')
composite_data.add_points(r, 'r')
```

`sigman.file_manager` contains functions to save `sigman.Composite_data` objects for later.
```python
fm.save_composite_data('temporary_save.pickle', composite_data)
```
as well as
```python
composite_data = fm.load_composite_data('temporary_save.pickle')
```

Please note that the above functions use `pickle` and hence are not safe when loading files of unknown origin.

#### sigman.visualizer
The sigman library contains a module `visualizer` allowing for quick yet fairly limited visualization of `sigman.Composite_data`. Having created `composite_data` using steps from above it may be visualized:
```python
from sigman import visualizer as vis
vis.visualize_composite_data(composite_data)
```
`visualizer` also allows to visualize a chosen time range or specifically selected data from `sigman.Composite_data`.
```python
vis.visualize_composite_data(composite_data, begin_time=40, end_time=60, 
                             wanted_waves=['ecg'], title="ECG plot") 
```

#### sigman.analyzer
The `analyzer` module allows for the use of external procedures from the `procedures` folder. The exact structure of procedures is described in detail in `sigman/analyzer.py`.

Procedures may be used by first importing them with `analyzer.import_procedure`, modifying chosen arguments from `procedure.default_arguments`, applying them with an appropriate function from `sigman.analyzer` and replacing the data in `sigman.Composite_data` with the outputs.

##### Filtering/modifying waveforms
Filtering or modifying waveforms may be accompllished by importing a procedure of the `modify` type and applying it using `analyzer.modify_wave`. The function takes as an argument `sigman.Wave` to modify, the beginning and the end of the time range on which the procedure is to be performed, the imported procedure module as well as a `dict` of arguments based on `procedure.default_arguments`. It returns a new `sigman.Wave` with the length of the specified time range which we can use to replace the same time range slice from the old `sigman.Wave` using `Wave.replace_slice`

Filtering example:
```python
import sigman as sm
from sigman import file_manager as fm
from sigman import analyzer
from sigman import visualizer as vis

ecg = fm.import_wave('example_data/EKG.dat', 'ecg')
composite_data = sm.Composite_data(waves={'ecg':ecg})

butterworth = analyzer.import_procedure('modify_filter_butterworth')
arguments = butterworth.default_arguments
arguments['N'] = 3
arguments['Wn'] = 30
filtered_wave = analyzer.modify_wave(composite_data.waves['ecg'], 55, 60, butterworth, arguments)
composite_data.waves['ecg'].replace_slice(55,60, filtered_wave)

vis.visualize_composite_data(composite_data, begin_time=55, end_time=65, 
    title="Comparison of filtered <55s, 60s> and unfiltered <60s, 65s> ranges")
```

##### Finding points
Points may be found using procedures of the `points` type and applying it with `analyzer.find_points`. The function takes as arguments two `dict` objects contianing `sigman.Wave` and `sigman.Points` where the keys are the same as `procedure.required_waves` and `.required_points`, the beginning and end of the specified time range, the procedure module as well as arguments based on `procedure.default_arguments` like above. It returns a `sigman.Points` which we can add to the rest of the data using `Composite_data.add_points` or to a different set of points using `Points.add_points`.

Example of finding DBP points on the entire BP signal:
```python
import sigman as sm
from sigman import file_manager as fm
from sigman import analyzer
from sigman import visualizer as vis

bp = fm.import_wave('example_data/BP.dat', 'bp')
composite_data = sm.Composite_data(waves={'bp':bp})

dbp_finder = analyzer.import_procedure('points_dbp_simple')
# we have to calculate the maximum time range (i.e. containing the entirety of bp)
begin_time, end_time = composite_data.calculate_time_range(['bp'])
dbp = analyzer.find_points(composite_data, begin_time, end_time, dbp_finder, dbp_finder.default_arguments)
composite_data.add_points(dbp, 'dbp')

vis.visualize_composite_data(composite_data)
```

##### Calculating parameters
Parameters may be calculated by importing a procedure of type `parameter` and applying it using `analyzer.calculate_parameter`. The function takes as an argument two dicts, one for waveforms and one for points like above, a list of tuples containing the beginnings and ends of time ranges on which we wish to calculate our parameter, the procedure module and additional arguments based on `procedure.default_arguments`.

Example calculating the heart rate on ranges <0s, 15s>, <15s, 60s> and <60s, 120s> based on the ECG signal.
```python
import sigman as sm
from sigman import file_manager as fm
from sigman import analyzer
from sigman import visualizer as vis

ecg = fm.import_wave('example_data/EKG.dat', 'ecg')
composite_data = sm.Composite_data(waves={'ecg':ecg})

# we must first find the r points
r_finder = analyzer.import_procedure('points_r_simple')
begin_time, end_time = composite_data.calculate_time_range(['ecg'])
r = analyzer.find_points(composite_data, begin_time, end_time, r_finder, r_finder.default_arguments)
composite_data.add_points(r, 'r')

# heart rate calculation
hr_proc = analyzer.import_procedure('parameter_heart_rate')
param_tuples = [(0,15),(15,60),(60,120)]
hr = analyzer.calculate_parameter(composite_data, param_tuples, hr_proc, hr_proc.default_arguments)
composite_data.add_parameter(hr, 'hr')

vis.visualize_composite_data(composite_data)
```

Examples of various sigman functions may be found in the file `test_sigman.py`

## Code standards
The code should stick to the [PEP-8](https://www.python.org/dev/peps/pep-0008/) as closely as possible. The **sigman** library naming convention is `lowercase_with_underscore`, whereas the **QtSigman** application naming convention, in an effort to be consistent with PyQt, is `CamelCase`.

## Credits
* [Mossakowski Medical Research Centre PAN](http://imdik.pan.pl/en/) - assistance and directing the project, data

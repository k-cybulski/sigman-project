from PyQt5 import QtCore as QC

from QtSigman.DefaultColors import getColor
from sigman import Wave, Points, Parameter

class VObject(QC.QObject):
    """Contains a collection of plottable data, e.g. a set of points
    or a waveform.

    These are kept in MplWidgets.PlotWidget instances, and are updated 
    whenever sigman data objects to which they refer change via calls
    from the PlotWidget.

    Emits a VObject.changed signal whenever its settings change via
    setSettings.

    Attributes:
        VObject.color     - colour of this VObject
        VObject.axis      - number/id of the axis to paint on (e.g.
                            -1 - none/hidden, 0 - left, 1 - right)
        VObject.mplObject - drawn matplotlib object, e.g. Line2D
    """
    changed = QC.pyqtSignal()
    axisChanged = QC.pyqtSignal()

    def __init__(self, qDataObject, color=None, axis=-1):
        super().__init__()
        self.data = qDataObject
        qDataObject.changed.connect(self.update)
        if color is None:
            color = getColor(qDataObject.type)
        self.color = color
        self.mplObject = None
        self.axis = axis

    def update(self):
        """Plots the VObject if visible on an axis.

        Ran whenever self.data QDataObject emits QDataObject.changed.
        """
        if self.axis >= 0 and self.mplObject is not None:
            self.plot(self.mplObject.axes)
            self.mplObject.axes.figure.canvas.draw()

    def plot(self, mplAxis, beginTime=None, endTime=None):
        """Paints or updates the VObject on the given Axes.
        
        Abstract method ot be overriden.

        Arguments:
            beginTime - Beginning of the time range where the object is
                        shown.
            endTime   - Ending of the time range where the object is 
                        shown.
        """
    
    def setSettings(self, color, axis):
        """Sets the color and axis and emits a VObject.changed signal
        if changed.

        If axis is changed, it also deletes self.mplObject.
        """
        changed = False
        if color != self.color:
            self.setColor(color)
            changed = True
        if self.axis != axis:
            self.deleteMplObject()
            self.axis = axis
            self.axisChanged.emit()
            changed = True
        if changed:
            if self.mplObject is not None:
                self.update()
            self.changed.emit()

    def setDictKey(self, key):
        """Notifies the connected QDataObject that its key should be
        changed.
        """
        self.data.setDictKey(key)

    def delete(self):
        """Notifies the connected QDataObject that it should be deleted
        and deletes the mplObject.
        """
        self.data.delete()
        self.deleteMplObject()

    def deleteMplObject(self):
        """Deletes the painted matplotlib object."""
        if self.mplObject is not None:
            axes = self.mplObject.axes
            self.mplObject.remove()
            self.mplObject = None
            axes.figure.canvas.draw()

    def setColor(self, color):
        """Sets the color of the matplotlib object."""
        self.color = color
        if self.mplObject is not None:
            self.mplObject.set_color(color)

class VWave(VObject):
    """Overrides VObject to accommodate sm.Wave as self.data."""

    def copy(self):
        """Returns a VWave that references the same sm.VWave, has the
        same color and axis.
        """
        return VWave(self.data, self.color, self.axis)

    def plot(self, mplAxis, beginTime=None, endTime=None):
        """Plots sm.Wave from self.data on mplAxis.
        
        Overrides VObject.plot.
        """
        if beginTime is None:
            beginTime = self.data.offset
        else:
            beginTime = max(beginTime, 
                            self.data.offset)
        if endTime is None:
            endTime = self.data.offset + self.data.complete_length
        else:
            endTime = min(endTime, 
                          self.data.offset + self.data.complete_length)

        x, y = self.data.generate_coordinate_tables(
            begin_time=beginTime,
            end_time=endTime,
            begin_x=beginTime)
        if self.mplObject is None:
            self.mplObject, = mplAxis.plot(
                x, y, color=self.color, label=self.data.type)
        else:
            self.mplObject.set_xdata(x)
            self.mplObject.set_ydata(y)

class VPoints(VObject):
    """Overrides VObject to accommodate sm.Points as self.data."""
    
    def copy(self):
        """Returns a VPoints that references the same sm.Points, has
        the same color and axis.
        """
        return VPoints(self.data, self.color, self.axis)

    def plot(self, mplAxis, beginTime=None, endTime=None):
        """Plots sm.Points from self.data on mplAxis.

        Overrides VObject.plot.
        """
        if beginTime is None:
            beginTime = self.data.data_x[0]
        if endTime is None:
            endTime = self.data.data_x[-1]
        
        slice_ = self.data.data_slice(beginTime, endTime)
        if slice_ is None:
            return
        x, y = slice_
        if self.mplObject is None:
            self.mplObject, = mplAxis.plot(
                x, y, color=self.color, label=self.data.type,
                marker='o', linestyle='None', picker=5)
        else:
            self.mplObject.set_xdata(x)
            self.mplObject.set_ydata(y)

class VParameter(VObject):
    """OVerrides VObject to accommodate sm.Parameter as self.data."""

    def copy(self):
        """Returns a VParameter that references the same sm.Points, has
        the same color and axis.
        """
        return VParameter(self.data, self.color, self.axis)

    def update(self):
        """Plots the VParameter if visible on an axis.

        Ran whenever self.data QDataObject emits QDataObject.changed.
        """
        if self.axis != 0 and self.mplObject != []:
            self.plot(self.mplObject[0].axes)
            self.mplObject[0].axes.figure.canvas.draw()

    def plot(self, mplAxis, beginTime=None, endTime=None):
        """Plots sm.Parameter from self.data on mplAxis.

        Overrides VObject.plot.
        """
        if beginTime is None:
            beginTime = self.data.begin_times[0]
        else:
            beginTime = max(beginTime,
                            self.data.begin_times[0])
        if endTime is None:
            endTime = max(self.data.end_times)
        else:
            endTime = min(endTime,
                          max(self.data.end_times))

        lineTuples = self.generate_parameter_line_tuples(
            begin_time=beginTime, end_time=endTime)
        if len(self.mplObject) != len(lineTuples):
            self.deleteMplObject()
        if self.mplObject == []:
            for tup in lineTuples:
                line, = mplAxis.plot(
                    tup[0], tup[1], color=self.color, label=self.data.type)
                self.mplObject.append(line)
        else:
            for line, tup in zip(self.mplObject, lineTuples):
                line.set_xdata(tup[0])
                line.set_ydata(tup[1])

    def deleteMplObject(self):
        """Deletes all painted matplotlib lines and declares
        self.mplObject to be an empty list.

        Overrides VObject.deleteMplObject.
        """
        if self.mplObject is not None: # set to None in VObject.__init__
            for line in self.mplObject:
                line.delete()
        self.mplObject = []

    def setColor(self, color):
        """Sets the color of all painted matplotlib lines.
        
        Overrides VObject.setColor.
        """
        self.color = color
        for line in self.mplObject:
            line.set_color(color)
            line.axes.draw_artist(line)

class VCollection(QC.QObject):
    """Contains three dicts of VObjects, similar to Composite_data."""
    waveAdded = QC.pyqtSignal(VWave, str)
    waveKeyChanged = QC.pyqtSignal(str, str)
    waveDeleted = QC.pyqtSignal(str)
    pointsAdded = QC.pyqtSignal(VPoints, str)
    pointsKeyChanged = QC.pyqtSignal(str, str)
    pointsDeleted = QC.pyqtSignal(str)
    parameterAdded = QC.pyqtSignal(VParameter, str)
    parameterKeyChanged = QC.pyqtSignal(str, str)
    parameterDeleted = QC.pyqtSignal(str)

    def __init__(self, waves={}, points={}, parameters={}):
        """Initializes a VCollection with VObjects from given dicts."""
        super().__init__()
        self.waves = {}
        self.points = {}
        self.parameters = {}
        for key, item in waves.items():
            self.addWave(item, key)
        for key, item in points.items():
            self.addPoints(item, key)
        for key, item in parameters.items():
            self.addParameter(item, key)
        self.connections = []
    
    @classmethod
    def fromCompositeDataWrapper(cls, compositeDataWrapper):
        """Creates a VCollection with data from a CompositeDataWrapper.
        
        All VObjects have default colors and are in the hidden axis.
        """
        waves = compositeDataWrapper.waves.copy()
        points = compositeDataWrapper.points.copy()
        parameters = compositeDataWrapper.parameters.copy()
        for key, item in waves.items():
            waves[key] = VWave(item)
        for key, item in points.items():
            points[key] = VPoints(item)
        for key, item in parameters.items():
            parameters[key] = VParameter(item)
        out = cls(waves, points, parameters)
        connections = [
            (compositeDataWrapper.waveAdded, out.addWave),
            (compositeDataWrapper.waveKeyChanged, out.changeWaveKey),
            (compositeDataWrapper.waveDeleted, out.deleteWave),
            (compositeDataWrapper.pointsAdded, out.addPoints),
            (compositeDataWrapper.pointsKeyChanged, out.changePointsKey),
            (compositeDataWrapper.pointsDeleted, out.deletePoints),
            (compositeDataWrapper.parameterAdded, out.addParameter),
            (compositeDataWrapper.parameterKeyChanged, out.changeParameterKey),
            (compositeDataWrapper.parameterDeleted, out.deleteParameter)]
        out.connectConnections(connections)
        return out

    @classmethod
    def fromVCollection(cls, vCollection, allHidden=False):
        """Creates a VCollection that is a copy of the given one.
        
        Arguments:
            allHidden   - if True all VObjects in the VCollection will
                          be in the -1 axis.
        """
        waves = {}
        points = {}
        parameters = {}
        for key, item in vCollection.waves.items():
            axis = item.axis
            if allHidden:
                axis = -1
            waves[key] = VWave(item.data, item.color, axis)
        for key, item in vCollection.points.items():
            axis = item.axis
            if allHidden:
                axis = -1
            points[key] = VPoints(item.data, item.color, axis)
        for key, item in vCollection.parameters.items():
            axis = item.axis
            if allHidden:
                axis = -1
            parameters[key] = VParameter(item.data, item.color, axis)
        out = cls(waves, points, parameters)
        connections = [
            (vCollection.waveAdded, out.addWave),
            (vCollection.waveKeyChanged, out.changeWaveKey),
            (vCollection.waveDeleted, out.deleteWave),
            (vCollection.pointsAdded, out.addPoints),
            (vCollection.pointsKeyChanged, out.changePointsKey),
            (vCollection.pointsDeleted, out.deletePoints),
            (vCollection.parameterAdded, out.addParameter),
            (vCollection.parameterKeyChanged, out.changeParameterKey),
            (vCollection.parameterDeleted, out.deleteParameter)]
        out.connectConnections(connections)
        return out

    def connectConnections(self, connections):
        for connection in connections:
            connection[0].connect(connection[1])
        self.connections.extend(connections)

    def delete(self):
        self.waveAdded.disconnect()
        self.waveDeleted.disconnect()
        self.pointsAdded.disconnect()
        self.pointsDeleted.disconnect()
        self.parameterAdded.disconnect()
        self.parameterDeleted.disconnect()
        for connection in self.connections:
            connection[0].disconnect(connection[1])
        for dict_ in [self.waves,
                      self.points,
                      self.parameters]:
            for item in dict_.values():
                item.deleteMplObject()
        self.waves = {}
        self.points = {}
        self.parameters = {}

    def addWave(self, wave, key):
        if key in self.waves:
            raise ValueError("Key %s is taken"
                             % key)
        if not isinstance(wave, VWave):
            wave = VWave(wave)
        else:
            wave = wave.copy()
        self.waves[key] = wave
        self.waveAdded.emit(wave, key)

    def changeWaveKey(self, keyFrom, keyTo):
        self.waves[keyTo] = self.waves[keyFrom]
        self.waves.pop(keyFrom)
        self.waveKeyChanged.emit(keyFrom, keyTo)

    def deleteWave(self, key):
        if key not in self.waves:
            return
        self.waves[key].deleteMplObject()
        self.waves.pop(key)
        self.waveDeleted.emit(key)

    def addPoints(self, points, key):
        if key in self.points:
            raise ValueError("Key %s is taken"
                             % key)
        if not isinstance(points, VPoints):
            points = VPoints(points)
        else:
            points = points.copy()
        self.points[key] = points
        self.pointsAdded.emit(points, key)

    def deletePoints(self, key):
        if key not in self.points:
            return
        self.points[key].deleteMplObject()
        self.points.pop(key)
        self.pointsDeleted.emit(key)

    def changePointsKey(self, keyFrom, keyTo):
        self.points[keyTo] = self.points[keyFrom]
        self.points.pop(keyFrom)
        self.pointsKeyChanged.emit(keyFrom, keyTo)

    def addParameter(self, parameter, key):
        if key in self.parameters:
            raise ValueError("Key %s is taken"
                             % key)
        if not isinstance(parameter, VParameter):
            parameter = VPoints(parameter)
        else:
            parameter = parameter.copy()
        self.parameters[key] = parameter
        self.parameterAdded.emit(parameter, key)

    def deleteParameter(self, key):
        if key not in self.parameters:
            return
        self.parameters[key].deleteMplObject()
        self.parameters.pop(key)
        self.parameterDeleted.emit(key)

    def changeParameterKey(self, keyFrom, keyTo):
        self.parameters[keyTo] = self.parameters[keyFrom]
        self.parameters.pop(keyFrom)
        self.parameterKeyChanged.emit(keyFrom, keyTo)

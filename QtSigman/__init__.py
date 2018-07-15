"""
QtSigman
========
PyQt5 application providing a GUI to the `sigman` library.
"""
from functools import partial
import os
from PyQt5 import QtWidgets as QW
from PyQt5 import QtCore as QC
import sigman as sm
from QtSigman import MplWidgets, DataActions, ListWidgets

from QtSigman import MplWidgets, DataActions, ListWidgets, DefaultColors
from QtSigman.DataActions import ActionCancelledError
from QtSigman.VisualObjects import VCollection, VWave, VPoints

class QDataObject(QC.QObject):
    """Abstract class containing a self.changed signal to be emitted
    whenever instances of its children classes changed, as well as a
    toDelete and toSetKey signal to inform CompositeDataWrapper of
    desired changes.
    """
    changed = QC.pyqtSignal()
    toDelete = QC.pyqtSignal()
    toSetKey = QC.pyqtSignal(str)

    def delete(self):
        self.toDelete.emit()

    def setDictKey(self, key):
        self.toSetKey.emit(key)

class QWave(sm.Wave, QDataObject):
    """Extends sm.Wave to emit a self.changed Qt signal whenever any
    operation changes it.
    """

    def __init__(self, data):
        super().__init__(data.data,
                         data.sample_rate,
                         data.type,
                         offset=data.offset)
        QDataObject.__init__(self)

    def replace_slice(self, begin_time, end_time, wave):
        super().replace_slice(begin_time, end_time, wave)
        self.changed.emit()

class QPoints(sm.Points, QDataObject):
    """Extends sm.Points to emit a self.changed Qt signal whenever any
    operation changes it.
    """

    def __init__(self, data):
        super().__init__(data.data_x,
                         data.data_y,
                         data.type)
        QDataObject.__init__(self)

    def delete_slice(self, begin_time, end_time):
        super().delete_slice(begin_time, end_time)
        self.changed.emit()

    def replace_slice(self, begin_time, end_time, points):
        super().replace_slice(begin_time, end_time, points)
        self.changed.emit()

    def add_point(self, x, y):
        super().add_point(x, y)
        self.changed.emit()

    def add_points(self, points, begin_time=0):
        super().add_points(points, begin_time=begin_time)
        self.changed.emit()

    def delete_point(self, x, y=None):
        super().delete_point(x, y=y)
        self.changed.emit()

    def move_point(self, x1, y1, x2, y2):
        super().move_point(x1, y1, x2, y2)
        self.changed.emit()

    def align_to_line(self, line):
        super().align_to_line(line)
        self.changed.emit()

    def move_in_time(self, time):
        super().move_in_time(time)
        self.changed.emit()

class QParameter(sm.Parameter, QDataObject):
    """Extends sm.Parameter to emit a self.changed Qt signal whenever
    any operation changes it.
    """

    def __init__(self, parameter_type):
        super().__init__(parameter_type)
        QDataObject.__init__(self)

    def add_value(self, begin_time, end_time, value):
        super().add_value(begin_time, end_time, value)
        self.changed.emit()

class CompositeDataWrapper(sm.Composite_data, QC.QObject):
    """Class extending sm.Composite_data with Qt signals and methods
    that allow for external editing (e.g. via functions from
    QtSigman.DataActions).
    """
    waveAdded = QC.pyqtSignal(QWave, str)
    waveKeyChanged = QC.pyqtSignal(str, str)
    waveDeleted = QC.pyqtSignal(str)
    pointsAdded = QC.pyqtSignal(QPoints, str)
    pointsKeyChanged = QC.pyqtSignal(str, str)
    pointsDeleted = QC.pyqtSignal(str)
    parameterAdded = QC.pyqtSignal(QParameter, str)
    parameterKeyChanged = QC.pyqtSignal(str, str)
    parameterDeleted = QC.pyqtSignal(str)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        QC.QObject.__init__(self)

        for key, item in self.waves.items():
            self.add_wave(item, key)
        for key, item in self.points.items():
            self.add_points(item, key)
        for key, item in self.parameters.items():
            self.add_parameter(item, key)

    @classmethod
    def fromCompositeData(cls, compositeData):
        """Creates a CompositeDataWrapper instance from Composite_data."""
        return cls(
            waves=compositeData.waves,
            points=compositeData.points,
            parameters=compositeData.parameters)

    def replace(self, compData):
        """Replaces all of the items in this CompositeDataWrapper with
        those from an other Composite_data instance.
        """
        for dict_ in [self.waves,
                      self.points,
                      self.parameters]:
            for key in list(dict_.keys()):
                self._delete(dict_[key], key)
        waves = compData.waves
        points = compData.points
        parameters = compData.parameters
        for key, item in waves.items():
            self.add_wave(item, key)
        for key, item in points.items():
            self.add_points(item, key)
        for key, item in parameters.items():
            self.add_parameter(item, key)

    def _delete(self, data, key):
        if isinstance(data, QWave):
            self.delete_wave(key)
        elif isinstance(data, QPoints):
            self.delete_points(key)
        elif isinstance(data, QParameter):
            self.delete_parameter(key)

    def add_wave(self, wave, dict_type, replace=False):
        """Adds a Wave as a QWave and emits waveNumberChanged signal.
        
        Overrides add_wave.
        """
        # super().add_wave checks if it's possible to add it
        super().add_wave(wave, dict_type, replace=replace)
        self.waves[dict_type] = QWave(wave)
        self.waves[dict_type].toDelete.connect(
            lambda: self.delete_wave(dict_type))
        self.waves[dict_type].toSetKey.connect(
            lambda key: self.setWaveKey(
                dict_type, key))
        self.waveAdded.emit(self.waves[dict_type], dict_type)

    def delete_wave(self, dict_type):
        """Deletes a QWave with the given dict type and emits
        waveNumberChanged signal.

        Overrides delete_wave."""
        self.waves[dict_type].changed.disconnect()
        self.waves[dict_type].toDelete.disconnect()
        self.waves[dict_type].toSetKey.disconnect()
        super().delete_wave(dict_type)
        self.waveDeleted.emit(dict_type)

    def setWaveKey(self, dictTypeFrom, dictTypeTo):
        """Changes the dict key of a chosen wave from one to an other.
        Reconnects the toDelete and toSetKey signals.
        """
        if dictTypeFrom == dictTypeTo:
            return
        self.waves[dictTypeTo] = self.waves[dictTypeFrom]
        self.waves.pop(dictTypeFrom)
        self.waves[dictTypeTo].toDelete.disconnect()
        self.waves[dictTypeTo].toDelete.connect(
            lambda: self.delete_wave(
                dictTypeTo))
        self.waves[dictTypeTo].toSetKey.disconnect()
        self.waves[dictTypeTo].toSetKey.connect(
            lambda key: self.setWaveKey(
                dictTypeTo, key))
        self.waveKeyChanged.emit(dictTypeFrom, dictTypeTo)

    def add_points(self, points, dict_type, join=False):
        """Adds a Points instance as a QPoints and emits
        pointNumberChanged signal.
        
        Overrides add_points.
        """
        super().add_points(points, dict_type, join=join)
        self.points[dict_type] = QPoints(points)
        self.points[dict_type].toDelete.connect(
            lambda: self.delete_points(dict_type))
        self.points[dict_type].toSetKey.connect(
            lambda key: self.setPointsKey(
                dict_type, key))
        self.pointsAdded.emit(self.points[dict_type], dict_type)

    def delete_points(self, dict_type):
        """Deletes a QPoints with the given dict type and emits
        pointNumberChanged signal.
        
        Overrides delete_points.
        """
        self.points[dict_type].changed.disconnect()
        self.points[dict_type].toDelete.disconnect()
        self.points[dict_type].toSetKey.disconnect()
        super().delete_points(dict_type)
        self.pointsDeleted.emit(dict_type)

    def setPointsKey(self, dictTypeFrom, dictTypeTo):
        """Changes the dict key of chosen points from one to an other."""
        if dictTypeFrom == dictTypeTo:
            return
        self.points[dictTypeTo] = self.points[dictTypeFrom]
        self.points.pop(dictTypeFrom)
        self.points[dictTypeTo].toSetKey.disconnect()
        self.points[dictTypeTo].toSetKey.connect(
            lambda key: self.setPointsKey(
                dictTypeTo, key))
        self.pointsKeyChanged.emit(dictTypeFrom, dictTypeTo)

    def add_parameter(self, parameter, dict_type, replace=False):
        """Adds a Parameter as a QParameter and emits
        parameterNumberChanged signal.
        
        Overrides add_parameter.
        """
        super().add_parameter(points, dict_type, replace=replace)
        self.parameters[dict_type] = QParameter(parameter)
        self.parameters[dict_type].toDelete.connect(
            lambda: self.delete_parameter(dict_type))
        self.parameters[dict_type].toSetKey.connect(
            lambda key: self.setParameterKey(
                dict_type, key))
        self.parameterAdded.emit(self.parameters[dict_type], dict_type)

    def delete_parameter(self, dict_type):
        """Deletes a QParameter with the given dict type and emits
        parameterNumberChanged signal.

        Overrides delete_parameter.
        """
        self.parameters[dict_type].changed.disconnect()
        self.parameters[dict_type].toDelete.disconnect()
        self.parameters[dict_type].toSetKey.disconnect()
        super().delete_parameter(dict_type)
        self.parameterDeleted.emit(dict_type)

    def setParameterKey(self, dictTypeFrom, dictTypeTo):
        """Changes the dict key of a chosen parameter from one to an 
        other.
        """
        if dictTypeFrom == dictTypeTo:
            return
        self.parameters[dictTypeTo] = self.parameters[dictTypeFrom]
        self.parameters.pop(dictTypeFrom)
        self.parameters[dictTypeTo].toSetKey.disconnect()
        self.parameters[dictTypeTo].toSetKey.connect(
            lambda key: self.setParameterKey(
                dictTypeTo, key))
        self.parameterKeyChanged.emit(dictTypeFrom, dictTypeTo)

class QtSigmanWindow(QW.QMainWindow):
    """Class containing the main window of the application."""
    def __init__(self):
        QW.QMainWindow.__init__(self)
        self.setAttribute(QC.Qt.WA_DeleteOnClose)
        self.setWindowTitle("QtSigman")

        self.compositeDataWrapper = CompositeDataWrapper()

        # Setting up the main layout
        self.mainWidget = QW.QWidget(self)
        mainLayout = QW.QHBoxLayout(self.mainWidget)
        self.setCentralWidget(self.mainWidget)
        # Elements on the left
        self.plotWidgets = []
        self.plotTabWidget = QW.QTabWidget(self.mainWidget)
        mainLayout.addWidget(self.plotTabWidget)

        # Elements on the right
        rightVBoxLayout = QW.QVBoxLayout()
        self.listWidgets = []
        self.stackedListWidget = QW.QStackedWidget(self)
        self.stackedListWidget.setSizePolicy(QW.QSizePolicy.Fixed,
                                             QW.QSizePolicy.Expanding)
        self.plotTabWidget.currentChanged.connect(self._sortListWidgets)
        mainLayout.addWidget(self.stackedListWidget)
        self.addPlot()

        # Menu bar
        self.file_menu = QW.QMenu('File', self)
        self.file_menu.addAction('Import waveform', self.importWave)
        self.file_menu.addAction('Import points', self.importPoints)
        self.file_menu.addAction('Load Modelflow data',
                self.importModelflow)        
        self.file_menu.addAction('Load project', self.loadCompositeData)
        self.file_menu.addAction('Save project', self.saveCompositeData)
        self.file_menu.addAction('Quit', self.quit)
        self.menuBar().addMenu(self.file_menu)

        self.windowMenu = QW.QMenu('View', self)
        self.windowMenu.addAction('Add a plot', self.addPlot)
        self.menuBar().addMenu(self.windowMenu)
        self.windowMenu.addAction('Remove a plot', self.deletePlot)
        self.menuBar().addMenu(self.windowMenu)

        self.procedure_menu = QW.QMenu('Procedures', self)
        self.procedure_menu.addAction('Modify waveform', self.modifyWave)
        self.procedure_menu.addAction('Find points', self.findPoints)
        self.menuBar().addMenu(self.procedure_menu)

        #TODO: Clean
        self.analize_menu = QW.QMenu('Macros', self)
        path = "macros"    
        analize_List = os.listdir(path);
        for i in range (0,len(analize_List)):
            self.analize_menu.addAction(analize_List[i], partial(self.executeMacros,analize_List[i]))
             
        self.menuBar().addMenu(self.analize_menu)

        self.help_menu = QW.QMenu('Help', self)
        self.help_menu.addAction('About', self.about)
        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.help_menu)

    def _replaceCompositeDataWrapper(self, compositeDataWrapper):
        if compositeDataWrapper is not None:
            self.compositeDataWrapper.replaceWithCompositeDataWrapper(
                compositeDataWrapper)
            for plot in self.plotWidgets:
                vCollection = VCollection.fromCompositeData(
                    compositeDataWrapper)
                plot.replaceVCollection(vCollection)

    def _sortListWidgets(self):
        self.stackedListWidget.setCurrentIndex(
            self.plotTabWidget.currentIndex())

    def addPlot(self):
        """Adds a new PlotWidget to self.plotTabWidget based on the 
        first PlotWidget, as well as a corresponding 
        VCollectionListWidget to self.listWidgets. If it is the first
        PlotWidget, it's instead directly based on self.compositeDataWrapper.
        """
        if len(self.plotWidgets) == 0:
            self.plotWidgets.append(
                MplWidgets.PlotWidget.fromCompositeDataWrapper(
                    self.compositeDataWrapper))
            self.plotTabWidget.addTab(
                self.plotWidgets[0], "Main")
        else:
            self.plotWidgets.append(
                MplWidgets.PlotWidget.fromVCollection(
                    self.plotWidgets[0].vCollection,
                    allHidden=True))
            self.plotTabWidget.addTab(
                self.plotWidgets[-1], str(len(self.plotWidgets)-1))
        self.listWidgets.append(
            ListWidgets.VCollectionListWidget(
                self.plotWidgets[-1].vCollection))
        self.stackedListWidget.addWidget(
            self.listWidgets[-1])

    def deletePlot(self):
        """Deletes the currently selected plot. If the main plot is
        selected, it does nothing.
        """
        index = self.plotTabWidget.currentIndex()
        if index == 0:
            return
        self.plotWidgets[index].vCollection.delete()
        self.plotTabWidget.removeTab(index)
        self.stackedListWidget.removeWidget(
            self.stackedListWidget.widget(index))
        del self.plotWidgets[index]
        del self.listWidgets[index]
        for i in range(1, self.plotTabWidget.count()+1):
            self.plotTabWidget.setTabText(i, str(i))
        
    def importWave(self):
        try:
            setOfWaves = DataActions.loadWave(
                    self.compositeDataWrapper.waves.keys())
            for waveTuple in setOfWaves:
                wave, key, color, axis = waveTuple
                self.compositeDataWrapper.add_wave(wave, key)
                self.plotTabWidget.currentWidget().vCollection.waves[
                        key].setSettings(color, axis)
        except ActionCancelledError:
            pass

    def importPoints(self):
        try:
            setOfPoints = DataActions.loadPoints(
                    self.compositeDataWrapper.points.keys())
            for pointsTuple in setOfPoints:
                points, key, color, axis = pointsTuple
                self.compositeDataWrapper.add_points(points, key)
                self.plotTabWidget.currentWidget().vCollection.points[
                        key].setSettings(color, axis)
        except ActionCancelledError:
            pass
   
    def importModelflow(self):
        try:
            modelflowPoints, modelflowData = DataActions.loadModelflow(
                    self.compositeDataWrapper)

            for i in range(len(modelflowPoints)):
                wave = modelflowPoints[i]
                key = modelflowData[i]
                color = DefaultColors.getColor(key)
                axis = -1
                try:
                    self.compositeDataWrapper.add_points(wave, key)
                except ValueError:
                    QW.QMessageBox.warning(
                        self, "Error", ("Key "+key+" already taken. "
                                        "Cannot import."))
                    raise ActionCancelledError
                self.plotTabWidget.currentWidget().vCollection.points[
                        key].setSettings(color, axis)
        except ActionCancelledError:
            pass

    def saveCompositeData(self):
        try:
            DataActions.saveCompositeData(self.compositeDataWrapper)
        except ActionCancelledError:
            pass

    def loadCompositeData(self):
        try:
            compData = DataActions.loadCompositeData()
            self.compositeDataWrapper.replace(compData)
        except ActionCancelledError:
            pass

    def modifyWave(self):
        try:
            DataActions.modifyWave(self.compositeDataWrapper)
        except ActionCancelledError:
            pass

    def findPoints(self):
        try:
            points, key, color, axis = DataActions.findPoints(
                self.compositeDataWrapper)
            self.compositeDataWrapper.add_points(points, key)
            self.plotTabWidget.currentWidget().vCollection.points[key].setSettings(
                color, axis)
        except ActionCancelledError:
            pass

    def executeMacros(self, macroName):
        setOfPoints, setOfWaves = DataActions.executeMacro(self.compositeDataWrapper,macroName)
        for i in range(len(setOfPoints)):
            self.compositeDataWrapper.add_points(setOfPoints[i][0], setOfPoints[i][1])
            self.plotTabWidget.currentWidget().vCollection.points[setOfPoints[i][1]].setSettings(
                setOfPoints[i][2], setOfPoints[i][3])
        for i in range(len(setOfWaves)):
            self.compositeDataWrapper.add_wave(setOfWaves[i][0], setOfWaves[i][1])
            self.plotTabWidget.currentWidget().vCollection.waves[
                        setOfWaves[i][1]].setSettings(setOfWaves[i][2], setOfWaves[i][3])


    def quit(self):
        self.close()

    def closeEvent(self, ce):
        self.quit()

    def about(self):
        QW.QMessageBox.about(self, "About",
                                    """QtSigman
GUI for the digital signal library sigman.
Alpha version
                                                                Krzysztof Cybulski 2018""")

   
        


def initialize():
    """Initializes the application."""
    app = QW.QApplication([])
    qtSigmanWindow = QtSigmanWindow()
    qtSigmanWindow.show()
    app.exec()

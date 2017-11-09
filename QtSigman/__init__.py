"""
QtSigman
======
Biblioteka tworząca GUI w PyQt5 do bezpośredniej współpracy z 
biblioteką sigman.

Tutaj utrzymujemy nazewnictwo camelCase na tyle na ile to możliwe ze
względu na zgodność z biblioteką PyQt5.
"""
from PyQt5 import QtWidgets as QW
from PyQt5 import QtCore as QC
import sigman as sm
from matplotlib import colors

from QtSigman.DefaultColors import defaultColors
from QtSigman import MplWidgets, DataActions, ListWidgets
from QtSigman.MplWidgets import Axis

class VisualDataObject():
    def __init__(self, data, color, axis):
        self.color = color
        self.axis = axis
        self.mplObject = None

    def plot(self, axis, beginTime, endTime):
        pass

    def removeMplObject(self):
        if self.mplObject is not None:
            self.mplObject.remove()
            self.mplObject = None

    def setMplColor(self, color):
        if self.mplObject is not None:
            self.mplObject.set_color(color)

class VisualDataWave(VisualDataObject, sm.Data_wave):
    def __init__(self, data, color, axis):
        VisualDataObject.__init__(self, data, color, axis)
        sm.Data_wave.__init__(self,
                              data.data,
                              data.complete_length,
                              line_type = data.type,
                              offset = data.offset)

    def plot(self, axis, beginTime, endTime):
        tempBeginTime = max(beginTime, self.offset)
        tempEndTime = min(endTime, self.offset 
                          + self.complete_length)
        x, y = self.generate_coordinate_tables(
            begin_time = tempBeginTime,
            end_time = tempEndTime,
            begin_x = tempBeginTime)
        if self.mplObject is None:
            self.mplObject, = axis.plot(x, y, color = self.color)
        else:
            self.mplObject.set_xdata(x)
            self.mplObject.set_ydata(y)

class VisualDataPoints(VisualDataObject, sm.Data_points):
    def __init__(self, data, color, axis):
        VisualDataObject.__init__(self, data, color, axis)
        sm.Data_points.__init__(self,
                                data.data_x,
                                data.data_y,
                                point_type = data.type)

    def plot(self, axis, beginTime, endTime):
        x, y = self.data_slice(beginTime, endTime)
        if self.mplObject is None:
            self.mplObject, = axis.plot(x, y, color = self.color, marker = 'o', linestyle = 'None')
        else:
            self.mplObject.set_xdata(x)
            self.mplObject.set_ydata(y)

class VisualParameter(VisualDataObject, sm.Parameter):
    def __init__(self, data, color, axis):
        VisualDataObject.__init__(self, data, color, axis)
        sm.Data_points.__init__(self,
                                data.type)
        self.begin_times = data.begin_times
        self.end_times = data.end_times
        self.values = data.values
        self.mplObjects = []

    def plot(self, axis, beginTime, endTime):
        lineTuples = self.generate_parameter_line_tuples(
            begin_time = beginTime, end_time = endTime)
        if len(self.mplObjects) != len(lineTuples):
            self.removeMplObject()
        if self.mplObjects == []:
            for tup in lineTuples:
                mplLine, = axis.plot(tup[0], tup[1], color = self.color)
                self.mplObject.append(mplLine)
        else:
            for mplLine, tup in zip(self.mplObject, lineTuples):
                mplLine.set_xdata(tup[0])
                mplLine.set_ydata(tup[1])

    def removeMplObject(self):
        for mplLine in mplObject:
            mplLine.remove()
        self.mplObject = []

    def setMplColor(self, color):
        for mplLine in mplObject:
            mplLine.set_color(color)

class CompositeDataWrapper(sm.Composite_data, QC.QObject):
    """Klasa rozszerzająca sm.Composite_data o zmienne i funkcje 
    pozwalające na wykorzystanie go graficznie."""
    
    # Sygnały do pozostałych obiektów Qt
    # informujące o dodawaniu i usuwaniu obiektów danych, np do list
    lineNumberChanged = QC.pyqtSignal()
    pointNumberChanged = QC.pyqtSignal()
    parameterNumberChanged = QC.pyqtSignal()
    # informujące o zmianach wewnątrz obiektów danych, np do rysowania
    lineChanged = QC.pyqtSignal()
    pointChanged = QC.pyqtSignal()
    parameterChanged = QC.pyqtSignal()

    def __init__(self, **kwargs):
        # Inicjalizujemy parents
        sm.Composite_data.__init__(self, **kwargs)
        QC.QObject.__init__(self)

        for key, item in self.data_waves.items():
            self.data_waves[key] = VisualDataWave(
                item, 
                colors.to_hex(defaultColors[key]),
                Axis.Hidden)
        for key, item in self.data_points.items():
            self.data_points[key] = VisualDataPoints(
                item, 
                colors.to_hex(defaultColors[key]),
                Axis.Hidden)
        for key, item in self.parameters.items():
            self.parameters[key] = VisualParameter(
                item, 
                colors.to_hex(defaultColors[key]),
                Axis.Hidden)
        self.dataDicts = [self.data_waves, self.data_points, self.parameters]

    def replaceWithCompositeDataWrapper(self, compositeDataWrapper):
        newDataDicts = [
            compositeDataWrapper.data_waves,
            compositeDataWrapper.data_points,
            compositeDataWrapper.parameters]
        for dataDict, newDataDict in zip(self.dataDicts, newDataDicts):
            for key, item in dataDict.items():
                item.removeMplObject()
            # Oczyszczanie zapisanych danych graficznych
            for key, item in newDataDict.items():
                item.mplObject = None
        self.data_waves = compositeDataWrapper.data_waves
        self.data_points = compositeDataWrapper.data_points
        self.parameters = compositeDataWrapper.parameters
        self.dataDicts = [
            self.data_waves,
            self.data_points,
            self.parameters]

        self.lineNumberChanged.emit()
        self.pointNumberChanged.emit()
        self.parameterNumberChanged.emit()
        self.lineChanged.emit()
        self.pointChanged.emit()
        self.parameterChanged.emit()

    @classmethod
    def fromSigmanCompositeData(cls, compositeData):
        return cls(
            data_waves = compositeData.data_waves,
            data_points = compositeData.data_points,
            parameters = compositeData.parameters)

    def add_data_wave(self, data_wave, dict_type, color, replace=False,
                      axis=Axis.Hidden):
        super(CompositeDataWrapper, self).add_data_wave(data_wave,
                                                        dict_type,
                                                        replace = replace)
        self.data_waves[dict_type] = VisualDataWave(
            self.data_waves[dict_type],
            color,
            axis)
        self.lineNumberChanged.emit()

    def editDataWaveSettings(self, dictType, newDictType, 
                                color, axis, offset):
        data_wave = self.data_waves[dictType]
        if data_wave.color != color:
            data_wave.setMplColor(color)
        if data_wave.axis != axis:
            data_wave.axis = axis
            data_wave.removeMplObject()
        data_wave.offset = offset 
        if dictType != newDictType:
            self.data_waves[newDictType] = data_wave
            self.data_waves.pop(dictType)
            self.lineNumberChanged.emit()
        self.lineChanged.emit()

    def delete_data_wave(self, dict_type):
        self.data_waves[dict_type].removeMplObject()
        super(CompositeDataWrapper, self).delete_data_wave(dict_type)
        self.lineNumberChanged.emit()

    def add_data_points(self, data_points, dict_type, color, join=False,
                        axis=Axis.Hidden):
        super(CompositeDataWrapper, self).add_data_points(data_points,
                                                          dict_type,
                                                          join = join)
        self.data_points[dict_type] = VisualDataPoints(
            self.data_points[dict_type],
            color,
            axis)
        self.pointNumberChanged.emit()

    def editDataPointsSettings(self, dictType, newDictType, 
                                color, axis, offset):
        data_points = self.data_points[dictType]
        if data_points.color != color:
            data_points.setMplColor(color)
        if data_points.axis != axis:
            data_points.axis = axis
            data_points.removeMplObject()
        data_points.move_in_time(offset)
        if dictType != newDictType:
            self.data_points[newDictType] = data_points
            self.data_points.pop(dictType)
            self.pointNumberChanged.emit()
        self.pointChanged.emit()

    def delete_data_points(self, dict_type):
        self.data_points[dict_type].removeMplObject()
        super(CompositeDataWrapper, self).delete_data_points(dict_type)
        self.pointNumberChanged.emit()

    def add_parameter(self, parameter, dict_type, color, replace=False,
                      axis=Axis.Hidden):
        super(CompositeDataWrapper, self).add_parameter(parameter,
                                                        dict_type,
                                                        replace = replace)
        self.parameters[dict_type] = VisualParameter(
            self.parameters[dict_type],
            color,
            axis)
        self.parameterNumberChanged.emit()

    def editParameterSettings(self, dictType, newDictType, 
                                color, axis):
        parameter = self.parameters[dictType]
        parameter.color = color
        if parameter.axis != axis:
            parameter.axis = axis
            parameter.removeMplObject()
        if dictType != newDictType:
            self.parameters[newDictType] = parameter
            self.parameters.pop(dictType)
            self.parameterNumberChanged.emit()
        self.parameterChanged.emit()

    def delete_parameter(self, dict_type):
        self.parameters[dict_type].removeMplObject()
        super(CompositeDataWrapper, self).delete_parameter(dict_type)
        self.parameterNumberChanged.emit()


class QtSigmanWindow(QW.QMainWindow):
    """Klasa zawierająca główne okno programu."""
    def __init__(self):
        QW.QMainWindow.__init__(self)
        self.setAttribute(QC.Qt.WA_DeleteOnClose)
        self.setWindowTitle("QtSigman")

        # Inicjalizacja biblioteki sigman i utworzenie pustego
        # CompositeDataWrapper
        self.compositeDataWrapper = CompositeDataWrapper()

        # Ustawienie elementów okna
        self.mainWidget = QW.QWidget(self)
        mainLayout = QW.QHBoxLayout(self.mainWidget)
        self.setCentralWidget(self.mainWidget)
        # Po lewej
        self.mplPlotWidget = MplWidgets.PlotWidget()
        mainLayout.addWidget(self.mplPlotWidget)
        # Podłączamy wszystkie możliwe sygnały qt wpływające na wykres do
        # obiektu wykresu
        self.compositeDataWrapper.lineNumberChanged.connect(self._refreshPlot)
        self.compositeDataWrapper.pointNumberChanged.connect(self._refreshPlot)
        self.compositeDataWrapper.parameterNumberChanged.connect(self._refreshPlot)
        self.compositeDataWrapper.lineChanged.connect(self._refreshPlot)
        self.compositeDataWrapper.pointChanged.connect(self._refreshPlot)
        self.compositeDataWrapper.parameterChanged.connect(self._refreshPlot)

        # Po prawej
        rightVBoxLayout = QW.QVBoxLayout()
        lineListLabel = QW.QLabel()
        lineListLabel.setText("Przebiegi")
        lineList = ListWidgets.DataListWidget()
        lineList.itemClicked.connect(lambda listItemWidget:
            DataActions.editLineSettings(self.compositeDataWrapper, 
                lineList.itemWidget(listItemWidget).typeLabel.text()))
        self.compositeDataWrapper.lineNumberChanged.connect(
            lambda:
            lineList.updateData(self.compositeDataWrapper, 'line'))
#        self.compositeDataReloaded.connect(
#            lambda:
#            lineList.updateData(self.compositeDataWrapper, 'line'))
        lineList.setSizePolicy(QW.QSizePolicy.Fixed,
                               QW.QSizePolicy.Expanding)
        rightVBoxLayout.addWidget(lineListLabel)
        rightVBoxLayout.addWidget(lineList)
        pointListLabel = QW.QLabel()
        pointListLabel.setText("Punkty") 
        pointList = ListWidgets.DataListWidget()
        pointList.itemClicked.connect(lambda listItemWidget:
            DataActions.editPointSettings(self.compositeDataWrapper, 
                pointList.itemWidget(listItemWidget).typeLabel.text()))
        self.compositeDataWrapper.pointNumberChanged.connect(
            lambda:
            pointList.updateData(self.compositeDataWrapper, 'point'))
#        self.compositeDataReloaded.connect(
#            lambda:
#            pointList.updateData(self.compositeDataWrapper, 'point'))
        pointList.setSizePolicy(QW.QSizePolicy.Fixed,
                                QW.QSizePolicy.Expanding) 
        rightVBoxLayout.addWidget(pointListLabel)
        rightVBoxLayout.addWidget(pointList)
        parameterListLabel = QW.QLabel() 
        parameterListLabel.setText("Obliczone parametry")
        self.compositeDataWrapper.parameterNumberChanged.connect(
            lambda:
            parameterList.updateData(self.compositeDataWrapper, 'parameter'))
#        self.compositeDataReloaded.connect(
#            lambda:
#            parameterList.updateData(self.compositeDataWrapper, 'parameter'))
        parameterList = ListWidgets.DataListWidget()
        parameterList.setSizePolicy(QW.QSizePolicy.Fixed,
                                    QW.QSizePolicy.Expanding) 
        rightVBoxLayout.addWidget(parameterListLabel)
        rightVBoxLayout.addWidget(parameterList)
        mainLayout.addLayout(rightVBoxLayout)

        # Ustawienie paska menu
        self.file_menu = QW.QMenu('Plik', self)
        self.file_menu.addAction('Importuj przebieg', lambda:
            DataActions.importLine(self.compositeDataWrapper))
        self.file_menu.addAction('Importuj punkty', lambda:
            DataActions.importPoints(self.compositeDataWrapper))
        self.file_menu.addAction('Wczytaj projekt', lambda:
            self._replaceCompositeDataWrapper(
                DataActions.loadCompositeData()))
        self.file_menu.addAction('Zapisz projekt', lambda:
            DataActions.saveCompositeData(self.compositeDataWrapper))
        self.file_menu.addAction('Zamknij', self.fileQuit)
        self.menuBar().addMenu(self.file_menu)

        self.help_menu = QW.QMenu('Pomoc', self)
        self.help_menu.addAction('O programie', self.about)
        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.help_menu)

    def _refreshPlot(self):
        self.mplPlotWidget.updateCompositeData(self.compositeDataWrapper)

    def _replaceCompositeDataWrapper(self, compositeDataWrapper):
        self.compositeDataWrapper.replaceWithCompositeDataWrapper(compositeDataWrapper)

    def fileQuit(self):
        self.close()

    def closeEvent(self, ce):
        self.fileQuit()

    def about(self):
        QW.QMessageBox.about(self, "O programie",
                                    """QtSigman
Program zapewniający GUI do bezpośredniej obsługi biblioteki sigman do 
analizy danych.
Wersja pre-beta
                                                                Krzysztof Cybulski 2017""")

        


def initialize():
    """Uruchamia aplikację."""
    app = QW.QApplication([])
    qtSigmanWindow = QtSigmanWindow()
    qtSigmanWindow.show()
    app.exec()

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
import os
import sigman as sm
import array
from matplotlib import colors

from functools import partial
from QtSigman.DefaultColors import defaultColors
from QtSigman import MplWidgets, DataActions, ListWidgets
from QtSigman.MplWidgets import Axis

class VisualDataObject():
    def __init__(self, data, color, axis):
        self.color = color
        self.axis = axis
        self.mplObject = None

    def plot(self, axis, beginTime, endTime,
             keepMplObject=True, color=None):
        """Metoda rysująca dane na wykresie matplotlib. Jeśli już są
        narysowane to tylko je zmienia / odświeża.
        
        Argumenty:
        keepMplObject - czy zachować narysowane figury geometryczne do
                        późniejszego odświeżenia. Powinno być True
                        jeśli rysujemy na wykresie głównego okna, oraz
                        False w innych wypadkach.
        color - kolor wykresu. Jeśli None, wykorzystany zostanie
                self.color
        """
    
    def removeMplObject(self):
        if self.mplObject is not None:
            self.mplObject.remove()
            self.mplObject = None

    def setMplColor(self, color):
        if self.mplObject is not None:
            self.mplObject.set_color(color)

class VisualDataWave(VisualDataObject, sm.Wave):
    def __init__(self, data, color, axis):
        VisualDataObject.__init__(self, data, color, axis)
        sm.Wave.__init__(self,
                              data.data,
                              data.complete_length,
                              wave_type=data.type,
                              offset=data.offset)

    def plot(self, axis, beginTime, endTime,
             keepMplObject=True, color=None):
        if color is None:
            color = self.color
        tempBeginTime = max(beginTime, self.offset)
        tempEndTime = min(endTime, self.offset 
                          + self.complete_length)
        x, y = self.generate_coordinate_tables(
            begin_time=tempBeginTime,
            end_time=tempEndTime,
            begin_x=tempBeginTime)
        if keepMplObject:
            if self.mplObject is None:
                self.mplObject, = axis.plot(x, y, 
                                            color=color, label=self.type)
            else:
                self.mplObject.set_xdata(x)
                self.mplObject.set_ydata(y)
        else:
            axis.plot(x, y, color=color, label=self.type)

class VisualDataPoints(VisualDataObject, sm.Points):
    def __init__(self, data, color, axis):
        VisualDataObject.__init__(self, data, color, axis)
        sm.Points.__init__(self,
                                data.data_x,
                                data.data_y,
                                point_type=data.type)

    def plot(self, axis, beginTime, endTime,
             keepMplObject=True, color=None):
        if color is None:
            color = self.color
        x, y = self.data_slice(beginTime, endTime)
        if keepMplObject:
            if self.mplObject is None:
                self.mplObject, = axis.plot(x, y, color=color, marker='o',
                                            linestyle='None', picker=5,
                                            label=self.type)
            else:
                self.mplObject.set_xdata(x)
                self.mplObject.set_ydata(y)
        else:
            axis.plot(x, y, color=color, marker='o', linestyle='None',
                      picker=5, label=self.type)

class VisualParameter(VisualDataObject, sm.Parameter):
    def __init__(self, data, color, axis):
        VisualDataObject.__init__(self, data, color, axis)
        sm.Parameter.__init__(self,
                              data.type)
        self.begin_times = data.begin_times
        self.end_times = data.end_times
        self.values = data.values
        self.mplObject = []

    def plot(self, axis, beginTime, endTime,
             keepMplObject=True, color=None):
        if color is None:
            color = self.color
        waveTuples = self.generate_parameter_wave_tuples(
            begin_time=beginTime, end_time=endTime)
        if keepMplObject:
            if self.mplObject is None: #TODO: Ten if powinien być niepotrzebny
                self.mplObject = []
            if len(self.mplObject) != len(waveTuples):
                self.removeMplObject()
            if self.mplObject == []:
                for tup in waveTuples:
                    mplLine, = axis.plot(tup[0], tup[1], 
                                         color=color, label=self.type)
                    self.mplObject.append(mplLine)
            else:
                for mplLine, tup in zip(self.mplObject, waveTuples):
                    mplLine.set_xdata(tup[0])
                    mplLine.set_ydata(tup[1])
        else:
            for tup in waveTuples:
                axis.plot(tup[0], tup[1], color=color, label=self.type)


    def removeMplObject(self):
        for mplLine in self.mplObject:
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
    waveNumberChanged = QC.pyqtSignal()
    pointNumberChanged = QC.pyqtSignal()
    parameterNumberChanged = QC.pyqtSignal()
    # informujące o zmianach wewnątrz obiektów danych, np do rysowania
    waveChanged = QC.pyqtSignal()
    pointChanged = QC.pyqtSignal()
    parameterChanged = QC.pyqtSignal()

    def __init__(self, **kwargs):
        # Inicjalizujemy parents
        sm.Composite_data.__init__(self, **kwargs)
        QC.QObject.__init__(self)

        for key, item in self.waves.items():
            self.waves[key] = VisualDataWave(
                item, 
                colors.to_hex(defaultColors[key]),
                Axis.Hidden)
        for key, item in self.points.items():
            self.points[key] = VisualDataPoints(
                item, 
                colors.to_hex(defaultColors[key]),
                Axis.Hidden)
        for key, item in self.parameters.items():
            self.parameters[key] = VisualParameter(
                item, 
                colors.to_hex(defaultColors[key]),
                Axis.Hidden)
        self.dataDicts = [self.waves, self.points, self.parameters]

    def replaceWithCompositeDataWrapper(self, compositeDataWrapper):
        newDataDicts = [
            compositeDataWrapper.waves,
            compositeDataWrapper.points,
            compositeDataWrapper.parameters]
        for dataDict, newDataDict in zip(self.dataDicts, newDataDicts):
            for key, item in dataDict.items():
                item.removeMplObject()
            # Oczyszczanie zapisanych danych graficznych
            for key, item in newDataDict.items():
                item.mplObject = None
        self.waves = compositeDataWrapper.waves
        self.points = compositeDataWrapper.points
        self.parameters = compositeDataWrapper.parameters
        self.dataDicts = [
            self.waves,
            self.points,
            self.parameters]

        self.waveNumberChanged.emit()
        self.pointNumberChanged.emit()
        self.parameterNumberChanged.emit()
        self.waveChanged.emit()
        self.pointChanged.emit()
        self.parameterChanged.emit()

    @classmethod
    def fromSigmanCompositeData(cls, compositeData):
        return cls(
            waves = compositeData.waves,
            points = compositeData.points,
            parameters = compositeData.parameters)

    def add_wave(self, wave, dict_type, color=None, replace=False,
                      axis=Axis.Hidden):
        super(CompositeDataWrapper, self).add_wave(wave,
                                                        dict_type,
                                                        replace=replace)
        if color is None:
            color = defaultColors.getColor(dict_type)
        self.waves[dict_type] = VisualDataWave(
            self.waves[dict_type],
            color,
            axis)
        self.waveNumberChanged.emit()

    def editWaveSettings(self, dictType, newDictType, 
                                color, axis, offset):
        """Changes settings of a selected wave."""
        wave = self.waves[dictType]
        if wave.color != color:
            wave.setMplColor(color)
        if wave.axis != axis:
            wave.axis = axis
            wave.removeMplObject()
        wave.offset = offset 
        if dictType != newDictType:
            wave.type = newDictType
            wave.mplObject.set_label(wave.type)
            self.waves[newDictType] = wave
            self.waves.pop(dictType)
            self.waveNumberChanged.emit()
        self.waveChanged.emit()

    def delete_wave(self, dict_type):
        self.waves[dict_type].removeMplObject()
        super(CompositeDataWrapper, self).delete_wave(dict_type)
        self.waveNumberChanged.emit()

    def add_points(self, points, dict_type, color=None, join=False,
                        axis=Axis.Hidden):
        super(CompositeDataWrapper, self).add_points(points,
                                                          dict_type,
                                                          join=join)
        if color is None:
            color = defaultColors.getColor(dict_type)
        self.points[dict_type] = VisualDataPoints(
            self.points[dict_type],
            color,
            axis)
        self.pointNumberChanged.emit()

    def editPointsSettings(self, dictType, newDictType, 
                                color, axis, offset):
        """Changes settings of a selected set of points."""
        points = self.points[dictType]
        if points.color != color:
            points.setMplColor(color)
        if points.axis != axis:
            points.axis = axis
            points.removeMplObject()
        points.move_in_time(offset)
        if dictType != newDictType:
            points.type = newDictType
            points.mplObject.set_label(points.type)
            self.points[newDictType] = points
            self.points.pop(dictType)
            self.pointNumberChanged.emit()
        self.pointChanged.emit()

    def delete_points(self, dict_type):
        self.points[dict_type].removeMplObject()
        super(CompositeDataWrapper, self).delete_points(dict_type)
        self.pointNumberChanged.emit()

    def add_parameter(self, parameter, dict_type, color=None, replace=False,
                      axis=Axis.Hidden):
        super(CompositeDataWrapper, self).add_parameter(parameter,
                                                        dict_type,
                                                        replace=replace)
        if color is None:
            color = defaultColors.getColor(dict_type)
        self.parameters[dict_type] = VisualParameter(
            self.parameters[dict_type],
            color,
            axis)
        self.parameterNumberChanged.emit()

    def editParameterSettings(self, dictType, newDictType, 
                                color, axis):
        """Changes settings of a selected parameter."""
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
        self.mplPlotWidget = MplWidgets.PlotWidget(self.compositeDataWrapper)
        mainLayout.addWidget(self.mplPlotWidget)
        # Podłączamy wszystkie możliwe sygnały qt wpływające na wykres do
        # obiektu wykresu
        self.compositeDataWrapper.waveNumberChanged.connect(self._refreshPlot)
        self.compositeDataWrapper.pointNumberChanged.connect(self._refreshPlot)
        self.compositeDataWrapper.parameterNumberChanged.connect(self._refreshPlot)
        self.compositeDataWrapper.waveChanged.connect(self._refreshPlot)
        self.compositeDataWrapper.pointChanged.connect(self._refreshPlot)
        self.compositeDataWrapper.parameterChanged.connect(self._refreshPlot)
        self.compositeDataWrapper.pointNumberChanged.connect(lambda:
            self.mplPlotWidget.plotToolbar.updatePointComboBox(
                self.compositeDataWrapper))
        self.compositeDataWrapper.pointChanged.connect(lambda:
            self.mplPlotWidget.plotToolbar.updatePointComboBox(
                self.compositeDataWrapper))

        # Po prawej
        rightVBoxLayout = QW.QVBoxLayout()
        waveListLabel = QW.QLabel()
        waveListLabel.setText("Przebiegi")
        waveList = ListWidgets.DataListWidget()
#        waveList.itemClicked.connect(lambda listItemWidget:
#            DataActions.inputWaveSettings(self.compositeDataWrapper, 
#                waveList.itemWidget(listItemWidget).typeLabel.text()))
        self.compositeDataWrapper.waveNumberChanged.connect(
            lambda:
            waveList.updateData(self.compositeDataWrapper, 'wave'))
#        self.compositeDataReloaded.connect(
#            lambda:
#            waveList.updateData(self.compositeDataWrapper, 'wave'))
        waveList.setSizePolicy(QW.QSizePolicy.Fixed,
                               QW.QSizePolicy.Expanding)
        rightVBoxLayout.addWidget(waveListLabel)
        rightVBoxLayout.addWidget(waveList)
        pointListLabel = QW.QLabel()
        pointListLabel.setText("Punkty") 
        pointList = ListWidgets.DataListWidget()
#        pointList.itemClicked.connect(lambda listItemWidget:
#            DataActions.inputPointSettings(self.compositeDataWrapper, 
#                pointList.itemWidget(listItemWidget).typeLabel.text()))
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
            DataActions.importWave(self.compositeDataWrapper))
        #self.file_menu.addAction('Eksportuj przebieg // TODO', lambda:
        #    QW.QMessageBox.information(self, "Informacja",
        #                              "Nie zaimplementowano"))
        self.file_menu.addAction('Wczytaj dane Modelflow', lambda:
            DataActions.importModelflow(self.compositeDataWrapper))
        self.file_menu.addAction('Importuj punkty', lambda:
            DataActions.importPoints(self.compositeDataWrapper))
        #self.file_menu.addAction('Eksportuj punkty // TODO', lambda:
        #    QW.QMessageBox.information(self, "Informacja",
        #                              "Nie zaimplementowano"))
        #self.file_menu.addAction('Eksportuj parametr // TODO', lambda:
        #    QW.QMessageBox.information(self, "Informacja",
        #                              "Nie zaimplementowano"))
        self.file_menu.addAction('Wczytaj projekt', lambda:
            self._replaceCompositeDataWrapper(
                DataActions.loadCompositeData()))
        self.file_menu.addAction('Zapisz projekt', lambda:
            DataActions.saveCompositeData(self.compositeDataWrapper))
        self.file_menu.addAction('Zamknij', self.fileQuit)
        self.menuBar().addMenu(self.file_menu)

        self.procedure_menu = QW.QMenu('Procedury', self)
        self.procedure_menu.addAction('Modyfikuj przebieg', lambda:
            DataActions.modifyWave(self.compositeDataWrapper))
        self.procedure_menu.addAction('Znajdź punkty', lambda:
            DataActions.findPoints(self.compositeDataWrapper))
        #self.procedure_menu.addAction('Oblicz parametr // TODO', lambda:
        #    QW.QMessageBox.information(self, "Informacja",
        #                              "Nie zaimplementowano"))
        self.menuBar().addMenu(self.procedure_menu)


        self.analize_menu = QW.QMenu('Makra/narzędzia do analizy', self)

        path = "macros"    
        analize_List = os.listdir(path);
        for i in range (0,len(analize_List)):
            self.analize_menu.addAction(analize_List[i],partial(DataActions.executeMacro,self.compositeDataWrapper,analize_List[i]))
             
        self.menuBar().addMenu(self.analize_menu)

        self.help_menu = QW.QMenu('Pomoc', self)
        self.help_menu.addAction('O programie', self.about)
        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.help_menu)

    def _refreshPlot(self):
        self.mplPlotWidget.updateCompositeData(self.compositeDataWrapper)
    
    

    def _replaceCompositeDataWrapper(self, compositeDataWrapper):
        if compositeDataWrapper is not None:
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

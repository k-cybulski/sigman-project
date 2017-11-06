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

    def plot(self, axis, beginTime, endTime):
        pass

class VisualDataLine(VisualDataObject, sm.Data_line):
    def __init__(self, data, color, axis):
        VisualDataObject.__init__(self, data, color, axis)
        sm.Data_line.__init__(self,
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
        axis.plot(x, y, color = self.color)

class VisualDataPoints(VisualDataObject, sm.Data_points):
    def __init__(self, data, color, axis):
        VisualDataObject.__init__(self, data, color, axis)
        sm.Data_points.__init__(self,
                                data.data_x,
                                data.data_y,
                                point_type = data.type)

    def plot(self, axis, beginTime, endTime):
        x, y = self.data_slice(beginTime, endTime)
        axis.plot(x, y, color = self.color, marker = 'o', linestyle = 'None')

class VisualParameter(VisualDataObject, sm.Parameter):
    def __init__(self, data, color, axis):
        VisualDataObject.__init__(self, data, color, axis)
        sm.Data_points.__init__(self,
                                data.type)
        self.begin_times = data.begin_times
        self.end_times = data.end_times
        self.values = data.values

    def plot(self, axis, beginTime, endTime):
        lineTuples = self.generate_parameter_line_tuples(
            begin_time = beginTime, end_time = endTime)
        for tup in lineTuples:
            axis.plot(tup[0], tup[1], color = self.color)

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

        for key, item in self.data_lines.items():
            self.data_lines[key] = VisualDataLine(
                item, 
                colors.to_hex(defaultColors[key]),
                Axis.Hidden)
        for key, item in self.data_points.items():
            self.data_lines[key] = VisualDataPoints(
                item, 
                colors.to_hex(defaultColors[key]),
                Axis.Hidden)
        for key, item in self.parameters.items():
            self.parameters[key] = VisualParameter(
                item, 
                colors.to_hex(defaultColors[key]),
                Axis.Hidden)
        self.dataDicts = [self.data_lines, self.data_points, self.parameters]

    def add_data_line(self, data_line, dict_type, color, replace=False,
                      axis=Axis.Hidden):
        super(CompositeDataWrapper, self).add_data_line(data_line,
                                                        dict_type,
                                                        replace = replace)
        self.data_lines[dict_type] = VisualDataLine(
            self.data_lines[dict_type],
            color,
            axis)
        self.lineNumberChanged.emit()

    def editDataLineSettings(self, dictType, newDictType, 
                                color, axis, offset):
        self.data_lines[dictType].color = color
        self.data_lines[dictType].axis = axis
        self.data_lines[dictType].offset = offset 
        if dictType != newDictType:
            self.data_lines[newDictType] = self.data_lines[dictType]
            self.data_lines.pop(dictType)
            self.lineNumberChanged.emit()
        self.lineChanged.emit()

    def delete_data_line(self, dict_type):
        super(CompositeDataWrapper, self).delete_data_line(dict_type)
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
        self.data_points[dictType].color = color
        self.data_points[dictType].axis = axis
        self.data_points[dictType].move_in_time(offset)
        if dictType != newDictType:
            self.data_points[newDictType] = self.data_points[dictType]
            self.data_points.pop(dictType)
            self.pointNumberChanged.emit()
        self.pointChanged.emit()

    def delete_data_points(self, dict_type):
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

    def delete_parameter(self, dict_type):
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
        self.compositeDataWrapper.lineNumberChanged.connect(
            lambda:
            self.mplPlotWidget.updateCompositeData(self.compositeDataWrapper))
        self.compositeDataWrapper.pointNumberChanged.connect(
            lambda:
            self.mplPlotWidget.updateCompositeData(self.compositeDataWrapper))
        self.compositeDataWrapper.parameterNumberChanged.connect(
            lambda:
            self.mplPlotWidget.updateCompositeData(self.compositeDataWrapper))
        self.compositeDataWrapper.lineChanged.connect(
            lambda:
            self.mplPlotWidget.updateCompositeData(self.compositeDataWrapper))
        self.compositeDataWrapper.pointChanged.connect(
            lambda:
            self.mplPlotWidget.updateCompositeData(self.compositeDataWrapper))
        self.compositeDataWrapper.parameterChanged.connect(
            lambda:
            self.mplPlotWidget.updateCompositeData(self.compositeDataWrapper))

        # Po prawej
        rightVBoxLayout = QW.QVBoxLayout()
        lineListLabel = QW.QLabel()
        lineListLabel.setText("Przebiegi")
        lineList = ListWidgets.DataListWidget()
        lineList.itemClicked.connect(lambda x:
            DataActions.editLineSettings(self.compositeDataWrapper, 
                                 lineList.itemWidget(x).typeLabel.text()))
        self.compositeDataWrapper.lineNumberChanged.connect(
            lambda:
            lineList.updateData(self.compositeDataWrapper, 'line'))
        lineList.setSizePolicy(QW.QSizePolicy.Fixed,
                               QW.QSizePolicy.Expanding)
        rightVBoxLayout.addWidget(lineListLabel)
        rightVBoxLayout.addWidget(lineList)
        pointListLabel = QW.QLabel()
        pointListLabel.setText("Punkty") 
        pointList = ListWidgets.DataListWidget()
        pointList.itemClicked.connect(lambda x:
            DataActions.editPointSettings(self.compositeDataWrapper, 
                                 pointList.itemWidget(x).typeLabel.text()))
        self.compositeDataWrapper.pointNumberChanged.connect(
            lambda:
            pointList.updateData(self.compositeDataWrapper, 'point'))
        pointList.setSizePolicy(QW.QSizePolicy.Fixed,
                                QW.QSizePolicy.Expanding) 
        rightVBoxLayout.addWidget(pointListLabel)
        rightVBoxLayout.addWidget(pointList)
        parameterListLabel = QW.QLabel() 
        parameterListLabel.setText("Obliczone parametry")
        self.compositeDataWrapper.parameterNumberChanged.connect(
            lambda:
            parameterList.updateData(self.compositeDataWrapper, 'parameter'))
        parameterList = ListWidgets.DataListWidget()
        parameterList.setSizePolicy(QW.QSizePolicy.Fixed,
                                    QW.QSizePolicy.Expanding) 
        rightVBoxLayout.addWidget(parameterListLabel)
        rightVBoxLayout.addWidget(parameterList)
        mainLayout.addLayout(rightVBoxLayout)

        # Ustawienie paska menu
        self.file_menu = QW.QMenu('&Plik', self)
        self.file_menu.addAction('Importuj przebieg', lambda:
                                 DataActions.importLine(self.compositeDataWrapper))
        self.file_menu.addAction('Importuj punkty', lambda:
                                 DataActions.importPoints(self.compositeDataWrapper))
        self.file_menu.addAction('&Quit', self.fileQuit)
        self.menuBar().addMenu(self.file_menu)

        self.help_menu = QW.QMenu('&Help', self)
        self.help_menu.addAction('&About', self.about)
        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.help_menu)

    def fileQuit(self):
        self.close()

    def closeEvent(self, ce):
        self.fileQuit()

    def about(self):
        QW.QMessageBox.about(self, "About",
                                    """QtSigman
Program zapewniający GUI do bezpośredniej obsługi biblioteki sigman do 
analizy danych.""")

        


def initialize():
    """Uruchamia aplikację."""
    app = QW.QApplication([])
    qtSigmanWindow = QtSigmanWindow()
    qtSigmanWindow.show()
    app.exec()

"""
Moduł zajmujący się widgetem wizualizującym wykres.
"""
from enum import Enum

import numpy as np
from PyQt5 import QtWidgets as QW
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT
import matplotlib.patches as mPatches
import sigman as sm

class Axis(Enum):
    Left = 1
    Right = 2
    Hidden = 3

class EditMode(Enum):
    Inactive = 1
    Static = 2 # Addition or removal of points
    Dynamic = 3 # Movement of existing points

class PlotCanvas(FigureCanvas):
    """Widget przedstawiający sam wykres."""
    
    def __init__(self, parent=None):
        figure = matplotlib.figure.Figure()
        figure.set_tight_layout(True)
        super(PlotCanvas, self).__init__(figure)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self,
                                   QW.QSizePolicy.Expanding,
                                   QW.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        self.axisLeft = self.figure.add_subplot(1,1,1)
        self.axisRight = self.axisLeft.twinx()

    def plotCompositeDataWrapper(self, compositeDataWrapper, beginTime, endTime):
        """Rysuje lub tylko odświeża już narysowane dane z 
        CompositeDataWrapper.
        """

        for dataDict in compositeDataWrapper.dataDicts:
            for key, data in dataDict.items():
                axis = data.axis
                if axis is Axis.Hidden:
                    continue
                elif axis is Axis.Left:
                    plot_axis = self.axisLeft
                elif axis is Axis.Right:
                    plot_axis = self.axisRight
                data.plot(plot_axis, beginTime, endTime)
            for plot_axis in [self.axisLeft, self.axisRight]:
                plot_axis.relim()
                plot_axis.autoscale(axis='y')
        self.draw()

    def plotDataWaveComparison(self, waveDict, beginTime, endTime):
        """Rysuje VisualDataWave z dict oraz podpisuje je zgodnie z ich
        kluczem w dict.
        """
        # Chcemy listę defaultowych kolorów matplotlib
        prop_cycle = matplotlib.rcParams['axes.prop_cycle']
        colors = prop_cycle.by_key()['color']
        handles = []
        for key, item in waveDict.items():
            color = colors.pop(0)
            colors.append(color)
            handles.append(
                mPatches.Patch(color = color, label = key))
            item.plot(self.axisLeft, beginTime, endTime, 
                      keepMplObject = False, color = color)
        self.axisLeft.legend(handles = handles)

class PlotToolbar(NavigationToolbar2QT):
    toolitems = [t for t in NavigationToolbar2QT.toolitems if
                 t[0] in ('Pan', 'Zoom', 'Save')] # 'Home' do skorygowania
    
    def __init__(self, canvas, parent):
        NavigationToolbar2QT.__init__(self, canvas, parent)
        
        self.editCheckBox = QW.QCheckBox("Tryb edycji")
        self.addWidget(self.editCheckBox)

        editTypes = ["Dodaj LPM/Usuń PPM",
                    "Przesuń"]
        self.editTypeComboBox = QW.QComboBox()
        self.editTypeComboBox.addItems(editTypes)
        self.addWidget(self.editTypeComboBox)

        self.selectedLabel = QW.QLabel("Wybrane punkty:")
        self.addWidget(self.selectedLabel)
        
        self.selectedPointsComboBox = QW.QComboBox()
        self.addWidget(self.selectedPointsComboBox)

    def updatePointComboBox(self, compositeDataWrapper):
        selectedPoints = self.getSelectedPointType()
        self.selectedPointsComboBox.clear()
        items = []
        for key, item in compositeDataWrapper.points.items():
            items.append(key)
        self.selectedPointsComboBox.addItems(items)
        found = self.selectedPointsComboBox.findText(selectedPoints)
        if found >= 0:
            self.selectedPointsComboBox.setCurrentIndex(found)
    
    def getEditMode(self):
        if self.editCheckBox.isChecked():
            if self.editTypeComboBox.currentIndex() == 0:
                return EditMode.Static
            else:
                return EditMode.Dynamic
        else:
            return EditMode.Inactive

    def getSelectedPointType(self):
        return self.selectedPointsComboBox.currentText()


class PlotWidget(QW.QWidget):
    """Widget przedstawiający wykres wraz z paskiem nawigacji."""

    def __init__(self, compositeDataWrapper, parent=None):     
        super(PlotWidget, self).__init__(parent)

        self.plotCanvas = PlotCanvas()
        self.plotToolbar = PlotToolbar(self.plotCanvas, self)

        self.plotCanvas.mpl_connect('button_press_event', self.handlePress)
        self.plotCanvas.mpl_connect('pick_event', self.handlePick)
        self.plotCanvas.mpl_connect('motion_notify_event', self.handleMotion)
        self.plotCanvas.mpl_connect('button_release_event', self.handleRelease)
        self.plotCanvas.mpl_connect('axes_leave_event', self.handleLeave)

        layout = QW.QVBoxLayout(self)
        layout.addWidget(self.plotCanvas)
        layout.addWidget(self.plotToolbar)

        self.compositeDataWrapper = compositeDataWrapper

        self.dragging = False
        self.lastX = 0
        self.lastY = 0

    def _getEventXY(self, event):
        """This method returns x and y coordinates of an event on the 
        axis of currently selected points to edit. This is a workaround 
        for the way matplotlib handles events when more than 1 axis is 
        present on the same canvas (with twinx).
        """
        # matplotlib only returns xdata and ydata for the topmost axis
        # https://stackoverflow.com/questions/16672530/cursor-tracking-using-matplotlib-and-twinx/16672970#16672970
        selectedPoints = self.plotToolbar.getSelectedPointType()
        visualPoints = self.compositeDataWrapper.points[selectedPoints]
        ax = visualPoints.mplObject.axes
        if event.inaxes != ax:
            inv = ax.transData.inverted()
            x, y = inv.transform(
                np.array((event.x, event.y)).reshape(1, 2)).ravel()
        else:
            x, y = event.xdata, event.ydata
        return x, y

    def handlePress(self, event):
        mode = self.plotToolbar.getEditMode()
        selectedPoints = self.plotToolbar.getSelectedPointType()
        if (selectedPoints
                not in self.compositeDataWrapper.points):
            return
        if mode is EditMode.Static and event.button == 1:
            x, y = self._getEventXY(event)
            self.compositeDataWrapper.points[
                selectedPoints].add_point(x, y)
            self.compositeDataWrapper.pointNumberChanged.emit()
        else:
            # if a pick had been made on an object not on the topmost axis
            # it will not trigger; this is a workaround
            self.compositeDataWrapper.points[
                selectedPoints].mplObject.pick(event)

    def handlePick(self, event):
        mode = self.plotToolbar.getEditMode()
        selectedPoints = self.plotToolbar.getSelectedPointType()
        if (selectedPoints 
                not in self.compositeDataWrapper.points):
            return
        if mode is EditMode.Static and event.mouseevent.button == 3:
            points = event.artist
            if(points.get_label() == selectedPoints):
                xData = points.get_xdata()
                yData = points.get_ydata()
                ind = [event.ind[0]]
                self.compositeDataWrapper.points[
                    selectedPoints].delete_point(
                        xData[ind], y=yData[ind])
                self.compositeDataWrapper.pointNumberChanged.emit()
        if mode is EditMode.Dynamic and event.mouseevent.button == 1:
            points = event.artist
            if(points.get_label() == selectedPoints):
                xData = points.get_xdata()
                yData = points.get_ydata()
                ind = [event.ind[0]]
                self.lastX = xData[ind]
                self.lastY = yData[ind]
                self.dragging = True
                self.compositeDataWrapper.pointChanged.emit()

    def handleMotion(self, event):
        mode = self.plotToolbar.getEditMode()
        selectedPoints = self.plotToolbar.getSelectedPointType()
        if(mode is EditMode.Dynamic and event.button == 1 and
                self.dragging):
            x, y = self._getEventXY(event)
            points = self.compositeDataWrapper.points[
                selectedPoints]
            points.move_point(
                self.lastX, self.lastY,
                x, y)
            self.lastX = np.array([x])
            self.lastY = np.array([y])
            self.compositeDataWrapper.pointChanged.emit()

    def handleRelease(self, event):
        mode = self.plotToolbar.getEditMode()
        selectedPoints = self.plotToolbar.getSelectedPointType()
        if(mode is EditMode.Dynamic and event.button == 1 and
                self.dragging):
            x, y = self._getEventXY(event)
            points = self.compositeDataWrapper.points[
                selectedPoints]
            points.move_point(
                self.lastX, self.lastY,
                x, y)
            self.dragging = False
        
    def handleLeave(self, event):
        if self.dragging:
            self.dragging = False

    def updateCompositeData(self, compositeDataWrapper):
        #TODO: Wykres powinien być tylko odświeżony nie resetując pozycji
        # obserwatora
        self.compositeDataWrapper = compositeDataWrapper
        beginTime, endTime = compositeDataWrapper.calculate_complete_time_span()
        self.plotCanvas.plotCompositeDataWrapper(compositeDataWrapper,
                                                 beginTime, endTime)



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
from QtSigman.VisualObjects import VCollection, VWave, VPoints, VParameter

class EditMode(Enum):
    Inactive = 1
    Static = 2 # Addition or removal of points
    Dynamic = 3 # Movement of existing points

class PlotCanvas(FigureCanvas):
    """Widget containing the plot itself."""
    
    def __init__(self, parent=None):
        figure = matplotlib.figure.Figure()
        figure.set_tight_layout(True)
        super(PlotCanvas, self).__init__(figure)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self,
                                   QW.QSizePolicy.Expanding,
                                   QW.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        self.axes = []
        self.axes.append(self.figure.add_subplot(1,1,1))
        self.axes.append(self.axes[0].twinx())

    def plotVCollection(self, vCollection, beginTime=None, endTime=None):
        """Plots all VObjects contained in a VCollection."""
        for dict_ in [vCollection.waves,
                        vCollection.points,
                        vCollection.parameters]:
            for vObject in dict_.values():
                self.plotVObject(vObject)
        self.rescaleAxes()
        self.draw()

    def plotVObject(self, vObject, beginTime=None, endTime=None):
        """Assigns an axis to a VObject and plots it. If it is hidden,
        it merely redraws the plot."""
        axis = vObject.axis
        if axis >= 0:
            mplAxis = self.axes[axis]
            vObject.plot(mplAxis)
        self.rescaleAxes()
        self.draw()

    def rescaleAxes(self):
        """Rescales axes so the minimum and maximum values of objects
        in each are at the same visual height.
        """
        for mplAxis in self.axes:
            mplAxis.relim()
            mplAxis.autoscale(axis='y')

class PlotToolbar(NavigationToolbar2QT):
    toolitems = [t for t in NavigationToolbar2QT.toolitems if
                 t[0] in ('Pan', 'Zoom', 'Save')] # 'Home' do skorygowania
    
    def __init__(self, canvas, parent):
        NavigationToolbar2QT.__init__(self, canvas, parent)

        self.parent = parent # we assume it has a vCollection

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

    def updatePointComboBox(self):
        """Updates the combo box with points to edit and fills it up
        with VPoints that are on a visible axis.
        """
        selectedPoints = self.getSelectedPointType()
        self.selectedPointsComboBox.clear()
        keys = []
        for key, item in self.parent.vCollection.points.items():
            if item.axis >= 0:
                keys.append(key)
        self.selectedPointsComboBox.addItems(keys)
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

    def __init__(self, vCollection, parent=None):     
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

        self.vCollection = vCollection
        for dict_ in [vCollection.waves,
                      vCollection.points,
                      vCollection.parameters]:
            for key, vObject in dict_.items():
                self.plotCanvas.plotVObject(vObject)
                self._added(vObject, key)
        self.vCollection.waveAdded.connect(self._waveAdded)
        self.vCollection.pointsAdded.connect(self._pointsAdded)
        self.vCollection.parameterAdded.connect(self._parameterAdded)

        self.vCollection.pointsAdded.connect(self.plotToolbar.updatePointComboBox)
        self.vCollection.pointsKeyChanged.connect(self.plotToolbar.updatePointComboBox)
        self.vCollection.pointsDeleted.connect(self.plotToolbar.updatePointComboBox)

        self.dragging = False
        self.lastX = 0
        self.lastY = 0

    @classmethod
    def fromCompositeDataWrapper(cls, compositeDataWrapper, parent=None):
        """Initializes a PlotWidget with a VCollection corresponding
        to a CompositeDataWrapper.
        """
        vCollection = VCollection.fromCompositeDataWrapper(
            compositeDataWrapper)
        return cls(vCollection, parent=parent)
    
    @classmethod
    def fromVCollection(cls, vCollection, parent=None, allHidden=False):
        """Initializes a PlotWidget with a VCollection corresponding
        to the given one.

        Arguments:
            allHidden   - if True all VObjects in the VCollection will
                          be in the -1 axis.
        """
        outVCollection = VCollection.fromVCollection(vCollection, allHidden)
        return cls(outVCollection, parent=parent)

    def _waveAdded(self, vObject, key):
        self.plotCanvas.plotVObject(vObject)
        vObject.axisChanged.connect(
            lambda: self.plotCanvas.plotVObject(vObject))

    def _pointsAdded(self, vObject, key):
        self.plotCanvas.plotVObject(vObject)
        vObject.axisChanged.connect(
            lambda: self.plotCanvas.plotVObject(vObject))
        vObject.axisChanged.connect(self.plotToolbar.updatePointComboBox)

    def _parameterAdded(self, vObject, key):
        self.plotCanvas.plotVObject(vObject)
        vObject.axisChanged.connect(
            lambda: self.plotCanvas.plotVObject(vObject))
    
    def _added(self, vObject, key):
        if isinstance(vObject, VWave):
            self._waveAdded(vObject, key)
        elif isinstance(vObject, VPoints):
            self._pointsAdded(vObject, key)
        elif isinstance(vObject, VParameter):
            self._parameterAdded(vObject, key)

    def _getEventXY(self, event):
        """This method returns x and y coordinates of an event on the 
        axis of currently selected points to edit. This is a workaround 
        for the way matplotlib handles events when more than 1 axis is 
        present on the same canvas (with twinx).
        """
        # matplotlib only returns xdata and ydata for the topmost axis
        # https://stackoverflow.com/questions/16672530/cursor-tracking-using-matplotlib-and-twinx/16672970#16672970
        selectedPoints = self.plotToolbar.getSelectedPointType()
        visualPoints = self.vCollection.points[selectedPoints]
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
                not in self.vCollection.points):
            return
        if mode is EditMode.Static and event.button == 1:
            x, y = self._getEventXY(event)
            self.vCollection.points[selectedPoints].data.add_point(x, y)
        else:
            # if a pick had been made on an object not on the topmost axis
            # it will not trigger; this is a workaround
            self.vCollection.points[selectedPoints].mplObject.pick(event)

    def handlePick(self, event):
        mode = self.plotToolbar.getEditMode()
        selectedPoints = self.plotToolbar.getSelectedPointType()
        if (selectedPoints 
                not in self.vCollection.points):
            return
        if mode is EditMode.Static and event.mouseevent.button == 3:
            points = event.artist
            if(points.get_label() == selectedPoints):
                xData = points.get_xdata()
                yData = points.get_ydata()
                ind = [event.ind[0]]
                self.vCollection.points[selectedPoints].data.delete_point(
                    xData[ind], y=yData[ind])
        if mode is EditMode.Dynamic and event.mouseevent.button == 1:
            points = event.artist
            if(points.get_label() == selectedPoints):
                xData = points.get_xdata()
                yData = points.get_ydata()
                ind = [event.ind[0]]
                self.lastX = xData[ind]
                self.lastY = yData[ind]
                self.dragging = True

    def handleMotion(self, event):
        mode = self.plotToolbar.getEditMode()
        selectedPoints = self.plotToolbar.getSelectedPointType()
        if(mode is EditMode.Dynamic and event.button == 1 and
                self.dragging):
            x, y = self._getEventXY(event)
            points = self.vCollection.points[selectedPoints].data
            points.move_point(
                self.lastX, self.lastY,
                x, y)
            self.lastX = np.array([x])
            self.lastY = np.array([y])

    def handleRelease(self, event):
        mode = self.plotToolbar.getEditMode()
        selectedPoints = self.plotToolbar.getSelectedPointType()
        if(mode is EditMode.Dynamic and event.button == 1 and
                self.dragging):
            x, y = self._getEventXY(event)
            points = self.vCollection.points[selectedPoints].data
            points.move_point(
                self.lastX, self.lastY,
                x, y)
            self.dragging = False
        
    def handleLeave(self, event):
        if self.dragging:
            self.dragging = False

    def replaceVCollection(self, vCollection):
        self.vCollection.remove()
        self.vCollection = vCollection
        for dict_ in [vCollection.waves,
                      vCollection.points,
                      vCollection.parameters]:
            for key, vObject in dict_.items():
                self.plotCanvas.plotVObject(vObject)
                self._added(vObject, key)
        self.plotCanvas.plotVCollection(vCollection)

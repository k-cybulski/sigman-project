from PyQt5 import QtWidgets as QW
from PyQt5 import QtGui
import numpy as np
from QtSigman import DataActions

class DataListItemWidget(QW.QWidget):
    def __init__(self, parent=None):
        super(DataListItemWidget, self).__init__(parent)
        self.mainHBoxLayout = QW.QHBoxLayout()
        
        self.typeLabel = QW.QLabel()
        self.mainHBoxLayout.addWidget(self.typeLabel)

        self.editMetaButton = QW.QPushButton()
        self.editMetaButton.setText("Change metadata")
        self.mainHBoxLayout.addWidget(self.editMetaButton)

        self.setLayout(self.mainHBoxLayout)
        self.setStyleSheet("""
        .QWidget {
            border: 20px solid black;
            border-radius: 10px;
            background-color: rgb(255, 255, 255);
            }
        """)

    def setInfo(self, vObject, key):
        self.typeLabel.setText(key)

def _generateFunction(function, *args):
    return lambda: function(*args)

class DataListWidget(QW.QListWidget):
    """A widget that contains a list corresponding to a single data
    dict within a VCollection.

    Attributes:
        DataListWidget.metaFunction - function that is ran when the
                                      edit metainformation button is
                                      clicked. It is given the vObject
                                      and its key as an argument.
    """

    def __init__(self, metaFunction, dict_=None, parent=None):
        super().__init__(parent=parent)
        self.metaFunction = metaFunction
        self.setSizePolicy(QW.QSizePolicy.Fixed,
                           QW.QSizePolicy.Expanding)
        if dict_ is not None:
            self.updateData(dict_)
    
    def updateData(self, dict_):
        """Clears out all items from the list and fills it with
        vObjects from a given dict.
        """
        self.clear()
        for key, item in dict_.items():
            itemWidget = DataListItemWidget()
            itemWidget.editMetaButton.clicked.connect(
                _generateFunction(
                    self.metaFunction, item, key, dict_.keys()))
            itemWidget.setInfo(item, key)
            item = QW.QListWidgetItem(self)
            item.setSizeHint(itemWidget.sizeHint())
            self.addItem(item)
            self.setItemWidget(item, itemWidget)

    def contextMenuEvent(self, event):
        self.menu = QW.QMenu(self)
        row = []
        for i in self.selectionModel().selection().indexes():
            row, column = i.row(), i.column()
        a = list(self.items)
        if (type(row) is int):
            if hasattr(a[row][1], 'offset'):
                settingsFunction = DataActions.inputWaveSettings
                datay = a[row][1].data
                offset = a[row][1].offset
                sampleLength = a[row][1].sample_length
                time = a[row][1].complete_length
                datax = np.arange (offset, offset+time,sampleLength)
            else:
                settingsFunction = DataActions.inputPointSettings
                datax = a[row][1].data_x
                datay = a[row][1].data_y


            renameAction = QW.QAction('Zmień metainformacje', self)
            renameAction.triggered.connect( generateMetadataButtonResponse(
                        settingsFunction, self.CompositeDataWraper, a[row][0]))
            self.menu.addAction(renameAction)

            saveAction = QW.QAction('Zapisz dane', self)
            saveAction.triggered.connect(lambda: DataActions.saveData (datax,datay,a[row][0]))
            self.menu.addAction(saveAction)

            self.menu.popup(QtGui.QCursor.pos())

class VCollectionListWidget(QW.QWidget):
    """A widget containing three lists corresponding to data in a
    VCollection.
    """

    def __init__(self, vCollection, parent=None):
        super().__init__(parent=parent)
        self.vCollection = vCollection

        self.setSizePolicy(QW.QSizePolicy.Fixed,
                           QW.QSizePolicy.Expanding)
        
        vBoxLayout = QW.QVBoxLayout(self)
        self.setLayout(vBoxLayout)

        wavesLabel = QW.QLabel("Waveforms")
        vBoxLayout.addWidget(wavesLabel)
        self.waveList = DataListWidget(
            DataActions.setVWaveSettings, vCollection.waves)
        vBoxLayout.addWidget(self.waveList)
        updateWavesList = lambda: self.waveList.updateData(
            vCollection.waves)
        vCollection.waveAdded.connect(updateWavesList)
        vCollection.waveKeyChanged.connect(updateWavesList)
        vCollection.waveDeleted.connect(updateWavesList)

        pointsLabel = QW.QLabel("Points")
        vBoxLayout.addWidget(pointsLabel)
        self.pointsList = DataListWidget(
            DataActions.setVPointsSettings, vCollection.points)
        vBoxLayout.addWidget(self.pointsList)
        updatePointsList = lambda: self.pointsList.updateData(
            vCollection.points)
        vCollection.pointsAdded.connect(updatePointsList)
        vCollection.pointsKeyChanged.connect(updatePointsList)
        vCollection.pointsDeleted.connect(updatePointsList)

        parametersLabel = QW.QLabel("Parameters")
        vBoxLayout.addWidget(parametersLabel)
        _parameterFunctionPlaceholder = lambda x, y: x+y # Unfinished
        self.parameterList = DataListWidget(
            _parameterFunctionPlaceholder, vCollection.parameters)
        vBoxLayout.addWidget(self.parameterList)
        updateParametersList = lambda: self.parameterList.updateData(
            vCollection.parameters)
        vCollection.parameterAdded.connect(updateParametersList)
        vCollection.parameterKeyChanged.connect(updateParametersList)
        vCollection.parameterDeleted.connect(updateParametersList)

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

        #self.editMetadataButton = QW.QPushButton()
        #self.editMetadataButton.setText("Zmień metainformacje")
        #self.mainHBoxLayout.addWidget(self.editMetadataButton)

        self.setLayout(self.mainHBoxLayout)
        self.setStyleSheet("""
        .QWidget {
            border: 20px solid black;
            border-radius: 10px;
            background-color: rgb(255, 255, 255);
            }
        """)

    def setInfo(self, compositeDataWrapper, dataType, key):
        self.typeLabel.setText(key)

def generateMetadataButtonResponse(settingsFunction, compositeDataWrapper, key):
    return lambda: settingsFunction(compositeDataWrapper, key)


class DataListWidget(QW.QListWidget):
    items = []
    CompositeDataWraper = None
    def updateData(self, compositeDataWrapper, dataType):
        self.CompositeDataWraper = compositeDataWrapper

        if dataType == 'wave':
            self.items = compositeDataWrapper.waves.items()
            #settingsFunction = DataActions.inputWaveSettings
        elif dataType == 'point':
            self.items = compositeDataWrapper.points.items()
           # settingsFunction = DataActions.inputPointSettings
        #elif dataType == 'parameter':
         #   self.items = compositeDataWrapper.parameters.items()
          #  settingsFunction = DataActions.inputParameterSettings
        
        self.clear()
        for key, item in self.items:
            itemWidget = DataListItemWidget()
            itemWidget.setInfo(compositeDataWrapper, dataType, key)
            #itemWidget.editMetadataButton.clicked.connect(
             #   generateMetadataButtonResponse(
              #      settingsFunction, compositeDataWrapper, key))

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
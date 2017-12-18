from PyQt5 import QtWidgets as QW

from QtSigman import DataActions

class DataListItemWidget(QW.QWidget):
    def __init__(self, parent=None):
        super(DataListItemWidget, self).__init__(parent)
        self.mainHBoxLayout = QW.QHBoxLayout()
        
        self.typeLabel = QW.QLabel()
        self.mainHBoxLayout.addWidget(self.typeLabel)

        self.editMetadataButton = QW.QPushButton()
        self.editMetadataButton.setText("Zmień metainformacje")
        self.mainHBoxLayout.addWidget(self.editMetadataButton)

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
    def updateData(self, compositeDataWrapper, dataType):
        if dataType == 'wave':
            items = compositeDataWrapper.waves.items()
            settingsFunction = DataActions.inputWaveSettings
        elif dataType == 'point':
            items = compositeDataWrapper.points.items()
            settingsFunction = DataActions.inputPointSettings
        elif dataType == 'parameter':
            items = compositeDataWrapper.parameters.items()
            settingsFunction = DataActions.inputParameterSettings

        self.clear()
        for key, item in items:
            itemWidget = DataListItemWidget()
            itemWidget.setInfo(compositeDataWrapper, dataType, key)
            itemWidget.editMetadataButton.clicked.connect(
                generateMetadataButtonResponse(
                    settingsFunction, compositeDataWrapper, key))
            item = QW.QListWidgetItem(self)
            item.setSizeHint(itemWidget.sizeHint())
            self.addItem(item)
            self.setItemWidget(item, itemWidget)

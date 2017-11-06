from PyQt5 import QtWidgets as QW

class DataListItemWidget(QW.QWidget):
    def __init__(self, parent=None):
        super(DataListItemWidget, self).__init__(parent)
        self.mainHBoxLayout = QW.QHBoxLayout()
        self.typeLabel = QW.QLabel()
        self.mainHBoxLayout.addWidget(self.typeLabel)
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

class DataListWidget(QW.QListWidget):
    def updateData(self, compositeDataWrapper, dataType):
        if dataType == 'line':
            items = compositeDataWrapper.data_lines.items()
        elif dataType == 'point':
            items = compositeDataWrapper.data_points.items()
        elif dataType == 'parameter':
            items = compositeDataWrapper.parameters.items()

        self.clear()
        for key, item in items:
            itemWidget = DataListItemWidget()
            itemWidget.setInfo(compositeDataWrapper, dataType, key)
            item = QW.QListWidgetItem(self)
            item.setSizeHint(itemWidget.sizeHint())
            self.addItem(item)
            self.setItemWidget(item, itemWidget)

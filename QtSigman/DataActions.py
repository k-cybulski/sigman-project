from os import getcwd
import pickle

from PyQt5 import QtWidgets as QW
from sigman import file_manager as fm
import sigman as sm

import QtSigman
from QtSigman import DataActionWidgets
from QtSigman.DataActionWidgets import DataActionStatus

def importLine(compositeDataWrapper):
    fileFilter = "dat (*.dat)"
    fileDialog = QW.QFileDialog()
    fileDialog.setFileMode(QW.QFileDialog.ExistingFiles)
    try:
        path = fileDialog.getOpenFileName(filter = fileFilter)
        assert path[0] != ""
        dataWave = fm.import_line(path[0])
        dictType, color, axis, offset, status = DataActionWidgets.DataSettingsDialog.getDataSettings(
            forbiddenNames = compositeDataWrapper.data_waves.keys(),
            title = path[0])
        if status is DataActionStatus.Ok: 
            dataWave.offset = offset
            compositeDataWrapper.add_data_wave(dataWave, dictType, 
                                               color, axis = axis)
    # W wypadku, gdy plik nie zostanie wybrany, po prostu udajemy że nic się
    # nie stało i nic nie zmieniamy
    except AssertionError:
        pass

def importPoints(compositeDataWrapper):
    fileFilter = "dat (*.dat)"
    fileDialog = QW.QFileDialog()
    fileDialog.setFileMode(QW.QFileDialog.ExistingFiles)
    try:
        path = fileDialog.getOpenFileName(filter = fileFilter)
        assert path[0] != ""
        dataPoints = fm.import_points(path[0])
        dictType, color, axis, offset, status = DataActionWidgets.DataSettingsDialog.getDataSettings(
            forbiddenNames = compositeDataWrapper.data_points.keys(),
            title = path[0])
        if status is DataActionStatus.Ok:
            dataPoints.move_in_time(offset)
            compositeDataWrapper.add_data_points(dataPoints, dictType, color, axis = axis)
    # W wypadku, gdy plik nie zostanie wybrany, po prostu udajemy że nic się
    # nie stało i nic nie zmieniamy
    except AssertionError:
        pass

def editLineSettings(compositeDataWrapper, dictType):
    forbiddenNames = list(compositeDataWrapper.data_waves.keys())
    forbiddenNames.remove(dictType)
    newDictType, color, axis, offset, status = DataActionWidgets.DataSettingsDialog.getDataSettings(
        forbiddenNames = forbiddenNames,
        dictType = dictType,
        title = dictType,
        axis = compositeDataWrapper.data_waves[dictType].axis,
        offset = str(compositeDataWrapper.data_waves[dictType].offset),
        askDelete = True,
        color = compositeDataWrapper.data_waves[dictType].color)
    if status is DataActionStatus.Ok:
        compositeDataWrapper.editDataWaveSettings(
            dictType, newDictType, color, axis, offset)
    if status is DataActionStatus.Delete:
        compositeDataWrapper.delete_data_wave(dictType)

def editPointSettings(compositeDataWrapper, dictType):
    forbiddenNames = list(compositeDataWrapper.data_points.keys())
    forbiddenNames.remove(dictType)
    newDictType, color, axis, offset, status = DataActionWidgets.DataSettingsDialog.getDataSettings(
        forbiddenNames = forbiddenNames,
        dictType = dictType,
        title = dictType,
        axis = compositeDataWrapper.data_points[dictType].axis,
        askDelete = True,
        color = compositeDataWrapper.data_points[dictType].color)
    if status is DataActionStatus.Ok:
        compositeDataWrapper.editDataPointsSettings(
            dictType, newDictType, color, axis, offset)
    if status is DataActionStatus.Delete:
        compositeDataWrapper.delete_data_points(dictType)

def editParameterSettings(compositeDataWrapper, dictType):
    forbiddenNames = list(compositeDataWrapper.parameters.keys())
    forbiddenNames.remove(dictType)
    newDictType, color, axis, offset, status = DataActionWidgets.DataSettingsDialog.getDataSettings(
        forbiddenNames = forbiddenNames,
        dictType = dictType,
        title = dictType,
        axis = compositeDataWrapper.parameters[dictType].axis,
        askDelete = True,
        color = compositeDataWrapper.parameters[dictType].color,
        offset = None)
    if status is DataActionStatus.Ok:
        compositeDataWrapper.editParameterSettings(
            dictType, newDictType, color, axis)
    if status is DataActionStatus.Delete:
        compositeDataWrapper.delete_parameter(dictType)

class _PickledCompositeDataWrapper:
    """Obiekt zawierający wszystkie kluczowe informacje zawarte w 
    CompositeDataWrapper, lecz bez sygnałów Qt oraz informacji
    graficznych które uniemożliwiają użycie na nim pickle."""
    def __init__(self, compositeDataWrapper):
        data = [
            compositeDataWrapper.data_waves,
            compositeDataWrapper.data_points,
            compositeDataWrapper.parameters]
#       mplObject każdego obiektu danych powinien być usunięty, by nie
#       przeszkadzać przy wczytywaniu, lecz jeśli zostanie to zrobione przy
#       zapisywaniu to obecnie wyświetlone dane znikną. Zamiast tego jest to
#       robione w trakcie wczytywania
#        for dataItem in data:
#            for key, item in dataItem.items():
#                item.removeMplObject()
        self.data_waves = compositeDataWrapper.data_waves
        self.data_points = compositeDataWrapper.data_points
        self.parameters = compositeDataWrapper.parameters

def loadCompositeData():
    fileFilter = "pickle (*.pickle)"
    fileDialog = QW.QFileDialog()
    fileDialog.setFileMode(QW.QFileDialog.ExistingFiles)
    try:
        path = fileDialog.getOpenFileName(filter = fileFilter)
        assert path[0] != ""
        with open(path[0], 'rb') as pickleFile:
            compositeData = pickle.load(pickleFile)
            if isinstance(compositeData, sm.Composite_data):
                return QtSigman.CompositeDataWrapper.fromSigmanCompositeData(compositeData)
            elif (isinstance(compositeData, QtSigman.CompositeDataWrapper) or
                  isinstance(compositeData, _PickledCompositeDataWrapper)):
                return compositeData
            else:
                msg = QW.QMessageBox()
                msg.setIcon(QW.QMessageBox.Warning)
                msg.setText("Niewłaściwy plik.")
                msg.exec_()
    # W wypadku, gdy plik nie zostanie wybrany, po prostu udajemy że nic się
    # nie stało i nic nie zmieniamy
    except AssertionError:
        pass

def saveCompositeData(compositeData):
    fileDialog = QW.QFileDialog()
    fileDialog.setFileMode(QW.QFileDialog.AnyFile)
    fileDialog.setDefaultSuffix('.pickle')
    try:
        path = fileDialog.getSaveFileName()
        assert path[0] != ""
        with open(path[0], 'wb') as pickleFile:
            pickledData = _PickledCompositeDataWrapper(compositeData)
            pickle.dump(pickledData, pickleFile)
    except AssertionError:
        pass

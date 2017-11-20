from os import getcwd
import pickle

from PyQt5 import QtWidgets as QW
from sigman import file_manager as fm
from sigman import analyzer
import sigman as sm

import QtSigman
from QtSigman import DataActionWidgets
from QtSigman.DataActionWidgets import DataActionStatus
from QtSigman.MplWidgets import Axis

def importLine(compositeDataWrapper):
    fileFilter = "dat (*.dat)"
    fileDialog = QW.QFileDialog()
    fileDialog.setFileMode(QW.QFileDialog.ExistingFiles)
    try:
        path = fileDialog.getOpenFileName(filter = fileFilter)
        assert path[0] != ""
        title = path[0].split("/")[-1]
        wave = fm.import_wave(path[0], 'default')
        dictType, color, axis, offset, status = DataActionWidgets.DataSettingsDialog.getDataSettings(
            forbiddenNames = compositeDataWrapper.waves.keys(),
            title = title)
        if status is DataActionStatus.Ok: 
            wave.offset = offset
            compositeDataWrapper.add_wave(wave, dictType, 
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
        points = fm.import_points(path[0], 'default')
        dictType, color, axis, offset, status = DataActionWidgets.DataSettingsDialog.getDataSettings(
            forbiddenNames = compositeDataWrapper.points.keys(),
            title = path[0])
        if status is DataActionStatus.Ok:
            points.move_in_time(offset)
            compositeDataWrapper.add_points(points, dictType, color, axis = axis)
    # W wypadku, gdy plik nie zostanie wybrany, po prostu udajemy że nic się
    # nie stało i nic nie zmieniamy
    except AssertionError:
        pass

def editLineSettings(compositeDataWrapper, dictType):
    forbiddenNames = list(compositeDataWrapper.waves.keys())
    forbiddenNames.remove(dictType)
    newDictType, color, axis, offset, status = DataActionWidgets.DataSettingsDialog.getDataSettings(
        forbiddenNames = forbiddenNames,
        dictType = dictType,
        title = dictType,
        axis = compositeDataWrapper.waves[dictType].axis,
        offset = str(compositeDataWrapper.waves[dictType].offset),
        askDelete = True,
        color = compositeDataWrapper.waves[dictType].color)
    if status is DataActionStatus.Ok:
        compositeDataWrapper.editDataWaveSettings(
            dictType, newDictType, color, axis, offset)
    if status is DataActionStatus.Delete:
        compositeDataWrapper.delete_wave(dictType)

def editPointSettings(compositeDataWrapper, dictType):
    forbiddenNames = list(compositeDataWrapper.points.keys())
    forbiddenNames.remove(dictType)
    newDictType, color, axis, offset, status = DataActionWidgets.DataSettingsDialog.getDataSettings(
        forbiddenNames = forbiddenNames,
        dictType = dictType,
        title = dictType,
        axis = compositeDataWrapper.points[dictType].axis,
        askDelete = True,
        color = compositeDataWrapper.points[dictType].color)
    if status is DataActionStatus.Ok:
        compositeDataWrapper.editDataPointsSettings(
            dictType, newDictType, color, axis, offset)
    if status is DataActionStatus.Delete:
        compositeDataWrapper.delete_points(dictType)

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
            compositeDataWrapper.waves,
            compositeDataWrapper.points,
            compositeDataWrapper.parameters]
#       mplObject każdego obiektu danych powinien być usunięty, by nie
#       przeszkadzać przy wczytywaniu, lecz jeśli zostanie to zrobione przy
#       zapisywaniu to obecnie wyświetlone dane znikną. Zamiast tego jest to
#       robione w trakcie wczytywania
#        for dataItem in data:
#            for key, item in dataItem.items():
#                item.removeMplObject()
        self.waves = compositeDataWrapper.waves
        self.points = compositeDataWrapper.points
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

def modifyWave(compositeDataWrapper):
    proc = DataActionWidgets.ProcedureDialog.getProcedure(
        'modify', compositeDataWrapper)
    dictType, beginTime, endTime, procedure, arguments, status = proc
    if status is DataActionStatus.Ok:
        originalWave = compositeDataWrapper.waves[dictType]
        modifiedWave = analyzer.modify_wave(originalWave, 
                                            beginTime, endTime, 
                                            procedure, arguments)
        if status is DataActionStatus.Cancel:
            return
        compositeDataWrapper.waves[dictType].replace_slice(
            beginTime, endTime, modifiedWave)
        compositeDataWrapper.lineChanged.emit()

def findPoints(compositeDataWrapper):
    proc = DataActionWidgets.ProcedureDialog.getProcedure(
        'points', compositeDataWrapper)
    beginTime, endTime, procedure, arguments, status = proc
    if status is DataActionStatus.Ok:
        newPoints = analyzer.find_points(compositeDataWrapper, 
                                         beginTime, endTime, 
                                         procedure, arguments)
        nameBase = 'found_points'
        nameNum = 0
        name = nameBase + str(nameNum)
        while name in compositeDataWrapper.points:
            nameNum += 1
            name = nameBase + str(nameNum)
        dictType, color, axis, offset, status = DataActionWidgets.DataSettingsDialog.getDataSettings(
            forbiddenNames = compositeDataWrapper.points.keys(),
            title=procedure.__name__)
        if status is DataActionStatus.Cancel:
            return
        compositeDataWrapper.add_points(newPoints, dictType, color, axis=axis)

from os import getcwd
import pickle

from PyQt5 import QtWidgets as QW
from sigman import file_manager as fm
from sigman import analyzer, EmptyPointsError
import sigman as sm

import QtSigman
from QtSigman import DataActionWidgets
from QtSigman.DataActionWidgets import DataActionStatus
from QtSigman.VisualObjects import VWave

class ActionCancelledError(Exception):
    """Raised when an action is cancelled."""

def loadWave(forbiddenNames):
    """Imports an sm.Wave instance from a file and opens up a dialog
    window with possible metainformaiton options.

    Returns the Wave, chosen dictType, color and axis.
    """
    fileFilter = "dat (*.dat)"
    fileDialog = QW.QFileDialog()
    fileDialog.setFileMode(QW.QFileDialog.ExistingFiles)
    path = fileDialog.getOpenFileName(filter=fileFilter)
    if path[0] == "":
        raise ActionCancelledError
    title = path[0].split("/")[-1]
    wave = fm.import_wave(path[0], 'default')
    dictType, color, axis, offset, status = DataActionWidgets.DataSettingsDialog.getDataSettings(
        forbiddenNames=forbiddenNames,
        title=title)
    if status is DataActionStatus.Ok: 
        wave.offset = offset
        wave.type = dictType
        return wave, dictType, color, axis
    else:
        raise ActionCancelledError

def loadPoints(forbiddenNames):
    """Imports an sm.Points instance from a file and opens up a dialog
    window with possible metainformaiton options.

    Returns the Points, chosen dictType, color and axis.
    """
    fileFilter = "dat (*.dat)"
    fileDialog = QW.QFileDialog()
    fileDialog.setFileMode(QW.QFileDialog.ExistingFiles)
    path = fileDialog.getOpenFileName(filter=fileFilter)
    if path[0] == "":
        raise ActionCancelledError
    points = fm.import_points(path[0], 'default')
    dictType, color, axis, offset, status = DataActionWidgets.DataSettingsDialog.getDataSettings(
        forbiddenNames=forbiddenNames,
        title=path[0])
    if status is DataActionStatus.Ok:
        points.move_in_time(offset)
        points.type = dictType
        return points, dictType, color, axis
    else:
        raise ActionCancelledError

def setVWaveSettings(vWave, key, allKeys):
    forbiddenKeys = list(allKeys)
    forbiddenKeys.remove(key)
    newKey, color, axis, offset, status = DataActionWidgets.DataSettingsDialog.getDataSettings(
        forbiddenNames=forbiddenKeys,
        dictType=key,
        title=key,
        axis=vWave.axis,
        offset=str(vWave.data.offset),
        askDelete=True,
        color=vWave.color)
    if status is DataActionStatus.Ok:
        vWave.setSettings(color, axis)
        vWave.data.type = newKey
        vWave.data.offset = offset
        vWave.data.changed.emit()
        vWave.setDictKey(newKey)
    if status is DataActionStatus.Delete:
        vWave.delete()

def setVPointsSettings(vPoints, key, allKeys):
    forbiddenKeys = list(allKeys)
    forbiddenKeys.remove(key)
    newKey, color, axis, offset, status = DataActionWidgets.DataSettingsDialog.getDataSettings(
        forbiddenNames=forbiddenKeys,
        dictType=key,
        title=key,
        axis=vPoints.axis,
        offset="0",
        askDelete=True,
        color=vPoints.color)
    if status is DataActionStatus.Ok:
        vPoints.setSettings(color, axis)
        vPoints.data.type = newKey
        vPoints.data.move_in_time(offset)
        vPoints.setDictKey(newKey)
    if status is DataActionStatus.Delete:
        vPoints.delete()

class _PickledCompositeDataWrapper:
    """Obiekt zawierający wszystkie kluczowe informacje zawarte w 
    CompositeDataWrapper, lecz bez sygnałów Qt oraz informacji
    graficznych które uniemożliwiają użycie na nim pickle."""
    def __init__(self, compositeDataWrapper):
        self.waves = {}
        self.points = {}
        self.parameters = {}
        for selfDict, argDict in [
                (self.waves, compositeDataWrapper.waves),
                (self.points, compositeDataWrapper.points),
                (self.parameters, compositeDataWrapper.parameters)]:
            for key, item in argDict.items():
                selfDict[key] = item.copy()

def loadCompositeData():
    fileFilter = "pickle (*.pickle)"
    fileDialog = QW.QFileDialog()
    fileDialog.setFileMode(QW.QFileDialog.ExistingFiles)
    path = fileDialog.getOpenFileName(filter = fileFilter)
    assert path[0] != ""
    if path[0] == "":
        raise ActionCancelledError
    with open(path[0], 'rb') as pickleFile:
        compositeData = pickle.load(pickleFile)
        if (isinstance(compositeData, sm.Composite_data) or
                isinstance(compositeData, QtSigman.CompositeDataWrapper) or
                isinstance(compositeData, _PickledCompositeDataWrapper)):
            return compositeData
        else:
            QW.QMessageBox.warning(None, 'Błąd', 'Niewłaściwy plik')

def saveCompositeData(compositeData):
    fileDialog = QW.QFileDialog()
    fileDialog.setFileMode(QW.QFileDialog.AnyFile)
    fileDialog.setDefaultSuffix('.pickle')
    path = fileDialog.getSaveFileName()
    if path[0] == "":
        raise ActionCancelledError
    with open(path[0], 'wb') as pickleFile:
        pickledData = _PickledCompositeDataWrapper(compositeData)
        pickle.dump(pickledData, pickleFile)

def modifyWave(compositeDataWrapper):
    pr = DataActionWidgets.ProcedureDialog.getProcedure(
        'modify', compositeDataWrapper)
    waveKey, beginTime, endTime, procedure, arguments, status = pr
    if status is DataActionStatus.Ok:
        originalWave = compositeDataWrapper.waves[waveKey]
        modifiedWave = analyzer.modify_wave(originalWave, 
                                            beginTime, endTime, 
                                            procedure, arguments)
        if status is DataActionStatus.Cancel:
            return
        compositeDataWrapper.waves[waveKey].replace_slice(
            beginTime, endTime, modifiedWave)
        compositeDataWrapper.waveChanged.emit()

def findPoints(compositeDataWrapper):
    pr = DataActionWidgets.ProcedureDialog.getProcedure(
        'points', compositeDataWrapper)
    waveDict, pointsDict, beginTime, endTime, procedure, arguments, status = pr
    if status is DataActionStatus.Ok:
        try:
            newPoints = analyzer.find_points(waveDict, pointsDict, 
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
            compositeDataWrapper.add_points(newPoints, dictType, 
                                            color=color, axis=axis)
        except EmptyPointsError:
            QW.QMessageBox.warning(None, 'Błąd', 'Nie odnaleziono punktów')

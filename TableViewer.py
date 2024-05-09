from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QValidator,QIntValidator,QBrush


class CustomIntValidator(QValidator):
    def __init__(self,mini,maxi):
        super(CustomIntValidator,self).__init__()
        self.mini=mini
        self.maxi=maxi

    def validate(self, input, pos):
        if pos==0:
            return (QValidator.Intermediate,input,pos)
        if input.lower().startswith("0x"):
            if pos<=1:
                return (QValidator.Intermediate, input, pos)
            else:
                return (QValidator.Acceptable,input,pos)
        try:
            value=int(input)
        except ValueError:
            return (QValidator.Invalid,input,pos)
        if (value>=self.mini) and (value <=self.maxi):
            return (QValidator.Acceptable,input,pos)
        else:
            return (QValidator.Invalid,input,pos)



class CustomDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        datatype=index.model().getDataType(index.row())
        if "enum" in datatype:
            editor= QComboBox(parent)
            items=index.model().getRange(index.row())
            editor.addItems(items.keys())
        elif "uint" in datatype:
            editor = QLineEdit(parent)
            itemrange=index.model().getRange(index.row())
            validator=CustomIntValidator(*itemrange)
            editor.setValidator(validator)
        else:
            editor =QLineEdit(parent)
        return editor

    def setEditorData(self, editor, index):
        if isinstance(editor,QComboBox):
            model_value = index.model().data(index, Qt.EditRole)
            current_index = editor.findText(model_value)
            if current_index > 0:
                editor.setCurrentIndex(current_index)

    def setModelData(self, editor, model, index):
        if isinstance(editor,QLineEdit):
            editor_value=editor.text()
        elif isinstance(editor,QComboBox):
            editor_value = editor.currentText()
        else:
            editor_value=None
        model.setData(index, editor_value, Qt.EditRole)

class CustomTableModel(QAbstractTableModel):
    def __init__(self,table,parent=None):
        QAbstractTableModel.__init__(self, parent)
        self._table=table
        self.columns=["Name","Description","Datatype","Value"]
        self.stack = QUndoStack()

    def flags(self, index):
        if index.column() < len(self.columns)-1 or not self.isEditable(index.row()):
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        else:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable| Qt.ItemIsEditable

    def rowCount(self, parent=None):
        return len(self._table)

    def columnCount(self, parent=None):
        return len(self.columns)

    def data(self, index, role=None):
        if not index.isValid():
            return None
        if role in [Qt.DisplayRole,Qt.EditRole]:
            return self._table.get(index.row(),self.columns[index.column()].lower())
        if role==Qt.BackgroundRole and  not self.isEditable(index.row()):
            return QBrush(Qt.lightGray)

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.columns[section]
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return f"{section + 1}"

    def setData(self, index, value, role):
        if not index.isValid():
            return False
        if role == Qt.EditRole:
            prev=self._table.values[index.row()]
            if self._table.set(index.row(),value):
                self.stack.push(CellEdit(index, prev, self))
                self.dataChanged.emit(index, index)
                return True
        return False

    def getDataType(self,row):
        tdef=self._table.tabledef.items[row]
        return self._table.get(row,"datatype")

    def getRange(self,row):
        return self._table.get(row,"datarange")

    def isEditable(self,row):
        return self._table.get(row,"editable")>0

    def isModified(self):
        return self._table.isEdited

    def getInfo(self):
        return self._table.info()

    def findIndex(self,name):
        return self._table.tabledef.findIndex(name)

    def copyText(self):
        return self._table.copyText()

    def getCurrentFilename(self):
        return self._table.currentfilename

    def getItem(self,index_or_name):
        if type(index_or_name)==type(str()):
            index_or_name=self.findIndex(index_or_name)
        return self._table.tabledef.items[index_or_name]

    def encode(self,filename,offset,numbytes):
        is_new_tabledef=self._table.encode(filename,offset,numbytes)
        self._table.isEdited = False
        return is_new_tabledef

class CellEdit(QUndoCommand):
    def __init__(self, index, prev, model, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.index = index
        self.value = model._table.values[index.row()]
        self.prev = prev
        self.model = model

    def undo(self):
        self.model._table.values[self.index.row()] = self.prev
        self.model.dataChanged.emit(self.index,self.index,[Qt.DisplayRole])

    def redo(self):
        self.model._table.values[self.index.row()] = self.value
        self.model.dataChanged.emit(self.index,self.index,[Qt.DisplayRole])

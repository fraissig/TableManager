from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QColor,QKeySequence
from PyQt5.Qt import QApplication
from functools import partial

import sys
import logging
import configparser
from TableObject import *
from TableDefinition import *
from TableViewer import *

CONFIG_FILENAME="TableManager.ini"
README_FILENAME="README.md"
LOGGING_FILENAME="TableManager.log"

logging.basicConfig(filename=LOGGING_FILENAME,
                    format='%(asctime)s - %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S',
                    filemode="w")

class TableManagerTextDialog(QDialog):
    def __init__(self,parent,title,filename):
        super(TableManagerTextDialog,self).__init__(parent)
        self.setWindowTitle(title)
        layout = QVBoxLayout()
        te = QTextEdit()
        te.setReadOnly(True)
        te.setAcceptRichText(True)
        layout.addWidget(te)
        if os.path.isfile(filename):
            with open(filename,'r') as fd:
                text=fd.read()
            if filename.endswith(".md"):
                te.setMarkdown(text)
            else:
                te.setText(text)
        else:
            te.setText("ERROR:\n File {0} doesn't exist".format(filename))
        button=QDialogButtonBox(QDialogButtonBox.Ok )
        button.accepted.connect(self.accept)
        layout.addWidget(button)
        self.setLayout(layout)
        self.setMinimumSize(500,500)
        self.adjustSize()

class TableManagerMain(QMainWindow):
    """
    TableManager Main Window manager
    """
    def __init__(self):
        super().__init__()

        self.statusbar=QStatusBar()
        self.setStatusBar(self.statusbar)
        self.loadedfile=None
        self.tablesdefinition = {}
        self.InitUI()
        self.InitMenu()

        self.logger=logging.getLogger("TableManager")
        self.logger.setLevel(logging.DEBUG)

        # Load Tables Definition from config file
        config = configparser.ConfigParser()
        if CONFIG_FILENAME in os.listdir():
            config.read(CONFIG_FILENAME)
            dirname=config['TableDefinitionDir']['path']
            self.LoadTablesDefinition(dirname)
        else:
            # no config file found in the current directory
            msg="No Config File {0} found".format(CONFIG_FILENAME)
            self.logger.error(msg)
            dlg = QMessageBox.critical(self)
            dlg.setWindowTitle("Table Manager Config File Error")
            dlg.setText(msg)
            dlg.setStandardButtons(QMessageBox.Ok)
            dlg.exec()
            self.Quit()

    def InitUI(self):
        """
        function to initialize the TableManager window

        :return: nothing
        """
        self.window=QWidget()
        self.setCentralWidget(self.window)
        self.setWindowTitle("TableManager")
        self.setMinimumSize(QSize(600, 600))
        # Layout
        layout = QVBoxLayout()
        self.window.setLayout(layout)

        # TextEdit for information
        group=QGroupBox("Information")
        vbox=QVBoxLayout()
        group.setLayout(vbox)
        self.info=QTextEdit(self)
        vbox.addWidget(self.info)
        layout.addWidget(group)

        self.info.setFixedHeight(120)
        self.info.setReadOnly(True)
        self.info.setPlainText("No Table Selected")
        self.info.setTextBackgroundColor(QColor(145,145,1))

        # Tabs view
        self.tabs=QTabWidget(self)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.CloseTab)
        self.tabs.currentChanged.connect(self.UpdateInfo)
        layout.addWidget(self.tabs)

    def InitMenu(self):
        """
        function to create the Menu File and About

        :return: nothing
        """
        menuBar=QMenuBar(self)
        menuBar.setNativeMenuBar(False)
        self.setMenuBar(menuBar)
        # File Menu
        filemenu=QMenu("&File",self)
        menuBar.addMenu(filemenu)
        # New Table SubMenu extended by list of Tables Definition
        self.newSubMenu=QMenu("&New TBL file", self)
        filemenu.addMenu(self.newSubMenu)
        self.newSubMenu.setEnabled(False)
        # Open Table Menu
        self.openAction=QAction("&Open TBL file...",self)
        self.openAction.triggered.connect(self.Open)
        self.openAction.setShortcut(QKeySequence(Qt.CTRL+Qt.Key_O))
        filemenu.addAction(self.openAction)
        self.openAction.setEnabled(False)
        # Save Table Menu
        self.saveAction=QAction("&Save TBL file",self)
        self.saveAction.triggered.connect(self.Save)
        self.saveAction.setShortcut(QKeySequence(Qt.CTRL+Qt.Key_S))
        filemenu.addAction(self.saveAction)
        self.saveAction.setEnabled(False)
        # SaveAs Table Menu
        self.saveAsAction=QAction("&Save TBL file As ...",self)
        self.saveAsAction.triggered.connect(self.SaveAs)
        filemenu.addAction(self.saveAsAction)
        self.saveAsAction.setEnabled(False)
        # --------- Change Tables Definition -----
        filemenu.addSeparator()
        changeAction = QAction("&Change Tables Definition directory...",self)
        changeAction.triggered.connect(self.ChangeTablesDefinition)
        filemenu.addAction(changeAction)
        # --------- Quit Menu ----------
        filemenu.addSeparator()
        exitAction=QAction("&Quit",self)
        exitAction.triggered.connect(self.Quit)
        exitAction.setShortcut(QKeySequence(Qt.CTRL+Qt.Key_Q))
        filemenu.addAction(exitAction)
        # --------- Edit Menu ----------
        editmenu=QMenu("Edit",self)
        menuBar.addMenu(editmenu)
        undoaction=QAction("Undo",self)
        undoaction.triggered.connect(self.Undo)
        undoaction.setShortcut(QKeySequence(Qt.CTRL+Qt.Key_Z))
        editmenu.addAction(undoaction)
        redoaction=QAction("Redo",self)
        redoaction.triggered.connect(self.Redo)
        redoaction.setShortcut(QKeySequence(Qt.CTRL+Qt.Key_Y))
        editmenu.addAction(redoaction)
        copyaction=QAction("Copy to Clipboard",self)
        copyaction.triggered.connect(self.CopyToClipboard)
        copyaction.setShortcut(QKeySequence(Qt.CTRL+Qt.Key_C))
        editmenu.addAction(copyaction)
        pasteaction=QAction("Paste from Clipboard",self)
        pasteaction.setShortcut(QKeySequence(Qt.CTRL+Qt.Key_V))
        pasteaction.triggered.connect(self.PasteFromClipboard)
        editmenu.addAction(pasteaction)
        # ------------ Help Menu -------------
        helpmenu=QMenu("Help",self)
        menuBar.addMenu(helpmenu)
        aboutaction=QAction("About",self)
        aboutaction.triggered.connect(self.About)
        helpmenu.addAction(aboutaction)
        helpaction=QAction("Help",self)
        helpmenu.addAction(helpaction)
        helpaction.triggered.connect(self.Help)
        logaction=QAction("Display log",self)
        helpmenu.addAction(logaction)
        logaction.triggered.connect(self.DisplayLog)

    def UpdateTablesDefinitionMenu(self):
        self.newSubMenu.clear()
        submenus={}
        for name in sorted(self.tablesdefinition.keys()):
            submenus.setdefault(name.split('.')[0],[]).append((name,partial(self.New,name)))
        for family in sorted(submenus.keys()):
            actions=submenus[family]
            menu = QMenu(family, self)
            for action in actions:
                menu.addAction(*action)
            self.newSubMenu.addMenu(menu)
        if len(self.tablesdefinition)>0:
            self.saveAsAction.setEnabled(True)
            self.saveAction.setEnabled(True)
            self.openAction.setEnabled(True)
        else:
            self.saveAsAction.setEnabled(False)
            self.saveAction.setEnabled(False)
            self.openAction.setEnabled(False)
        self.newSubMenu.setEnabled(True)

    def LoadTablesDefinition(self,dirname):
        self.tablesdefinition = {}
        if os.path.exists(dirname):
            for file in os.listdir(dirname):
                if file.endswith(".json"):
                    self.logger.info("load table definition from file {0}".format(file))
                    try:
                        tdef=TableDefinition(os.path.join(dirname,file))
                        self.tablesdefinition[tdef.getTableName()] = tdef
                    except TypeError as err:
                        self.statusbar.showMessage("Parsing error during file {0} reading".format(file))
                        self.logger.error("Uncorrect table definition in file {0}".format(file))
                        self.logger.error(err)
            self.statusbar.showMessage("Loading {0} Tables Definition from {1}".format(len(self.tablesdefinition),dirname))
        self.UpdateTablesDefinitionMenu()

    def ChangeTablesDefinition(self):
        idx=self.tabs.currentIndex()
        if idx!=-1:
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Change Table Definition")
            dlg.setText("All the tables already open will be closed without saving. Do you want to continue ?")
            dlg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            if dlg.exec() == QMessageBox.Ok:
                while idx!=-1:
                    self.tabs.removeTab(idx)
                    idx=self.tabs.currentIndex()
        dirname = str(QFileDialog().getExistingDirectory())
        config = configparser.ConfigParser()
        config['TableDefinitionDir']={'path': dirname}
        config['Convention']={'bigendian':'True'}
        with open(CONFIG_FILENAME, 'w') as fd:
            config.write(fd)
        self.LoadTablesDefinition(dirname)


    def CreateTable(self,table,name):
        # Table View creation
        tableview=QTableView()
        tablemodel=CustomTableModel(table)
        tableview.setModel(tablemodel)
        tableview.setItemDelegate(CustomDelegate())
        tableview.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        tableview.resizeColumnToContents(0)
        tableview.resizeColumnToContents(3)
        self.tabs.setCurrentIndex(self.tabs.addTab(tableview,name))

    def UpdateInfo(self,idx=None):
        if not idx:
            idx=self.tabs.currentIndex()
        tableview = self.tabs.widget(idx)
        if tableview:
            self.info.setPlainText(tableview.model().getInfo())
        else:
            self.info.setPlainText("No Table Selected")

    def SaveAs(self):
        filename = QFileDialog.getSaveFileName(self,caption= "Save TBL File as",filter="*.tbl")[0]
        if filename:
            self.Save(filename)

    def CloseTab(self,idx):
        tableview=self.tabs.widget(idx)
        if tableview:
            if tableview.model().isModified():
                dlg = QMessageBox(self)
                dlg.setWindowTitle("File not saved")
                dlg.setText("File not saved. Do you want to continue ?")
                dlg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                if dlg.exec()==QMessageBox.Ok:
                    name=self.tabs.tabText(idx)
                    self.tabs.removeTab(idx)
                    self.logger.warning("tab {0} not saved".format(name))
            else:
                self.tabs.removeTab(idx)

    def CopyToClipboard(self):
        tableview=self.tabs.widget(self.tabs.currentIndex())
        clipboard=QApplication.clipboard()
        clipboard.setText(tableview.model().copyText())
        msg="Table {0} copied to clipboard".format(self.tabs.tabText(self.tabs.currentIndex()))
        self.logger.info(msg)
        self.statusbar.showMessage(msg)

    def PasteFromClipboard(self):
        itab=self.tabs.currentIndex()
        if itab!=-1:
            tableview=self.tabs.widget(itab)
            model=tableview.model()
            clipboard=QApplication.clipboard()
            mimeData = clipboard.mimeData()
            if mimeData.hasText():
                cnt=0
                for line in mimeData.text().split('\n'):
                    name,valuestr=line.split()
                    idx=model.findIndex(name)
                    if idx:
                        logging.info("{0} found".format(name),valuestr)
                        if model.setData(model.index(idx,0),valuestr,Qt.EditRole):
                            cnt+=1
                        else:
                            logging.error("{0} value error {1}".format(name,valuestr))
                    else:
                        logging.error("{0} not found".format(name),valuestr)
                msg="{0} values pasted".format(cnt)
                logging.info(msg)
                self.statusbar.showMessage(msg)

    def Redo(self):
        self.Do(False)

    def Undo(self):
        self.Do(True)

    def Do(self,undo=True):
        itab = self.tabs.currentIndex()
        if itab != -1:
            tableview=self.tabs.widget(itab)
            if undo:
                tableview.model().stack.undo()
            else:
                tableview.model().stack.redo()

    def New(self,tblname):
        tdef=self.tablesdefinition[tblname]
        # create new tab
        table=TableObject(tdef)
        table.setCurrentTime()
        self.CreateTable(table,tblname)
        self.logger.info("Create new table {0}".format(tblname))

    def Open(self):
        filename = QFileDialog.getOpenFileName(filter="*.tbl")[0]
        self.Open_file(filename)

    def Open_file(self,filename):
        if filename:
            table=TableObject()
            try:
                tblname = table.decodeTableName(filename)
                if not tblname in self.tablesdefinition:
                    msg="No table definition available for table name '{0}'".format(tblname)
                    self.statusbar.showMessage(msg)
                    self.logger.error(msg)
                else:
                    table.loadTableDefinition(self.tablesdefinition[tblname])
                    try:
                        table.decode(filename)
                        self.CreateTable(table,os.path.basename(filename))
                        self.statusbar.showMessage("file {0} opened with {1} table definition".format(filename,tblname))
                    except struct.error:
                        msg="ERROR reading file {0}".format(filename)
                        self.statusbar.showMessage(msg)
                        self.logger.error(msg)
            except struct.error:
                msg="ERROR file {0} is not TBL file".format(filename)
                self.statusbar.showMessage(msg)
                self.logger.error(msg)

    def Save(self,filename=None):
        idx=self.tabs.currentIndex()
        tableview=self.tabs.widget(idx)
        selectedrows=tableview.selectionModel().selectedRows()
        # default values
        offset = 0; numbytes = None
        # check if selected rows outside table headers and set offset & numbytes accordingly
        if len(selectedrows)>0:
            indexes=[index.row() for index in selectedrows if tableview.model().getItem(index.row()).offset>=0]
            if len(indexes)>0:
                offset=min([tableview.model().getItem(idx).offset for idx in indexes])
                numbytes=sum([tableview.model().getItem(idx).bytesSize() for idx in range(min(indexes),max(indexes)+1)])
        if not filename:
            filename=tableview.model().getCurrentFilename()
            if not filename:
                # define a new filename
                filename = QFileDialog.getSaveFileName(self,caption= "Save TBL File as",filter="*.tbl")[0]
        if filename:
            if not filename.endswith('.tbl'):
                filename+='.tbl'
            try:
                is_new_tabledef=tableview.model().encode(filename,offset,numbytes)
                self.UpdateInfo(idx)
                msg="file {0} saved".format(filename)
                self.statusbar.showMessage(msg)
                self.logger.info(msg)
                if is_new_tabledef:
                    self.Open_file(filename)
                else:
                    self.tabs.setTabText(self.tabs.currentIndex(),os.path.basename(filename))
            except ValueError as err:
                self.statusbar.showMessage(str(err))
                self.logger.error(str(err))
        else:
            self.statusbar.showMessage("No file saved")


    def Quit(self):
        # check all the tabs before closing window
        for idx in range(self.tabs.count()):
            self.CloseTab(idx)
        self.close()

    def About(self):
        dlg = QMessageBox(self)
        dlg.setWindowTitle("About TableManager")
        dlg.setTextFormat(Qt.RichText)
        dlg.setText("<h1>TableManager</h1><br>Version 1.0<br>May 2024<br><br><a href='https://github.com/FRAISSIG/TableManager'>source code on Github</a>")
        dlg.setStandardButtons(QMessageBox.Ok)
        dlg.setIcon(QMessageBox.Information)
        button = dlg.exec()

    def Help(self):
        dlg=TableManagerTextDialog(self,"Table Manager Help",README_FILENAME)
        dlg.exec()

    def DisplayLog(self):
        dlg=TableManagerTextDialog(self,"Table Manager Logging",LOGGING_FILENAME)
        dlg.exec()


if __name__=="__main__":
    app = QApplication(sys.argv)
    screen = TableManagerMain()
    screen.show()
    sys.exit(app.exec_())
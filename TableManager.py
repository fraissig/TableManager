from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QValidator,QIntValidator,QBrush,QClipboard
from PyQt5.Qt import QApplication
from functools import partial

import sys
import os
import logging
import configparser
from TableObject import *
from TableDefinition import *
from TableViewer import *

CONFIG_FILENAME="TableManager.ini"
logging.basicConfig(filename="TableManager.log",
                    format='%(asctime)s - %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S')

class TableDefinitionDialog(QDialog):
    def __init__(self,parent=None,choices=None):
        super(TableDefinitionDialog,self).__init__(parent)
        self.setWindowTitle("Choose Table Definition")
        self.choice=QComboBox(self)
        if choices:
            self.choice.addItems(choices)
        layout=QVBoxLayout()
        layout.addWidget(self.choice)
        buttons=QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)


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
        self.setMinimumSize(QSize(600, 500))
        # Layout
        layout = QVBoxLayout()
        self.window.setLayout(layout)

        # TextEdit for information
        group=QGroupBox("Information")
        vbox=QVBoxLayout()
        group.setLayout(vbox)
        self.info=QTextEdit(self)
        vbox.addWidget(self.info)
        #group.setContentsMargins(0,0,10,10)
        layout.addWidget(group)

        self.info.setFixedHeight(120)
        self.info.setReadOnly(True)
        self.info.setPlainText("No Table Selected")

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
        self.newSubMenu=QMenu("&New Binary Table", self)
        filemenu.addMenu(self.newSubMenu)
        self.newSubMenu.setEnabled(False)
        # Open Table Menu
        self.openAction=QAction("&Open Binary Table...",self)
        self.openAction.triggered.connect(self.Open)
        filemenu.addAction(self.openAction)
        self.openAction.setEnabled(False)
        # Save Table Menu
        self.saveAction=QAction("&Save Binary Table",self)
        self.saveAction.triggered.connect(self.Save)
        filemenu.addAction(self.saveAction)
        self.saveAction.setEnabled(False)
        # SaveAs Table Menu
        self.saveAsAction=QAction("&Save Binary Table As ...",self)
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
        filemenu.addAction(exitAction)
        # Edit Menu
        editmenu=QMenu("Edit",self)
        menuBar.addMenu(editmenu)
        copyaction=QAction("Copy to Clipboard",self)
        copyaction.triggered.connect(self.CopyClipboard)
        editmenu.addAction(copyaction)
        # Help Menu
        helpmenu=QMenu("Help",self)
        menuBar.addMenu(helpmenu)
        aboutaction=QAction("About",self)
        aboutaction.triggered.connect(self.About)
        helpmenu.addAction(aboutaction)
        helpaction=QAction("Help",self)
        helpmenu.addAction(helpaction)

    def UpdateTablesDefinitionMenu(self):
        self.newSubMenu.clear()
        actions={k:partial(self.New,k) for k in sorted(self.tablesdefinition.keys())}
        for k,f in actions.items():
            self.newSubMenu.addAction(k,f)
        self.saveAsAction.setEnabled(True)
        self.saveAction.setEnabled(True)
        self.newSubMenu.setEnabled(True)
        self.openAction.setEnabled(True)

    def LoadTablesDefinition(self,dirname):
        self.tablesdefinition = {}
        if os.path.exists(dirname):
            for file in os.listdir(dirname):
                if file.endswith(".json"):
                    self.logger.info("load table definition from file {0}".format(file))
                    tdef=TableDefinition(os.path.join(dirname,file))
                    if tdef:
                        self.tablesdefinition[tdef.getTableName()]=tdef
                    else:
                        self.logger.error("No table definition in file {0}".format(file))
        self.statusbar.showMessage("Loading {0} Tables Definition from {1}".format(len(self.tablesdefinition),dirname))
        self.UpdateTablesDefinitionMenu()

    def ChangeTablesDefinition(self):
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
        self.adjustSize()

    def UpdateInfo(self,idx=None):
        if not idx:
            idx=self.tabs.currentIndex()
        tableview = self.tabs.widget(idx)
        if tableview:
            self.info.setPlainText(tableview.model()._table.info())
        else:
            self.info.setPlainText("No Table Selected")

    def SaveAs(self):
        fileName = QFileDialog.getSaveFileName(self,caption= "Save Binary File as",filter="*.tbl")[0]
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
                    self.tabs.removeTab(idx)
                    self.logger.warning("tab {0} not saved".format(self.tabs.currentIndex()))
            else:
                self.tabs.removeTab(idx)

    def CopyClipboard(self):
        tableview=self.tabs.widget(self.tabs.currentIndex())
        clipboard=QApplication.clipboard()
        clipboard.setText(tableview.model()._table.copyText())
        msg="{0} copied to clipboard".format(self.tabs.tabText(self.tabs.currentIndex()))
        self.logger.info(msg)
        self.statusbar.showMessage(msg)

    def New(self,tblname):
        tdef=self.tablesdefinition[tblname]
        # create new tab
        table=TableObject(tdef)
        table.setCurrentTime()
        self.CreateTable(table,tblname)
        self.logger.info("Create new table {0}".format(tblname))

    def Open(self):
        filename = QFileDialog.getOpenFileName(filter="*.tbl")[0]
        if filename:
            table=TableObject()
            tblname = table.decodeTableName(filename)
            if not tblname in self.tablesdefinition:
                dlg = QMessageBox.warning(self)
                dlg.setWindowTitle("No Definition for binary file")
                dlg.setText("No table definition available for table name '{0}'".format(tblname))
                dlg.setStandardButtons(QMessageBox.Ok)
                self.logger.error("file {0} not binary file".format(filename))
            else:
                table.loadTableDefinition(self.tablesdefinition[tblname])
                table.decode(filename)
                self.CreateTable(table,os.path.basename(filename))
                self.statusbar.showMessage("file {0} opened with {1} table definition".format(filename,tblname))


    def Save(self,filename=None):
        idx=self.tabs.currentIndex()
        tableview=self.tabs.widget(idx)
        table=tableview.model()._table
        if table.currentfilename and not filename:
            table.encode(table.currentfilename)
            filename=table.currentfilename
        elif filename:
            table.encode(filename)
        else:
            filename = QFileDialog.getSaveFileName(self,caption= "Save Binary File as",filter="*.tbl")[0]
            if filename:
                table.encode(filename)
        tableview.model()._table.isEdited=False # update isEdited Status
        self.UpdateInfo(idx)
        msg="file {0} saved".format(filename)
        self.statusbar.showMessage(msg)
        self.logger.info(msg)
        self.tabs.setTabText(self.tabs.currentIndex(),os.path.basename(filename))

    def Quit(self):
        # check all the tabs before closing window
        for idx in range(self.tabs.count()):
            self.CloseTab(idx)
        self.close()

    def About(self):
        dlg = QMessageBox(self)
        dlg.setWindowTitle("About TableManager")
        dlg.setText("TableManager\nVersion Alpha")
        dlg.setStandardButtons(QMessageBox.Ok)
        dlg.setIcon(QMessageBox.Information)
        button = dlg.exec()

    def Help(self):
        # TODO
        pass

if __name__=="__main__":
    app = QApplication(sys.argv)
    screen = TableManagerMain()
    screen.show()
    sys.exit(app.exec_())

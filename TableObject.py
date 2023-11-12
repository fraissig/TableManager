import datetime
from TableDefinition import *
from TableCRC import crc16arc

class TableObject(object):
    """
    TableObject contains
     - a TableTemplate having the template of the table but with default values
     - a values list, with the current values modified by the user
     - the current file name from decode or from encode
    """
    def __init__(self ,tabledef=None):
        self.values=[]
        self.tabledef=TableDefinition()
        if tabledef:
            self.loadTableDefinition(tabledef)
        self.isEdited =False
        self.currentfilename=None
        self.crc=None

    def info(self):
        infos={"Table Name           ":self.tabledef.getTableName(),
               "Table Definition Path": self.tabledef.filename,
               "Bytes Size           ": self.tabledef.bytesSize(),
               "Current File Name    ": self.currentfilename,
               "Creation Date        ": self.getTableTime(),
               "Current CRC          ": "0x{:04x}".format(self.calculateCRC())}
        return "\n".join(["{0}:\t{1}".format(k,v) for k,v in infos.items()])

    def loadTableDefinition(self, tabledef):
        self.tabledef =tabledef
        self.values = self.tabledef.getdefaultvalues()

    def __len__(self):
        return len(self.values)

    def getTableTime(self):
        i = self.tabledef.findIndex("TimeSeconds")
        j = self.tabledef.findIndex("TimeSubSeconds")
        if i and j:
            return datetime.datetime(2000, 1, 1, 11, 58, 56, 816000)+datetime.timedelta(seconds=self.values[i],
                                                                                        microseconds=self.values[j])

    def setCurrentTime(self):
        # --- Timestamp compared to reference Epoch (1 jan 2000 11:58:56.816)
        i = self.tabledef.findIndex("TimeSeconds")
        j = self.tabledef.findIndex("TimeSubSeconds")
        if i and j:
            dt = datetime.datetime.now() - datetime.datetime(2000, 1, 1, 11, 58, 56, 816000)
            self.values[i] = dt.days * 86400 + dt.seconds
            self.values[j] = dt.microseconds

    def get(self ,row ,colname):
        item = self.tabledef.items[row]
        if colname=="value":
            return item.display(self.values[row])
        else:
            return getattr(item, colname)

    def set(self ,row ,valuestr):
        self.isEdited =True
        item = self.tabledef.items[row]
        self.values[row]=item.cast(valuestr)

    def calculateCRC(self,bigendian=True):
        # compute CRC without table headers
        buffer=self.tabledef.encode(self.values,bigendian)
        return crc16arc(buffer[struct.calcsize(HEADER_ENCODING):])

    def encode(self,filename,bigendian=True):
        # TODO : update offset & bitssize
        self.setCurrentTime()
        with open(filename,'wb') as fd:
            fd.write(self.tabledef.encode(self.values,bigendian))
        self.currentfilename=filename

    def decodeTableName(self ,filename,bigendian=True):
        with open(filename,'rb') as fd:
            buffer=fd.read()
        self.currentfilename=filename
        return self.tabledef.decodeTableName(buffer,bigendian)

    def decode(self ,filename,bigendian=True):
        with open(filename,'rb') as fd:
            buffer=fd.read()
        self.currentfilename=filename
        self.values=self.tabledef.decode(buffer,bigendian)

    def copyText(self):
        return self.info()+"\n\n"+str(self)

    def __repr__(self):
        s=["Name\tDescription\tDataType\tValue"]
        s.extend(["{0}\t{1}\t{2}\t{3}".format(item.name,
                                              item.description,
                                              item.datatype,
                                              item.display(v)) for item,v in zip(self.tabledef.items,self.values)])
        return "\n".join(s)

if __name__=="__main__":
    import os
    filename="RIDU_v0_6_TBL_RID_AJ_RtAddr.tbl"
    directory="./TableDefinitionDir"
    t=TableObject(TableDefinition(os.path.join(directory,"RIDU_v0_6_TBL_RID_AJ_RtAddr.json")))
    t.setCurrentTime()
    t.encode(filename)
    print(t.info())

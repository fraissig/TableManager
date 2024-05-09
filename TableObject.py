import datetime
from TableDefinition import *
from TableCRC import crc16arc
import os
JD2000 = datetime.datetime(2000, 1, 1, 11, 58, 56, 816000)

class TableObject(object):
    """
    TableObject contains
     - a TableTemplate having the template of the table but with default values
     - a values list, with the current values modified by the user
     - the current file name from decode or from encode
    """
    def __init__(self,tabledef=None):
        self.values=[]
        if tabledef:
            self.loadTableDefinition(tabledef)
        else:
            self.tabledef = TableDefinition()
        self.isEdited =False
        self.currentfilename=None
        self.crc=None

    def info(self):
        crc=self.calculateCRC()
        infos={"Table Name           ": self.tabledef.getTableName(),
               "Table Definition Path": self.tabledef.filename,
               "Total Bytes Size     ": self.tabledef.bytesSize(),
               "Current File Name    ": self.currentfilename,
               "Creation Date        ": self.getTableTime(),
               "Current CRC          ": "0x{:04x}".format(crc) if crc!=None else "ERROR"}
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
            return JD2000+datetime.timedelta(seconds=self.values[i],microseconds=self.values[j])

    def setCurrentTime(self):
        # --- Timestamp compared to reference Epoch (1 jan 2000 11:58:56.816)
        i = self.tabledef.findIndex("TimeSeconds")
        j = self.tabledef.findIndex("TimeSubSeconds")
        if i and j:
            dt = datetime.datetime.now() - JD2000
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
        value = item.cast(valuestr)
        if value!=None:
            self.values[row]=value
            return True
        return False

    def calculateCRC(self,bigendian=True):
        # compute CRC without table headers
        buffer=self.tabledef.encode(self.values,bigendian)
        if buffer:
            return crc16arc(buffer[struct.calcsize(HEADER_ENCODING):])
        else:
            return None


    def encode(self,filename,offset=0,nbytes=None,bigendian=True):
        self.setCurrentTime()
        if offset==0 and nbytes==None:
            buffer = self.tabledef.encode(self.values, bigendian)
            new_tabledef = None
        else:
            new_tabledef,indexes=self.tabledef.reduceTo(offset,nbytes)
            new_values=self.values.copy()
            idx=new_tabledef.findIndex("NumBytes")
            new_values[idx]=nbytes
            idx=new_tabledef.findIndex("Offset")
            new_values[idx]=offset
            buffer=new_tabledef.encode([new_values[i] for i in indexes],bigendian)
        if buffer:
            with open(filename, 'wb') as fd:
                fd.write(buffer)
            if not new_tabledef:
                self.currentfilename = filename
                return False
            else:
                return True
        else:
            raise ValueError("Error during encoding {0}".format(os.path.basename(filename)))

    def decodeTableName(self ,filename,bigendian=True):
        with open(filename,'rb') as fd:
            buffer=fd.read()
        self.currentfilename=filename
        return self.tabledef.decodeTableName(buffer,bigendian)

    def decode(self ,filename,bigendian=True):
        with open(filename,'rb') as fd:
            buffer=fd.read()
        self.currentfilename=filename
        offset,nbytes=self.tabledef.decodeOffsetAndNumBytes(buffer,bigendian)
        new_tabledef,indexes=self.tabledef.reduceTo(offset,nbytes)
        self.values=new_tabledef.decode(buffer,bigendian)
        self.tabledef=new_tabledef

    def copyText(self):
        return str(self)

    def __repr__(self):
        s=["Name\tValue"]
        s.extend(["{0}\t{1}".format(item.name,item.display(v)) for item,v in zip(self.tabledef.items,self.values)])
        return "\n".join(s)



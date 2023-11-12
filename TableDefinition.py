import struct
import json

# TODO gestion des paddings

HEADER_ENCODING="8I32s3I40s"

class TableDefinitionGenericItem(object):
    def __init__(self):
        self.name=""
        self.datatype=""
        self.defaultvalue=None
        self.description=""
        self.length=1
        self.datarange= []
        self.editable=1
        self.displaytype=""
        self.encoding="B"

    def parse(self,data):
        for key,value in data.items():
            setattr(self,key.lower(),value)

    def display(self,value):
        return str(value)

    def cast(self,valuestr):
        return valuestr

    def bytesSize(self):
        return struct.calcsize(self.encoding)

    def maxi(self):
        pass

    def mini(self):
        pass

    def encode(self,value):
        return value

    def decode(self,value):
        return value

    def display(self,value):
        return str(value)

class TableDefinitionUint8Item(TableDefinitionGenericItem):
    def __init__(self):
        super(TableDefinitionUint8Item,self).__init__()
        self.datatype="uint8"
        self.encoding="B"

    def maxi(self):
        bits = 8 * self.bytesSize()
        return 2 ** bits - 1

    def mini(self):
        return 0

    def parse(self,data):
        super(TableDefinitionUint8Item,self).parse(data)
        self.datarange=[self.mini(),self.maxi()]

    def cast(self,valuestr):
        if type(valuestr)==type(str()):
            if valuestr.lower().startswith("0x"):
                return eval(valuestr)
            elif valuestr!='':
                return int(valuestr)
            else:
                return 0
        else:
            return valuestr

    def display(self,value):
        if self.displaytype.lower()=="hex":
            return hex(value)
        else:
            return value

class TableDefinitionInt8Item(TableDefinitionUint8Item):
    def __init__(self):
        super(TableDefinitionInt8Item,self).__init__()
        self.datatype="int8"
        self.encoding="b"

    def maxi(self):
        return 127

    def mini(self):
        return -128

class TableDefinitionUint16Item(TableDefinitionUint8Item):
    def __init__(self):
        super(TableDefinitionUint16Item,self).__init__()
        self.datatype="uint16"
        self.encoding="H"

class TableDefinitionUint32Item(TableDefinitionUint8Item):
    def __init__(self):
        super(TableDefinitionUint32Item,self).__init__()
        self.datatype="uint32"
        self.encoding="I"

class TableDefinitionUint64Item(TableDefinitionUint8Item):
    def __init__(self):
        super(TableDefinitionUint64Item,self).__init__()
        self.datatype="uint64"
        self.encoding="Q"

class TableDefinitionFloatItem(TableDefinitionUint8Item):
    def __init__(self):
        super(TableDefinitionFloatItem,self).__init__()
        self.datatype="float"
        self.encoding="f"

    def maxi(self):
        return struct.unpack('>f', b'\x7f\x7f\xff\xff')[0]

    def mini(self):
        return struct.unpack('>f', b'\xff\x7f\xff\xff')[0]

    def cast(self,valuestr):
        if valuestr!='':
            return float(valuestr)
        else:
            return 0.0

class TableDefinitionLongFloatItem(TableDefinitionFloatItem):
    def __init__(self):
        super(TableDefinitionLongFloatItem,self).__init__()
        self.datatype="longfloat"
        self.encoding="d"

    def maxi(self):
        return struct.unpack('>d', b'\x7f\xef\xff\xff\xff\xff\xff\xff')[0]

    def mini(self):
        return struct.unpack('>d', b'\xff\xef\xff\xff\xff\xff\xff\xff')[0]


class TableDefinitionStringItem(TableDefinitionGenericItem):
    def __init__(self):
        super(TableDefinitionStringItem,self).__init__()
        self.datatype="string"

    def parse(self,data):
        super(TableDefinitionStringItem,self).parse(data)
        self.encoding = "{0}s".format(self.length)

    def encode(self,valuestr):
        return bytes(valuestr,"utf-8")

    def decode(self,value):
        if type(value)==type(bytes()):
            return value.decode("utf-8").replace("\x00","")
        else:
            return value

class TableDefinitionEnum8Item(TableDefinitionGenericItem):
    def __init__(self):
        super(TableDefinitionEnum8Item,self).__init__()
        self.datatype="enum8"
        self.encoding="B"

    def parse(self,data):
        super(TableDefinitionEnum8Item,self).parse(data)
        self.reverse={v:k for k,v in self.datarange.items()}

    def cast(self,valuestr):
        if type(valuestr)==type(str()):
            return self.datarange[valuestr]
        else:
            return valuestr

    def display(self,value):
        try:
            return self.reverse[value]
        except KeyError:
            return "ERROR"

class TableDefinitionEnum32Item(TableDefinitionEnum8Item):
    def __init__(self):
        super(TableDefinitionEnum32Item,self).__init__()
        self.datatype="enum32"
        self.encoding="I"

class TableDefinitionEnum16Item(TableDefinitionEnum8Item):
    def __init__(self):
        super(TableDefinitionEnum16Item,self).__init__()
        self.datatype="enum32"
        self.encoding="H"

class TableDefinitionItemFactory(object):
    def __init__(self):
        self.definitionlist=[TableDefinitionUint8Item,TableDefinitionUint16Item,
                            TableDefinitionUint32Item,TableDefinitionFloatItem,
                            TableDefinitionStringItem,TableDefinitionEnum8Item,
                             TableDefinitionLongFloatItem,TableDefinitionInt8Item,
                             TableDefinitionEnum32Item,TableDefinitionEnum16Item,
                             TableDefinitionUint64Item]
        self.tdefs={td().datatype:td for td in self.definitionlist}

    def create(self,data):
        tdg=TableDefinitionGenericItem()
        tdg.parse(data)
        try:
            tdef=self.tdefs[tdg.datatype]()
            tdef.parse(data)
            return tdef
        except KeyError:
            #print(tdg.datatype,tdg.name)
            return None

class TableDefinition(object):
    def __init__(self,filename=None):
        self.items = []
        self.loadJSON(filename)

    def loadJSON(self,filename):
        if filename:
            fid=open(filename,'r')
            listjson=json.load(fid)
            fid.close()
            tdif=TableDefinitionItemFactory()
            for itemdata in listjson:
                item=tdif.create(itemdata)
                if item:
                    item.defaultvalue=item.cast(item.defaultvalue)
                    self.items.append(item)
            # Define the number of Bytes to be loaded
            # assume to be total size - header size
            idx=self.findIndex("NumBytes")
            self.items[idx].defaultvalue=self.bytesSize()-struct.calcsize(HEADER_ENCODING)
        self.filename=filename

    def getTableName(self):
        return self.items[self.findIndex("TableName")].defaultvalue

    def findIndex(self,name):
        res=[i for i,item in enumerate(self.items) if item.name==name]
        return res[0] if len(res) else None

    def get(self,attr):
        return [getattr(item,attr) for item in self.items]

    def getdefaultvalues(self):
        return [item.defaultvalue for item in self.items]

    def bytesSize(self):
        return sum([item.bytesSize() for item in self.items])

    def decode(self,buffer,bigendian=True):
        convention =">" if bigendian else "<"
        fmt=[convention]
        fmt.extend([item.encoding for item in self.items])
        data=list(struct.unpack("".join(fmt),buffer[:self.bytesSize()]))
        for i,item in enumerate(self.items):
            if item.datatype=="string":
                data[i]=item.decode(data[i])
        return data

    def encode(self,values,bigendian=True):
        convention =">" if bigendian else "<"
        buffer = bytearray()
        for item,value in zip(self.items,values):
            buffer.extend(struct.pack(convention +item.encoding ,item.encode(value)))
        return buffer

    def decodeTableName(self,buffer,bigendian=True):
        convention =">" if bigendian else "<"
        header=convention+HEADER_ENCODING
        headersize=struct.calcsize(header)
        if len(buffer) >= headersize:
            data=struct.unpack(header,buffer[:headersize])
            return data[12].decode('utf-8').replace("\x00","")
        else:
            return None

if __name__=="__main__":
    tdef=TableDefinition()
    tdef.loadJSON("./TableDefinitionDir/COM_v1_2_TBL_COM_AJ_K2_NextPermTbl.json")
    for item in tdef.items:
        print(item.name, item.datatype, type(item.defaultvalue), item.display(item.defaultvalue))
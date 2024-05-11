import struct
import json
import re

# corresponds to CFE file primary header and to TBL secondary header
HEADER_ENCODING="8I32s3I40s"

class TableDefinitionGenericItem(object):
    def __init__(self):
        self.name=""
        self.datatype=""
        self.defaultvalue=0
        self.description=""
        self.length=1
        self.datarange= []
        self.editable=1
        self.displaytype=""
        self.encoding="B"
        self.offset=0

    def parse(self,data):
        for key,value in data.items():
            setattr(self,key.lower(),value)

    def display(self,value):
        return str(value)

    def cast(self,valuestr):
        return valuestr

    def bytesSize(self):
        return struct.calcsize(">"+self.encoding)

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
                v=int(valuestr)
                if v<0:
                    return None
                else:
                    return v
            else:
                return None
        else:
            return valuestr

    def display(self,value):
        if self.displaytype.lower()=="hex":
            return hex(value)
        else:
            return value

    def encode(self,value):
        return int(value)

class TableDefinitionUint24Item(TableDefinitionUint8Item):
    # for padding 24 bits
    def __init__(self):
        super(TableDefinitionUint24Item,self).__init__()
        self.datatype="uint24"
        self.encoding="BH"
        self.defaultvalue=0

    def decode(self,value):
        return 0

    def encode(self,value):
        return (0,0)


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

    def encode(self,value):
        return float(value)

class TableDefinitionFloat16Item(TableDefinitionFloatItem):
    def __init__(self):
        super(TableDefinitionFloat16Item,self).__init__()
        self.datatype="float16"
        self.encoding="e"

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
        self.datarange={"{0} [{1}]".format(k,v):v for k,v in self.datarange.items()}
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

    def encode(self,value):
        return int(value)

class TableDefinitionEnum32Item(TableDefinitionEnum8Item):
    def __init__(self):
        super(TableDefinitionEnum32Item,self).__init__()
        self.datatype="enum32"
        self.encoding="I"

class TableDefinitionEnum16Item(TableDefinitionEnum8Item):
    def __init__(self):
        super(TableDefinitionEnum16Item,self).__init__()
        self.datatype="enum16"
        self.encoding="H"


class TableDefinitionItemFactory(object):
    def __init__(self):
        self.definitionlist=[TableDefinitionUint8Item,TableDefinitionUint16Item,
                            TableDefinitionUint32Item,TableDefinitionFloatItem,
                            TableDefinitionStringItem,TableDefinitionEnum8Item,
                             TableDefinitionLongFloatItem,TableDefinitionInt8Item,
                             TableDefinitionEnum32Item,TableDefinitionEnum16Item,
                             TableDefinitionUint64Item,TableDefinitionUint24Item]
        self.tdefs={td().datatype:td for td in self.definitionlist}
        self.tdefs.update({'float16':TableDefinitionFloat16Item,
                           'float32':TableDefinitionFloatItem,
                           'double64':TableDefinitionLongFloatItem,
                           'double':TableDefinitionLongFloatItem,
                           'raw24':TableDefinitionUint24Item})

    def datatypes(self):
        return sorted(self.tdefs.keys())

    def create(self,data):
        tdg=TableDefinitionGenericItem()
        tdg.parse(data)
        m=re.match("^char(\d+)",tdg.datatype)
        if m:
            tdg.datatype='string'
            tdg.length=m.group(1)
        try:
            tdef=self.tdefs[tdg.datatype]()
            tdef.parse(data)
            return tdef
        except KeyError:
            return None

class TableDefinition(object):
    def __init__(self,filename=None):
        self.items = []
        self.loadJSON(filename)
        self.saved=False

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
                else:
                    raise TypeError(itemdata)
            # Define the number of Bytes to be loaded
            # assume to be total size - header size
            idx=self.findIndex("NumBytes")
            self.items[idx].defaultvalue=self.bytesSize()-struct.calcsize(HEADER_ENCODING)
            # Update Offset in bytes for each item
            self.setOffset()
        self.filename=filename
        self.saved=True

    def __len__(self):
        return len(self.items)

    def getTableName(self):
        return self.items[self.findIndex("TableName")].defaultvalue

    def findIndex(self,name):
        res=[i for i,item in enumerate(self.items) if item.name.lower()==name.lower()]
        return res[0] if len(res) else None

    def get(self,attr):
        return [getattr(item,attr) for item in self.items]

    def getdefaultvalues(self):
        return [item.defaultvalue for item in self.items]

    def bytesSize(self):
        return sum([item.bytesSize() for item in self.items])

    def setOffset(self):
        offset=0
        headersize=struct.calcsize(HEADER_ENCODING)
        for i in range(len(self.items)):
            self.items[i].offset=offset-headersize
            offset+=self.items[i].bytesSize()
        return True

    def reduceTo(self,offset,nbytes):
        partial=TableDefinition()
        if not nbytes:
            nbytes=self.items[self.findIndex("NumBytes")].defaultvalue
        totalbytes=0
        indexes=[]
        for idx,item in enumerate(self.items):
            if item.offset<0:
                partial.items.append(item)
                indexes.append(idx)
            elif (item.offset>=offset and (totalbytes+item.bytesSize())<=nbytes):
                partial.items.append(item)
                indexes.append(idx)
                totalbytes += item.bytesSize()
        partial.filename=self.filename
        idx = partial.findIndex("NumBytes")
        partial.items[idx].defaultvalue = partial.bytesSize() - struct.calcsize(HEADER_ENCODING)
        idx = partial.findIndex("Offset")
        partial.items[idx].defaultvalue = offset
        return partial,indexes

    def decode(self,buffer,bigendian=True):
        convention =">" if bigendian else "<"
        fmt=[convention]
        fmt.extend([item.encoding for item in self.items])
        data=list(struct.unpack("".join(fmt),buffer[:self.bytesSize()]))
        result=[]
        i=0
        for item in self.items:
            if item.datatype=="string":
                result.append(item.decode(data[i]))
                i+=1
            elif isinstance(item,TableDefinitionUint24Item):
                result.append(data[i])
                i+=2
            else:
                result.append(data[i])
                i+=1
        return result

    def encode(self,values,bigendian=True):
        convention =">" if bigendian else "<"
        buffer = bytearray()
        try:
            for item,value in zip(self.items,values):
                x=item.encode(value)
                if isinstance(item,TableDefinitionUint24Item):
                    buffer.extend(struct.pack(convention +item.encoding ,*x))
                else:
                    buffer.extend(struct.pack(convention + item.encoding, x))
            return buffer
        except struct.error:
            return None

    def decodeHeader(self,buffer,bigendian=True):
        convention =">" if bigendian else "<"
        header=convention+HEADER_ENCODING
        headersize=struct.calcsize(header)
        if len(buffer) >= headersize:
            data=list(struct.unpack(header,buffer[:headersize]))
            return data
        else:
            return None

    def decodeTableName(self,buffer,bigendian=True):
        data=self.decodeHeader(buffer,bigendian)
        return data[12].decode("utf-8").replace("\x00","") if data else None

    def decodeOffsetAndNumBytes(self,buffer,bigendian=True):
        data=self.decodeHeader(buffer,bigendian)
        return (data[10],data[11]) if data else None

    def __repr__(self):
        return '\n'.join(['{0}\t{1}'.format(item.name,item.defaultvalue) for item in self.items])

# TableManager
This python tool allows to manage cFE Table binary file as defined in cFS Framework https://github.com/nasa/cfs .
The TableManager tool is based on Table Definition JSON file, to decode and encode cFE Table as binary file.
The tool is coded in Python and request PyQt5 for the Graphical User Interface.

## Table Definition (.json file)
The following dictionary fields are expected, for each item of the table:
'''
{
"name"        : <item name (string)>,
**"datatype"    : <item data type (string)>,
**"defaultvalue": <item default value>,
**"description" : <item short description (string)>,
**"length"      : <item length (optional: default=1)>,
**"datarange"   : <item range (optional: list) or item enumerated values (optional: dict)>
**"editable"    : <item edit boolean (optional: default=1 True)>,
**"displaytype" : <item displaying mode (optional: "hex" to display in hex format>
}
'''

Available datatype
------------------
* "uint8" : unsigned integer 8 bits
* "uint16": unsigned integer 16 bits
* "uint32": unsigned integer 32 bits
* "uint64": unsigned integer 64 bits
* "int8"  : signed integer 8 bits
* "enum8" : enumerated values coded 8 bits
* "enum16": enumerated values coded 16 bits
* "enum32": enumerated values coded 32 bits
* "float" : floating value (32 bits)
* "double": floating value (64 bits)

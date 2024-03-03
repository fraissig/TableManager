# TableManager
This python tool allows to manage cFE Table binary file as defined in cFS Framework https://github.com/nasa/cfs .
The TableManager tool is based on Table Definition JSON file, to decode and to encode cFE Table as a binary file.
The tool is coded in Python (>=3.9) and requires PyQt5 for the Graphical User Interface.

## Menus
### *File Menu*
**> New TBL File** 
: create a new table based on table definition selected in the submenu

**> Open TBL File** 
: open an existing .tbl file and display it in a new tab

**> Save TBL File** 
: save the current table in a .tbl file

**> Save TBL File as...*** 
: same than save but allow to define a new name

**> Change Tables Definition directory** 
: allow to select a new directory containing all the tables definition (.json)

**> Quit** 
: Quit the application
### *Edit Menu*
**> Copy to clipboard** 
: copy the current table in the clipboard
### *Help Menu*
**> About** 
: display the application name and version

**> Help** 
: display the application help (this document)

**> Display log** 
: display the application logging file

## Table Definition (.json file)
TableManager requires the tables' definition (one json file per table).
The following dictionary fields are expected, for each item of the table:
```
{
"name"        : <item name (string)>,
"datatype"    : <item data type (string)>,
"defaultvalue": <item default value>,
"description" : <item short description (string)>,
"length"      : <item length (optional: default=1, required for string datatype)>,
"datarange"   : <item range (optional: list) or item enumerated values (optional: dict)>
"editable"    : <item edit boolean (optional: default=1 True)>,
"displaytype" : <item displaying mode (optional: "hex" to display in hex format>
}
```
The table definition JSON file shall include CFE File Primary Header and TBL Secondary Header.

Available datatype
------------------
* "uint8" : unsigned integer 8 bits
* "uint16": unsigned integer 16 bits
* "uint24": unsigned interger 24 bits 
* "uint32": unsigned integer 32 bits
* "uint64": unsigned integer 64 bits
* "int8"  : signed integer 8 bits
* "enum8" : enumerated values coded 8 bits
* "enum16": enumerated values coded 16 bits
* "enum32": enumerated values coded 32 bits
* "float16": floating value (16 bits)
* "float" : floating value (32 bits)
* "double": floating value (64 bits)
* "string": String with length to be defined

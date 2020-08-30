# Autopsy-filecarver
Python Module for Autopsy that carves files and slack space for embedded jpgs, bmps, pngs and gifs and adds them as derived files of the parent file 

Tested on Linux and Windows

When running the file carver module, there are 3 options to choose 

* Default mime types
* All files
* Include slack space

If choosing Default mime types, the module file type identification must first be ran. The Default mime types include 
"application/octet-stream","application/x-sqlite3", "application/vnd.ms-excel.sheet.4", "application/msword", "application/msoffice", "application/vnd.ms-excel", "application/vnd.ms-powerpoint"

If choosing All files it is not necessary to run the file type identication module prior to running the filecarver module with this option.

Running Include slack space can add considerable time 

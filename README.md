Genderize
=========

What Is This?
-------------

It is a script that will read in an excel sheet and spit out another one
after passing a bunch of names to [genderize.io](http://genderize.io/) which does the real work.

How Do I Run It?
----------------

    >> python genderize.py --file /path/to/my/excel_file.xls

There are some variables in `genderize.py` you may want to alter.

Changing Some Settings
----------------------

`NAME_COLUMN`: The column in the excel sheet that holds the name to be read. 
0 maps to column A, 1 maps to column B, etc.

    NAME_COLUMN = 1

`PROBABILITY`: The minimum probability needed to assign a gender. Use an integer from 0 to 100.

    PROBABILITY = 95

`WRITE_COLUMN`: The column that results will be written in (male as M and female as F). Only blank fields will be written into. If you already have gender data in a field it will not be overwritten.
0 maps to column A, 1 maps to column B, etc.

    WRITE_COLUMN = 13


*NOTE:* You will need some python packages to run this. Easiest way to get them is to install using `pip`.

    >> pip install xlrd xlwt requests

If you do not have `pip` easiest way to install `pip` is with `easy_install`.

    >> sudo easy_install pip

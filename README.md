Genderize
=========

What Is This?
-------------

It is a script that will read in an excel sheet and spit out another one
after passing a bunch of names to [genderize.io](http://genderize.io/) which does the real work.

How Do I Run It?
----------------

    >> python genderize.py --file /path/to/my/excel_file.xls


This will read column B of each row in `excel_file.xls` and add a cell on the end of the row if the probability of 
the results being correct are at least 95%.


Options
-------

You can pass optional arguments `-r`, `-w`, and `-p`.

`-r` read column: The column in the excel sheet that hold the name to be read
        0 = column A, 1 = column B, etc.
        
`-w` write column: The column that results will be written into (male as M and female as F).
        0 = column A, 1 = column B, etc.
        If nothing is passed a column will be appended to the end of rows.
        
`-p` minimum probability: The minimum probability needed to assign a gender. An integer from 0 to 100.
        Default is 95.

Example usage:

    >> python genderize.py --file /path/to/my/excel_file.xls -p 80 -r 5 -w 13



*NOTE:* You will need some python packages to run this. Easiest way to get them is to install using `pip`.

    >> pip install xlrd xlwt requests

If you do not have `pip` easiest way to install `pip` is with `easy_install`.

    >> sudo easy_install pip

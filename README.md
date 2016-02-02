Genderize
=========

What Is This?
-------------

It is a script that will read in an csv sheet and save results
after passing a bunch of names to [genderize.io](http://genderize.io/) which does the real work.

How Do I Run It?
----------------

    >> python genderize.py --file /path/to/my/excel_file.xls

This will read from the `name` column of the csv and check the genderize.io
The results will be saved to a SQLite database `genderize.db`.


*NOTE:* You will need some python packages to run this. Easiest way to get them is to install using `pip`.

    >> pip install requests

If you do not have `pip` easiest way to install `pip` is with `easy_install`.

    >> sudo easy_install pip

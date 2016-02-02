Genderize
=========

What Is This?
-------------

It is a script that will read in a csv of names, pass them to [genderize.io](http://genderize.io/) and then save the results to a SQLite db so you can out put them however you like.

How Do I Run It?
----------------

    >> python genderize.py --file /path/to/my/csv_file.csv

This will read from the `name` column of the csv.
The results will be saved to a SQLite database `genderize.db`.


*NOTE:* You will need some python packages to run this. Easiest way to get them is to install using `pip`.

    >> pip install requests

If you do not have `pip` easiest way to install `pip` is with `easy_install`.

    >> sudo easy_install pip

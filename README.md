IFT_Forks_Classifier
====================

This program is written to extract information from the IFT Forks database in a way that can be read by Weka.

The Github repository location for this file is at:

https://github.com/IrwinKwan/IFT_Forks_FeatureGenerator

Prerequisites
-------------

* Python 2.7

* Python's SQLite connector (which I think comes installed by default)

* The ift_forks.sqlite DB. This is currently private access on OSU servers. Talk to me if you're one of our research collaborators and need access.

What this does
--------------

The script ```ift_forks_featuregather.py``` reads from the SQLite database (see the Constants) and creates an ARFF file for use with WEKA.

How do I use this?
------------------

Look at the "Constants" class and set the constants for how you want the run's parameters to look like.

On a console, type:

```python ift_forks_featuregather.py```

The result is a file named ```ift_features-_-_DATE.arff``` (that has the current date as part of the filename).

Now, you can use the WEKA Explorer to open the ARFF file.

Why is it so slow?
------------------

I didn't spent a lot of time optimizing SQL queries. If you want to help optimize them, that would be great, but it just wasn't really a priority.


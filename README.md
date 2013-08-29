IFT_Forks_Classifier
====================

This program is written to extract information from the IFT Forks database in a way that can be read by Weka.

Irwin's currently working on this with Chris Scaffidi's help.

Prerequisites
-------------

* Python 2.7

* Python's SQLite connector (which I think comes installed by default)

* The ift_forks.sqlite DB from nome.eecs.oregonstate.edu:/nfs/guille/burnett/iftdata/chi2014/analysis/IFT_Forks_DB.git

What this does
--------------

The script ```ift_forks_classifier.py``` reads from the SQLite database (see the Constants) and creates an ARFF file for use with WEKA.

How do I use this?
------------------

On a console, type:

```python ift_forks_classifier.py```

The result is a file named ```ift_features-_-_DATE.arff``` (that has the current date as part of the filename).

Now, you can use the WEKA Explorer to open the ARFF file.

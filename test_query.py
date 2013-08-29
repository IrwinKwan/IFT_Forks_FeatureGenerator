#!/usr/bin/env python

import os
import datetime
import sqlite3
from collections import OrderedDict


class Constants:
    DB = os.path.join('..', 'IFT_Forks_DB', 'ift_forks.sqlite')
    OUTFILE = "ift_features-" + datetime.datetime.now().strftime("_-_%Y-%m-%d_%H%M") + ".arff"
    NAME = "iftforks"
    BEFORE = -60
    FORKSTART = 0
    FORKEND = 30
    AFTER = 60


class Groups:
    search = ['org.eclipse.ui.edit.findNext',
        'org.eclipse.search.ui.performTextSearchFile',
        'org.eclipse.search.ui.openSearchDialog',
        'org.eclipse.search.ui.openFileSearchPage',
        'org.eclipse.search.ui.performTextSearchFile',
        'org.eclipse.search.ui.performTextSearchWorkspace',
        'org.eclipse.jdt.ui.edit.text.java.search.declarations.in.project',
        'org.eclipse.jdt.ui.edit.text.java.search.declarations.in.workspace',
        'org.eclipse.jdt.ui.edit.text.java.search.references.in.project',
        'org.eclipse.jdt.ui.edit.text.java.search.references.in.workspace']


def confirmed_forks(c):
    forks_query = "SELECT participant, videotime, retrospective, forks FROM codes \
        WHERE (retrospective <> '')"
    return c.execute(forks_query)

def exists_search_before_open(conn, c, fork_row, start, after):
    exists = False

    q = "SELECT * FROM commands WHERE \
        eclipsecommand = ? \
        AND EXISTS \
            (SELECT videotime FROM  \
                (SELECT videotime FROM codes WHERE \
                (participant = ? and videotime = ?)) \
            AS times \
            WHERE strftime('%s', commands.videotime) - strftime('%s', times.videotime) >= ?  \
            AND strftime('%s', commands.videotime) - strftime('%s', times.videotime) <= ? \
            AND participant = ?)"

    r = "SELECT * FROM commands WHERE command = 'FileOpenCommand' \
        AND strftime('%s', commands.videotime) - strftime('%s', ?) > 0 \
        AND strftime('%s', commands.videotime) - strftime('%s', ?) < 30"

    for i in Groups.search:
        result_set_forks = c.execute(q, (i,
            fork_row['participant'], fork_row['videotime'],
            start, after,
            fork_row['participant']))

        for j in result_set_forks:
            search_time = j['videotime']
            
            result_set_opens = c.execute(r, (search_time, fork_row['videotime']))
            for k in result_set_opens:
                exists = True

    return exists

if __name__ == "__main__":
    conn = sqlite3.connect(Constants.DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    for row in confirmed_forks(c):
        print exists_search_before_open(conn, conn.cursor(), row, -60, 0)


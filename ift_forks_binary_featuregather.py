#!/usr/bin/env python
"""Creates an ARFF file for use in WEKA based on the features in the
commands and the codes SQLite database.

This particular classifier makes "binary" features where we test
for existence or non-existence of a command Constants.BEFORE seconds before a fork."""

import os
import datetime
import sqlite3
from collections import OrderedDict


class Constants:
    DB = os.path.join('..', 'IFT_Forks_DB', 'ift_forks.sqlite')
    OUTFILE = "ift_features-" + datetime.datetime.now().strftime("_-_%Y-%m-%d_%H%M") + ".arff"
    NAME = "iftforks"
    BEFORE = -60 # in seconds
    FORKSTART = 0 # in seconds
    FORKEND = 30 # in seconds
    AFTER = 60 # in seconds


class Groups:
    search = ['org.eclipse.ui.edit.findNext',
        'org.eclipse.search.ui.performTextSearchFile',
        'org.eclipse.search.ui.openSearchDialog',
        'org.eclipse.search.ui.openFileSearchPage',
        'org.eclipse.search.ui.performTextSearchFile',
        'org.eclipse.search.ui.performTextSearchWorkspace',
        'org.eclipse.jdt.ui.edit.text.java.search.declarations.in.project',
        'org.eclipse.jdt.ui.edit.text.java.search.declarations.in.workspace'
    ]

    debugging_eclipsecommands = ["org.eclipse.debug.ui.commands.DebugLast",
        "org.eclipse.debug.ui.commands.Resume",
        "org.eclipse.debug.ui.commands.RunLast",
        "org.eclipse.debug.ui.commands.StepInto",
        "org.eclipse.debug.ui.commands.StepOver",
        "org.eclipse.debug.ui.commands.StepReturn",
        "org.eclipse.jdt.ui.JavaPerspective"]


def num_to_bool(number):
    if number == 0:
        return False
    elif number > 0:
        return True
    else:
        raise Exception("A natural number is less than 0 is being converted to a bool.")
        return None

def confirmed_forks(c):
    forks_query = "SELECT participant, videotime, retrospective, forks FROM codes \
        WHERE (retrospective <> '')"
    return c.execute(forks_query)


def time_range(c, event, start, after):
    range_query = "SELECT COUNT(*) FROM commands WHERE EXISTS \
        ( SELECT videotime FROM \
            (SELECT videotime FROM codes WHERE \
            (retrospective ='y' AND forks > 0)) AS times \
        WHERE strftime('%s', commands.videotime) - strftime('%s', times.videotime) >= -? \
        AND strftime('%s', commands.videotime) - strftime('%s', times.videotime) <= ?)"
    return c.execute(range_query, (start, after))


def num_commands_at_fork(c, fork_row, event, start, after):
    q = "SELECT COUNT(*) FROM commands WHERE \
        command = ? \
        AND EXISTS \
            (SELECT videotime FROM  \
                (SELECT videotime FROM codes WHERE \
                (participant = ? and videotime = ?)) \
            AS times \
            WHERE strftime('%s', commands.videotime) - strftime('%s', times.videotime) >= ?  \
            AND strftime('%s', commands.videotime) - strftime('%s', times.videotime) <= ? \
            AND participant = ?)"

    return c.execute(q, (event,
        fork_row['participant'], fork_row['videotime'],
        start, after,
        fork_row['participant'])).fetchone()[0]


def num_eclipsecommands_at_fork(c, fork_row, event, start, after):
    q = "SELECT COUNT(*) FROM commands WHERE \
        eclipsecommand = ? \
        AND EXISTS \
            (SELECT videotime FROM  \
                (SELECT videotime FROM codes WHERE \
                (participant = ? and videotime = ?)) \
            AS times \
            WHERE strftime('%s', commands.videotime) - strftime('%s', times.videotime) >= ?  \
            AND strftime('%s', commands.videotime) - strftime('%s', times.videotime) <= ? \
            AND participant = ?)"

    return c.execute(q, (event,
        fork_row['participant'], fork_row['videotime'],
        start, after,
        fork_row['participant'])).fetchone()[0]

def num_search_before_select(c, fork_row, start, after):
    exists = 0

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

    r = "SELECT * FROM commands WHERE command = 'SelectTextCommand' \
        AND strftime('%s', commands.videotime) - strftime('%s', ?) > 0 \
        AND strftime('%s', commands.videotime) - strftime('%s', ?) < ?"

    for i in Groups.search:
        result_set_forks = c.execute(q, (i,
            fork_row['participant'], fork_row['videotime'],
            start, after,
            fork_row['participant']))

        for j in result_set_forks:
            search_time = j['videotime']
            
            result_set_opens = c.execute(r, (search_time, fork_row['videotime'], after))
            for k in result_set_opens:
                exists += 1

    return exists

def num_search_before_open(c, fork_row, start, after):
    exists = 0

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
        AND strftime('%s', commands.videotime) - strftime('%s', ?) < ?"

    for i in Groups.search:
        result_set_forks = c.execute(q, (i,
            fork_row['participant'], fork_row['videotime'],
            start, after,
            fork_row['participant']))

        for j in result_set_forks:
            search_time = j['videotime']
            
            result_set_opens = c.execute(r, (search_time, fork_row['videotime'], after))
            for k in result_set_opens:
                exists += 1

    return exists


def num_commands_before(c, fork_row, event):
    """Finds the specified commands that occur 60 seconds before the start of the fork segment
    (that is, the two segments before the fork segment)."""
    return num_commands_at_fork(c, fork_row, event, -60, 0)


def num_commands_after(c, fork_row, event):
    """Finds the specified commands that occur 60 seconds after the start of the fork segment (that is,
    the fork segment itself and the next segment after.)"""
    return num_commands_at_fork(c, fork_row, event, 0, 60)

def num_eclipsecommands_before(c, fork_row, event):
    """Finds the specified commands that occur 60 seconds before the start of the fork segment
    (that is, the two segments before the fork segment)."""
    return num_eclipsecommands_at_fork(c, fork_row, event, -60, 0)


def num_eclipsecommands_after(c, fork_row, event):
    """Finds the specified commands that occur 60 seconds after the start of the fork segment (that is,
    the fork segment itself and the next segment after.)"""
    return num_eclipsecommands_at_fork(c, fork_row, event, 0, 60)


def num_editing_before(c, fork_row):
    """Finds the commands related to editing before the fork"""
    b = Constants.BEFORE
    a = Constants.FORKEND
    return num_commands_at_fork(c, fork_row, 'Insert', b, a) \
        + num_commands_at_fork(c, fork_row, 'Delete', b, a) \
        + num_commands_at_fork(c, fork_row, 'Replace', b, a) \
        + num_commands_at_fork(c, fork_row, 'UndoCommand', b, a)


def num_editing_after(c, fork_row):
    """Finds the commands related to editin after the fork"""
    b = Constants.FORKEND
    a = Constants.AFTER
    return num_commands_at_fork(c, fork_row, 'Insert', b, a) \
        + num_commands_at_fork(c, fork_row, 'Delete', b, a) \
        + num_commands_at_fork(c, fork_row, 'Replace', b, a) \
        + num_commands_at_fork(c, fork_row, 'UndoCommand', b, a)    

def num_debugging_before(c, fork_row):
    b = Constants.BEFORE
    a = Constants.FORKEND

    total = 0
    for i in Groups.debugging_eclipsecommands:
        total += num_eclipsecommands_at_fork(c, fork_row, i, b, a)

    return total

def num_debugging_after(c, fork_row):
    b = Constants.FORKEND
    a = Constants.AFTER

    total = 0
    for i in Groups.debugging_eclipsecommands:
        total += num_eclipsecommands_at_fork(c, fork_row, i, b, a)    

    return total

def event_ordering(c, fork_row):
    pass

class ForkException(Exception):
    pass


def num_searching_before(c, fork_row):
    """Finds the commands related to editing before the fork"""
    b = Constants.BEFORE
    a = Constants.FORKEND
    
    total = 0
    for i in Groups.search:
        total += num_eclipsecommands_at_fork(c, fork_row, i, b, a)

    return total


def num_searching_after(c, fork_row):
    """Finds the commands related to editin after the fork"""
    b = Constants.FORKEND
    a = Constants.AFTER

    total = 0
    for i in Groups.search:
        total += num_eclipsecommands_at_fork(c, fork_row, i, b, a)

    return total


def coded_as_fork(fork_row):
    if (fork_row['forks'] > 0 and fork_row['retrospective'] == 'y'):
        #return "TrueFork"
        return "Fork"
    elif (fork_row['forks'] == 0 and fork_row['retrospective'] == 'n'):
        #return "HiddenFork"
        return "Fork"
    elif (fork_row['forks'] > 0 and fork_row['retrospective'] == 'n'):
        #return "FakeFork"
        return "NotFork"
    elif (fork_row['forks'] == 0 and fork_row['retrospective'] == 'y'):
        #return "NotFork"
        return "NotFork"
    else:
        raise ForkException("Fork conditions appear incorrect. Please check it!\n\t%s" % fork_row)

def gather_features(c, fork_row):
    # participant = str(fork_row['participant'])
    # videotime = fork_row['videotime']

    attributes = [
        # participant,
        # videotime,
        num_to_bool(num_commands_before(c, fork_row, 'FileOpenCommand')),
        num_to_bool(num_commands_after(c, fork_row, 'FileOpenCommand')),
        num_commands_before(c, fork_row, 'SelectTextCommand'),
        num_commands_after(c, fork_row, 'SelectTextCommand'),
        num_editing_before(c, fork_row),
        num_editing_after(c, fork_row),
        num_searching_before(c, fork_row),
        num_searching_after(c, fork_row),
        num_eclipsecommands_before(c, fork_row, 'org.eclipse.jdt.ui.edit.text.java.search.references.in.workspace') \
            + num_eclipsecommands_before(c, fork_row, 'org.eclipse.jdt.ui.edit.text.java.search.references.in.project'),
        num_eclipsecommands_after(c, fork_row, 'org.eclipse.jdt.ui.edit.text.java.search.references.in.workspace') \
            + num_eclipsecommands_before(c, fork_row, 'org.eclipse.jdt.ui.edit.text.java.search.references.in.project'),
        num_debugging_before(c, fork_row),
        num_debugging_after(c, fork_row),
        num_commands_before(c, fork_row, 'RunCommand'),
        num_commands_after(c, fork_row, 'RunCommand'),
        num_search_before_open(c, fork_row, Constants.BEFORE, Constants.FORKEND),
        num_search_before_select(c, fork_row, Constants.FORKEND, Constants.AFTER)
    ]

    output = ""
    for attribute in attributes:
        output += str(attribute) + ","
    output += " "
    
    # for attribute1 in range(0, len(attributes)):
    #     for attribute2 in range(attribute1 + 1, len(attributes)):
    #         output += str(attributes[attribute1] + attributes[attribute2]) + ","
    #     output += " "

    output += str(coded_as_fork(fork_row)) + "\n"
    return output


def header():
    output = "@RELATION " + Constants.NAME + "\n\n"

    relations = OrderedDict()
    # relations['participant'] = 'STRING'
    # relations['videotime'] = 'STRING'

    relations['opens_before'] = '{True, False}'
    relations['opens_after'] = '{True, False}'
    relations['selects_before'] = 'NUMERIC'
    relations['selects_after'] = 'NUMERIC'
    relations['edits_before'] = 'NUMERIC'
    relations['edits_after'] = 'NUMERIC'
    relations['searching_before'] = 'NUMERIC'
    relations['searching_after'] = 'NUMERIC'
    relations['references_before'] = 'NUMERIC'
    relations['references_after'] = 'NUMERIC'
    relations['debugging_before'] = 'NUMERIC'
    relations['debugging_after'] = 'NUMERIC'
    relations['runs_before'] = 'NUMERIC'
    relations['runs_after'] = 'NUMERIC'
    relations['exists_search_before_open'] = 'NUMERIC'
    relations['exists_search_before_select'] = 'NUMERIC'

    #relations['real_fork'] = '{Fork, NotFork}'

    # TrueFork: coded as fork and retrospective agrees
    # HiddenFork: not coded as fork and retrospective disagrees
    # FakeFork: coded as fork and retrospective disagrees
    # NotFork: not coded as fork and retrospective agrees

    for k,v in relations.iteritems():
        output += "@ATTRIBUTE " + k + " " + v + "\n"
    output += "\n"

    # keys = relations.keys()
    # for k1 in range(0, len(keys)):
    #     for k2 in range(k1 + 1, len(keys)):

    #         output += "@ATTRIBUTE " + keys[k1] + "-plus-" + keys[k2] + " " + relations[keys[k2]] + "\n"
    #     output += "\n"

    # output += "@ATTRIBUTE real_fork {Fork, TrueFork, HiddenFork, FakeFork, NotFork}"
    output += "@ATTRIBUTE real_fork {Fork, NotFork}"
    
    output += "\n\n@DATA\n"

    return output

if __name__ == "__main__":
    conn = sqlite3.connect(Constants.DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    with open(Constants.OUTFILE, 'w') as f:
        output = header()
        for row in confirmed_forks(c):
            # print row
            output += gather_features(conn.cursor(), row)

        print output
        f.write(output)


#!/usr/bin/env python
"""Creates an ARFF file for use in WEKA based on the features in the
commands and the codes SQLite database.

This particular classifier creates features where we test numbers of instances
before/after a fork."""

import os
import datetime
import sqlite3
from collections import OrderedDict


class Constants:
    """Constants for this program"""
    DB = os.path.join('..', 'IFT_Forks_DB', 'ift_forks.sqlite')
    OUTFILE = "ift_features-count-" + datetime.datetime.now().strftime("_-_%Y-%m-%d_%H%M") + ".arff"
    NAME = "iftforks"
    BEFORE = -180
    FORKSTART = 0
    FORKEND = 30
    AFTER = 30

    """Whether to output the attribute counts as binned nominal data"""
    CATEGORY = True

    """Whether to output the attribute counts as boolean nominal data"""
    BINARY = True

    """Whether to include two-factor interactions"""
    TWO_FACTOR = False


class Groups:
    """Groups create a grouping of various events, for example, things that are searches, or debugging, etc."""
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
    """Converts a number to a boolean, used to make a count into a exists/not exists."""
    if number == 0:
        return False
    elif number > 0:
        return True
    else:
        raise Exception("A natural number less than 0 is being converted to a bool.")
        return None

def num_to_categories(number, category_map = None):
    """Convert a number to a bin, used to make into a category.
    A bin_table is an OrderedDict of the actual range mapped to the result."""

    if category_map == None:
        category_map = {0: "None", 1: "Few", 5: "Some", 9: "Many", 12: "Lots"}

    for a_range in sorted(category_map.iterkeys()):

        # Fix 16 isn't showing up as 'Lots' (in row 5)
        if number > a_range:
            pass
        else:
            return category_map[a_range]

    if number > max(category_map.keys()):
        return category_map[max(category_map.keys())]
    else:
        return category_map[0]

def confirmed_forks(c):
    """Gets a list of forks that have a retrospective entry."""
    forks_query = "SELECT participant, videotime, retrospective, forks FROM codes \
        WHERE (retrospective <> '')"
    return c.execute(forks_query)


def num_commands_at_fork(c, fork_row, event, start, after):
    """Gets the number of commands for a specified Command event 'start' seconds before the fork and 'after' seconds after the
    start of the fork."""
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
    """Gets the number of commands for a specified EclipseCommand event 'start' seconds before the fork and 'after' seconds after the
    start of the fork."""
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
    """Counts the number of SelectTextCommands that occur after a search before a fork."""
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
    """Counts the number of FileOpenCommands that occur after a search before a fork."""
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
    """Debugging commands before a fork"""
    b = Constants.BEFORE
    a = Constants.FORKEND

    total = 0
    for i in Groups.debugging_eclipsecommands:
        total += num_eclipsecommands_at_fork(c, fork_row, i, b, a)

    return total

def num_debugging_after(c, fork_row):
    """Debugging commands after a fork"""
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
    """How the fork is coded"""
    if (fork_row['forks'] > 0 and fork_row['retrospective'] == 'y'):
        #return "TrueFork" # True because everyone agreed that it's a fork
        return "Fork"
    elif (fork_row['forks'] == 0 and fork_row['retrospective'] == 'n'):
        #return "HiddenFork" # Hidden because the participant thought it was a fork, but it was hidden from our coders
        return "Fork"
    elif (fork_row['forks'] > 0 and fork_row['retrospective'] == 'n'):
        #return "FakeFork" # Fake because the coders thought it was a fork, but it was fake as announced by the participant
        return "NotFork"
    elif (fork_row['forks'] == 0 and fork_row['retrospective'] == 'y'):
        #return "NotFork" # NotFork because everyone agreed that it isn't a fork
        return "NotFork"
    else:
        raise ForkException("Fork conditions appear incorrect. Please check it!\n\t%s" % fork_row)


def make_features_into_categories(attributes):
    categories = []
    for attribute in attributes:
        categories.append(num_to_categories(attribute))
    return categories

def make_features_into_booleans(attributes):
    booleans = []
    for attribute in attributes:
        booleans.append(num_to_bool(attribute))
    return booleans

def gather_features(c, fork_row):
    """A list of the features"""
    # participant = str(fork_row['participant'])
    # videotime = fork_row['videotime']

    attributes = [
        # participant,
        # videotime,
        num_commands_before(c, fork_row, 'FileOpenCommand'),
        num_commands_after(c, fork_row, 'FileOpenCommand'),
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
        num_search_before_select(c, fork_row, Constants.FORKEND, Constants.AFTER),
    ]

    # Gather all of the attributes again, but put them into categories.
    categories = []
    if Constants.CATEGORY:
        categories += make_features_into_categories(attributes)

    booleans = []
    if Constants.BINARY:
        booleans += make_features_into_booleans(attributes) 

    if Constants.CATEGORY:
        attributes += categories

    if Constants.BINARY:
        attributes += booleans

    return attributes

def main_effects(attributes):
    output = ""
    for attribute in attributes:
        output += "%2s," % str(attribute)
    output += " "
    return output

def two_factor_effects(attributes):
    output = ""
    for attribute1 in range(0, len(attributes)):
        for attribute2 in range(attribute1 + 1, len(attributes)):
            output += "%2s," % (str(attributes[attribute1] + attributes[attribute2]))
        output += " "
    return output

def response_variable(fork_row):
    output = ""
    output += str(coded_as_fork(fork_row)) + "\n"
    return output

def features_to_datatable(attributes, fork_row):
    output = ""
    output += main_effects(attributes)

    if Constants.TWO_FACTOR:
        output += two_factor_effects(attributes)

    output += response_variable(fork_row)
    return output    


def _header_main_effects(relations):
    output = ""
    for k,v in relations.iteritems():
        output += "@ATTRIBUTE " + k + " " + v + "\n"
    output += "\n"
    return output

def _header_categories(relations):
    """For each attribute, output the version that is a categorical variable."""
    output = ""
    for k,v in relations.iteritems():
        output += "@ATTRIBUTE " + 'category__' + k + " " + '{None,Few,Some,Many,Lots}' + "\n"
    output += "\n"
    return output

def _header_binary(relations):
    """For each attribute, output the version that is a categorical variable."""
    output = ""
    for k,v in relations.iteritems():
        output += "@ATTRIBUTE " + 'binary__' + k + " " + '{True,False,None}' + "\n"
    output += "\n"
    return output

def _header_two_factor_effects(relations):
    output = ""
    keys = relations.keys()
    for k1 in range(0, len(keys)):
        for k2 in range(k1 + 1, len(keys)):
            output += "@ATTRIBUTE " + keys[k1] + "-plus-" + keys[k2] + " " + relations[keys[k2]] + "\n"
        output += "\n"
    return output

def _header_response_variable():
    # TrueFork: coded as fork and retrospective agrees
    # HiddenFork: not coded as fork and retrospective disagrees
    # FakeFork: coded as fork and retrospective disagrees
    # NotFork: not coded as fork and retrospective agrees

    # previously was "@ATTRIBUTE real_fork {Fork, TrueFork, HiddenFork, FakeFork, NotFork}"
    return "@ATTRIBUTE real_fork {Fork, NotFork}"

def header():
    """Outputs the ARFF header. If you change the features in gather_features, you have to change the
    header as well and add the relations."""
    output = "@RELATION " + Constants.NAME + "\n\n"

    relations = OrderedDict()
    # relations['participant'] = 'STRING'
    # relations['videotime'] = 'STRING'
    relations['opens_before'] = 'NUMERIC'
    relations['opens_after'] = 'NUMERIC'
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

    output += _header_main_effects(relations)

    if Constants.CATEGORY:
        output += _header_categories(relations)

    if Constants.BINARY:
        output += _header_binary(relations)        

    if Constants.TWO_FACTOR:
        output += _header_two_factor_effects(relations) 

    output += _header_response_variable()

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
            features = gather_features(conn.cursor(), row)
            output += features_to_datatable(features, row)

        print output
        f.write(output)


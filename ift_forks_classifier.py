#!/usr/bin/env python

import os
import datetime
import sqlite3


class Constants:
    DB = os.path.join('..', 'IFT_Forks_DB', 'ift_forks.sqlite')
    OUTFILE = "ift_features-" + datetime.datetime.now().strftime("_-_%Y-%m-%d_%H%M") + ".txt"


def confirmed_forks(c):
    forks_query = "SELECT participant, videotime, retrospective, forks FROM codes \
        WHERE (forks > 0 and retrospective = 'y') \
        or (forks = 0 and retrospective = 'n') \
        or (forks > 0 and retrospective ='n')"
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


def num_commands_before(c, fork_row, event):
    """Finds the specified commands that occur 60 seconds before the start of the fork segment
    (that is, the two segments before the fork segment)."""
    return num_commands_at_fork(c, fork_row, event, -60, 0)


def num_commands_after(c, fork_row, event):
    """Finds the specified commands that occur 60 seconds after the start of the fork segment (that is,
    the fork segment itself and the next segment after.)"""
    return num_commands_at_fork(c, fork_row, event, 0, 60)


class ForkException(Exception):
    pass


def coded_as_fork(fork_row):
    if (fork_row['forks'] > 0 and fork_row['retrospective'] == 'y') \
        or (fork_row['forks'] == 0 and fork_row['retrospective'] == 'n'):
        return True
    elif (fork_row['forks'] > 0 and fork_row['retrospective'] == 'n'):
        return False
    else:
        raise ForkException("Fork conditions appear incorrect. Please check it!\n\t%s" % fork_row)

def gather_features(c, fork_row):
    return "p%d@%s, %d, %d, %d, %d, %s\n" % (fork_row['participant'], fork_row['videotime'],
    num_commands_before(c, fork_row, 'FileOpenCommand'),
    num_commands_after(c, fork_row, 'FileOpenCommand'),
    num_commands_before(c, fork_row, 'SelectTextCommand'),
    num_commands_after(c, fork_row, 'SelectTextCommand'),
    str(coded_as_fork(fork_row)))



def header():
    return "participant_fork, opens_before, opens_after, selects_before, selects_after, real_fork\n"

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


#!/usr/bin/env python

import os
import sqlite3

class Constants:
    DB = os.path.join('..', 'IFT_Forks_DB', 'ift_forks.sqlite')


def forks(c, num_forks, retrospective_agreement):
	forks_query = "SELECT participant, videotime FROM coding WHERE (forks > ? AND retrospective ='?')"

	return c.execute(forks_query, (num_forks, retrospective_agreement)


def range(c, start, after):
	range_query = "SELECT COUNT(*) FROM commands WHERE EXISTS \
      	( SELECT videotime FROM (SELECT videotime FROM codes WHERE \
            AND (retrospective ='y' AND forks > 0)) AS times \
        	WHERE strftime('%s', commands.videotime) - strftime('%s', times.videotime) >= -? \
            AND strftime('%s', commands.videotime) - strftime('%s', times.videotime) <= ?)"

	return c.execute(range_query, (start, after)

class Feature:
	def __init__(self):
		pass


if __name__ == "__main__":
    conn = sqlite3.connect(Constants.DB)

    c = conn.cursor()

    t = (3, )
    for row in forks(c, -60, 0):
    	print row


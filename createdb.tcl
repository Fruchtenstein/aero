#!/usr/bin/tclsh

package require sqlite3

sqlite3 db aerobia.db
db eval {CREATE TABLE teams (teamid INTEGER PRIMARY KEY, teamname)}
db eval {CREATE TABLE runners (runnerid INTEGER PRIMARY KEY, runnername, teamid INTEGER, goal REAL, isill BOOLEAN NOT NULL DEFAULT 0)}
db eval {CREATE TABLE log (runnerid INTEGER, date, distance REAL, time, type, PRIMARY KEY(runnerid, date));}
db eval {CREATE TABLE wlog (runnerid INTEGER, week INTEGER, distance REAL, PRIMARY KEY(runnerid, week))}
db eval {CREATE TABLE tlog (teamid INTEGER, week INTEGER, pts INTEGER, result REAL)}
db eval {INSERT INTO teams values (1, "раз")}
db eval {INSERT INTO teams values (2, "два")}
db eval {INSERT INTO teams values (3, "три")}
db eval {INSERT INTO teams values (4, "четыре")}
#db eval {INSERT INTO runners values (19999, 1, 4500.0)}
#db eval {INSERT INTO runners values (40, 2, 2750.0)}
#db eval {INSERT INTO runners values (31319, 3, 3500.0)}

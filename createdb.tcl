#!/usr/bin/tclsh

package require sqlite3

sqlite3 db aerobia.db
db eval {CREATE TABLE teams (teamid INTEGER PRIMARY KEY, teamname)}
db eval {CREATE TABLE runners (runnerid INTEGER PRIMARY KEY, teamid INTEGER, goal REAL)}
db eval {CREATE TABLE log (runnerid INTEGER, week INTEGER, distance REAL, PRIMARY KEY(runnerid, week))}
db eval {INSERT INTO teams values (1, "Мурзилки")}
db eval {INSERT INTO teams values (2, "Веселые картинки")}
db eval {INSERT INTO teams values (3, "Крокодилы")}
db eval {INSERT INTO teams values (4, "Ленивые тюлени")}
#db eval {INSERT INTO runners values (19999, 1, 4500.0)}
#db eval {INSERT INTO runners values (40, 2, 2750.0)}
#db eval {INSERT INTO runners values (31319, 3, 3500.0)}

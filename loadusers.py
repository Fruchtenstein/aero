#!/usr/bin/python3

import csv
import sqlite3

db = sqlite3.connect("aerobia.db")
c = db.cursor()
f = open('users.csv')
reader = csv.reader(f)
for row in reader:
    userid = int(row[1])
    teamid = (userid % 3) + 1
    goal = float(row[3])
    print(userid)
    print(teamid)
    print(goal)
    c.execute("INSERT OR REPLACE INTO runners VALUES (?, ?, ?)", (userid, teamid, goal))
db.commit()
db.close()
f.close()

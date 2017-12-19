#!/usr/bin/python3

import csv
import sqlite3

db = sqlite3.connect('aerobia.db')
c = db.cursor()
nofteams = 4
teams = [[],[],[],[]]
goals = [0,0,0,0]
f = open('users.csv')
reader = csv.reader(f)
for i, row in enumerate(reader):
    if i in range(0,3):
        teams[i].append([row[2], row[1], row[3]])
        goals[i] += float(row[3])
    else:
        goesto = goals.index(min(goals))
        teams[goesto].append([row[2], row[1], row[3]])
        goals[goesto] += float(row[3])

print("===========")
for i, t in enumerate(teams):
    print ("Команда {} (цель: {:.2f}):".format(i+1, goals[i]/52))
    print ("==========")
    for r in t:
        print(r[0], r[1], r[2])
        c.execute('INSERT OR REPLACE INTO runners  VALUES (?, ?, ?, ?)', (r[1], r[0], i+1, r[2]))
    print("")
db.commit()
db.close()
f.close()

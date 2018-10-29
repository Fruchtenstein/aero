#!/usr/bin/python3

from urllib.request import urlopen,Request
import datetime
import dateutil.parser
import pytz
import sqlite3
import os
import re
import requests
import lxml.etree


def week_range(date):
    utc=pytz.UTC
    year, week, dow = date.isocalendar()
    start_date = date - datetime.timedelta(dow-1)
    end_date = start_date + datetime.timedelta(6)
    return (week, utc.localize(datetime.datetime.combine(start_date, datetime.datetime.min.time())), utc.localize(datetime.datetime.combine(end_date, datetime.datetime.max.time())))

def parseuser(runnerid, date, session):
    weekrange = week_range(date)
    db = sqlite3.connect('aerobia.db')
    c2 = db.cursor()
    c2.execute("DELETE FROM log WHERE runnerid=? AND date>? AND date<?", (runnerid, weekrange[1].isoformat(), weekrange[2].isoformat()))
    goal = c2.execute("SELECT wplan*52 FROM wlog WHERE runnerid=? AND week=?", (runnerid, weekrange[0])).fetchone()[0]
    db.commit()
    db.close()
    dataurl = "http://aerobia.ru/api/users/{}/calendar/{}/{:02d}".format(runnerid, weekrange[2].year, weekrange[2].month)
    getdata(runnerid, date, session, dataurl, goal)
    if weekrange[1].month < weekrange[2].month:
        dataurl = "http://aerobia.ru/api/users/{}/calendar/{}/{:02d}".format(runnerid, weekrange[1].year, weekrange[1].month)
        getdata(runnerid, date, session, dataurl, goal)


def getdata(runnerid, date, session, dataurl, goal):
    weekrange = week_range(date)
    print("requesting "+dataurl)
    r = session.get(dataurl)
    xml = r.content
    root = lxml.etree.fromstring(xml)
    workouts = root.findall('.//r')
    for w in workouts:
#        print("  ---- workout:", w.attrib['id'], runnerid, w.attrib['start_at'])
        if w.attrib['sport'] in ["Бег", "Спортивное ориентирование", "Беговая дорожка"]:
#            print("    ==== run:", w.attrib['distance'], " km, ", w.attrib['duration'])
            rundate = dateutil.parser.parse(w.attrib['start_at'])
            if rundate >= weekrange[1] and rundate <= weekrange[2]:
                print("      >>>> valid date: ", rundate, w.attrib['distance'], " km, ", w.attrib['duration'])
                db = sqlite3.connect('aerobia.db')
                c2 = db.cursor()
                thisdistance = w.attrib['distance']
                c2.execute('INSERT OR REPLACE INTO log VALUES (?, ?, ?, ?, ?, ?)', (w.attrib['id'], runnerid, w.attrib['start_at'], thisdistance, w.attrib['duration'], w.attrib['sport']))
                db.commit()
                db.close()


print("-------------------- ",datetime.datetime.now())
now = datetime.date.today()
months = {'янв.':1,'фев.':2,'мар.':3,'апр.':4,'мая':5,'июня':6,'июля':7,'авг.':8,'сент.':9,'окт.':10,'нояб.':11,'дек.':12}
invmonths = {v: k for k, v in months.items()}
with open('credentials') as f:
        credentials = f.read().splitlines()
weekago = now - datetime.timedelta(days=7)
monthago = now.replace(day=1) - datetime.timedelta(days=1)
thisweek = week_range(now) 
lastweek = week_range(weekago)
loginurl="https://aerobia.ru/users/sign_in"
data = {"user[email]": credentials[0], "user[password]": credentials[1]}
s = requests.session()
s.headers.update({'User-Agent':'Mozilla/4.0'})
print("log in")
r = s.post(loginurl,data)
db = sqlite3.connect('aerobia.db')
c1 = db.cursor()
runners = c1.execute('SELECT runnerid, isill from runners').fetchall()
db.close()
for r in runners:
    print("**** Runner:", r)
    runnerid = r[0]
#    isill = r[1]
    db = sqlite3.connect('aerobia.db')
    goal = db.execute('SELECT goal FROM runners WHERE runnerid=?', (runnerid,)).fetchone()[0]
    ill = db.execute('SELECT wasill FROM wlog WHERE runnerid=? ORDER BY week DESC LIMIT 1', (runnerid,)).fetchone()
    isill = ill[0] if ill else 0
    print(" #### retrieve this week")
    parseuser(runnerid, now, s)
    total = db.execute('SELECT SUM(distance) FROM log WHERE runnerid=?', (runnerid,)).fetchone()[0]
    thisweekresult = db.execute('SELECT SUM(distance) FROM log WHERE runnerid=? AND date>? AND date<?', (runnerid, thisweek[1].isoformat(), thisweek[2].isoformat())).fetchone()[0] or 0
    print(" #### this week result: ", thisweekresult)
    if total > goal:
        if (total - thisweekresult) >= goal:
            # goal exceeded before this week, tax full result
            thisweekresult *= 0.2
        else:
            # goal exceeded this week, calculate the excess and tax it
            excess = total - goal
            thisweekresult = (thisweekresult - excess) + (excess * 0.2)
#    db.execute('INSERT OR REPLACE INTO wlog VALUES (?, ?, ?, ?)', (runnerid, thisweek[0], thisweekresult, isill))
    db.execute('UPDATE wlog SET distance=?,wasill=? WHERE runnerid=? AND week=?', (thisweekresult, isill, runnerid, thisweek[0]))
    db.commit()
    if now.weekday() < 2:
        print(" #### retrieve last week")
        ill = db.execute('SELECT wasill FROM wlog WHERE runnerid=? AND week=?', (runnerid, lastweek[0])).fetchone()
        wasill = ill[0] if ill else 0
        parseuser(runnerid, weekago, s)
        total = db.execute('SELECT SUM(distance) FROM log WHERE runnerid=? and date<?', (runnerid, lastweek[2].isoformat())).fetchone()[0]
        lastweekresult = db.execute('SELECT SUM(distance) FROM log WHERE runnerid=? AND date>? AND date<?', (runnerid, lastweek[1].isoformat(), lastweek[2].isoformat())).fetchone()[0]
        print(" #### last week result: ", lastweekresult, lastweek[1].isoformat()[1], lastweek[2].isoformat()[1])
        if total > goal:
            if (total - lastweekresult) >= goal:
                # goal exceeded before this week, tax full result
                lastweekresult *= 0.2
            else:
                # goal exceeded this week, calculate the excess and tax it
                excess = total - goal
                lastweekresult = (lastweekresult - excess) + (excess * 0.2)
#        db.execute('INSERT OR REPLACE INTO wlog VALUES (?, ?, ?, ?)', (runnerid, lastweek[0], lastweekresult, wasill))
        db.execute('UPDATE wlog SET distance=?,wasill=? WHERE runnerid=? AND week=?', (lastweekresult, isill, runnerid, lastweek[0]))
        db.commit()
    db.close()
#db.commit()
#db.close()
print("-------------------- ",datetime.datetime.now())

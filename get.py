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

def datestring(date):
    return "{:d}-{:02d}-{:02d}".format(date.year, date.month, date.day)

def parseuser(db, runnerid, isill, date, session):
    dataurl = "http://aerobia.ru/api/users/{}/calendar/{}/{:02d}".format(runnerid, date.year, date.month)
    print("requesting "+dataurl)
    r = session.get(dataurl)
    xml = r.content
    root = lxml.etree.fromstring(xml)
    workouts = root.findall('.//r')
    c2 = db.cursor()
    for w in workouts:
        print("  ---- workout:", w.attrib['id'], runnerid, w.attrib['start_at'])
        if w.attrib['sport'] in ["Бег", "Спортивное ориентирование", "Беговая дорожка"]:
            print("    ==== run:", w.attrib['distance'], " km, ", w.attrib['duration'])
            c2.execute('INSERT OR REPLACE INTO log VALUES (?, ?, ?, ?, ?, ?)', (w.attrib['id'], runnerid, w.attrib['start_at'], w.attrib['distance'], w.attrib['duration'], w.attrib['sport']))


print("-------------------- ",datetime.datetime.now())
now = datetime.date.today()
months = {'янв.':1,'фев.':2,'мар.':3,'апр.':4,'мая':5,'июня':6,'июля':7,'авг.':8,'сент.':9,'окт.':10,'нояб.':11,'дек.':12}
invmonths = {v: k for k, v in months.items()}
with open('credentials') as f:
        credentials = f.read().splitlines()
weekago = now - datetime.timedelta(days=7)
thisweek = week_range(now) 
lastweek = week_range(weekago)
loginurl="http://aerobia.ru/users/sign_in"
data = {"user[email]": credentials[0], "user[password]": credentials[1]}
s = requests.session()
s.headers.update({'User-Agent':'Mozilla/4.0'})
print("log in")
r = s.post(loginurl,data)
db = sqlite3.connect('aerobia.db')
c1 = db.cursor()
runners = c1.execute('SELECT runnerid, isill from runners').fetchall()
for r in runners:
    print("**** Runner:", r)
    runnerid = r[0]
    isill = r[1]
#    parseuser(db, runnerid, isill, weekago, s)
    parseuser(db, runnerid, isill, now, s)
    lastweekresult = c1.execute('SELECT SUM(distance) FROM log WHERE runnerid=? AND date>? AND date<?', (runnerid, lastweek[1], lastweek[2])).fetchone()[0]
    thisweekresult = c1.execute('SELECT SUM(distance) FROM log WHERE runnerid=? AND date>? AND date<?', (runnerid, thisweek[1], thisweek[2])).fetchone()[0]
    c1.execute('INSERT OR REPLACE INTO wlog VALUES (?, ?, ?, ?)', (runnerid, lastweek[0], lastweekresult, isill))
    c1.execute('INSERT OR REPLACE INTO wlog VALUES (?, ?, ?, ?)', (runnerid, thisweek[0], thisweekresult, isill))
db.commit()
db.close()
print("-------------------- ",datetime.datetime.now())

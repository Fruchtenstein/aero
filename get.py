#!/usr/bin/python3

from urllib.request import urlopen,Request
from bs4 import BeautifulSoup
import datetime
import dateutil.parser
import pytz
import sqlite3
import os
import re

def week_range(date):
    utc=pytz.UTC
    year, week, dow = date.isocalendar()
    start_date = date - datetime.timedelta(dow-1)
    end_date = start_date + datetime.timedelta(6)
    return (week, utc.localize(datetime.datetime.combine(start_date, datetime.datetime.min.time())), utc.localize(datetime.datetime.combine(end_date, datetime.datetime.max.time())))

def getlog(date):
    datestring = "{:d}-{:02d}-{:02d}".format(date.year, date.month, date.day)
    week = week_range(date) 
    print(week)
    db = sqlite3.connect('aerobia.db')
    c1 = db.cursor()
    for row in c1.execute('SELECT runnerid, isill from runners').fetchall():
        runnerid = row[0]
        isill = row[1]
        weeklytotal = 0
        print("-----fetching http://aerobia.ru/users/{}/workouts?month={}".format(runnerid, datestring))
        html = urlopen(Request("http://aerobia.ru/users/{}/workouts?month={}".format(runnerid, datestring), headers={'User-Agent': 'Mozilla/4.0'}))
        bs = BeautifulSoup(html.read(), "lxml")
        workouts = bs.findAll("a", {"class":"sport"})
        username = bs.aside.div.div.strong.get_text()
        for w in workouts:
            r = re.search('^([\s\w]*) |',w['data-title'])
            runtype = r.group(1)
            if runtype in ["Бег", "Спортивное ориентирование", "Беговая дорожка"]:
                print("  -----fetching http://aerobia.ru/"+w['href'])
                wkoutpage= urlopen(Request("http://aerobia.ru/"+w['href'], headers={'User-Agent': 'Mozilla/4.0'}))
                wkbs = BeautifulSoup(wkoutpage.read(), "lxml")
                rundate = wkbs.find("time", {"class":"js_created"})['datetime']
                distance = 0
                t = "0ч 0м 0с"
                wkout = wkbs.find("table", {"class":"data"})
                trs = wkout.find_all("tr")
                for tr in trs:
                    if tr.th.get_text() == "Дистанция":
                        dist = tr.td.get_text()
                        distance = float(dist.split()[0])
                    if tr.th.get_text() == "Длительность":
                        t = tr.td.get_text()
#                    if tr.th.get_text() == "Дата начала":
#                        rundate2 = tr.td.get_text()
                h = re.search('([0-9]*)ч', t)
                runh = h.group(1) if h else "00"
                runm = re.search('([0-9]*)м', t).group(1)
                runs = re.search('([0-9]*)с', t).group(1)
                runtime = "{:02d}:{:02d}:{:02d}".format(int(runh),int(runm),int(runs))
                if week[1] < dateutil.parser.parse(rundate) < week[2]:
                    print("    >>>>>> ", runnerid, username, rundate, runtype, distance, runtime)
                    weeklytotal += distance
                    c2 = db.cursor()
                    c2.execute('INSERT OR REPLACE INTO log VALUES (?, ?, ?, ?, ?)', (runnerid, rundate, distance, runtime, runtype))
                else:
                    print("    ------ ",runnerid, username, rundate, runtype, distance, runtime)
        print("Weekly total: {}".format(weeklytotal))
        c3 = db.cursor()
        c3.execute('INSERT OR REPLACE INTO wlog VALUES (?, ?, ?, ?)', (runnerid,  week[0], weeklytotal, isill))
#    c4 = db.cursor()
#    tbl = []
#    for row in c4.execute('SELECT teamid, 100*SUM(distance)/(SUM(goal)/52) AS target FROM wlog,runners WHERE wlog.runnerid=runners.runnerid AND week=? GROUP BY teamid ORDER BY target DESC',
#            (week[0],)).fetchall():
#        tbl.append([row[0], week[0], row[1]])
#    print(tbl)
#    for n,t in enumerate(tbl):
#        pts = len(tbl)*5-n*5-5
#        print(t[0],t[1],pts,t[2])
#        c4.execute('INSERT OR REPLACE INTO tlog VALUES (?, ?, ?, ?)', (t[0], t[1], pts, t[2]))
    db.commit()
    db.close()

now = datetime.date.today()
months = {'янв.':1,'фев.':2,'мар.':3,'апр.':4,'мая':5,'июня':6,'июля':7,'авг.':8,'сент.':9,'окт.':10,'нояб.':11,'дек.':12}
invmonths = {v: k for k, v in months.items()}
print("-------------------- ",datetime.datetime.now())
getlog(now - datetime.timedelta(days=7))
print("-------------------- ",datetime.datetime.now())

#!/usr/bin/python3

from urllib.request import urlopen,Request
from bs4 import BeautifulSoup
import datetime
import sqlite3
import os
import re

def week_range(date):
    year, week, dow = date.isocalendar()
    start_date = date - datetime.timedelta(dow-1)
    end_date = start_date + datetime.timedelta(6)
    return (datetime.datetime.combine(start_date, datetime.datetime.min.time()), datetime.datetime.combine(end_date, datetime.datetime.max.time()))

def getlog(date):
    datestring = "{:d}-{:02d}-{:02d}".format(date.year, date.month, date.day)
    week = week_range(date) 
    db = sqlite3.connect('aerobia.db')
    c1 = db.cursor()
    for row in c1.execute('SELECT runnerid from runners').fetchall():
        runnerid = row[0]
        print("-----fetching http://aerobia.ru/users/{}/workouts?month={}".format(runnerid, datestring))
        html = urlopen(Request("http://aerobia.ru/users/{}/workouts?month={}".format(runnerid, datestring), headers={'User-Agent': 'Mozilla/4.0'}))
        bs = BeautifulSoup(html.read(), "lxml")
        workouts = bs.findAll("div", {"class":"info"})
        username = bs.aside.div.div.strong.get_text()
        for w in workouts:
            pars = w.find_all("p")
            runtype = w.p.get_text()
            if len(pars) == 3:
                runtype = pars[0].get_text()
                when = pars[1].get_text()
                dist = pars[2].get_text()
            elif len(pars) == 4:
                runtype = pars[1].get_text()
                when = pars[2].get_text()
                dist = pars[3].get_text()
            if (runtype in ["Бег", "Спортивное ориентирование", "Беговая дорожка"]):
                d = when.split()
                day = int(d[0])
                month = months[d[1]]
                year = d[2][0:4]
                time = d[4]
                rundate = "{}-{:02d}-{:02d} {}".format(year, month, day, time)
                d = dist.split()
                distance = float(d[0])
                if len(d)>2:
                    t = d[2]
                else:
                    t = "0ч 0м 0с"
                h = re.search('([0-9]*)ч', t)
                runh = h.group(1) if h else "00"
                runm = re.search('([0-9]*)м', t).group(1)
                runs = re.search('([0-9]*)с', t).group(1)
                runtime = "{:02d}:{:02d}:{:02d}".format(int(runh),int(runm),int(runs))
                if week[0] < datetime.datetime.strptime(rundate, '%Y-%m-%d %H:%M') < week[1]:
                    print(">>>>>> ", runnerid, username, rundate, runtype, d[0], runtime)
                    c2 = db.cursor()
                    c2.execute('INSERT OR REPLACE INTO log VALUES (?, ?, ?, ?, ?)', (runnerid, rundate, float(d[0]), runtime, runtype))
                else:
                    print("------ ",runnerid, username, rundate, runtype, d[0], runtime)
    db.commit()
    db.close()


now = datetime.date.today()
months = {'янв.':1,'фев.':2,'мар.':3,'апр.':4,'мая':5,'июня':6,'июля':7,'авг.':8,'сент.':9,'окт.':10,'нояб.':11,'дек.':12}
invmonths = {v: k for k, v in months.items()}

print("-------------------- ",datetime.datetime.now())
getlog(now - datetime.timedelta(days=7))
print("-------------------- ",datetime.datetime.now())

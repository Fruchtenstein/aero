#!/usr/bin/python3

from urllib.request import urlopen,Request
from bs4 import BeautifulSoup
import datetime
import sqlite3
import os
###import gspread
###from oauth2client.service_account import ServiceAccountCredentials

def getDistance(runnerid, date):
    total = 0
    datestring = "{:d}-{:02d}-{:02d}".format(date.year, date.month, date.day)
    print("-----datestring", datestring)
    print("-----fetching http://aerobia.ru/users/{}/workouts?month={}".format(runnerid, datestring))
    html = urlopen(Request("http://aerobia.ru/users/{}/workouts?month={}".format(runnerid, datestring), headers={'User-Agent': 'Mozilla/4.0'}))
    bs = BeautifulSoup(html.read(), "lxml")
    workouts = bs.findAll("div", {"class":"info"})
    username = bs.aside.div.div.strong.get_text()
    for w in workouts:
        pars = w.find_all("p")
        type = w.p.get_text()
        if len(pars) == 3:
            type = pars[0].get_text()
            when = pars[1].get_text()
            dist = pars[2].get_text()
        elif len(pars) == 4:
            type = pars[1].get_text()
            when = pars[2].get_text()
            dist = pars[3].get_text()
        print("===", type)
        print("===", when)
        print("===", dist)
        if (not type in ["Бег", "Спортивное ориентирование", "Беговая дорожка"]):
            continue
        d = when.split()
        day = int(d[0])
        month = months[d[1]]
        year = int(d[2][0:4])
        rundate = datetime.date(year,month,day)
        d = dist.split()
        distance = float(d[0])
#        print("-----rundate", rundate)
#        print("-----week", rundate.isocalendar()[1])
#        print("-----type", type)
#        print("-----distance", distance)
        if (rundate.isocalendar()[1] == date.isocalendar()[1] and date.year == year):
            print("-----rundate", rundate)
            print("-----week", rundate.isocalendar()[1])
            print("-----", type)
            print("-----distance", distance)
            total += distance
    return (username, total)

def loadDB(date):
    db = sqlite3.connect('aerobia.db')
    c1 = db.cursor()
    week = date.isocalendar()[1]
    for row in c1.execute('SELECT * from runners').fetchall():
        runnerid = row[0]
        teamid = row[1]
        dist = getDistance(runnerid, date)
        print("Week {} total for {}: {}".format(week, dist[0], dist[1]))
        c2 = db.cursor()
#        c2.execute('SELECT COUNT(*) FROM wlog WHERE runnerid = ? AND week = ?', (runnerid, week))
#        res = c2.fetchone()
#        print('--------', res[0])
        c2.execute('INSERT OR REPLACE INTO wlog (runnerid, week, distance) VALUES (?, ?, ?)', (runnerid, week, dist[1]))
        c2.execute('SELECT * FROM wlog WHERE runnerid = ? AND week = ?', (runnerid, week))
        res = c2.fetchone()
        print('--------', res[0], res[1], res[2])
    db.commit()
    db.close()


when = datetime.date.today() - datetime.timedelta(days=7)
#onemonthago = when.replace(day=1)-datetime.timedelta(days=1)
#twomonthago = onemonthago.replace(day=1)-datetime.timedelta(days=1)
months = {'янв.':1,'фев.':2,'мар.':3,'апр.':4,'мая':5,'июня':6,'июля':7,'авг.':8,'сент.':9,'окт.':10,'нояб.':11,'дек.':12}
invmonths = {v: k for k, v in months.items()}
###scope = ['https://spreadsheets.google.com/feeds']
###creds = ServiceAccountCredentials.from_json_keyfile_name('Aerobia-bba95b59edbd.json', scope)
###client = gspread.authorize(creds)
###sheet = client.open("2018in2018").sheet1

print("-------------------- ",datetime.datetime.now())
#loadDB(now - datetime.timedelta(days=70))
#loadDB(now - datetime.timedelta(days=63))
#loadDB(now - datetime.timedelta(days=56))
#loadDB(now - datetime.timedelta(days=49))
#loadDB(now - datetime.timedelta(days=42))
#loadDB(now - datetime.timedelta(days=35))
#loadDB(now - datetime.timedelta(days=28))
#loadDB(now - datetime.timedelta(days=21))
#loadDB(now - datetime.timedelta(days=14))
#loadDB(twomonthago)
#loadDB(onemonthago)
loadDB(when)
print("-------------------- ",datetime.datetime.now())

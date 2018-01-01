#!/usr/bin/python3

import sqlite3
import datetime
import pytz
import os
from string import Template

def week_range(date):
    utc=pytz.UTC
    year, week, dow = date.isocalendar()
    start_date = date - datetime.timedelta(dow-1)
    end_date = start_date + datetime.timedelta(6)
    return (week, utc.localize(datetime.datetime.combine(start_date, datetime.datetime.min.time())), utc.localize(datetime.datetime.combine(end_date, datetime.datetime.max.time())))

def mkIndex(date):
    week = date.isocalendar()[1]
    db = sqlite3.connect('aerobia.db')
    c1 = db.cursor()
    c2 = db.cursor()
    teams = c1.execute('SELECT * FROM teams ORDER BY teamid').fetchall()
    teampoints = []
    teamlog = []
    for i in teams:
        teampoints.append(0)
    for w in range(1,week+1):
        oneweeklog = []
        for row in c1.execute('SELECT teamid, 100*SUM(distance)/(SUM(goal)/52) AS percentage, SUM(distance), SUM(goal)/52 FROM wlog,runners WHERE wlog.runnerid=runners.runnerid AND week=? AND wlog.wasill=0 GROUP BY teamid ORDER BY percentage DESC',
                (w,)).fetchall():
            oneweeklog.append([w, row[0], row[1], row[2], row[3]])
        for n,t in enumerate(oneweeklog):
            pts = len(oneweeklog)*5-n*5-5
            teampoints[t[1]-1] += pts
            oneweeklog[n].append(pts)
            oneweeklog[n].append(teampoints[t[1]-1])
        teamlog += oneweeklog

    output = []
    for w in range(week, 0, -1):
        weeklog = [t for t in teamlog if t[0]==w]
        print(">>>> Week ", w)
        print(weeklog)
        if weeklog:
            output.append('            <center>')
            output.append('                <h1>Результаты {0} недели</h1>'.format(w))
            output.append('                <a href="teams{0:02d}.html">Подробнее</a>'.format(w))
            output.append('                <br />')
            output.append('                <br />')
            output.append('            </center>')
            output.append('            <div class="datagrid"><table>')
            output.append('               <thead><tr><th>Команда</th><th>Цель (км/нед)</th><th>Результат (км)</th><th>Выполнено (%)</th><th>Очки</th><th>Сумма</th></tr></thead>')
            output.append('               <tbody>')
            odd = True
            for t in weeklog:
                teamname = next(el[1] for el in teams if el[0]==t[1])
                alt = ' class="alt"' if odd else ''
                output.append('                 <tr{}><td>{}</td><td>{:.2f}</td><td>{:.2f}</td><td>{:.2f}</td><td>{}</td><td>{}</td></tr>'.format(alt, teamname, t[4], t[3], t[2], t[5], t[6]))
                odd = not odd
            output.append('               </tbody>')
            output.append('            </table></div>')
            output.append('            <br />')
            output.append('            <hr />')
#    tbl = []
#    for t in teams:
#        tgoal = c1.execute('SELECT coalesce(sum(goal),0) FROM runners WHERE teamid=? AND isill=0', (t[0],)).fetchone()[0]/52
#        runners = c1.execute('SELECT runnerid FROM runners WHERE teamid=? AND isill=0', (t[0],)).fetchall()
#        tmileage = 0
#        tpercentage = 0
#        for r in runners:
#            rmileage = c1.execute('SELECT coalesce(sum(distance),0) FROM wlog WHERE runnerid=? AND week=?', (r[0], week)).fetchone()[0]
#            rgoal = c1.execute('SELECT goal FROM runners WHERE runnerid=? AND isill=0', (r[0],)).fetchone()[0]/52
#            print(r[0], week, rmileage, rgoal)
#            print("{}: {:.2f} {:.2f} {:.2f}".format(r[0], rmileage, rgoal, rmileage*100/rgoal))
#            tmileage += rmileage
#            tpercentage += rmileage*100/rgoal
#        tpercentage = tpercentage/len(runners)
#        print("==== Team ", t[1])
#        print(".... tgoal:   ", tgoal)
#        print(".... tmileage:", tmileage)
#        print(".... sum pct: ", tmileage*100/tgoal)
#        print(".... avg pct: ", tpercentage)
#        tbl.append([t[0], t[1], tgoal, tmileage, tmileage*100/tgoal, tpercentage])
#    
#    tbl = sorted(tbl, key=lambda x: x[5], reverse = True)
#    output = []
#    output.append('            <center>')
#    output.append('                <h1>Результаты {} недели</h1>'.format(week))
#    output.append('            </center>')
#    
#    output.append('            <div class="datagrid"><table>')
#    output.append('               <thead><tr><th>Команда</th><th>Цель (км/нед)</th><th>Результат (км)</th><th>Выполнено (%)</th><th>Очки</th></tr></thead>')
#    output.append('               <tbody>')
#    odd = True
#    for n, t in enumerate(tbl):
#        alt = ' class="alt"' if odd else ''
#        pts = len(teams)*5-n*5-5
#        output.append('                 <tr{}><td>{}</td><td>{:.2f}</td><td>{:.2f}</td><td>{:.2f}</td><td>{}</td></tr>'.format(alt, t[1], t[2], t[3], t[5], pts))
##        c1.execute('INSERT OR REPLACE INTO tlog VALUES (?, ?, ?, ?)', (t[0], week, pts, t[5]))
#        odd = not odd
#    output.append('               </tbody>')
#    output.append('            </table></div>')
#    
#    db.commit()
    
    output2 = []
    output2.append('            <br />')
    output2.append('            <br />')
    output2.append('            <center>')
    output2.append('                <h1>Таблица соревнования</h1>')
    output2.append('            </center>')
    
    output2.append('            <div class="datagrid"><table>')
    output2.append('               <thead><tr><th>Команда</th><th>Очки</th></tr></thead>')
    output2.append('               <tbody>')
    odd = True
    tbl=[]
    for t in teams:
#        pts = c1.execute('SELECT coalesce(SUM(pts),0) FROM tlog WHERE teamid=?',(t[0],)).fetchone()[0]
        pts = teampoints[t[0]-1]
        tbl.append([t[1], pts])
    
    tbl = sorted(tbl, key=lambda x: x[1], reverse = True)
    for n, t in enumerate(tbl):
        alt = ' class="alt"' if odd else ''
        output2.append('                 <tr{}><td>{}</td><td>{}</td></tr>'.format(alt, t[0], t[1]))
        odd = not odd
    output2.append('               </tbody>')
    output2.append('            </table></div>')
    output2.append('            <hr />')
            
    output.append('            <center>')
    output.append('                <h1>Результаты текущей недели</h1>'.format(w))
    output.append('            </center>')
    output.append('            <div class="datagrid"><table>')
    output.append('               <thead><tr><th>Команда</th><th>Цель (км/нед)</th><th>Результат (км)</th><th>Выполнено (%)</th></tr></thead>')
    output.append('               <tbody>')
    odd = True
    w = week_range(datetime.datetime.now())
#    tbl = []
    for t in teams:
        tmileage = 0
        tgoal = 0
        for (r,g) in c1.execute('SELECT runnerid,goal FROM runners WHERE teamid = ?', (t[0],)).fetchall():
            tgoal += g
            (d,) = c2.execute('SELECT SUM(distance) FROM log WHERE runnerid=? AND date > ?', (r, w[1].isoformat())).fetchone()
            if d:
                tmileage += d
#        tbl.append([t[1], tmileage, tgoal])
        output.append('                    <tr><td>{}</td><td>{:0.2f}</td><td>{:0.2f}</td><td>{:0.2f}</td></tr>'.format(t[1], tgoal/52, tmileage, 100*tmileage*52/tgoal))
    output.append('                </tbody>')
    output.append('             </table>')
    output.append('           </div>')
    inp = open('index.template')
    tpl = Template(inp.read())
    outstr = '\n'.join(output)
    outstr2 = '\n'.join(output2)
    subst = {'table':outstr, 'table2':outstr2, 'week':str(week).zfill(2)}
    result = tpl.substitute(subst)
    inp.close()
    out = open('html/index.html', 'w')
    out.write(result)
    out.close()
    db.close()
 

def mkTeams(date):
    week = date.isocalendar()[1]
    db = sqlite3.connect('aerobia.db')
    c1 = db.cursor()
    teams = c1.execute('SELECT * FROM teams ORDER BY teamid').fetchall()
    tbl = []
    outteam = []
    outteam.append('            <br />')
    outteam.append('            <center>')
    outteam.append('                <h1>Команды</h1>')
    outteam.append('            </center>')
    for t in teams:
        tmileage = 0
        tgoal = 0
        tpct = 0
        outteam.append('            <center>')
        outteam.append('                <h2>{}</h2>'.format(t[1]))
        outteam.append('            </center>')
        outteam.append('            <div class="datagrid"><table>')
        outteam.append('               <thead><tr><th>Имя</th><th>Цель (км/нед)</th><th>Результат (км)</th><th>Выполнено (%)</th><th>На больничном</th></tr></thead>')
        outteam.append('               <tbody>')
        runners = c1.execute('SELECT * FROM runners WHERE teamid=? ORDER BY runnername', (t[0],)).fetchall()
        odd = True
        for r in runners:
            rdata = c1.execute('SELECT distance,wasill FROM wlog WHERE runnerid=? AND week=?', (r[0], week)).fetchone()
            if not rdata:
                rdata = (0,0)
            rmileage = rdata[0]
            rgoal = r[3]/52
            if rdata[1]==0:
                alt = ' class="alt"' if odd else ''
                tmileage += rmileage
                tgoal += rgoal
                tpct += rmileage*100/rgoal
                ill = ""
            else:
                alt = ' class="alt ill"' if odd else ''
                ill = "ДА"
            outteam.append('                 <tr{}><td><a href="http://aerobia.ru/users/{}">{}</a></td><td>{:0.2f}</td><td>{:0.2f}</td><td>{:0.2f}</td><td>{}</td></tr>'.format(alt, r[0], r[1], rgoal, rmileage, rmileage*100/rgoal, ill))
            odd = not odd
        print(t, tgoal, tmileage)
        outteam.append('               <tfoot><tr><td>Всего:</td><td>{:0.2f}</td><td>{:0.2f}</td><td>{:0.2f}</td><td></td></tr></tfoot>'.format(tgoal, tmileage, tpct/len(runners)))
        outteam.append('               </tbody>')
        outteam.append('            </table></div>')
        outteam.append('            <br />')
    outteambox=[]
    outteambox.append('    <nav class="sub">')
    outteambox.append('      <ul>')
    for w in range(1,week+1):
        if w == week:
#            print("current week")
            outteambox.append('        <li class="active"><span>{} неделя</span></li>'.format(w))
        elif os.path.isfile("html/teams{:02d}.html".format(w)):
#            print("statistics{:02d}.html exists".format(w))
            outteambox.append('        <li><a href="teams{0:02d}.html">{0} неделя</a></li>'.format(w))
#        else:
#            print("statistics{:02d}.html doesn't exist".format(w))
#            outteambox.append('        <li>{} неделя</li>'.format(w))
    outteambox.append('      </ul>')
    outteambox.append('    </nav>')
    inp = open('teams.template')
    tpl = Template(inp.read())
    outstr = '\n'.join(outteam)
    outbox = '\n'.join(outteambox)
    subst = {'box':outbox, 'table':outstr, 'week':str(week).zfill(2)}
    result = tpl.substitute(subst)
    inp.close()
    out = open('html/teams{:02d}.html'.format(week), 'w')
    out.write(result)
    out.close()
    db.close()


def mkStat(date):
    w = week_range(date)
    week = w[0]
    db = sqlite3.connect('aerobia.db')
    c1 = db.cursor()
    outstat = []
    outstat.append('            <br />')
    outstat.append('            <center>')
    outstat.append('                <h1>Лучший бегун {} недели:</h1>'.format(week))
#    outstat.append('                <h1>Митя ☮ Фруктенштейн</h1>')
    outstat.append('                <hr />')
    outstat.append('            </center>')
    outstat.append('')

    winner = c1.execute('SELECT runnerid, MAX(d) FROM (SELECT runnerid, SUM(distance) AS d FROM log WHERE date > ? AND date < ? GROUP BY runnerid)',(w[1].isoformat(), w[2].isoformat())).fetchone()
    print("Winner: ",winner)
    if winner[0]:
        winnername = c1.execute('SELECT runnername FROM runners WHERE runnerid=?',(winner[0],)).fetchone()
        outstat.append('            <br />')
        outstat.append('            <center>')
        outstat.append('                <h1>Больше всех за неделю пробежал:</h1>')
        outstat.append('                <h1>{} — {} км.</h1>'.format(winnername[0], winner[1]))
        outstat.append('                <hr />')
        outstat.append('            </center>')
        outstat.append('')

    winner = c1.execute('SELECT runnerid, MAX(pct) FROM (SELECT log.runnerid, 100*SUM(distance)/(goal/52) AS pct FROM log,runners WHERE date > ? AND date < ? AND log.runnerid=runners.runnerid GROUP BY log.runnerid)',(w[1].isoformat(), w[2].isoformat())).fetchone()
    print("Winner: ",winner)
    if winner[0]:
        winnername = c1.execute('SELECT runnername FROM runners WHERE runnerid=?',(winner[0],)).fetchone()
        outstat.append('            <br />')
        outstat.append('            <center>')
        outstat.append('                <h1>Максимальное выполнение плана:</h1>')
        outstat.append('                <h1>{} — {:0.2f}%</h1>'.format(winnername[0], winner[1]))
        outstat.append('                <hr />')
        outstat.append('            </center>')
        outstat.append('')

    outstatbox=[]
    outstatbox.append('    <nav class="sub">')
    outstatbox.append('      <ul>')
    for w in range(1,week+1):
        if w == week:
#            print("current week")
            outstatbox.append('        <li class="active"><span>{} неделя</span></li>'.format(w))
        elif os.path.isfile("html/statistics{:02d}.html".format(w)):
#            print("statistics{:02d}.html exists".format(w))
            outstatbox.append('        <li><a href="statistics{0:02d}.html">{0} неделя</a></li>'.format(w))
#        else:
#            print("statistics{:02d}.html doesn't exist".format(w))
#            outstatbox.append('        <li>{} неделя</li>'.format(w))
    outstatbox.append('      </ul>')
    outstatbox.append('    </nav>')
    inp = open('statistics.template')
    tpl = Template(inp.read())
    outstr = '\n'.join(outstat)
    outbox = '\n'.join(outstatbox)
    subst = {'box':outbox, 'data':outstr, 'week':str(week).zfill(2)}
    result = tpl.substitute(subst)
    inp.close()
    out = open('html/statistics{:02d}.html'.format(week), 'w')
    out.write(result)
    out.close()
    db.close()

print("-------------------- ",datetime.datetime.now())
now = datetime.date.today()
mkIndex(now - datetime.timedelta(days=7))
mkTeams(now - datetime.timedelta(days=7))
mkStat(now - datetime.timedelta(days=7))
print("-------------------- ",datetime.datetime.now())


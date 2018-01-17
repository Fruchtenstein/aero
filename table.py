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

def printfinalresults(w, weeklog, teams):
    print("====== Final:", w)
    output = []
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
    return output

def printintermediateresults(date, teams, db):
    print("====== Intermediate:", date)
    c1 = db.cursor()
    c2 = db.cursor()
    output = []
    output.append('            <center>')
    output.append('                <h1>Промежуточные результаты {} недели</h1>'.format(date.isocalendar()[1]))
    output.append('            </center>')
    output.append('            <div class="datagrid"><table>')
    output.append('               <thead><tr><th>Команда</th><th>Цель (км/нед)</th><th>Результат (км)</th><th>Выполнено (%)</th></tr></thead>')
    output.append('               <tbody>')
    weekrange = week_range(date)
    tbl = []
    for t in teams:
        tmileage = 0
        tgoal = 0
        tpct = 0
        runners = c1.execute('SELECT runnerid,goal FROM runners WHERE teamid = ?', (t[0],)).fetchall()
        illcount = 0
        for (r,g) in runners:
            tgoal += g
            d = c2.execute('SELECT COALESCE(distance,0),wasill FROM wlog WHERE runnerid=? AND week=?', (r, weekrange[0])).fetchone()
#            (d,) = c2.execute('SELECT SUM(distance) FROM log WHERE runnerid=? AND date > ? AND date < ? AND isill=0', (r, weekrange[1].isoformat(), weekrange[2].isoformat())).fetchone()
            if d and not d[1]:
                print("   +++ ", r, d[0], g/52, 100*52*d[0]/g)
                tmileage += d[0]
                tpct += 100*52*d[0]/g
                print("tpct:", tpct)
            else:
                print("   --- ", r, 0, g/52, 0)
            if d[1]:
                illcount += 1
        tbl.append([t[1], tgoal, tmileage, tpct/(len(runners)-illcount)])
        print("   ==== team ", [t[1], tgoal, tmileage, tpct/(len(runners)-illcount)])
    print(tbl)
    tbl = sorted(tbl, key=lambda x: x[3], reverse = True)
    odd = True
    for team in tbl:
        alt = ' class="alt"' if odd else ''
        output.append('                    <tr{}><td>{}</td><td>{:0.2f}</td><td>{:0.2f}</td><td>{:0.2f}</td></tr>'.format(alt, team[0], team[1]/52, team[2], team[3]))
        odd = not odd
    output.append('                </tbody>')
    output.append('             </table>')
    output.append('           </div>')
    output.append('            <br />')
    output.append('            <hr />')
    return output

def printstandings(teams, teampoints):
    output = []
    output.append('            <br />')
    output.append('            <br />')
    output.append('            <center>')
    output.append('                <h1>Таблица соревнования</h1>')
    output.append('            </center>')
    
    output.append('            <div class="datagrid"><table>')
    output.append('               <thead><tr><th>Команда</th><th>Очки</th></tr></thead>')
    output.append('               <tbody>')
    odd = True
    tbl=[]
    for t in teams:
        pts = teampoints[t[0]-1]
        tbl.append([t[1], pts])
    
    tbl = sorted(tbl, key=lambda x: x[1], reverse = True)
    for n, t in enumerate(tbl):
        alt = ' class="alt"' if odd else ''
        output.append('                 <tr{}><td>{}</td><td>{}</td></tr>'.format(alt, t[0], t[1]))
        odd = not odd
    output.append('               </tbody>')
    output.append('            </table></div>')
    output.append('            <hr />')
    return output

def mkIndex(date):
    dolastweek = date.weekday() < 2
    print("date: ", date, "; weekday: ", date.weekday())
    print("do last week = ", dolastweek)
    if dolastweek:
        week = date.isocalendar()[1] - 2
    else:
        week = date.isocalendar()[1] - 1
    print("index week:", week)
    db = sqlite3.connect('aerobia.db')
    c1 = db.cursor()
    teams = c1.execute('SELECT * FROM teams ORDER BY teamid').fetchall()
    teampoints = []
    teamlog = []
    for i in teams:
        teampoints.append(0)
    for w in range(1,week+1):
        oneweeklog = []
        for row in c1.execute('SELECT teamid, SUM(100*distance/(goal/52))/COUNT(*) AS percentage, SUM(distance), SUM(goal)/52 FROM wlog,runners WHERE wlog.runnerid=runners.runnerid AND week=? AND wlog.wasill=0 GROUP BY teamid ORDER BY percentage DESC',
                (w,)).fetchall():
            oneweeklog.append([w, row[0], row[1], row[2], row[3]])
            print("   ******", [w, row])
        for n,t in enumerate(oneweeklog):
            pts = len(oneweeklog)*5-n*5-5
            teampoints[t[1]-1] += pts
            oneweeklog[n].append(pts)
            oneweeklog[n].append(teampoints[t[1]-1])
        teamlog += oneweeklog

    output2 = printstandings(teams, teampoints) 

    output = []
    output += printintermediateresults(date, teams, db)
    if dolastweek:
        output += printintermediateresults(date - datetime.timedelta(days=7), teams, db)
    for w in range(week, 0, -1):
        weeklog = [t for t in teamlog if t[0]==w]
        print(">>>> Week ", w)
        print(weeklog)
        if weeklog:
            output += printfinalresults(w, weeklog, teams)
    inp = open('index.template')
    tpl = Template(inp.read())
    outstr = '\n'.join(output)
    outstr2 = '\n'.join(output2)
    subst = {'table':outstr, 'table2':outstr2, 'week':str(date.isocalendar()[1]).zfill(2)}
    result = tpl.substitute(subst)
    inp.close()
    out = open('html/index.html', 'w')
    out.write(result)
    out.close()
    db.close()
 

def mkTeams(date):
    for week in range(1, date.isocalendar()[1]+1):
        print("teams week:", week)
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
            runners = sorted(runners, key=lambda x: x[3], reverse = True)
            numberofrunners = len(runners)
            odd = True
            for r in runners:
                rdata = c1.execute('SELECT COALESCE(distance,0),wasill FROM wlog WHERE runnerid=? AND week=?', (r[0], week)).fetchone()
                print(" ////////// ", r[0], week, rdata)
                rmileage = rdata[0] 
                rgoal = r[3]/52
                if rdata[1]==0:
                    alt = ' class="alt"' if odd else ''
                    tmileage += rmileage
                    tgoal += rgoal
                    tpct += rmileage*100/rgoal
                    ill = ""
                else:
                    numberofrunners -= 1
                    alt = ' class="alt ill"' if odd else ' class="ill"'
                    ill = "ДА"
                outteam.append('                 <tr{}><td><a href="http://aerobia.ru/users/{}">{}</a></td><td>{:0.2f}</td><td>{:0.2f}</td><td>{:0.2f}</td><td>{}</td></tr>'.format(alt, r[0], r[1], rgoal, rmileage, rmileage*100/rgoal, ill))
                odd = not odd
            print(t, tgoal, tmileage)
            outteam.append('               <tfoot><tr><td>Всего:</td><td>{:0.2f}</td><td>{:0.2f}</td><td>{:0.2f}</td><td></td></tr></tfoot>'.format(tgoal, tmileage, tpct/numberofrunners))
            outteam.append('               </tbody>')
            outteam.append('            </table></div>')
            outteam.append('            <br />')
        outteambox=[]
        outteambox.append('    <nav class="sub">')
        outteambox.append('      <ul>')
        for w in range(1,date.isocalendar()[1]+1):
            if w == week:
                outteambox.append('        <li class="active"><span>{} неделя</span></li>'.format(w))
    #        elif os.path.isfile("html/teams{:02d}.html".format(w)):
    #            print("statistics{:02d}.html exists".format(w))
            else:
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
        subst = {'box':outbox, 'table':outstr, 'week':str(date.isocalendar()[1]).zfill(2)}
        result = tpl.substitute(subst)
        inp.close()
        out = open('html/teams{:02d}.html'.format(week), 'w')
        out.write(result)
        out.close()
        db.close()


def mkStat(date):
    dolastweek = date.weekday() < 2
    for weeksago in range(0, date.isocalendar()[1]):
        dodate = date - datetime.timedelta(days=7*weeksago)
        w = week_range(dodate)
        week = w[0]
        print("stats week:", week, "weeks ago: ", weeksago, "dodate ", dodate)
        db = sqlite3.connect('aerobia.db')
        c1 = db.cursor()
        outstat = []
        outstat.append('            <br />')
        outstat.append('            <center>')
        outstat.append('                <h1>Лучший бегун {} недели:</h1>'.format(week))
        outstat.append('                <h1>Митя ☮ Фруктенштейн</h1>')
        outstat.append('                <h2>(самый остроумный)</h2>')
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
            outstat.append('                <h1><a href="http://aerobia.ru/users/{}">{}</a> — {:0.2f} км.</h1>'.format(winner[0], winnername[0], winner[1]))
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
            outstat.append('                <h1><a href="http://aerobia.ru/users/{}">{}</a> — {:0.2f}%</h1>'.format(winner[0], winnername[0], winner[1]))
            outstat.append('                <hr />')
            outstat.append('            </center>')
            outstat.append('')
    
        outstatbox=[]
        outstatbox.append('    <nav class="sub">')
        outstatbox.append('      <ul>')
        for w in range(1,date.isocalendar()[1]+1):
            if w == week:
    #            print("current week")
                outstatbox.append('        <li class="active"><span>{} неделя</span></li>'.format(w))
    #        elif os.path.isfile("html/statistics{:02d}.html".format(w)):
    #            print("statistics{:02d}.html exists".format(w))
            else:
                outstatbox.append('        <li><a href="statistics{0:02d}.html">{0} неделя</a></li>'.format(w))
    #        else:
    #            print("statistics{:02d}.html doesn't exist".format(w))
    #            outstatbox.append('        <li>{} неделя</li>'.format(w))
        outstatbox.append('      </ul>')
        outstatbox.append('    </nav>')
        inp = open('statistics.template')
        tpl = Template(inp.read())
        print("       ))))) week:", week, " isocalendar[1]: ", date.isocalendar()[1], "dolastweek: ", dolastweek)
        if week == date.isocalendar()[1] or (week == date.isocalendar()[1]-1 and dolastweek):
            outstat = []
            outstat.append('    <h1>Результаты недели будут подведены позже</h1>')
        outstr = '\n'.join(outstat)
        outbox = '\n'.join(outstatbox)
        subst = {'box':outbox, 'data':outstr, 'week':str(date.isocalendar()[1]).zfill(2)}
        result = tpl.substitute(subst)
        inp.close()
        out = open('html/statistics{:02d}.html'.format(week), 'w')
        out.write(result)
        out.close()
        db.close()

def mkRules(now):
        inp = open('rules.template')
        tpl = Template(inp.read())
        subst = {'week':str(now.isocalendar()[1]).zfill(2)}
        result = tpl.substitute(subst)
        inp.close()
        out = open('html/rules.html', 'w')
        out.write(result)
        out.close()


print("-------------------- ",datetime.datetime.now())
now = datetime.date.today()
#mkIndex(now - datetime.timedelta(days=7))
#mkTeams(now - datetime.timedelta(days=7))
#mkStat(now - datetime.timedelta(days=7))
mkIndex(now)
mkTeams(now)
mkStat(now)
mkRules(now)
print("-------------------- ",datetime.datetime.now())


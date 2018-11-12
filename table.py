#!/usr/bin/python3

import sqlite3
import datetime
import pytz
import os
from string import Template
import config

def week_range(date):
    utc=pytz.UTC
    year, week, dow = date.isocalendar()
    week = int(date.strftime("%W"))
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
    print("====== Intermediate:", date.strftime("%W"))
    c1 = db.cursor()
    c2 = db.cursor()
    output = []
    output.append('            <center>')
    output.append('                <h1>Предварительные результаты {} недели</h1>'.format(date.strftime("%W")))
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
            d = c2.execute('SELECT COALESCE(distance,0),wasill,wplan FROM wlog WHERE runnerid=? AND week=?', (r, weekrange[0])).fetchone()
#            (d,) = c2.execute('SELECT SUM(distance) FROM log WHERE runnerid=? AND date > ? AND date < ? AND isill=0', (r, weekrange[1].isoformat(), weekrange[2].isoformat())).fetchone()
            if d and not d[1]:
                print("   +++ ", r, d[0], d[2], 100*d[0]/d[2])
                tgoal += d[2]
                tmileage += d[0]
                tpct += 100*d[0]/d[2]
            if d and d[1]:
                illcount += 1
        tbl.append([t[1], tgoal, tmileage, tpct/(len(runners)-illcount)])
        print("   ==== team ", [t[1], tgoal, tmileage, tpct/(len(runners)-illcount)])
    tbl = sorted(tbl, key=lambda x: x[3], reverse = True)
    odd = True
    for team in tbl:
        alt = ' class="alt"' if odd else ''
        output.append('                    <tr{}><td>{}</td><td>{:0.2f}</td><td>{:0.2f}</td><td>{:0.2f}</td></tr>'.format(alt, team[0], team[1], team[2], team[3]))
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
        week = int(date.strftime("%W")) - 2
    else:
        week = int(date.strftime("%W")) - 1
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
#        for row in c1.execute('SELECT teamid, SUM(100*distance/(goal/52))/COUNT(*) AS percentage, SUM(distance), SUM(goal)/52 FROM wlog,runners WHERE wlog.runnerid=runners.runnerid AND week=? AND wlog.wasill=0 GROUP BY teamid ORDER BY percentage DESC',
        for row in c1.execute('SELECT teamid, SUM(100*distance/wplan)/COUNT(*) AS percentage, SUM(distance), SUM(wplan) FROM wlog,runners WHERE wlog.runnerid=runners.runnerid AND week=? AND wlog.wasill=0 GROUP BY teamid ORDER BY percentage DESC',
                (w,)).fetchall():
            totalrunners=c1.execute('SELECT COUNT(*) FROM wlog,runners WHERE wlog.runnerid=runners.runnerid AND teamid=? AND week=?', (row[0], w)).fetchone()
            illrunners=c1.execute('SELECT COUNT(*) FROM wlog,runners WHERE wlog.runnerid=runners.runnerid AND teamid=? AND week=? AND wasill=1', (row[0], w)).fetchone()
            if illrunners[0]/totalrunners[0] > 0.5:
                oneweeklog.append([w, row[0], -1, row[2], row[3]])
            else:
                oneweeklog.append([w, row[0], row[1], row[2], row[3]])
        oneweeklog = sorted(oneweeklog, key=lambda x: x[2], reverse = True)
        for n,t in enumerate(oneweeklog):
            if t[1]==-1:
                pts = 0
            else:
                pts = len(oneweeklog)*5-n*5-5
            teampoints[t[1]-1] += pts
            oneweeklog[n].append(pts)
            oneweeklog[n].append(teampoints[t[1]-1])
        teamlog += oneweeklog

    output2 = printstandings(teams, teampoints) 

    output = []
    if date < config.ENDCHM:
        output += printintermediateresults(date, teams, db)
    if dolastweek and date < config.ENDCHM:
        output += printintermediateresults(date - datetime.timedelta(days=7), teams, db)
    for w in range(week, 0, -1):
        weeklog = [t for t in teamlog if t[0]==w]
        print(">>>> Week ", w)
        if weeklog:
            output += printfinalresults(w, weeklog, teams)

    if datetime.date.today() >= config.STARTCUP and datetime.date.today() < config.ENDCUP:
        cupoutput = doCup()
    else:
        cupoutput = ['']


    inp = open('index.template')
    tpl = Template(inp.read())
    outstr = '\n'.join(output)
    outstr2 = '\n'.join(output2)
    cupstr = '\n'.join(cupoutput)
    subst = {'cup':cupstr, 'table':outstr, 'table2':outstr2, 'week':date.strftime("%W")}
    result = tpl.substitute(subst)
    inp.close()
    out = open('html/index.html', 'w')
    out.write(result)
    out.close()
    db.close()
 

def mkTeams(date):
    for week in range(1, int(date.strftime("%W"))+1):
        print("teams week:", week)
        eow = datetime.datetime.strptime("2018-W"+str(week)+"-1", "%Y-W%W-%w")
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
            outteam.append('               <thead><tr><th>Имя</th><th>Цель (км/нед)</th><th>Результат (км)</th><th>Выполнено (%)</th><th>Превышение</th></tr></thead>')
            outteam.append('               <tbody>')
            runners = c1.execute('SELECT * FROM runners WHERE teamid=? ORDER BY runnername', (t[0],)).fetchall()
            runners = sorted(runners, key=lambda x: x[3], reverse = True)
            numberofrunners = len(runners)
            odd = True
            for r in runners:
                rdata = c1.execute('SELECT COALESCE(distance,0),wasill,wplan FROM wlog WHERE runnerid=? AND week=?', (r[0], week)).fetchone()
                rmileage = rdata[0] if rdata else 0
                wasill = rdata[1] if rdata else 0
                rgoal = rdata[2] if rdata else r[3]/52
#                yeargoal = rdata[2]*52 if rdata else r[3]
                yeargoal = c1.execute('SELECT COALESCE(SUM(wplan),0) FROM wlog WHERE runnerid=?', (r[0],)).fetchone()[0]
                yeartotal = c1.execute('SELECT COALESCE(SUM(distance),0) FROM log WHERE runnerid=? AND date<?', (r[0], eow)).fetchone()[0]
                print("~~~~~~~ runner: ", r, " eow: ", eow, " total: ", yeartotal, " goal: ", yeargoal)
                if wasill==0:
                    if yeartotal > yeargoal:
                      alt = ' class="alt ill"' if odd else ' class="ill"'
                      ill = "ДА"
                    else:
                      alt = ' class="alt"' if odd else ''
                      ill = ""
                    tmileage += rmileage
                    tgoal += rgoal
                    tpct += rmileage*100/rgoal if rgoal else 100
                    outteam.append('                 <tr{}><td><a href="http://aerobia.ru/users/{}">{}</a></td><td>{:0.2f}</td><td>{:0.2f}</td><td>{:0.2f}</td><td>{}</td></tr>'.format(alt, r[0], r[1], rgoal, rmileage, rmileage*100/rgoal, ill))
                    odd = not odd
                else:
                    numberofrunners -= 1
                    alt = ' class="alt ill"' if odd else ' class="ill"'
                    ill = "ДА"
                    #outteam.append('                 <tr{}><td><a href="http://aerobia.ru/users/{}">{}</a></td><td>{:0.2f}</td><td>{:0.2f}</td><td>{:0.2f}</td><td>{}</td></tr>'.format(alt, r[0], r[1], rgoal, rmileage, rmileage*100/rgoal, ill))
#            print(t, tgoal, tmileage)
            outteam.append('               <tfoot><tr><td>Всего:</td><td>{:0.2f}</td><td>{:0.2f}</td><td>{:0.2f}</td><td></td></tr></tfoot>'.format(tgoal, tmileage, tpct/numberofrunners))
            outteam.append('               </tbody>')
            outteam.append('            </table></div>')
            outteam.append('            <br />')
        outteambox=[]
        outteambox.append('    <nav class="sub">')
        outteambox.append('      <ul>')
        for w in range(1,int(date.strftime("%W"))+1):
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
        subst = {'box':outbox, 'table':outstr, 'week':date.strftime("%W")}
        result = tpl.substitute(subst)
        inp.close()
        out = open('html/teams{:02d}.html'.format(week), 'w')
        out.write(result)
        out.close()
        db.close()


def mkStat(date):
    dolastweek = date.weekday() < 2
    for weeksago in range(0, int(date.strftime("%W"))):
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
        outstat.append('                <hr />')
        outstat.append('            </center>')
        outstat.append('')
    
        winner = c1.execute('SELECT runnerid, MAX(distance) FROM wlog WHERE week=? and wasill=0',(week,)).fetchone()
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
    
        winner = c1.execute('SELECT runnerid, MAX(100*distance/wplan) FROM wlog WHERE week=?',(week,)).fetchone()
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
        for w in range(1,int(date.strftime("%W"))+1):
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
        print("       ))))) week:", week, " week: ", date.strftime("%W"), "dolastweek: ", dolastweek)
        if week == int(date.strftime("%W")) or (week == int(date.strftime("%W"))-1 and dolastweek):
            outstat = []
            outstat.append('    <h1>Результаты недели будут подведены позже</h1>')
        outstr = '\n'.join(outstat)
        outbox = '\n'.join(outstatbox)
        subst = {'box':outbox, 'data':outstr, 'week':date.strftime("%W")}
        result = tpl.substitute(subst)
        inp.close()
        out = open('html/statistics{:02d}.html'.format(week), 'w')
        out.write(result)
        out.close()
        db.close()

def mkRules(now):
        inp = open('rules.template')
        tpl = Template(inp.read())
        subst = {'week':now.strftime("%W")}
        result = tpl.substitute(subst)
        inp.close()
        out = open('html/rules.html', 'w')
        out.write(result)
        out.close()

def doCup():
    print("UUUUUUUUUUU")
    today = datetime.date.today()
    startcupweek = int(config.STARTCUP.strftime("%W"))
    endcupweek = int(config.LASTCUP.strftime("%W"))
    week = int(today.strftime("%W"))
    cupweek = week - startcupweek + 1
    dow = today.isocalendar()[2]
    db = sqlite3.connect('aerobia.db')
    c1 = db.cursor()
    teams = c1.execute('SELECT teamid FROM playoff WHERE bracket=1 OR bracket=2').fetchall()
    cup = []
    doweeks = []
    if week >= startcupweek and week <= endcupweek:
        doweeks.append(week)
    if week > startcupweek and dow <3:
        doweeks.append(week-1)
    for w in doweeks:
        (_, wstart, wend) = week_range(config.STARTCUP + datetime.timedelta(days=((w-startcupweek)*7)))
        for t in teams:
            runners = c1.execute('SELECT runnerid FROM runners WHERE teamid = ?', (t[0],)).fetchall()
            runnerids = [i[0] for i in runners]
            print (t, w, wstart, wend)
            print('SELECT COALESCE(SUM(distance),0) FROM log WHERE runnerid IN ({}) AND date > ? AND date < ?'.format(','.join(map(str,runnerids))))
            d = c1.execute('SELECT COALESCE(SUM(distance),0) FROM log WHERE runnerid IN ({}) AND date > ? AND date < ?'.format( ','.join(map(str,runnerids))), (wstart, wend)).fetchone()[0]
            print(d)
            c1.execute('INSERT OR REPLACE INTO cup VALUES (?, ?, ?)', (t[0], w, d))
            cup.append([w,t[0],d])
            db.commit()
    print(cup)
    db.close()
    output = []
#    if today > CONFIG.startcup:
    output.append('            <center>')
    output.append('                <h1>Кубок Аэробии</h1>'.format(w))
    output.append('                <br />')
    output.append('                <br />')
    output.append('            </center>')
    for i in [1,2,3]:
        output.extend(printbracket(i))
    output.append('            <br />')
    output.append('            <hr />')
    return output

def printbracket(n):
    today = datetime.date.today()
    week = int(today.strftime("%W"))
    startcupweek = int(config.STARTCUP.strftime("%W"))
    endcupweek = int(config.LASTCUP.strftime("%W"))
    o = []
    db = sqlite3.connect('aerobia.db')
    c1 = db.cursor()
    o.append('            <center>')
    if n in [1,2]:
        o.append('                <h1>Полуфинал {}</h1>'.format(n))
    else:
        o.append('                <h1>Финал</h1>'.format(n))
    o.append('                <br />')
    o.append('                <br />')
    o.append('            </center>')
    o.append('            <div class="datagrid"><table>')
    o.append('               <thead><tr><th>Неделя</th><th>Команда</th><th>Результат (км)</th></thead>')
    o.append('               <tbody>')
    teams = c1.execute('SELECT teamid FROM playoff WHERE bracket=?', (n,)).fetchall() 
    if not teams:
        teams = ((0,),(0,))
        teamnames = ('?','?')
    else:
        t1 = c1.execute('SELECT teamname FROM teams WHERE teamid=?',(teams[0][0],)).fetchone()[0]
        t2 = c1.execute('SELECT teamname FROM teams WHERE teamid=?',(teams[1][0],)).fetchone()[0]
        teamnames = (t1, t2)
    for w in range (0,3):
        (dist1,) = c1.execute('SELECT COALESCE(distance,0) FROM cup WHERE teamid=? AND week=?', (teams[0][0], startcupweek+w)).fetchone() or (0.0,)
        (dist2,) = c1.execute('SELECT COALESCE(distance,0) FROM cup WHERE teamid=? AND week=?', (teams[1][0], startcupweek+w)).fetchone() or (0.0,)
        print('D1:',dist1)
        print('D2:',dist2)
        o.append('             <tr><td rowspan="2">{}</td><td>{}</td><td>{:0.2f}</td></tr>'.format(w,teamnames[0],dist1))
        o.append('             <tr><td>{}</td><td>{:0.2f}</td></tr>'.format(teamnames[1],dist2))
    o.append('               </tbody>')
    o.append('            </table></div>')
    return o

#            for r in runners:
#                teamdistance += c1.execute('SELECT COALESCE(SUM(distance),0) FROM log WHERE runnerid = ? AND date > ? AND date < ?', (r, wstart, wend)).fetchone()[0]





print("-------------------- ",datetime.datetime.now())
now = datetime.date.today()
if now > config.STARTCHM and now < config.ENDCHM:
    #mkIndex(now - datetime.timedelta(days=7))
    #mkTeams(now - datetime.timedelta(days=7))
    #mkStat(now - datetime.timedelta(days=7))
    mkIndex(now)
    mkTeams(now)
    mkStat(now)
    mkRules(now)
elif now > config.STARTCUP:
    mkIndexCup(now)
    mkTeamsCup(now)
    mkStatCup(now)
    mkRules(now)
print("-------------------- ",datetime.datetime.now())


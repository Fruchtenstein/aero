#!bin/python

import sqlite3
import datetime
from string import Template


def mkIndex(week):
    db = sqlite3.connect('aerobia.db')
    c1 = db.cursor()
    teams = c1.execute('SELECT * FROM teams ORDER BY teamid').fetchall()
    tbl = []
    
    for t in teams:
        tgoal = c1.execute('SELECT coalesce(sum(goal),0) FROM runners WHERE teamid=? AND isill=0', (t[0],)).fetchone()[0]/52
        runners = c1.execute('SELECT runnerid FROM runners WHERE teamid=? AND isill=0', (t[0],)).fetchall()
        tmileage = 0
        tpercentage = 0
        for r in runners:
            rmileage = c1.execute('SELECT coalesce(sum(distance),0) FROM wlog WHERE runnerid=? AND week=?', (r[0], week)).fetchone()[0]
            rgoal = c1.execute('SELECT goal FROM runners WHERE runnerid=? AND isill=0', (r[0],)).fetchone()[0]/52
            print(r[0], week, rmileage, rgoal)
            print("{}: {:.2f} {:.2f} {:.2f}".format(r[0], rmileage, rgoal, rmileage*100/rgoal))
            tmileage += rmileage
            tpercentage += rmileage*100/rgoal
        tpercentage = tpercentage/len(runners)
        print("==== Team ", t[1])
        print(".... tgoal:   ", tgoal)
        print(".... tmileage:", tmileage)
        print(".... sum pct: ", tmileage*100/tgoal)
        print(".... avg pct: ", tpercentage)
        tbl.append([t[0], t[1], tgoal, tmileage, tmileage*100/tgoal, tpercentage])
    
    tbl = sorted(tbl, key=lambda x: x[5], reverse = True)
    output = []
    output.append('            <center>')
    output.append('                <h1>Результаты {} недели</h1>'.format(week))
    output.append('            </center>')
    
    output.append('            <div class="datagrid"><table>')
    output.append('               <thead><tr><th>Команда</th><th>Цель (км/нед)</th><th>Результат (км)</th><th>Выполнено (%)</th><th>Очки</th></tr></thead>')
    output.append('               <tbody>')
    odd = True
    for n, t in enumerate(tbl):
        alt = ' class="alt"' if odd else ''
        pts = len(teams)*5-n*5-5
        output.append('                 <tr{}><td>{}</td><td>{:.2f}</td><td>{:.2f}</td><td>{:.2f}</td><td>{}</td></tr>'.format(alt, t[1], t[2], t[3], t[5], pts))
        c1.execute('INSERT OR REPLACE INTO tlog VALUES (?, ?, ?, ?)', (t[0], week, pts, t[5]))
        odd = not odd
    output.append('               </tbody>')
    output.append('            </table></div>')
    
    db.commit()
    
    output2 = []
    output2.append('            <center>')
    output2.append('                <h1>Таблица соревнования на {} неделю</h1>'.format(week))
    output2.append('            </center>')
    
    output2.append('            <div class="datagrid"><table>')
    output2.append('               <thead><tr><th>Команда</th><th>Очки</th></tr></thead>')
    output2.append('               <tbody>')
    odd = True
    tbl=[]
    for t in teams:
        pts = c1.execute('SELECT coalesce(SUM(pts),0) FROM tlog WHERE teamid=?',(t[0],)).fetchone()[0]
        tbl.append([t[1], pts])
    
    tbl = sorted(tbl, key=lambda x: x[1], reverse = True)
    for n, t in enumerate(tbl):
        alt = ' class="alt"' if odd else ''
        output2.append('                 <tr{}><td>{}</td><td>{}</td></tr>'.format(alt, t[0], t[1]))
        odd = not odd
    output2.append('               </tbody>')
    output2.append('            </table></div>')
    
    
    inp = open('index.template')
    tpl = Template(inp.read())
    outstr = '\n'.join(output)
    outstr2 = '\n'.join(output2)
    subst = {'table':outstr, 'table2':outstr2}
    result = tpl.substitute(subst)
    inp.close()
    out = open('html/index.html', 'w')
    out.write(result)
    out.close()
 

def mkTeams(week):
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
        outteam.append('            <center>')
        outteam.append('                <h2>{}</h2>'.format(t[1]))
        outteam.append('            </center>')
        outteam.append('            <div class="datagrid"><table>')
        outteam.append('               <thead><tr><th>Имя</th><th>Цель (км/нед)</th><th>Результат (км)</th><th>Выполнено (%)</th></tr></thead>')
        outteam.append('               <tbody>')
        runners = c1.execute('SELECT * FROM runners WHERE teamid=?', (t[0],)).fetchall()
        odd = True
        for r in runners:
            alt = ' class="alt"' if odd else ''
            if r[4]==0:
                rmileage = c1.execute('SELECT distance FROM wlog WHERE runnerid=? AND week=?', (r[0], week)).fetchone()[0]
                rgoal = r[3]/52
            else:
                rmileage = 0
                rgoal = 0
            outteam.append('                 <tr{}><td>{}</td><td>{:0.2f}</td><td>{:0.2f}</td><td>{:0.2f}</td></tr>'.format(alt, r[1], rgoal, rmileage, rmileage*100/rgoal))
            odd = not odd
        outteam.append('               </tbody>')
        outteam.append('            </table></div>')
        outteam.append('            <br />')
    
    inp = open('teams.template')
    tpl = Template(inp.read())
    outstr = '\n'.join(outteam)
    subst = {'table':outstr}
    result = tpl.substitute(subst)
    inp.close()
    out = open('html/teams.html', 'w')
    out.write(result)
    out.close()


def mkStat(week):
    outstat = []
    outstat.append('            <br />')
    outstat.append('            <center>')
    outstat.append('                <h1>Лучший бегун {} недели:</h1>'.format(week))
    outstat.append('                <h1>Dimitri ☮ Fruchtenstein</h1>'.format(week))
    outstat.append('                (по совокупности заслуг)'.format(week))
    outstat.append('            </center>')
    outstat.append('')
    
    inp = open('statistics.template')
    tpl = Template(inp.read())
    outstr = '\n'.join(outstat)
    subst = {'data':outstr}
    result = tpl.substitute(subst)
    inp.close()
    out = open('html/statistics.html', 'w')
    out.write(result)
    out.close()

print("-------------------- ",datetime.datetime.now())
for i in range(10,0,-1):
    week = (datetime.date.today() - datetime.timedelta(days=7*i)).isocalendar()[1]
    mkIndex(week)
week = (datetime.date.today() - datetime.timedelta(days=7)).isocalendar()[1]
mkTeams(week)
mkStat(week)
print("-------------------- ",datetime.datetime.now())


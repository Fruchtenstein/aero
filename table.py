#!bin/python

import sqlite3
import datetime
from string import Template


week = (datetime.date.today() - datetime.timedelta(days=7)).isocalendar()[1]
db = sqlite3.connect('aerobia.db')
c1 = db.cursor()
teams = c1.execute('SELECT * FROM teams ORDER BY teamid').fetchall()
tbl = []

#t = teams[0]
#tgoal = c1.execute('SELECT sum(goal) FROM runners WHERE teamid=?', (t[0],)).fetchone()[0]
#runners = c1.execute('SELECT runnerid FROM runners WHERE teamid=?', (t[0],)).fetchall()
#tmileage = 0
#for r in runners:
#    mileage = c1.execute('SELECT sum(distance) FROM log WHERE runnerid=? AND week=?', (r[0], week)).fetchone()
#    tmileage += mileage[0]
#tbl.append([t[1], tgoal, tmileage / tgoal])
for t in teams:
    tgoal = c1.execute('SELECT sum(goal) FROM runners WHERE teamid=?', (t[0],)).fetchone()[0]/52
    runners = c1.execute('SELECT runnerid FROM runners WHERE teamid=?', (t[0],)).fetchall()
    tmileage = 0
    for r in runners:
        mileage = c1.execute('SELECT sum(distance) FROM log WHERE runnerid=? AND week=?', (r[0], week)).fetchone()[0]
        print(r, mileage)
        tmileage += mileage
    tbl.append([t[1], tgoal, tmileage, tmileage*100/tgoal])
tbl = sorted(tbl, key=lambda x: x[3], reverse = True)
output = []
output.append('            <center>')
output.append('                <h1>Таблица соревнования: результаты {} недели</h1>'.format(week))
output.append('            </center>')

output.append('            <div class="datagrid"><table>')
output.append('               <thead><tr><th>Команда</th><th>Цель (км/нед)</th><th>Результат (км)</th><th>Выполнено %</th><th>Очки</th></tr></thead>')
output.append('               <tbody>')
odd = True
for n, t in enumerate(tbl):
    alt = ' class="alt"' if odd else ''
    pts = len(teams)*5-n*5-5
    output.append('                 <tr{}><td>{}</td><td>{:.2f}</td><td>{:.2f}</td><td>{:.2f}</td><td>{}</td></tr>'.format(alt, t[0], t[1], t[2], t[3], pts))
    odd = not odd
output.append('               </tbody>')
output.append('            </table></div>')
#print('\n'.join(output))
inp = open('index.template')
tpl = Template(inp.read())
outstr = '\n'.join(output)
subst = {'table':outstr}
result = tpl.substitute(subst)
inp.close()
out = open('html/index.html', 'w')
out.write(result)
out.close()
 


# template = open('index.template')
# src = Template( filein.read() )
# #document data
# title = "This is the title"
# subtitle = "And this is the subtitle"
# d={ 'title':title, 'subtitle':subtitle, 'list':'\n'.join(list) }
# #do the substitution
# result = src.substitute(d)
# print result

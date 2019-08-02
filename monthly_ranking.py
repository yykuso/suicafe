#!/usr/bin/python
# -*- coding: utf-8 -*-
import datetime
import json
import requests
import os
import MySQLdb

from config import *

filedir = os.path.dirname(__file__) + '/'

today   = datetime.date.today()
this_year  = today.year
this_month = today.month
last_year  = today.year
last_month = today.month - 1
if this_month == 1:
    last_year  = this_year - 1
    last_month = 12

target_month = '%4d-%02d' % (last_year,last_month)

print 'target month is ' + target_month

print 'DB Checking...'
connector = MySQLdb.connect(host=sql_host, db=sql_db, user=sql_user, passwd=sql_passwd, charset="utf8")
cursor = connector.cursor()

# タッチユーザが登録されているかDBに問い合わせる
sql = "SELECT name, count(name) as count FROM drink_log INNER JOIN users ON drink_log.id = users.id where date_format(timestamp, '%Y-%m') = '" + target_month + "' GROUP BY name ORDER BY count DESC;"
cursor.execute(sql)
ranking_res = cursor.fetchall()

if ranking_res == ():
    # slackに通知
    requests.post(SlackHookURL, data = json.dumps({
            'text' : u'先月は誰一人とコーヒーを飲んでないみたいです．',
            'username' : u'SuiCafe',
            'link_names': 1,
    }))

else:
    max_len = 0
    for data in ranking_res:
        temp_len = len(data[0])
        if max_len < temp_len: max_len = temp_len

    text = '<!channel> '

    print '{0:d}年{1:d}月のコーヒーランキングです！'.format(last_year, last_month)
    text += '{0:d}年{1:d}月のコーヒーランキングです！\n'.format(last_year, last_month)

    for data in ranking_res:
        print '{0:<{width}}{1:2d}杯'.format(data[0], data[1], width = max_len+4)
        text += '{0:<{width}}{1:2d}杯\n'.format(data[0], data[1], width = max_len+4)

    print '{0:d}月もがんばりましょう\n\n飲んだ人は“杯数x25円“をkyashで投げてください！'.format(this_month)
    text += '{0:d}月もがんばりましょう\n\n飲んだ人は“杯数x25円“をkyashで投げてください！'.format(this_month)

    # slackに通知
    requests.post(SlackHookURL, data = json.dumps({
            'text' : text,
            'username' : u'SuiCafe',
            'link_names': 1,
    }))
# end if

cursor.close()
connector.close()


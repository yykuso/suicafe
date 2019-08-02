#!/usr/bin/python
# -*- coding: utf-8 -*-
import binascii
import nfc
import time
from threading import Thread, Timer
from Crypto.Cipher import AES
import base64
import hashlib
import datetime
import requests
import json
import MySQLdb

from config import *
import se

################################################################################
# AES暗号化
def get_encrypt_data(raw_data, key, iv):
    raw_data_base64 = base64.b64encode(raw_data)
    # 16byte
    if len(raw_data_base64) % 16 != 0:
        raw_data_base64_16byte = raw_data_base64
        for i in range(16 - (len(raw_data_base64) % 16)):
            raw_data_base64_16byte += "_"
    else:
        raw_data_base64_16byte = raw_data_base64

    secret_key  = hashlib.sha256(key).digest()
    iv          = hashlib.md5(iv).digest()
    crypto      = AES.new(secret_key, AES.MODE_CBC, iv)
    cipher_data = crypto.encrypt(raw_data_base64_16byte)
    cipher_data_base64 = base64.b64encode(cipher_data)

    return cipher_data_base64
################################################################################
# nfc用
#   Suica待ち受けの1サイクル秒
TIME_cycle = 1.0
#   Suica待ち受けの反応インターバル秒
TIME_interval = 0.2
#   タッチされてから次の待ち受けを開始するまで無効化する秒
TIME_wait = 3
#   NFC接続リクエストのための準備
#   212F(FeliCa)で設定
target_req_suica = nfc.clf.RemoteTarget("212F")
#   0003(Suica)
target_req_suica.sensf_req = bytearray.fromhex("0000030000")
################################################################################

print 'Suica waiting...'
while True:
    # USBに接続されたNFCリーダに接続してインスタンス化
    clf = nfc.ContactlessFrontend('usb')
    # Suica待ち受け開始
    # clf.sense( [リモートターゲット], [検索回数], [検索の間隔] )
    target_res = clf.sense(target_req_suica, iterations=int(TIME_cycle//TIME_interval)+1 , interval=TIME_interval)

    if target_res != None:

        now = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")

        tag = nfc.tag.activate(clf,target_res)
        tag.sys = 3

        #IDmを取り出す
        idm = binascii.hexlify(tag.idm)
        #idmをAESで暗号化
        crypto_idm = get_encrypt_data(idm, idm_key, idm_iv)

        print 'Suica detected.'
        print 'now        = ' + now
        print 'idm        = ' + idm
        print 'crypto_idm = ' + crypto_idm

        connector = MySQLdb.connect(host=sql_host,
                                    db=sql_db,
                                    user=sql_user,
                                    passwd=sql_passwd,
                                    charset="utf8")
        cursor = connector.cursor()

        # タッチユーザが登録されているかDBに問い合わせる
        usercheck_sql = "SELECT name FROM users WHERE id = '" + crypto_idm + "'"
        cursor.execute(usercheck_sql)
        usercheck_res = cursor.fetchall()

        if usercheck_res == ():                     # 非登録ユーザーだった時の処理
            usercheck_res = 'UNKNOWN'

            # 効果音を鳴らす
            se.play(False)

            # slackに通知
            requests.post(SlackHookURL, data = json.dumps({
                    'text' : u'登録されていないユーザがICカードをタッチしました．\n未登録の場合は管理者までご連絡ください．',
                    'username' : u'SuiCafe',
                    'link_names': 1,
            }))

        else:
            # 効果音を鳴らす
            se.play(True)

            # DBにアップロード
            usercheck_res = (usercheck_res[0])[0]   # UserNameを抜き出す
            drinklog_sql = u"INSERT INTO drink_log (timestamp, id) VALUES ('" + now + "', '" + crypto_idm + "')"
            cursor.execute(drinklog_sql)
            connector.commit()

            # slackに通知
            requests.post(SlackHookURL, data = json.dumps({
                    'text' : usercheck_res + u'さんがラボで「コーヒータイム」中です！',
                    'username' : u'SuiCafe',
                    'link_names': 1,
            }))

        print 'User Name  = ' + usercheck_res

        cursor.close()
        connector.close()

        print 'completed upload!'
        print 'sleep ' + str(TIME_wait) + ' seconds'
        time.sleep(TIME_wait)
        print 'Suica waiting...'

    #end if
    clf.close()
#end while

p.terminate()

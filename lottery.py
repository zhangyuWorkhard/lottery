#!/usr/bin/python
# -*- coding:utf-8 -*-

from bs4 import BeautifulSoup

import urllib
import bs4
import requests
import time
import schedule
import json

#check mode 
#1: check latest by timer 3600s and if win a prize then send message to ifttt 
#2: check latest 30 times award number
#3: just check latest award number and if win a prize then send message to ifttt
CHECK_MODE = 3
#set you ifttt key
IFTTT_KEY = ''
#message type
MESSAGE_AWARD_NUMBER = 0
MESSAGE_COUNT15 = 1
#Notify mode
NOTIFY_BY_IFTTT = 0
NOTIFY_BY_PHONENUMBER = 1

#default number
check_number_red = []
check_number_blue = []

prizeData = [] 
checked_red = []
checked_blue = []
f_award_number_start = 0

def get_prize_data():
    print "get data form chart.lottery.gov.cn..."
    page = urllib.urlopen('http://chart.lottery.gov.cn//dltBasicKaiJiangHaoMa.do?typ=1&issueTop=30')
    pageCode = page.read()
    page.close()

    #pageFile = open('pageCode.txt','w')
    #pageFile.write(pageCode)
    #pageFile.close()

    return pageCode 

def create_list(obj):
    if type(obj) is bs4.element.Tag:
        #find Issue and get number
        if len(obj.select('.Issue')) > 0:
            tmpDate = {"NO":obj.select('.Issue')[0].string, "red":[], "blue":[]}
            #print(obj.select('.Issue')[0].string)
            for item in obj.select('.B_1'):
                tmpDate["red"].append(item.string)
                #print(item.string)
            for item in obj.select('.B_5'):
                tmpDate["blue"].append(item.string)
                #print(item.string)
            prizeData.append(tmpDate)

    if obj.next_sibling == None:
        return 
    create_list(obj.next_sibling)

def check_prize(list_d):
    del checked_blue[:]
    del checked_red[:]
    #check red
    for index in check_number_red:
        for x in list_d["red"]:
            if index == x:
                checked_red.append(index)
                break
    #check blue
    #for index in check_number_blue:
    #    for x in list_d["blue"]:
    #        if index == x:
    #            checked_blue.append(index)
    #            break
    map(f_check_blue, list_d["blue"])
    
def f_check_blue(number):
    for index in check_number_blue:
        if index == number:
            checked_blue.append(number)
            return number

def check_30_times_award_number():
    print "chack prize..."
    for i, item in enumerate(prizeData):
        if i%5 == 0:
            print "-----------------------------------"
        check_prize(item)
        print prizeData[i]["NO"], checked_red, checked_blue

def check_latest_award_number():
    global f_award_number_start
    global check_number_red
    global check_number_blue
    soup = BeautifulSoup(get_prize_data(), 'html.parser', from_encoding = 'gb2312')
    print "analysis data..."
    create_list(soup.tr)
    #get user data
    jsonData = get_user_data()
    for x in jsonData["data"]:
        check_number_red = x["red"]
        check_number_blue = x["blue"]

        print "check last prize result..." + x["name"]
        if check_latest_prize_result():
            if x["NotifyMode"] == NOTIFY_BY_IFTTT:
                IFTTT_KEY = x["key"]
                send_message_to_ifttt(MESSAGE_AWARD_NUMBER)
            elif x["NotifyMode"] == NOTIFY_BY_PHONENUMBER:
                #send by phone number
                print "1"
        #check start number
        if check_start_number(x["startNO"]):
            x["startNO"] = int(prizeData[-1]["NO"])
            if x["NotifyMode"] == NOTIFY_BY_IFTTT:
                IFTTT_KEY = x["key"]
                send_message_to_ifttt(MESSAGE_COUNT15)
            elif x["NotifyMode"] == NOTIFY_BY_PHONENUMBER:
                #send by phone number
                print "1"
    save_user_data(jsonData)            
    del prizeData[:]
    soup.decompose()

def main():
    if CHECK_MODE == 1:
        #1:run with schedule
        schedule.every().tuesday.at("8:00").do(check_latest_award_number) 
        schedule.every().thursday.at("8:00").do(check_latest_award_number) 
        schedule.every().sunday.at("8:00").do(check_latest_award_number) 
        while True:
            schedule.run_pending()
            time.sleep(60)
    elif CHECK_MODE == 2:
        #2:print last 30 times prize number
        soup = BeautifulSoup(get_prize_data(), 'html.parser', from_encoding = 'gb2312')
        print "analysis data..."
        create_list(soup.tr)
        check_30_times_award_number()
    elif CHECK_MODE == 3:
        #3:check last prize result
        check_latest_award_number()
    print "check end!"

def check_latest_prize_result():
    check_prize(prizeData[-1])
    print prizeData[-1]["NO"], checked_red, checked_blue
    if (len(checked_red) + len(checked_blue) > 2) or (len(checked_blue) == 2):
        return True
    return False

def send_message_to_ifttt(message_type):
    ifttt_webhook_url = 'https://maker.ifttt.com/trigger/lottery/with/key/' + IFTTT_KEY
    print "send message to ifttt..."
    if message_type == MESSAGE_AWARD_NUMBER:
        tmp = {'value1': prizeData[-1]["NO"], 'value2': checked_red, 'value3': checked_blue}
        requests.post(ifttt_webhook_url, json = tmp)
        return
    elif message_type == MESSAGE_COUNT15:
        tmp = {'value1': prizeData[-1]["NO"], 'value2': "it's time to buy a new lottery"}
        requests.post(ifttt_webhook_url, json = tmp)
        return
    print "same award_number, do not send..."
    return

def get_user_data():
    with open("data.json", "r") as f:
        return json.load(f)

def save_user_data(data):
    with open("data.json","w") as dump_f:
        json.dump(data,dump_f)

def check_start_number(start_number):
    count = 0
    for x in prizeData:
        if x["NO"] >= start_number:
            count += 1
            if count == 15:
               return True 
    return False       

if __name__ == '__main__':
    main()


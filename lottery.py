#lottery

from bs4 import BeautifulSoup

import urllib
import bs4
import requests
import time
import schedule

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

#default number
check_number_red = []
check_number_blue = []

prizeData = [] 
checked_red = []
checked_blue = []
pre_award_number = ''
f_award_number_start = 0
f_award_number_count = 0

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
    global f_award_number_count
    if type(obj) is bs4.element.Tag:
        #find Issue and get number
        if len(obj.select('.Issue')) > 0:
            tmpDate = {"NO":obj.select('.Issue')[0].string, "red":[], "blue":[]}
            if int(tmpDate["NO"]) >= f_award_number_start:
                f_award_number_count += 1
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
    global f_award_number_count
    global f_award_number_start
    soup = BeautifulSoup(get_prize_data(), 'html.parser', from_encoding = 'gb2312')
    print "analysis data..."
    create_list(soup.tr)
    if check_latest_prize_result():
        send_message_to_ifttt(MESSAGE_AWARD_NUMBER)
    if  f_award_number_count == 15:
        f_award_number_count = 0
        f_award_number_start = int(prizeData[-1]["NO"])
        send_message_to_ifttt(MESSAGE_COUNT15)
    del prizeData[:]
    soup.decompose()

def main():
    if CHECK_MODE == 1:
        #1:run with schedule
        schedule.every().monday.at("22:00").do(check_latest_award_number) 
        schedule.every().wednesday.at("22:00").do(check_latest_award_number) 
        schedule.every().saturday.at("22:00").do(check_latest_award_number) 
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
    print "check last prize result..."
    check_prize(prizeData[-1])
    print prizeData[-1]["NO"], checked_red, checked_blue
    if (len(checked_red) + len(checked_blue) > 2) or (len(checked_blue) == 2):
        return True
    return False

def send_message_to_ifttt(message_type):
    global pre_award_number
    ifttt_webhook_url = 'https://maker.ifttt.com/trigger/lottery/with/key/' + IFTTT_KEY
    print "send message to ifttt..."
    if message_type == MESSAGE_AWARD_NUMBER:
        tmp = {'value1': prizeData[-1]["NO"], 'value2': checked_red, 'value3': checked_blue}
        if pre_award_number != prizeData[-1]["NO"]:
            requests.post(ifttt_webhook_url, json = tmp)
            pre_award_number = prizeData[-1]["NO"]
            return
    elif message_type == MESSAGE_COUNT15:
        tmp = {'value1': prizeData[-1]["NO"], 'value2': "it's time to buy a new lottery"}
        requests.post(ifttt_webhook_url, json = tmp)
        return
    print "same award_number, do not send..."
    return

if __name__ == '__main__':
    main()


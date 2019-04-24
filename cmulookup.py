#!/usr/bin/env python3

# sudo easy_install ____
import gspread
from oauth2client.service_account import ServiceAccountCredentials
# basic dependencies
import csv
import json

from time import *
import datetime

def timeFn(f):
    def g(*args):
        start = time()
        requests = f(*args)
        msg = "request" if requests == 1 else "requests"
        print("Ran {} {} in {} seconds".format(requests,msg,time()-start))
    return g


class CMUDirStatic:
    def __init__(self,**kwargs):
        for kwarg in kwargs:
            exec("self.{} = \"{}\"".format(kwarg,kwargs[kwarg]))
    def getName(self,text):
        endKey = "(Student)"
        end = text.find(endKey)
        name = text[:end].split()
        return name[0],name[-1]
    def getClass(self,text,currDate):
        try:
            startKey = "Class Level:"
            endKey = "Names by Which This Person is Known"
            start,end = text.find(startKey),text.find(endKey)
            if currDate.month >= 8:
                fresh,soph,jun,sen = 4,3,2,1
            else:
                fresh,soph,jun,sen = 3,2,1,0
            classes = {"Freshman":fresh,"Sophomore":soph,"Junior":jun,
                       "Senior":sen,"Masters": None}
            stuClass = text[start+len(startKey):end]
            gradYear = str(int(currDate.year) + classes[stuClass])
            return gradYear
        except:
            pass
    def getEmail(self,text):
        startKey,endKey = "Email: ","Andrew UserID: "
        start,end = text.find(startKey),text.find(endKey)
        email = text[start+len(startKey):end]
        return email
    def getID(self,text):
        startKey,endKey = "Andrew UserID: ","Advisor"
        start,end = text.find(startKey),text.find(endKey)
        id = text[start+len(startKey):end]
        return id
    def getMajor(self,text):
        startKey,endKey = "this person is affiliated:","Student Class Level"
        start,end = text.find(startKey),text.find(endKey)
        major = text[start+len(startKey):end]
        return major
    def getAll(self,text):
        first,last = self.getName(text)
        currDate = datetime.datetime.now()
        gradYear = self.getClass(text,currDate)
        email = self.getEmail(text)
        id = self.getID(text)
        major = self.getMajor(text)
        return first,last,gradYear,email,id,major
    def numUpper(self,s):
        count = 0
        for char in s:
            if char.isupper():
                count += 1
        return count
    def cleanHTML(self,responseText):
        startIndicator,endIndicator = "directory name.","Acceptable Use:"
        start = responseText.find(startIndicator)
        end = responseText.find(endIndicator)
        start += len(startIndicator)
        return responseText[start:end].strip()
    def getYearJoined(self):
        currentDate = datetime.datetime.now()
        year = currentDate.year
        season = ""
        if 1 <= currentDate.month <= 7:
            season = "S"
        else:
            season = "F"
        return "{}{}".format(season,str(year)[len(str(year))//2:])
    @timeFn
    def accessDir(self,id):
        import requests
        from bs4 import BeautifulSoup
        # initializing and getting directory request
        addOn = "?action=search&searchtype=basic&search="
        headers = {'user-agent': 'Chrome/60.0.3112.90'}
        numRequests = 0
        dirResponse = requests.get(self.url+addOn+id)
        numRequests += 1
        dirHTML = BeautifulSoup(dirResponse.text,"html.parser")
        # obtaining basic student credentials
        info = self.cleanHTML(dirHTML.text)
        first,last,gradYear,email,id,major = self.getAll(info)
        try:
            L = major.split()
            for i in range(len(L)):
                if self.numUpper(L[i]) > 1 and not L[i].isupper():
                    count = 0; ind = 0
                    while count <= 1:
                        if L[i][ind].isupper():
                            count += 1
                        ind += 1
                    major = " ".join(L[:i]) + " " + L[i][:ind-1]
                    break
        except Exception as e:
            print(e)
        # obtaining college by major
        with open("majorsByCollege.json","r") as f:
            d = json.load(f)
        college = ""
        if major in d:
            college = d[major]
        else:
            pass
        yearJoined = self.getYearJoined()
        self.studentInfo = {"Year Joined":yearJoined,"Andrew ID":id,
                                   "Email":email,"First Name":first,
                        "Last Name":last,"Graduation Year":gradYear,
                                                  "College":college,
                                                      "Major":major}
        return numRequests

    def deployGoogleSheets(self):
        #https://www.twilio.com/blog/2017/02/an-easy-way-to-read-and-write-
        #to-a-google-spreadsheet-in-python.html
        # creation of client to interact with Google Drive API
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        name = 'club.json'
        creds = ServiceAccountCredentials.from_json_keyfile_name(name,scope)
        client = gspread.authorize(creds)
        # opened clubData (share spreadsheet with API email) and call sheet
        # sheet1
        sheet = client.open("clubData").sheet1
        studentKeys = list(self.studentInfo.keys())
        rows = len(sheet.get_all_values())
        if rows == 0:
            for i in range(len(studentKeys)):
                sheet.update_cell(rows+1,i+1,studentKeys[i])
            rows += 1
        rowToAdd = rows+1

        for i in range(len(studentKeys)):
            sheet.update_cell(rowToAdd,i+1, self.studentInfo[studentKeys[i]])

        return str(self.studentInfo)

def lookUp(andrewID):
    andrew_id_valid = False
    cmuSearch = CMUDirStatic(url = "https://directory.andrew.cmu.edu/index.cgi")
    cmuSearch.accessDir(andrewID)
    if len(cmuSearch.studentInfo["Andrew ID"].split()) == 1:
        andrew_id_valid = True
    if andrew_id_valid: return [True, cmuSearch.studentInfo]
    else: return [False, {}]

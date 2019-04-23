#!/usr/bin/env python3

# sudo easy_install ____
import gspread
from oauth2client.service_account import ServiceAccountCredentials
# basic dependencies
import csv
import json
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

options = webdriver.ChromeOptions()
options.add_argument('headless')

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
    def accessDB(self,id):
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
        print(self.studentInfo)
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

class CMUDirDynamic:
    def __init__(self,**kwargs):
        for kwarg in kwargs:
            exec("self.{} = \"{}\"".format(kwarg,kwargs[kwarg]))
        self.table = {"Joined":[],"Andrew ID":[],"Email":[], "First Name":[],
                      "Last Name":[],"Graduation Year":[],"College":[],
                      "Major":[]}
        self.chromeDriver = webdriver.Chrome(r"./chromedriver.exe",
                                             options = options)
        self.chromeDriver.get(self.url)

    # intended to have basic applicability of unique andrew ID's.
    @timeFn
    def seleniumQueryDB(self,*args):
        # code written by Juan Meza
        andrewID = args[0]
        searchPrompt = "//input[@id='basicsearch']"
        searchbar = self.chromeDriver.find_element_by_xpath(searchPrompt)
         #input each andrew ID into the search bar
        searchbar.send_keys(andrewID)
        classSearch = "//input[@class='small']"
        searchbutton = self.chromeDriver.find_element_by_xpath(classSearch)
        #clicks the search button
        searchbutton.click()
        #remember, this gives a list
        contentID = '//*[@id="content"]'
        student_info = self.chromeDriver.find_elements_by_xpath(contentID)
        #this converts the xpath info into nice text
        print(student_info[0].text.splitlines()[0])
        # clears the search bar
        self.chromeDriver.find_element_by_xpath(searchPrompt).clear()
        return len(args)
    def getMissingRows(self):
        result = pd.DataFrame()
        for index,row in self.table.iterrows():
            r = list(row)
            appendBool = False
            for elem in r:
                try:
                    if math.isnan(float(elem)):
                        appendBool = True
                except:
                    pass
            if appendBool:
                newdf = pd.DataFrame(columns = self.table.columns)
                newdf = newdf.append(row)
                result = pd.concat([result,newdf],ignore_index=True,axis=0)
                # note ignore index prevents using row labels that jump
                # in value
        result.to_csv("missingMemberRows.csv")
# cmuDir1 = CMUDirDynamic(url = "https://directory.andrew.cmu.edu/index.cgi")
# cmuDir1.seleniumQueryDB("dvchou")
#
# cmuDir2 = CMUDirStatic(url = "https://directory.andrew.cmu.edu/index.cgi")
# cmuDir2.accessDB("dvchou")

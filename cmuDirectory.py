#!/usr/bin/env python3

# dependencies
import sys,csv,selenium,time
import pandas as pd, requests, math, datetime,json, string
from requests import *
from time import *
# static page data scrape
from bs4 import BeautifulSoup
# note: sudo easy_install selenium

def timeFn(f):
    def g(*args):
        start = time()
        requests = f(*args)
        msg = "request" if requests == 1 else "requests"
        print("Ran {} {} in {} seconds".format(requests,msg,time()-start))
    return g

class CMUDirectory:
    def __init__(self,data,url="https://directory.andrew.cmu.edu/index.cgi"):
        self.url = url
        self.data = pd.read_csv(data)

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
    @timeFn
    def staticQueryDB(self):
        addOn = "?action=search&searchtype=basic&search="
        headers = {'user-agent': 'Chrome/60.0.3112.90'}
        numRequests = 0
        nullityTable = self.data.isnull()
        try:
            for index,row in self.data.iterrows():
                if type(row["Andrew ID"]) != float:
                    dirResponse = requests.get(self.url+addOn+str(row["Andrew ID"]))
                elif type(row["First Name"]) != float:
                    dirResponse = requests.get(self.url+addOn+\
                                           row["First Name"])
                elif type(row["First Name"]) != float and type(row["Last Name"]) == float:
                    dirResponse = requests.get(self.url+addOn+\
                                           row["First Name"]+str(row["Last Name"]))
                numRequests += 1
                dirHTML = BeautifulSoup(dirResponse.text,"html.parser")

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

                with open("majorsByCollege.json","r") as f:
                    d = json.load(f)

                college = ""
                if major in d:
                    college = d[major]
                else:
                    continue
                studentInfo = {"Andrew ID":id,"Email":email,"First Name":first,
                               "Last Name":last,"Graduation Year":gradYear,
                               "College":college,
                               "Major":major}
                for col in self.data.columns:
                    try:
                        if nullityTable.iloc[index][col]:
                            self.data.xs(index)[col] = studentInfo[col]
                    except Exception as e:
                        pass
            self.data.to_csv("newMembersTable.csv")
            return numRequests
        except Exception as e:
            return "{} error".format(e)
    def getMissingRows(self):
        result = pd.DataFrame()
        for index,row in self.data.iterrows():
            r = list(row[:])
            appendBool = False
            for elem in r:
                try:
                    if math.isnan(float(elem)):
                        appendBool = True
                except:
                    pass
            if appendBool:
                newdf = pd.DataFrame(columns = self.data.columns)
                newdf = newdf.append(row)
                result = pd.concat([result,newdf],ignore_index=True,axis=0)
                # note ignore index prevents using row labels that jump
                # in value
        result.to_csv("missingMemberRows.csv")

    def run(self):
        self.getMissingRows()
        self.staticQueryDB()

if __name__ == "__main__":
    try:
        dir = CMUDirectory(sys.argv[1])
        dir.run()
    except Exception as e:
        try:
            dir = CMUDirectory("MembersTable.csv")
            dir.run()
        except Exception as e:
            print("{} error".format(e))

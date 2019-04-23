#!/usr/bin/env python3

import tkinter as tk
from tkinter import *

from cmuDirectorySelenium import *

class BlinkingCursor:
    def __init__(self,x0,y0,x1,y1,fill,width):
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1
        self.fill = fill
        self.width = width
    # draws line along same x value and height of self.y1-self.y0
    def draw(self,c):
        c.create_line(self.x0,self.y0,self.x1,self.y1,fill=self.fill,
                      width=self.width)

class Space:
    def __init__(self,x0,y0,x1,y1,fill):
        self.x0 = x0; self.y0 = y0
        self.x1 = x1; self.y1 = y1
        self.fill = fill
    # draws the rectangle bounded by outline
    def draw(self,c):
        c.create_rectangle(self.x0,self.y0,self.x1,self.y1,fill=self.fill)
    # determines if x,y click inside the barspace
    def inSpace(self,x,y):
        return self.x0<=x<=self.x1 and self.y0<=y<=self.y1
class Input(Space):
    def __init__(self,x0,y0,x1,y1,fill,width):
        super().__init__(x0,y0,x1,y1,fill)
        self.width=width
    # draws input bar space with added thickness argument
    def draw(self,c):
        c.create_rectangle(self.x0,self.y0,self.x1,self.y1,fill=self.fill,
        width = self.width)
class Button(Space): pass

def init(d):
    d.isTyping, d.cursor = False,False
    d.dirScraper = CMUDirStatic(url="https://directory.andrew.cmu.edu/index.cgi")
    d.submitButton = Button(d.width*0.40,d.height*0.60,d.width*0.60,
                            d.height*0.65,fill="lightblue")
    d.inputBar = Input(0,d.height*0.50,d.width,d.height*0.60,
                       fill=None,width=10)
    d.second = 0
    d.incrementedSize = d.width*0.020
    d.currentID = ""
    d.label = ""
def timerFired(d):
    d.second += 1
    if d.second%3 == 0:
        d.cursor = not d.cursor
def keyPressed(e,d):
    if e.keysym not in ["Left","Right","Up","Down"]:
        if e.keysym == "Return":
            try:
                d.dirScraper.accessDB(d.currentID)
                d.dirScraper.deployGoogleSheets()
            except Exception as e:
                print(e)
        elif e.keysym == "BackSpace":
            d.currentID = d.currentID[:-1]
        else:
            d.currentID += e.char
def mousePressed(e,d):
    if d.inputBar.inSpace(e.x,e.y):
        d.isTyping = not d.isTyping
    if d.submitButton.inSpace(e.x,e.y):
        d.dirScraper.accessDB(d.currentID)
        d.label = d.dirScraper.deployGoogleSheets()
def redrawAll(c,d):
    c.create_text(d.width/2,d.height*0.30,
                  text="Club Student Entry\n\nEnter a Query",
                  fill="lightblue",
                  font="Merriweather " + str(int(d.incrementedSize)) + " bold")
    d.inputBar.draw(c)
    d.submitButton.draw(c)
    c.create_text(d.width*0.50,d.height*0.625,text="Submit",fill="darkBlue")
    centerX,centerY = d.width*0.50,d.height*0.55
    c.create_text(centerX,centerY,text=d.currentID,fill="lightblue",
                  font="Merriweather " + str(int(d.incrementedSize)) + " bold")
    if d.isTyping and d.cursor:
        cursor = BlinkingCursor((d.width/2)+\
                                (len(d.currentID)/2)*d.incrementedSize/2.25,
                                d.height*0.5,
                                (d.width/2)+\
                                (len(d.currentID)/2)*d.incrementedSize/2.25,
                                d.height*0.6,fill="lightblue",width=5)
        cursor.draw(c)
    middle = len(d.label)//2
    c.create_text(0,d.height*0.80,anchor="nw",
                  text=d.label[:middle-3]+"\n"+d.label[middle-3:],fill="darkblue",
                  font = "Merriweather " + str(int(d.width*0.017)) + " bold")

def run(width=300, height=300):
    def redrawAllWrapper(canvas, data):
        canvas.delete(ALL)
        canvas.create_rectangle(0, 0, data.width, data.height,
                                fill='white', width=0)
        redrawAll(canvas, data)
        canvas.update()

    def mousePressedWrapper(event, canvas, data):
        mousePressed(event, data)
        redrawAllWrapper(canvas, data)

    def keyPressedWrapper(event, canvas, data):
        keyPressed(event, data)
        redrawAllWrapper(canvas, data)

    def timerFiredWrapper(canvas, data):
        timerFired(data)
        redrawAllWrapper(canvas, data)
        # pause, then call timerFired again
        canvas.after(data.timerDelay, timerFiredWrapper, canvas, data)
    # Set up data and call init
    class Struct(object): pass
    data = Struct()
    data.width = width
    data.height = height
    data.timerDelay = 100 # milliseconds
    init(data)
    # create the root and the canvas
    root = Tk()
    root.resizable(width=False, height=False) # prevents resizing window
    canvas = Canvas(root, width=data.width, height=data.height)
    canvas.configure(bd=0, highlightthickness=0)
    canvas.pack()
    # set up events
    root.bind("<Button-1>", lambda event:
                            mousePressedWrapper(event, canvas, data))
    root.bind("<Key>", lambda event:
                            keyPressedWrapper(event, canvas, data))
    timerFiredWrapper(canvas, data)
    # and launch the app
    root.mainloop()  # blocks until window is closed

if __name__ == "__main__":
    run(600,800)

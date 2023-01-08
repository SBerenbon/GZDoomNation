#!/usr/bin/env python
# -*- coding: utf-8 -*-

import wx
import re
import os

import sys
import glob
import time
import shlex
import platform

from subprocess import Popen

def isIwad(nameoffile):
	f=open(nameoffile, "rb")
	wadHeader=f.read(4)
	f.close()
	if wadHeader==b'PWAD':
		return False
	else:
		return True

#these could all go in a config file
secretiwadlist=["harm1.wad"]
secretipk3list=["square1.pk3"]
home = os.path.expanduser("~")
gzHome=""
gzHomeGlobbing=""
if platform.system()=="Linux":
	gzHome=os.path.join(home, ".config", "gzdoom")
elif platform.system()=="Darwin":
	#TODO: Where does GZDoom live in OS X?
	gzHome=os.path.join(home, ".config", "gzdoom")
elif platform.system()=="Windows":
	#TODO: Where does GZDoom live in Windows?
	#Well, you run it from wherever, and drop the files on the executable
	gzHome=os.getcwd()
gzHomeGlobbing=gzHome+os.path.sep
os.chdir(gzHome)

class TheWindow(wx.Panel):
	def __init__(self, parent, id):
		wx.Panel.__init__(self, parent, id)

		self.bigsizer=wx.BoxSizer(wx.VERTICAL)
		self.sizerbuttonspart = wx.BoxSizer(wx.HORIZONTAL)
		
		self.button1 = wx.Button(self, label="&Generate Command")
		self.button1.Bind(wx.EVT_BUTTON, self.GenerateCommand)

		self.button2 = wx.Button(self, label="&Launch")
		self.button2.Bind(wx.EVT_BUTTON, self.Launch)

		self.button3 = wx.Button(self, label="&Reset")
		self.button3.Bind(wx.EVT_BUTTON, self.Reset)

		self.button4 = wx.Button(self, label="R&eload")
		self.button4.Bind(wx.EVT_BUTTON, self.Reload)

		self.button5 = wx.Button(self, label="&Custom Loading Order")
		self.button5.Bind(wx.EVT_BUTTON, self.CustomLoadingOrder)
		
		#maybe buttons to manually load WADs and PK3s, and GZDN can load a config at startup? Later

		self.buttonquit = wx.Button(self, label="&Quit")
		self.buttonquit.Bind(wx.EVT_BUTTON, self.Quitter)

		self.sizerbuttonspart.Add(self.button1, 1)
		self.sizerbuttonspart.Add(self.button2, 1)
		self.sizerbuttonspart.Add(self.button3, 1)
		self.sizerbuttonspart.Add(self.button4, 1)
		self.sizerbuttonspart.Add(self.button5, 1)
		self.sizerbuttonspart.Add(self.buttonquit, 1)
		
		self.sizerselectionspart = wx.BoxSizer(wx.HORIZONTAL)
		self.loadedbases=wx.ListBox(self, style=wx.LB_SINGLE|wx.LB_NEEDED_SB)
		self.loadedaddons=wx.ListBox(self, style=wx.LB_MULTIPLE|wx.LB_NEEDED_SB|wx.LB_EXTENDED)

		self.command=wx.TextCtrl(self)

		self.sizerselectionspart.Add(self.loadedbases, 1, wx.EXPAND)
		self.sizerselectionspart.Add(self.loadedaddons, 1, wx.EXPAND)
		
		self.bigsizer.Add(self.sizerbuttonspart, 1, wx.EXPAND)
		self.bigsizer.Add(self.sizerselectionspart, 8, wx.EXPAND)
		self.bigsizer.Add(self.command, 1, wx.EXPAND)

		self.SetSizer(self.bigsizer)
        
		self.SetAutoLayout(True)
		self.Layout()
		self.Load()

	def Load(self):
		wadsandipk3s=glob.glob(gzHomeGlobbing+"*.WAD")+glob.glob(gzHomeGlobbing+"*.wad")+glob.glob(gzHomeGlobbing+"*.IPK3")+glob.glob(gzHomeGlobbing+"*.ipk3")
		pkwhatevers=glob.glob(gzHomeGlobbing+"*.PK*")+glob.glob(gzHomeGlobbing+"*.pk*")
		bases=[]
		addOns=[]

		for wadipk in wadsandipk3s:
			if os.path.basename(wadipk) in secretiwadlist or isIwad(wadipk):
				bases.append(wadipk)
			else:
				addOns.append(wadipk)

		for pkwhatever in pkwhatevers:
			if os.path.basename(pkwhatever) in secretipk3list:
				bases.append(pkwhatever)
			else:
				addOns.append(pkwhatever)

		bases=sorted(bases)
		addOns=sorted(addOns)

		for base in bases:
			self.loadedbases.Append(base)
		for addOn in addOns:
			self.loadedaddons.Append(addOn)

	def CommandMaker(self, selectedAddOns):
		theBase=""
		gzdoomcommand="gzdoom"
		if platform.system()=="Windows":
			gzdoomcommand="gzdoom.exe"
		finalcommand=gzdoomcommand
		finalcommandlist=[gzdoomcommand]
		if self.loadedbases.GetSelection()>=0:
			theBase=self.loadedbases.GetString(self.loadedbases.GetSelection())
		theAddOns=[]
		for addOn in selectedAddOns:
			theAddOns.append(addOn)
		if theBase:
			finalcommand+=" -iwad "+shlex.quote(theBase)
			shlex.quote(theBase)
			finalcommandlist.append("-iwad")
			finalcommandlist.append(theBase)
		for addOn in theAddOns:
			finalcommand+=" -file "+shlex.quote(addOn)
			finalcommandlist.append("-file")
			finalcommandlist.append(addOn)
		self.command.SetValue(finalcommand)
		return finalcommandlist

	def GenerateCommand(self, event):
		theAddOns=[]
		for addOn in self.loadedaddons.GetSelections():
			theAddOns.append(self.loadedaddons.GetString(addOn))
		self.CommandMaker(theAddOns)

	def CustomLoadingOrder(self, event):
		if len(self.loadedaddons.GetSelections())>=2:
			theAddOns=[]
			theOrder=[]
			orderCount=0
			for addOn in self.loadedaddons.GetSelections():
				theAddOns.append(self.loadedaddons.GetString(addOn))
				theOrder.append(orderCount)
				orderCount+=1

			self.addonloadingorder=wx.RearrangeDialog(None, "Reorder the add-ons to your satisfaction.", "Add-On Order", order=theOrder, items=theAddOns)
			chosenOrder=self.addonloadingorder.ShowModal()
			if chosenOrder == wx.ID_OK:
				theItems=[]
				rawItems=self.addonloadingorder.List.GetItems()
				rawOrder=self.addonloadingorder.GetOrder()
				for i in range(0, len(rawOrder)):
					if rawOrder[i]>=0:
						theItems.append(rawItems[i])
				commandListForPopen=self.CommandMaker(theItems)
				showCommandDlg=wx.MessageDialog(None, "Show command?", "", wx.YES_NO | wx.CANCEL)
				showChoice=showCommandDlg.ShowModal()
				if showChoice==wx.ID_YES:
					self.command.SetValue(" ".join(commandListForPopen))
				launchDlg=wx.MessageDialog(None, "Launch?", "", wx.YES_NO | wx.CANCEL)
				launchChoice=launchDlg.ShowModal()
				if launchChoice==wx.ID_YES:
					p = Popen(commandListForPopen)
			else:
				pass

	def Launch(self, event):
		theAddOns=[]
		for addOn in self.loadedaddons.GetSelections():
			theAddOns.append(self.loadedaddons.GetString(addOn))
		commandListForPopen=self.CommandMaker(theAddOns)
		self.command.SetValue(" ".join(commandListForPopen))
		p = Popen(commandListForPopen)

	def Reset(self, event):
		for wadSelection in list(reversed(self.loadedbases.GetSelections())):
			self.loadedbases.Deselect(wadSelection)
		for addOnSelection in list(reversed(self.loadedaddons.GetSelections())):
			self.loadedaddons.Deselect(addOnSelection)
		self.command.Clear()

	def Reload(self, event):
		self.loadedbases.Clear()
		self.loadedaddons.Clear()
		self.Load()

	def Quitter(self, event):
		dlg=wx.MessageDialog(None, "Are you sure you want to quit?", "Confirm Exit", wx.YES_NO)
		choice=dlg.ShowModal()
		if choice==wx.ID_YES:
			sys.exit()

app = wx.App()
mainframe = wx.Frame(None, -1, "GZDoomNation", size = (800, 600))
# call the derived class
TheWindow(mainframe,-1)
mainframe.Show(1)
app.MainLoop()

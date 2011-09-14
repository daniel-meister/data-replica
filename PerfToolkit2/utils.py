#!/usr/bin/python

### BRAND NEW VERSION. CONTAINS MATERIAL FROM LEONARDO SALA AND MARCO-ANDREA BUCHMANN

import sys; sys.path.append('/usr/lib/root')
from sys import argv,exit
from os import popen
import re
import ROOT
from math import sqrt,ceil
from array import array

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

    def disable(self):
        self.HEADER = ''
        self.OKBLUE = ''
        self.OKGREEN = ''
        self.WARNING = ''
        self.FAIL = ''
        self.ENDC = ''

def makeabstracthisto1d2d3d(command,samplename,tree,c1,whichjob) :
  c1.cd()
  repcommand=command.replace(":","____")
  addendum=""
  if(command.find(":")==-1 and whichjob==-1) :
    # one dimensional draw command (standard)
    tree.Draw(command+">>h_"+samplename+"_"+repcommand)
    tempobject = ROOT.gPad.GetPrimitive(("h_"+samplename+"_"+repcommand+addendum));
  else :
#    print "dealing with a wn quantity for sample"+samplename
    if (whichjob!=-1) :
      #dealing with a WN quantity
      drawoption="Entry$=="+str(whichjob)
      addendum="__"+str(whichjob)
      if (command.find(":WN_net_Seconds")==-1):
	#it's possible that the user already specified to draw the WN quantity against WN_net_Seconds so we don't want to do this once more
	command=command+":WN_net_Seconds"
      tree.Draw(command+">>h_"+samplename+"_"+repcommand+addendum,drawoption,"l")
      tempobjecta = c1.cd().GetPrimitive("Graph");
      tempobject = tempobjecta.Clone("g_"+samplename+"_"+repcommand+addendum)
      #in the case of WN diagrams we really want the GRAPH and not the TH2F which just gives the area.
    else :
      #not dealing with a WN quantity but with a multidimensional canvas ... 
      print bcolors.WARNING+" drawing something multidimensional - is this working?"+bcolors.ENDC
      tree.Draw(command+">>h_"+samplename+"_"+repcommand+addendum,drawoption)
      tempobject = c1.cd().GetPrimitive(("h_"+samplename+"_"+repcommand+addendum));
    
#    print "just drawn command"+command+" with drawoption "+drawoption
#    c1.SaveAs("exp/"+samplename+"_"+repcommand+"__"+str(whichjob)+".png")
    
  return tempobject

#def REMOVE_makeabstracthisto(command,samplename,tree,c1,whichjob) :
#  ### REMOVE THIS IF NOT NEEDED ANYMORE!
#  c1.cd()
#  repcommand=command.replace(":","____")
#  addendum=""
#  if(whichjob==-1) :
#    tree.Draw(command+">>h_"+samplename+"_"+repcommand)
#  else :
##    print "dealing with a wn quantity for sample"+samplename
#    drawoption="Entry$=="+str(whichjob)
#    addendum="__"+str(whichjob)
#    command=command+":WN_net_Seconds"
#    tree.Draw(command+">>h_"+samplename+"_"+repcommand+addendum,drawoption,"l")
#    print "just drawn command"+command+" with drawoption "+drawoption
#    c1.SaveAs("exp/"+samplename+"_"+repcommand+"__"+str(whichjob)+".png")
#    
#  tempobject = ROOT.gPad.GetPrimitive(("h_"+samplename+"_"+repcommand+addendum));
#  print tempobject.GetEntries()
#  return tempobject

def makehisto(branch,quantity,samplename,tree,c1) :
  c1.cd()
  tree.Draw((branch.GetName()+">>h_"+samplename+"_"+quantity))
  tempobject = ROOT.gPad.GetPrimitive(("h_"+samplename+"_"+quantity));
  return tempobject

def retrieve_info_from_tree(configobjectname,infotree) :
  temphisto = ROOT.TH1F("histo","histo",100,0,100)
  drawstring=configobjectname+">>histo"
  infotree.Draw(drawstring)
  returnname=temphisto.GetXaxis().GetBinLabel(1)
  print configobjectname, returnname
  if(configobjectname=="nevents"): returnname=int(returnname.replace("ne",""))
  if(configobjectname=="njobs"): returnname=int(returnname.replace("nj",""))
  return returnname

def distribute_nPads(nPads,nPadsxy) :
  #we are trying to create a quadratic canvas
  a=sqrt(nPads)
  b=sqrt(nPads)
  nPadsxy[0]=0;
  nPadsxy[1]=0;
  difference=0.00;
  while((a-difference)>(int(a)) and (a+difference)<(int(a)+1)) :
    difference+=0.05
#    print "difference is atm : "+str(difference) + "so that a-difference is "+str(a-difference)+" and a+diff="+str(a+difference)
  if((a-difference)<(int(a))) :
    a=int(a)+1
  else:
    a=int(a)
  b=int(ceil(float(nPads)/a))
  #return str(a)+" : "+str(ceil(float(nPads)/a))
  if a>=b :
    nPadsxy[0]=a
    nPadsxy[1]=b
  if b>a :
    nPadsxy[0]=b
    nPadsxy[1]=a

def getinfoabout(filename,configuration) :
  infocanvas = ROOT.TCanvas("infocanvas","infocanvas")
  file =  ROOT.TFile(filename)
  info_tree = file.Get("info_tree")
  configuration["config"]=retrieve_info_from_tree("config",info_tree);
  configuration["eventsJob"]=retrieve_info_from_tree("eventsJob",info_tree);
  configuration["njobs"]=retrieve_info_from_tree("njobs",info_tree);
  configuration["sw"]=retrieve_info_from_tree("sw",info_tree);
  configuration["site"]=retrieve_info_from_tree("site",info_tree);
  configuration["timestamp"]=retrieve_info_from_tree("timestamp",info_tree);
  
def print_config(fileList,show=True) :
  filecounter=0
  for file in fileList :
    configuration={}
    filecounter+=1
    getinfoabout(file,configuration)
    print ""
    print bcolors.OKGREEN+"File "+str(filecounter)+" : "+file+bcolors.ENDC
    print "Configuration : "+configuration["config"]
    print "Number of Events: "+str(configuration["eventsJob"])
    print "Number of Jobs: "+str(configuration["njobs"])
    print "Sw: "+configuration["sw"]
    print "Site: "+configuration["site"]
    print "Time Stamp:"+configuration["timestamp"]
  print ""

def get_nPads(fileList,nPadarray) :
  maxnpad=0
  for file in fileList :
    configuration={}
    getinfoabout(file,configuration)
    nPadarray[file]=configuration["njobs"]
    if nPadarray[file] > maxnpad : 
      maxnpad=nPadarray[file]
  return maxnpad
    
def givenicecolor(index,setthis) :
  rindex=index%6
  mindex=int(index/6)
#  print "give nice color has been called with index="+str(index)+" so we have rindex="+str(rindex)+" (index%6) and mindex="+str(mindex)+" (index/6)"
  color=""
  if(rindex==0) : color = ROOT.TColor.GetColor("#2E2EFE") #BLUE
  if(rindex==1) : color = ROOT.TColor.GetColor("#81F781") #GREEN
  if(rindex==2) : color = ROOT.TColor.GetColor("#BE81F7") #PURPLE
  if(rindex==3) : color = ROOT.TColor.GetColor("#FA5858") #RED
  if(rindex==4) : color = ROOT.TColor.GetColor("#D7DF01") #YELLOWISH
  if(rindex==5) : color = ROOT.TColor.GetColor("#848484") #GRAY
  
  setthis["linestyle"]=mindex #this is the line style to be used. usually zero.
  setthis["color"]=color

def searchfor(keyword,firstfile,quiet=True) :
  if quiet!=True :
    print "Searching for keyword",keyword,"in",firstfile
  searchhere = ROOT.TFile(firstfile)
  newtree=searchhere.Get("Performance")
  BranchList=newtree.GetListOfBranches()
  totalhits=0
  collection = []
  for branch in BranchList:
    branchname=branch.GetName()
    if(branchname.find(keyword)!=-1):
      totalhits+=1
      if quiet != True :
	print "Have found a match (#"+str(totalhits)+") :",branchname[:branchname.find(keyword)]+bcolors.OKGREEN+branchname[branchname.find(keyword):branchname.find(keyword)+len(keyword)]+bcolors.ENDC+branchname[branchname.find(keyword)+len(keyword):]
      collection.append(branchname)
  if totalhits == 0 :
    if quiet != True:
      print bcolors.FAIL+"There were no results for your keyword ("+keyword+"). Please try again with a different keyword or try to be less specific"+bcolors.ENDC
  return collection
  
def compute_dimension(variable):
  if variable.find(":")==-1:
      return 1 #one dimensional variable
  else :
      if (variable[variable.find(":")+1:].find(":"))==-1:
	#the second part (after the :) doesn't contain any : i.e. the expression is two dimensional!
	return 2 #two dimensional variable
      else:
	redvar=variable[variable.find(":")+1:] #for 3 D this still contains a ":"
	if (redvar[redvar.find(":")+1:].find(":"))!=-1:
	  print bcolors.WARNING+"Warning: One of the requested draw commands,"+bcolors.FAIL+variable+bcolors.WARNING+", seems to contain more than 3 dimensions. Given our current computer standards, that's too much to expect. Variable rejected."+bcolors.ENDC
	  return 4
	else:
	  return 3
  
### This function will return all "candidates", that is, all variables that correspond to a given search keyword (and their combinations in case of 2D/3D)
def compute_all_candidates(currentvar,filename) :  
  variabledimension=compute_dimension(currentvar)
  if variabledimension==1: 
    candidates=searchfor(currentvar,filename[0],True)

  if variabledimension==2:
    candidates=[]
    vara=currentvar[:currentvar.find(":")]
    varb=currentvar[currentvar.find(":")+1:]
    candidatesa=searchfor(vara,filename[0],True);
    candidatesb=searchfor(varb,filename[0],True);
    for candidatea in candidatesa:
	for candidateb in candidatesb:
	  candidate=candidatea+":"+candidateb
	  candidates.append(candidate)
    
  if variabledimension==3:
    candidates=[]
    vara=currentvar[:currentvar.find(":")]
    varb=currentvar[currentvar.find(":")+1:]
    varc=varb[varb.find(":")+1:]  ## this is not a typo!
    varb=varb[:varb.find(":")]  ## this is not a typo!
    candidatesa=searchfor(vara,filename[0],True);
    candidatesb=searchfor(varb,filename[0],True);
    candidatesc=searchfor(varc,filename[0],True);
    for candidatea in candidatesa:
	for candidateb in candidatesb:
	  for candidatec in candidatesc:
	    candidate=candidatea+":"+candidateb+":"+candidatec
	    candidates.append(candidate)

  if variabledimension==4: ## there are no candidates (obviously)
    return []
    
  if len(candidates) == 0 and variabledimension<4:
    print bcolors.WARNING+"Warning: One of the requested draw commands,"+bcolors.FAIL+currentvar+bcolors.WARNING+", contains a quantity that cannot be found in the files. Please modify it and try again (or you can use --search to look for it)."+bcolors.ENDC
    return candidates

  if len(candidates) >= 10:
    print bcolors.WARNING+"Warning: One of the requested draw commands,"+bcolors.FAIL+currentvar+bcolors.WARNING+", contains a quantity that cannot be found in the files. Please modify it and try again (or you can use --search to look for it)."+bcolors.ENDC
    emptycandidates = []
    return emptycandidates
    
  if len(candidates) < 10 and len(candidates)>0 :
#    print bcolors.OKGREEN+"The draw command,"+bcolors.OKBLUE+currentvar+bcolors.OKGREEN+", was added succesfully to the list of plots to be created."+bcolors.ENDC	  
    return candidates

def new_compute_all_candidates(currentvar,filename,oldcandidates) :  
  variabledimension=compute_dimension(currentvar)
  if variabledimension==1: 
    candidates=searchfor(currentvar,filename[0],True)

  if variabledimension==2:
    candidates=[]
    vara=currentvar[:currentvar.find(":")]
    varb=currentvar[currentvar.find(":")+1:]
    candidatesa=searchfor(vara,filename[0],True);
    candidatesb=searchfor(varb,filename[0],True);
    for candidatea in candidatesa:
	for candidateb in candidatesb:
	  candidate=candidatea+":"+candidateb
	  candidates.append(candidate)
    
  if variabledimension==3:
    candidates=[]
    vara=currentvar[:currentvar.find(":")]
    varb=currentvar[currentvar.find(":")+1:]
    varc=varb[varb.find(":")+1:]  ## this is not a typo!
    varb=varb[:varb.find(":")]  ## this is not a typo!
    candidatesa=searchfor(vara,filename[0],True);
    candidatesb=searchfor(varb,filename[0],True);
    candidatesc=searchfor(varc,filename[0],True);
    for candidatea in candidatesa:
	for candidateb in candidatesb:
	  for candidatec in candidatesc:
	    candidate=candidatea+":"+candidateb+":"+candidatec
	    candidates.append(candidate)

  if variabledimension>3: ## there are no candidates (obviously)
    print bcolors.WARNING+"Warning: You seem to have requested a "+str(variabledimension)+"-dimensional draw command,"+bcolors.FAIL+currentvar+bcolors.WARNING+"; this is outside the scope of this script, sorry."+bcolors.ENDC
    return []
    
  if len(candidates) == 0 and variabledimension<4:
    print bcolors.WARNING+"Warning: One of the requested draw commands,"+bcolors.FAIL+currentvar+bcolors.WARNING+", contains a quantity that cannot be found in the files. Please modify it and try again (or you can use --search to look for it)."+bcolors.ENDC
    return candidates

  if len(candidates) >= 10:
    print bcolors.WARNING+"Warning: One of the requested draw commands,"+bcolors.FAIL+currentvar+bcolors.WARNING+", contains a quantity that cannot be found in the files. Please modify it and try again (or you can use --search to look for it)."+bcolors.ENDC
    emptycandidates = []
    return emptycandidates
    
  if len(candidates) < 10 and len(candidates)>0 :
    print bcolors.OKGREEN+"The draw command,"+bcolors.OKBLUE+currentvar+bcolors.OKGREEN+", was added succesfully to the list of plots to be created."+bcolors.ENDC	  
    for candidate in candidates:
      oldcandidates.append(candidate)
#    return candidates

def create_legend(QUANT,histos,fileList,fileinformation,i) :
  leg = ROOT.TLegend(0.7,0.7,0.85,0.85)
  leg.SetFillColor(10)
  leg.SetLineColor(10)
  leg.SetLineWidth(10)

  for filen in fileList:
    SAMPLE = filen[filen.find("SAMPLE")+len("SAMPLE")+1:]
    if (i==-1) :
      #case: not WN
      leg.AddEntry(histos[QUANT][SAMPLE],fileinformation[filen]["site"],"l")
    else :
      #case: WN
      leg.AddEntry(histos[QUANT][SAMPLE][i],fileinformation[filen]["site"],"l")
  return leg

def draw_multiple(fileList,canvases,candidate,nPads,histos,i) :
  xmax=-1;
  xmin=-1;
  ymax=-1;
  ymin=-1;
  canvases[candidate].cd(i+1)
  filecounter=0
  for file in fileList :
    SAMPLE = file[file.find("SAMPLE")+len("SAMPLE")+1:]
    QUANT=candidate
    colorconfiguration={}
    givenicecolor(filecounter,colorconfiguration)
    filecounter+=1
    histos[QUANT][SAMPLE][i].SetLineStyle(colorconfiguration["linestyle"])
    histos[QUANT][SAMPLE][i].SetLineColor(colorconfiguration["color"])
    histos[QUANT][SAMPLE][i].SetMarkerColor(colorconfiguration["color"])
    
    if file==fileList[0]:
      ymin=histos[QUANT][SAMPLE][i].GetYaxis().GetXmin()
      ymax=histos[QUANT][SAMPLE][i].GetYaxis().GetXmax()
      xmax=histos[QUANT][SAMPLE][i].GetXaxis().GetXmax()
      xmin=histos[QUANT][SAMPLE][i].GetXaxis().GetXmin()
    else :
      if histos[QUANT][SAMPLE][i].GetYaxis().GetXmin()<ymin:
	ymin=histos[QUANT][SAMPLE][i].GetYaxis().GetXmin()
      if histos[QUANT][SAMPLE][i].GetYaxis().GetXmax()>ymax:
	ymax=histos[QUANT][SAMPLE][i].GetYaxis().GetXmax()

      if histos[QUANT][SAMPLE][i].GetXaxis().GetXmin()<xmin:
	xmin=histos[QUANT][SAMPLE][i].GetXaxis().GetXmin()
      if histos[QUANT][SAMPLE][i].GetXaxis().GetXmax()>xmax:
	xmax=histos[QUANT][SAMPLE][i].GetXaxis().GetXmax()

  for file in fileList :
    SAMPLE = file[file.find("SAMPLE")+len("SAMPLE")+1:]
    QUANT=candidate
    if file==fileList[0]:
      pad2d=ROOT.TH2F("pad2d_"+QUANT+"_"+SAMPLE+"_pad"+str(i),"pad2d_"+QUANT+"_"+SAMPLE+"_pad"+str(i),100,xmin,xmax,100,ymin,ymax)
      histos[QUANT][SAMPLE][i].GetXaxis().SetTitle("Seconds")
      histos[QUANT][SAMPLE][i].GetYaxis().SetTitle(QUANT)
      histos[QUANT][SAMPLE][i].GetYaxis().CenterTitle()
      histos[QUANT][SAMPLE][i].GetXaxis().CenterTitle()
      histos[QUANT][SAMPLE][i].SetTitle(QUANT+": Job "+str(i+1))
      pad2d.Draw()
      histos[QUANT][SAMPLE][i].GetXaxis().SetRangeUser(float(xmin),float(xmax))
      histos[QUANT][SAMPLE][i].GetYaxis().SetRangeUser(float(0.8*ymin),float(1.2*ymax))
      histos[QUANT][SAMPLE][i].Draw("same AC")
    else:
      histos[QUANT][SAMPLE][i].SetTitle(QUANT+": Job "+str(i+1))
      histos[QUANT][SAMPLE][i].GetXaxis().SetTitle("Seconds")
      histos[QUANT][SAMPLE][i].GetYaxis().SetTitle(QUANT)
      histos[QUANT][SAMPLE][i].GetYaxis().CenterTitle()
      histos[QUANT][SAMPLE][i].GetXaxis().CenterTitle()
      histos[QUANT][SAMPLE][i].Draw("same AC")
#  canvases[candidate].SaveAs("exp/pads/test_pad_"+str(i+1)+".png")
  
  



def draw_one(fileList,canvases,candidate,nPads,histos) :
  xmax=-1;
  xmin=-1;
  ymax=-1;
  ymin=-1;
  canvases[candidate].cd()
  filecounter=0
  for file in fileList :
    SAMPLE = file[file.find("SAMPLE")+len("SAMPLE")+1:]
    QUANT=candidate
    colorconfiguration={}
    givenicecolor(filecounter,colorconfiguration)
    filecounter+=1
    histos[QUANT][SAMPLE].SetLineStyle(colorconfiguration["linestyle"])
    histos[QUANT][SAMPLE].SetLineColor(colorconfiguration["color"])
    histos[QUANT][SAMPLE].SetMarkerColor(colorconfiguration["color"])
    
    if file==fileList[0]:
      ymin=histos[QUANT][SAMPLE].GetMinimum()
      ymax=histos[QUANT][SAMPLE].GetMaximum()
      xmax=histos[QUANT][SAMPLE].GetXaxis().GetXmax()
      xmin=histos[QUANT][SAMPLE].GetXaxis().GetXmin()
    else :
      if histos[QUANT][SAMPLE].GetMinimum()<ymin:
	ymin=histos[QUANT][SAMPLE].GetMinimum()
      if histos[QUANT][SAMPLE].GetMaximum()>ymax:
	ymax=histos[QUANT][SAMPLE].GetMaximum()
      if histos[QUANT][SAMPLE].GetXaxis().GetXmax()>xmax:
	xmax=histos[QUANT][SAMPLE].GetXaxis().GetXmax()
      if histos[QUANT][SAMPLE].GetXaxis().GetXmin()<xmin:
	xmin=histos[QUANT][SAMPLE].GetXaxis().GetXmin()
  ROOT.gStyle.SetOptStat(0)
  for file in fileList :
    SAMPLE = file[file.find("SAMPLE")+len("SAMPLE")+1:]
    QUANT=candidate
    if file==fileList[0]:
      histos[QUANT][SAMPLE].GetXaxis().SetRangeUser(xmin,xmax)
      histos[QUANT][SAMPLE].GetYaxis().SetRangeUser(0.8*ymin,1.2*ymax)
      histos[QUANT][SAMPLE].Draw()
    else:
      histos[QUANT][SAMPLE].Draw("same")
      
  canvases[candidate].Update()

def processallvariables(variables,variablecollection,filename,performancetree,histos,canvases,fileinformation,legend,stats,savepng,saveroot,dosummary,outfile) :
####adds all variables containing the substring to our plotting collection
    ROOT.gROOT.SetStyle("Plain")
    #c1 = ROOT.TCanvas("c1","c1")
    candidates=[]
    plotcanvas=ROOT.TCanvas("plot_canvas","plot_canvas")
    for currentvar in variables:
#      print "Called for currentvar="+str(currentvar)+"; canvas currently contains "+str(len(canvases))
      new_compute_all_candidates(currentvar,filename,candidates)
    candcounter=0
    ##at this point we've "collected" all the variables that we'd like to draw and are ready for showtime !
    if not len(candidates) == 0:
	for candidate in candidates:
	  if candidate == "Error_weight" :
	    continue ## error weight is just basically the number of times a specific error code was encountered -> only relevant for success rate (handled in "Error" case)
	    #this has actually been replaced in the latest version.
	  if not canvases.has_key(candidate):
#	    print "starting round for candidate",candidate
	    candcounter+=1
	    variablecollection.append(candidate)
	    #variablecollectiondimension[candidate]=currentdimension
	    canvases[candidate]=ROOT.TCanvas(("canvas_"+str(candcounter)),("canvas for "+str(candidate)))
#	    print "opened canvases for "+candidate
	    nPadarray={}
	    isWnquantity=False;
	    nPads=1;
	    if(candidate.find("WN_")!=-1) : 
	      isWnquantity=True;
	      nPads=get_nPads(filename,nPadarray)
	      nPadsxy={}
	      distribute_nPads(nPads,nPadsxy)
	      canvases[candidate].Divide(nPadsxy[0],nPadsxy[1]);
	    for file in filename:
	      SAMPLE = file[file.find("SAMPLE")+len("SAMPLE")+1:]
	      QUANT=candidate
	      if not stats.has_key(SAMPLE): stats[SAMPLE]={'Error':{}}
	      mySTATS = stats[SAMPLE]
	      if not histos.has_key(QUANT):
		histos[QUANT] = {}
	      if isWnquantity==False:
		histos[QUANT][SAMPLE] = makeabstracthisto1d2d3d(candidate,SAMPLE,performancetree[file],plotcanvas,-1)
		stats[SAMPLE][QUANT]=(histos[QUANT][SAMPLE].GetMean(),histos[QUANT][SAMPLE].GetRMS())
	      else:
		#dealing with a "WN" quantity
		histos[QUANT][SAMPLE] = {}
		if dosummary==True: stats[SAMPLE][QUANT][i] = {}
		for i in range (0,nPads) :
		  histos[QUANT][SAMPLE][i] = makeabstracthisto1d2d3d(candidate,SAMPLE,performancetree[file],plotcanvas,i)
		  if dosummary==True: stats[SAMPLE][QUANT][i]=(histos[QUANT][SAMPLE][i].GetMean(),histos[QUANT][SAMPLE][i].GetRMS())
	      if candidate == "Error" :
		stats[SAMPLE]["Failures"] = failurehisto=(makeabstracthisto1d2d3d("Error",SAMPLE,performancetree[file],plotcanvas,-1)).Integral()
		if not histos.has_key("TimeJob_CpuPercentage"):
		  stats[SAMPLE]["Success"] = 0
		elif not histos["TimeJob_CpuPercentage"].has_key(SAMPLE):
		  stats[SAMPLE]["Success"] = 0
		else:
		  stats[SAMPLE]["Success"]  =  histos["TimeJob_CpuPercentage"][SAMPLE].Integral()
	      
		Total = float(stats[SAMPLE]["Success"])+ float(stats[SAMPLE]["Failures"])
		print "I've found a total of " + str(Total)
		for i in range(histos[QUANT][SAMPLE].GetNbinsX()):
		  errLabel = histos[QUANT][SAMPLE].GetXaxis().GetBinLabel(i+1)
		  if errLabel!="": 
                    if not stats[SAMPLE]["Error"].has_key(errLabel): 
                        stats[SAMPLE]["Error"][errLabel] = 0
                    print errLabel, myH.GetBinContent(i+1)
		    stats[SAMPLE]["Error"][errLabel] = 100*round(myH.GetBinContent(i+1)/Total,3)
		  
# at this point we are done preparing the histogram(s)
	    filecounter=0
	    draw_everything(filename,canvases,candidate,nPads,histos,legend,fileinformation,savepng,saveroot,outfile) ## draw the variable!


def SaveCanvasName(candidate) :
  return "img/"+candidate+".png"

def draw_everything(fileList,canvases,candidate,nPads,histos,legend,fileinformation,savepng,saveroot,outfile) :
  if nPads==1:
    draw_one(fileList,canvases,candidate,nPads,histos);
    legend[candidate]=create_legend(candidate,histos,fileList,fileinformation,-1,)
    legend[candidate].Draw()
  else :
    legend[candidate]=create_legend(candidate,histos,fileList,fileinformation,0)
    for i in range(0,nPads) :
      draw_multiple(fileList,canvases,candidate,nPads,histos,i);
      legend[candidate].Draw()
  canvases[candidate].Update()
  if(savepng) :
    canvases[candidate].SaveAs(SaveCanvasName(candidate));
  if(saveroot) :
    outfile.cd()
    canvases[candidate].SetName(candidate)
    canvases[candidate].Write()

    
def findPlotTogetherCandidates(plotFilter, plotTogether, histos, toBePlotAlone, toBePlotTogether, drawvar=False):
#      print "NOW RUNNING : findPlotTogetherCandidates"
      compiledFilters = []
      for f in plotFilter:
	compiledFilters.append( re.compile(f) )
      
      for quant in histos:
#        print "considering : ",quant
        selected = False        
        for f in compiledFilters:
            if not f.search(quant) == None:
                selected = True
                break
        if not selected and drawvar==False : continue ## if the variables were defined by the user we don't want any filters to interfere
#        print "... still considering ",quant
        together=False
        for sel in plotTogether:
            if not toBePlotTogether.has_key(sel): toBePlotTogether[sel] = []
            if quant.find(sel)!=-1 and quant.find("tstorage")==-1:
                if quant not in toBePlotTogether[sel]: toBePlotTogether[sel].append(quant)
                together = True
                break
        if not together:
            if quant not in toBePlotAlone: toBePlotAlone.append(quant)

def plot_everything(histos,keys,savePng):
  for quant in keys:
    for sample in histos[quant].keys():
      myH = histos[quant][sample]
#      print type(myH),quant
    #  print quant,sample,myH.Integral()
  
def do_cowbell():
  print "                     "
  print "        (__)"
  print "        (oo)"
  print "       /-\/-\ "
  print "      /      \ "
  print "      |      |"
  print "      |      |"
  print "     /        \ "
  print "    /__________\ "
  print "          \\\\ "
  print "          (_)"
  print "                     "
  print "    more cowbell?    "
  print "                     "
  print " (source: http://en.wikiversity.org/wiki/ASCII_art)"

##################################################################################### gray list
  


def fillLists(branchlist, modevariables, branches, histos, perftree, sitePalette, filename, posFilter, negFilter=""):
    c1 = ROOT.TCanvas("c1","c1")
    
    SAMPLE = filename[filename.find("SAMPLE")+len("SAMPLE")+1:]
    
    for branch in branchlist:
        histoName = branch.GetName()
        QUANT = histoName
        
        if not sitePalette.has_key(SAMPLE): 
                if len(sitePalette)>0: myColor = sorted(sitePalette.values())[-1] +1 
                else: myColor=1
                if myColor==10: myColor+=1 ###don't want white
                sitePalette[SAMPLE] = myColor

        toPlot = False
        for f in posFilter:
                myFilter = re.compile(f)
                if not myFilter.search(QUANT) == None:
                    toPlot = True
                    break

        if negFilter!='':
                for f in negFilter:
                    myFilter = re.compile(f)
                    if not myFilter.search(QUANT) == None:
                        toPlot = False
                        break

        if not toPlot: continue

        if not branches.has_key(QUANT):
            branches[QUANT] = {}
            histos[QUANT] = {}
            modevariables.append(QUANT);

        branches[QUANT][SAMPLE] = branch
#        histos[QUANT][SAMPLE] = makehisto(branch,QUANT,SAMPLE,perftree,c1)
            
    return SAMPLE

  
  
def setCPTMode(mode):
    if mode=="Default":
        PNG_NAME_FORMAT= ['Site',"Cfg","Sw"]
        legendComposition = ['Site','Cfg']     
        sampleTitles = [""]
        strippedText="" # this in case you want to remove some string from the set name
        
        ###filter quantities to be considered
        filter = [
            ".*read.*sec.*",
            "Time",
            "Percentage",
            "Error"
            ]
        negFilter = [
            "Time_Delay",
            "TimeModule",
            "TimeEvent",
            "local",
            ".*read.*m(in|ax).*",
            ".*open.*m(in|ax).*"
            ]
###filter quantities to be plotted
        plotFilter = [  
            "read-total-msecs",
            "CMSSW_CpuPercentage",
            "UserTime",
            "Error"
            ]
### plot these quantities overlapped (excluded)
        plotTogether = [
            "readv-total-megabytes",
            "read-total-megabytes",
            "readv-total-msecs",
            "read-total-msecs"
            ]
### they can not be in plotFilter?
        summaryPlots =  [
            "CMSSW_CpuPercentage",
            "TimeJob_User",
            "TimeJob_Exe",
            "tstoragefile-read-total-msecs"#,
            #"Error"
            ]
        doSummary = True

    elif mode.find("SiteMon")!=-1:
        PNG_NAME_FORMAT,legendComposition,sampleTitles,filter,negFilter,plotFilter,plotTogether,summaryPlots,doSummary = setCPTMode("Default")
        PNG_NAME_FORMAT= ['Site',"Cfg"]
        legendComposition = ["Sw",'Date']     
        sampleTitles = ["Site","Cfg"]
        strippedText="" 

    elif  mode.find("SiteCfr")!=-1 :
        PNG_NAME_FORMAT,legendComposition,sampleTitles,filter,negFilter,plotFilter,plotTogether,summaryPlots,doSummary = setCPTMode("Default")
        PNG_NAME_FORMAT= ['Site',"Cfg"]
        legendComposition = ["Site","Sw",'Date']     
        sampleTitles = ["Site","Cfg"]
        strippedText="" 
        #summaryPlots.append("Time_Delay")

    elif mode.find("CfgCfr")!=-1:
        PNG_NAME_FORMAT,legendComposition,sampleTitles,filter,negFilter,plotFilter,plotTogether,summaryPlots,doSummary = setCPTMode("Default")
        PNG_NAME_FORMAT= ['Site',"Cfg"]
        legendComposition = ["Cfg","Sw","Label"]     
        sampleTitles = ["Site"]
        filter.append(".*read.*num.*")
        strippedText="" 
        #summaryPlots.append("Time_Delay")
    else:
        print "Mode "+mode+" does not exist"
    
    ### extending modes
    if mode=="SiteMonExt" or mode=="SiteCfrExt" or mode=="CfgCfrExt":
        filter.append("TimeEvent")
        filter.append(".*read.*byte.*")
        plotFilter.append("TimeEvent")
        negFilter.remove("TimeEvent")
        filter.append("net-.*RX")
        plotFilter.append("net-.*RX")
        filter.append("stat-CPU")
        plotFilter.append("stat-CPU")
        filter.append("stat-DISK_Read")
        plotFilter.append("stat-DISK_Read")
        #filter.append("stat-MEM")
        #plotFilter.append("stat-MEM")

    #if mode.find("CfgCfrExt")!=-1:
    #    plotFilter.remove("Error")
    #    summaryPlots.remove("Error")

        

    return PNG_NAME_FORMAT,legendComposition,sampleTitles,filter,negFilter,plotFilter,plotTogether,summaryPlots,doSummary

def splitDirName(dirName, strippedText=""):
    output = {}
    if strippedText!="": 
        for st in strippedText:
            if dirName.find(st)!=-1:
                dirName = dirName.replace(st,"")
    splittedDirName = dirName.split("-")
    isKeyLabel = True
    for comp in splittedDirName:
        comp = comp.split(".")
        if len( comp ) <2:
            isKeyLabel = False
            output = {}
            break
        else:
            label=""
            for i in range(1, len(comp)): label += comp[i]+"_"
            if comp[0]=="Date": 
                output[comp[0]] = label[:-5]
                output["Hour"] = label[-5:-1]
            else: output[comp[0]] = label[:-1]
    ###returns dirName if not in the right format
    if len(splittedDirName)<6 and not isKeyLabel: 
        return dirName
    elif not isKeyLabel:
        output['Site'] = splittedDirName[0]
        output['Cfg'] = splittedDirName[1]
        output['Dataset'] = splittedDirName[2]
        output['EventsJob'] = splittedDirName[3]
        if output['EventsJob'][-3:] == '000': output['EventsJob'] = output['EventsJob'][:-3]+"k"
        output['Label'] = splittedDirName[4]
        output['Date'] = splittedDirName[5][0:8]
        output['Hour'] = splittedDirName[5][8:]

    return output


### from hh:mm:ss to secs
def translateTime(str):
    seconds = 0
    mult = 1
    time = str.split(':')
    i = 1
    while i <= len(time):
        seconds += float(time[-i])*mult
        mult *=60
        i +=1
    return seconds
                                                

######################### THIS IS THE GONER AREA -- OLD FUNCTIONS THAT NEED REIMPLEMENTING!

def PrintSummary(DIR_SUMMARY, posFilter, negFilter, legLabels, histoTitle=""):
    print "This is the new Wiki Stats Summary function ... will take some time to get this right but oh well :-)" 
    perc=0
    LABELS = []

    ###Creating header
    header = ""
    if histoTitle!="":
        print "|* "+ histoTitle+" *|"
    tasks = DIR_SUMMARY.keys()
    tasks.sort()
    for dir in tasks:
        header += " *"+legLabels[dir]+"* |"
        sortedKeys =  sorted(DIR_SUMMARY[dir].keys())
        for l in sortedKeys:
            if not l in LABELS: LABELS.append(l)

    print "|  |",header
   
    ###Success rate
    line = "| *Success*|"
    for dir in tasks:
        total = DIR_SUMMARY[dir]["Success"] + DIR_SUMMARY[dir]["Failures"]
        if total==0:
            perc = 0
            line += "%.1f%% (%.0f / %.0f) |" %(perc,DIR_SUMMARY[dir]["Success"], total)
        else:
            perc = 100*DIR_SUMMARY[dir]["Success"]/total
            line += "%.1f%% (%.0f / %.0f) |" %(perc,DIR_SUMMARY[dir]["Success"], total)
    print line

    ###Error Rate
    ### [dir][label] not useful here...
    pError = {}
    line=""
    for dir in tasks:
        for err in DIR_SUMMARY[dir]["Error"]:
	  if not pError.has_key(int(err)) :
                pError[int(err)] = {}
	  pError[int(err)][dir] = DIR_SUMMARY[dir]["Error"][int(err)]
    
    for err in pError.keys():
        line = "| *Error "+str(err)+"* |"
        for dir in tasks:
            if not pError[err].has_key(dir): line += " // | "
            else:
                line += "%s%%  |" %( pError[err][dir])
        print line

    #### Actual quantities
    orderedLabels = {}
    orderedProducers = []
    myPosFilter = re.compile(posFilter)
    myNegFilter = re.compile(negFilter)

    for label in LABELS:
        if myPosFilter.search(label) == None or not myNegFilter.search(label) == None : continue

        #orderedProducers = []
        lwork = label.split("-")
        if lwork[0]=="TimeModule":
            quant = lwork[-1]
            orderedProducers.append(quant)

        elif len(lwork)>2:
            tech = lwork[0]
            meas = lwork[1]
            quant = lwork[-1]
            quant2 = label[ label.find(meas):]
            
            char = ""
            for x in lwork[2:-1]:
                char = x+"-"
            char.strip("-")
            
            if not orderedLabels.has_key(meas):
                orderedLabels[meas] = {}
            if not orderedLabels[meas].has_key(quant): orderedLabels[meas][quant] = {}
            if not orderedLabels[meas][quant].has_key(quant2): orderedLabels[meas][quant][quant2] = []

            orderedLabels[meas][quant][quant2].append(label)
        else:
            if label != "ExeExitCode" and label!="Success" and label!="Failures" and label!="Error":
                line = ""
                line += "| *"+label+"*|"
                for dir in tasks:
                    if DIR_SUMMARY[dir].has_key(label):
                        if label.find("Module")!=-1:
                            line += " %.2e +- %.2e |" %(DIR_SUMMARY[dir][label][0], DIR_SUMMARY[dir][label][1])
                        else:
                            line += " %.2f +- %.2f |" %(DIR_SUMMARY[dir][label][0], DIR_SUMMARY[dir][label][1])
                    else:
                        line += " // |"
                print line


    #TimeModule printing
    if len(orderedProducers)>0:
        line = ""
        print "| *TimeProducers*||||||"
        for producer in sorted(orderedProducers):
            line = ""
            line += "| *"+producer+"*|"
            for dir in tasks:
                if DIR_SUMMARY[dir].has_key("TimeModule-"+producer):
                    line += " %.2e +- %.2e |" %(DIR_SUMMARY[dir]["TimeModule-"+producer][0], DIR_SUMMARY[dir]["TimeModule-"+producer][1])
                else:
                    line += " // |"
            print line

    # putting tstorage entries at the first place
    for meas in sorted(orderedLabels.keys()):
        for quant in  sorted(orderedLabels[meas].keys()):
            for quant2 in  sorted(orderedLabels[meas][quant].keys()):
                orderedLabels[meas][quant][quant2].sort()
                for label in orderedLabels[meas][quant][quant2]:
                    if label.find('tstoragefile')!=-1: 
                        orderedLabels[meas][quant][quant2].remove(label)
                        orderedLabels[meas][quant][quant2].insert(0, label)
                        break
    line =""
    for meas in sorted(orderedLabels.keys()):
        #if not meas in ["read","readv","seek","open"]: continue
        print "| *"+meas.upper()+"*|", header #|||||"
        for quant in  sorted(orderedLabels[meas].keys()):
            #for char in  orderedLabels[meas][quant].keys():
            for quant2 in  sorted(orderedLabels[meas][quant].keys()):
                for label in orderedLabels[meas][quant][quant2]:
                    if label != "ExeExitCode" and label!="Success" and label!="Failures":
                        line = ""
                        if label.find("tstorage")!=-1: line += "|*"+label+"* |"
                        else: line += "|  * _"+label+"_ *|"
                        for dir in tasks:
                            if DIR_SUMMARY[dir].has_key(label):
                                if DIR_SUMMARY[dir][label][0] <0.1:
                                    line += " %.2e +- %.2e |" %(DIR_SUMMARY[dir][label][0], DIR_SUMMARY[dir][label][1])
                                else:
                                    line += " %.2f +- %.2f |" %(DIR_SUMMARY[dir][label][0], DIR_SUMMARY[dir][label][1])

                            else:
                                line += " // |"
                        print line

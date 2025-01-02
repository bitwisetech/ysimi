#!/usr/bin/env python
#
##    ysimi.py: YASim Interactively Adjust Numbers: a pandas / bokeh testbench for YASim
#    takes a given YASim config file, offers a web based plotter for Lift, drag, L/D 
#    creates modified YASim configs for different YASim versions
#    offers slider control of various key YASim elements and re-plots interactively
#
#   [cdir]-yasim-inpt.xml yasim config xml Original 
#             ..-outp.xml yasim config xml generated with eg modified varied elements
#             ..-lvsd.txt       generated Lift / Drag tables    ( version specific )
#             ..-mia?.txt       generated IAS for 0vSpd vs AoA  ( version specific )
#             ..-soln.txt       generated solution values       ( version specific )
#
#  To run a local server: bokeh serve ysimi.py and then
#    browse to: http://localhost:5006/ysimi 
#
#  Suggested workflow ( various files are created / written )
#    Make a working directory named for the model ex: '[myModel]' for North-American-T6-Texan
#      and use it as your working directory:
#        mkdir [myModel]; cd [myModel]
#    Copy ysimi.py into this working directory so it can run 
#
#    Copy the YASim configuration from Flightgear's Aircraft folder
#      then rename it to retain the original
#      ( the executable's input YASim configuration file has a specific fileID )
#        cp    fgaddon/Aircraft/[myModel-yasim.xml] [thisDir]-yasim-inpt.xml
#        mv    fgaddon/Aircraft/[myModel-yasim.xml] fgaddon/Aircraft/[myModel-yasim-orig.xml] 
#    In Flightgear's Aircraft folder use the modified output as YASim config: 
#      ( This way you can continually flight test adhustments yo the FDM configuration ) 
#        ln -s [thisDir]-yasim-outp.xml] fgaddon/Aircraft/[myModel-yasim.xml]
#
#    In a command console: start bokeh server, with a refence to the python script:
#      Watch this console for updated YASim solution summaries
#      bokeh serve [ --port x ] ../ysimi.py
#
#    Browse with your web browser to the interactive panel:
#      http://localhost:5006/ysimi
#    As you adjust the sliders: YASim reruns, curves and console are updated
#       and the changed yasim configuration is written to [myModel]-yasim-outp.xml
#       save the changed yasim configuration [myModel]-yasim-outp.xml to the -inpt, 
#         whenever the web page is refreshed the screen will rload from -inpt
#      
#    For comparing with a model in aNewModel folder open a second command console:
#      mkdir aNewmodel;  cd aNewmodel
#      copy ysomi.py 
#      copy its configuration from flightgear into:  aNewModel-yasim-inpt.xml
#      and open the app on a different port: bokeh serve --port 5007  ysimi.py
#      Open a new tab with new port from your browser : http://localhost:5007
#      so that two models may be compared in side-by-side browser tabs
#    
#    ysim will not write any element that is missing ( ie defaulted ) in the input file,    
#      if you need to adjust an elemnt slider it must be included in the input file
#    
#    only the first ballast element is adjusted, following ones should be untouched. 
#    
#   developed from bokeh example: bokehSliders.py: 
#   https://www.pluralsight.com/guides/
#     importing-data-from-tab-delimited-files-with-python
#   https://pandas.pydata.org/docs/getting_started/intro_tutorials/
#      02_read_write.html#min-tut-02-read-write
#
##
##
import os, shlex, subprocess, sys, getopt, math
import csv, numpy as np, pandas as pd
#
from bokeh.io import curdoc      
from bokeh.models.callbacks import CustomJS
from bokeh.layouts  import column, row
from bokeh.models   import ColumnDataSource, Slider, Dropdown
from bokeh.models   import TextInput, DataTable, TableColumn
from bokeh.plotting import figure
from collections    import OrderedDict
from time import gmtime, strftime
#
from bs4 import BeautifulSoup
##
#  Python Version
global pythVers
pythVers = sys.version_info[0]
#print('pythVers:', pythVers)
if (pythVers < 3) :
  import xml.etree.ElementTree as ET
else :
  import xml.etree.ElementTree as ET
#
##
global wdir, procPref, lvsdFid, iasaFid, iascFid, drgaFid, solnFid
global solnDict, solnCDS, solnCols, solnDT, solnIter, solnElev, solnCgMC, solnCgWB
global yCfgName, yCfgFid, aCfgFid, vCfgFid, versDict, versToDo, versKywd
#
## These vbles correspond to the elements in the config file: 
global Va, Aa, Ka, Ta, Fa                            # Appr   Spd, Aoa, Thrt, Fuel, Flaps
global Vc, Hc, Kc, Gc, Tc                            # Cruise Spd, Alt, Thrt, GlideAngle, Fuel
global Iw, Aw, Cw, Lf, La,   Dw, Ww, Pw, Df, Da, Hw  # Wing, Flap, Ailr
global Tm, Am, Cm, Lg, Lt,   Dm, Wm, Pm, Dg, Dt, Tw  # Wng1, Flap, Ailr
global Ch, Ah, Eh, Le, Cv,   Dh, Wh, Ph, De, Dv, Hm  # HStab, Elev (incidence set by solver ) 
global Av, Ev, Iv, Tv, Lr,   Wv, Pv, Iu, Tu, Dr      # VStab V0:'v' V1:'u', Rudder 
global Mp, Rp, Ap, Np, Xp,   Ip, Op, Vp, Cp, Tp      # Prop
global Mb, Xb, Yb, Zb, Hy,   Vy, Wx, Wb, Gx          # Ballast, Solver, Wh main, base, CG
global fracInci, totlInci                            # Wing incidence and CoG 
##
#  Pull args from command line 
def pullArgs(argv):
  global wdir
  try:
    opts, args = getopt.getopt(argv, "i:w:", \
         ["inputID=", "workdir="] )
  except getopt.GetoptError:
     print ('sorry, args do not make sense ')
     sys.exit(2)
  #
  wdir = ''
  for opt, arg in opts:
    if   opt in ("-i", "--inputID"):
      print( "args I: ", arg)
    if   opt in ("-w", "--workdir"):
      wdir = arg 
      print( "wdir now: ", wdir)

#  Set Defaults
def presets():
  global wdir, procPref, lvsdFid, iasaFid, iascFid, drgaFid, solnFid
  global yCfgName, yCfgFid, aCfgFid, vCfgFid, versDict, versToDo, versKywd
  global Hy, Vy                                      # Solver    parms
  #print( 'Entr presets')
  # non blank wdir: work folder is specified in args
  if (wdir == ''): 
    wdir = os.getcwd()
  wdirTail = wdir.rfind( '/' )
  if ( wdirTail == -1 ) :
    procPref = 'ysimi'
  else :    
    procPref =  wdir[ ( wdirTail + 1 ):]
  #print(procPref)  
  #procPref = "ysimi"
  ## Default File IDs 
  # aCFig is output yasim config files with element(s) modified 
  aCfgFid  = wdir + '/' + procPref + '-yasim-outp.xml'
  # yasim config xml file read input 
  yCfgFid  = wdir + '/' + procPref + '-yasim-inpt.xml'
  #
  yCfgName = yCfgFid.find('.xml')
  yCfgName = yCfgFid[0:yCfgName]
  ##   
  # Versions in YASim configuration strings, OrderedDict
  # all versions 
  versDict =  OrderedDict([ ('-vOrig',   'YASIM_VERSION_ORIGINAL'), \
                            ('-v2017-2', '2017.2'),   \
                            ('-v32',     'YASIM_VERSION_32',), \
                            ('-vCurr',   'YASIM_VERSION_CURRENT',  )])
  versToDo = '-vCurr'
  versKywd = versDict[versToDo]
  #print('presets versKywd:', versKywd)
  #
  lvsdFid  = procPref + versToDo + '-lvsd.txt'
  drgaFid  = procPref + versToDo + '-drga.txt'
  iasaFid  = procPref + versToDo + '-iasa.txt'
  iascFid  = procPref + versToDo + '-iasc.txt'
  solnFid  = procPref + versToDo + '-soln.txt'
  #
  #print( 'Exit presets')
##

#  Return numeric value from 'name="nn.nnn"' tuple in config file
#
def tuplValu( tChrs, tText ):
  # opening quote is '="' chars beyond name 
  begnValu = tText.find( tChrs) + len(tChrs) + 2 
  endsValu = begnValu + (tText[begnValu:]).find('"')
  #print( tChrs, ': ', tText[(begnValu) : (endsValu) ] )
  return( float( tText[(begnValu) : (endsValu) ] ))
##

#  Return given text with given value substituted at name="value" in config file
#
def tuplSubs( tChrs, tText, tValu ):
  if ( tChrs in tText ) :
    # opening quote is '="' chars beyond name 
    begnValu = tText.find( tChrs) + len(tChrs) + 2 
    endsValu = begnValu + (tText[begnValu:]).find('"')
    resp = tText[ : begnValu] + (('%f' % tValu).rstrip('0').rstrip('.')) + tText[endsValu :]
    return(resp)
  else :  
    return(tText)
##

# Scan original YASim config and extract numeric elements, save for tix menu
#
def vblsFromTplt():
  #print( 'Entr vblsFromTplt')
  global procPref, lvsdFid, iasaFid, iascFid, drgaFid, solnFid
  global solnDict, solnCDS, solnCols, solnDT, solnIter, solnElev, solnCgMC, solnCgWB
  global yCfgName, yCfgFid, aCfgFid, vCfgFid, versDict, versToDo, versKywd
  #
  ## These vbles correspond to the elements in the config file: 
  global Va, Aa, Ka, Ta, Fa                            # Appr   Spd, Aoa, Thrt, Fuel, Flaps
  global Vc, Hc, Kc, Gc, Tc                            # Cruise Spd, Alt, Thrt, GlideAngle, Fuel
  global Iw, Aw, Cw, Lf, La,   Dw, Ww, Pw, Df, Da, Hw  # Wing, Flap, Ailr
  global Tm, Am, Cm, Lg, Lt,   Dm, Wm, Pm, Dg, Dt, Tw  # Wng1, Flap, Ailr
  global Ch, Ah, Eh, Le, Cv,   Dh, Wh, Ph, De, Dv, Hm  # HStab, Elev (incidence set by solver ) 
  global Av, Ev, Iv, Tv, Lr,   Wv, Pv, Iu, Tu, Dr      # VStab V0:'v' V1:'u', Rudder 
  global Mp, Rp, Ap, Np, Xp,   Ip, Op, Vp, Cp, Tp      # Prop
  global Mb, Xb, Yb, Zb, Hy,   Vy, Wx, Wb, Gx          # Ballast, Solver, Wh main, base, CG
  global fracInci, totlInci                            # Wing incidence and CoG 
  ##
  # YASim 'Solve At' values for Speed and Altitude 
  Vy = 100
  Hy = 1000
  # 
  Va = Aa = Ka = Ta = Fa = Vc = Hc = Kc = Gc = Hw = Hm = Im = Tc =      Wx = Wb = Gx = 0.00
  Iw = Aw = Tw = Tm = Am = Ah = Cv = Av = Wv = Pv = Iv = Tv = Iu = Tu = Cw = Cm = Ch = 0.00
  Eh = Ev = La = Lf = Lg = Lt = Lh = Lv = Lr = Da = Df = Dg = Dt = Dh = Dr = Dw = Dm = Dv = 1.00
  Pw = Pm = Ph = 1.50
  Ww = Wm = Wh = 2.00
  Mp = Rp = Ap = Np = Xp = Ip = Op = Vp = Cp = Tp = 0
  # in case ballast element is missing, fake with tiny value
  Mb = Xb = Yb = Zb = 0.001
  #
  # open base yasim config file and parse elements
  #  print(yCfgFid)
  yCfgSoup = BeautifulSoup( open(yCfgFid).read(), features="xml" )
  ## approach 
  if (yCfgSoup.approach.has_attr('speed')) :
    Va = float(yCfgSoup.approach['speed'])
  if (yCfgSoup.approach.has_attr('aoa')) :
    Aa = float(yCfgSoup.approach['aoa'])
  if (yCfgSoup.approach.has_attr('fuel')) :
    Ka = float(yCfgSoup.approach['fuel'])
  #
  apprCtls = yCfgSoup.approach.find_all('control-setting' )
  for iterCtrl in apprCtls :
    if ( 'throttle' in iterCtrl['axis'] ) :
      Ta = float(iterCtrl['value'])
    if ( 'flaps' in iterCtrl['axis'] ) :
      Fa = float(iterCtrl['value'])
  ## cruise 
  if (yCfgSoup.cruise.has_attr('speed')) :
    Vc = float(yCfgSoup.cruise['speed'])
  if (yCfgSoup.cruise.has_attr('alt')) :
    Hc = float(yCfgSoup.cruise['alt'])
  if (yCfgSoup.cruise.has_attr('fuel')) :
    Kc = float(yCfgSoup.cruise['fuel'])
  if (yCfgSoup.cruise.has_attr('glide-angle')) :
    Gc = float(yCfgSoup.cruise['glide-angle'])
  #
  cruzCtls = yCfgSoup.cruise.find_all('control-setting' )
  for iterCtrl in cruzCtls :
    if ( 'throttle' in iterCtrl['axis'] ) :
      Tc = float(iterCtrl['value'])
  ## wing[0] / mstab
  if (yCfgSoup.wing.has_attr('camber')) :
    Cw = float(yCfgSoup.wing['camber']) 
  if (yCfgSoup.wing.has_attr('idrag')) :
    Dw = float(yCfgSoup.wing['idrag']) 
  if (yCfgSoup.wing.has_attr('incidence')) :
    Iw = float(yCfgSoup.wing['incidence']) 
  if (yCfgSoup.wing.has_attr('twist')) :
    Tw = float(yCfgSoup.wing['twist']) 
  if (yCfgSoup.wing.has_attr('dihedral')) :
    Hw = float(yCfgSoup.wing['dihedral'])
  #   
  if (yCfgSoup.wing.find('stall')) :
    if (yCfgSoup.wing.stall.has_attr('aoa')) :
      Aw = float(yCfgSoup.wing.stall['aoa']) 
    if (yCfgSoup.wing.stall.has_attr('peak')) :
      Pw = float(yCfgSoup.wing.stall['peak']) 
    if (yCfgSoup.wing.stall.has_attr('width')) :
      Ww = float(yCfgSoup.wing.stall['width'])
  #    
  if (yCfgSoup.wing.find('flap0')) :
    if (yCfgSoup.wing.flap0.has_attr('lift')) :
      Lf = float(yCfgSoup.wing.flap0['lift']) 
    if (yCfgSoup.wing.flap0.has_attr('drag')) :
      Df = float(yCfgSoup.wing.flap0['drag']) 
  #    
  if (yCfgSoup.wing.find('flap1')) :
    if (yCfgSoup.wing.flap1.has_attr('lift')) :
      La = float(yCfgSoup.wing.flap1['lift']) 
    if (yCfgSoup.wing.flap1.has_attr('drag')) :
      Da = float(yCfgSoup.wing.flap1['drag']) 
  #    
  ## wing[1] / mstab[0]
  haveExtn = 0
  if ( len(yCfgSoup.find_all('wing')) > 1 ) :
    extnWing = (yCfgSoup.find_all('wing'))[1]
    haveExtn = 1
  if (( haveExtn == 0 ) and len(yCfgSoup.find_all('mstab')) > 0) :   
    extnWing = (yCfgSoup.find_all('mstab'))[0]
    haveExtn = 1
  if ( haveExtn ) :  
    # second wing section 
    if (extnWing.has_attr('camber')) :
      Cm = float(extnWing['camber']) 
    if (extnWing.has_attr('idrag')) :
      Dm = float(extnWing['idrag']) 
    if (extnWing.has_attr('incidence')) :
      Im = float(extnWing['incidence']) 
    if (extnWing.has_attr('twist')) :
      Tm = float(extnWing['twist']) 
    if (extnWing.has_attr('dihedral')) :
      Hm = float(extnWing['dihedral'])
    #   
    if (extnWing.find('stall')) :
      if (extnWing.stall.has_attr('aoa')) :
        Am = float(extnWing.stall['aoa']) 
      if (extnWing.stall.has_attr('peak')) :
        Pm = float(extnWing.stall['peak']) 
      if (extnWing.stall.has_attr('width')) :
        Wm = float(extnWing.stall['width'])
    #    
    if (extnWing.find('flap0')) :
      if (extnWing.flap0.has_attr('lift')) :
        Lg = float(extnWing.flap0['lift']) 
      if (extnWing.flap0.has_attr('drag')) :
        Dg = float(extnWing.flap0['drag']) 
    #    
    if (extnWing.find('flap1')) :
      if (extnWing.flap1.has_attr('lift')) :
        Lt = float(extnWing.flap1['lift']) 
      if (extnWing.flap1.has_attr('drag')) :
        Dt = float(extnWing.flap1['drag']) 
    #
  ## hstab
  if (yCfgSoup.hstab.has_attr('camber')) :
    Ch = float(yCfgSoup.hstab['camber']) 
  if (yCfgSoup.hstab.has_attr('idrag')) :
    Dh = float(yCfgSoup.hstab['idrag']) 
  if (yCfgSoup.hstab.has_attr('effectiveness')) :
    Eh = float(yCfgSoup.hstab['effectiveness']) 
  if (yCfgSoup.hstab.find('stall')) :
    if (yCfgSoup.hstab.stall.has_attr('aoa')) :
      Ah = float(yCfgSoup.hstab.stall['aoa']) 
    if (yCfgSoup.hstab.stall.has_attr('peak')) :
      Ph = float(yCfgSoup.hstab.stall['peak']) 
    if (yCfgSoup.hstab.stall.has_attr('width')) :
      Wh = float(yCfgSoup.hstab.stall['width'])
  #    
  if (yCfgSoup.hstab.find('flap0')) :
    if (yCfgSoup.hstab.flap0.has_attr('lift')) :
      Le = float(yCfgSoup.hstab.flap0['lift']) 
    if (yCfgSoup.hstab.flap0.has_attr('drag')) :
      De = float(yCfgSoup.hstab.flap0['drag']) 
  #    
  ## vstab
  if (yCfgSoup.find('vstab')) :
    if (yCfgSoup.vstab.has_attr('camber')) :
      Cv = float(yCfgSoup.vstab['camber']) 
    if (yCfgSoup.vstab.has_attr('idrag')) :
      Dv = float(yCfgSoup.vstab['idrag']) 
    if (yCfgSoup.vstab.has_attr('effectiveness')) :
      Ev = float(yCfgSoup.vstab['effectiveness']) 
    if (yCfgSoup.vstab.has_attr('incidence')) :
      Iv = float(yCfgSoup.vstab['incidence']) 
    if (yCfgSoup.vstab.has_attr('twist')) :
      Tv = float(yCfgSoup.vstab['twist']) 
    if (yCfgSoup.vstab.find('stall')) :
      if (yCfgSoup.vstab.stall.has_attr('aoa')) :
        Av = float(yCfgSoup.vstab.stall['aoa']) 
      if (yCfgSoup.vstab.stall.has_attr('peak')) :
        Pv = float(yCfgSoup.vstab.stall['peak']) 
      if (yCfgSoup.vstab.stall.has_attr('width')) :
        Wv = float(yCfgSoup.vstab.stall['width'])
  #    
    if (yCfgSoup.vstab.find('flap0')) :
      if (yCfgSoup.vstab.flap0.has_attr('lift')) :
        Lr = float(yCfgSoup.vstab.flap0['lift']) 
      if (yCfgSoup.vstab.flap0.has_attr('drag')) :
        Dr = float(yCfgSoup.vstab.flap0['drag']) 
    #
  ##  propeller
  if (yCfgSoup.find('propeller')) :
    if (yCfgSoup.propeller.has_attr('mass')) :
      Mp = float(yCfgSoup.propeller['mass']) 
    if (yCfgSoup.propeller.has_attr('radius')) :
      Rp = float(yCfgSoup.propeller['radius']) 
    if (yCfgSoup.propeller.has_attr('moment')) :
      Ap = float(yCfgSoup.propeller['moment']) 
    if (yCfgSoup.propeller.has_attr('min-rpm')) :
      Np = float(yCfgSoup.propeller['min-rpm']) 
    if (yCfgSoup.propeller.has_attr('max-rpm')) :
      Xp = float(yCfgSoup.propeller['max-rpm']) 
    if (yCfgSoup.propeller.has_attr('fine-stop')) :
      Ip = float(yCfgSoup.propeller['fine-stop']) 
    if (yCfgSoup.propeller.has_attr('coarse-stop')) :
      Op = float(yCfgSoup.propeller['coarse-stop']) 
    if (yCfgSoup.propeller.has_attr('cruise-speed')) :
      Vp = float(yCfgSoup.propeller['cruise-speed']) 
    if (yCfgSoup.propeller.has_attr('cruise-rpm')) :
      Cp = float(yCfgSoup.propeller['cruise-rpm']) 
    if (yCfgSoup.propeller.has_attr('takeoff-rpm')) :
      Tp = float(yCfgSoup.propeller['takeoff-rpm']) 
  ## ballast 
  if (yCfgSoup.find('ballast')) :
    if (yCfgSoup.ballast.has_attr('mass')) :
      Mb = float(yCfgSoup.ballast['mass']) 
    if (yCfgSoup.ballast.has_attr('x')) :
      Xb = float(yCfgSoup.ballast['x']) 
    if (yCfgSoup.ballast.has_attr('y')) :
      Yb = float(yCfgSoup.ballast['y']) 
    if (yCfgSoup.ballast.has_attr('z')) :
      Zb = float(yCfgSoup.ballast['z']) 
##

#
def cfigFromVbls( tFID):
  #print( 'Entr cfigFromVbls')
  global procPref, lvsdFid, iasaFid, iascFid, drgaFid, solnFid
  global solnDict, solnCDS, solnCols, solnDT, solnIter, solnElev, solnCgMC, solnCgWB
  global yCfgName, yCfgFid, aCfgFid, vCfgFid, versDict, versToDo, versKywd
  #
  ## These vbles correspond to the elements in the config file: 
  global Va, Aa, Ka, Ta, Fa                            # Appr   Spd, Aoa, Thrt, Fuel, Flaps
  global Vc, Hc, Kc, Gc, Tc                            # Cruise Spd, Alt, Thrt, GlideAngle, Fuel
  global Iw, Aw, Cw, Lf, La,   Dw, Ww, Pw, Df, Da, Hw  # Wing, Flap, Ailr
  global Tm, Am, Cm, Lg, Lt,   Dm, Wm, Pm, Dg, Dt, Tw  # Wng1, Flap, Ailr
  global Ch, Ah, Eh, Le, Cv,   Dh, Wh, Ph, De, Dv, Hm  # Hstab, Elev (incidence set by solver ) 
  global Av, Ev, Iv, Tv, Lr,   Wv, Pv, Iu, Tu, Dr      # Vstab V0:'v' V1:'u', Rudder 
  global Mp, Rp, Ap, Np, Xp,   Ip, Op, Vp, Cp, Tp      # Prop
  global Mb, Xb, Yb, Zb, Hy,   Vy, Wx, Wb, Gx          # Ballast, Solver, Wh main, base, CG
  global fracInci, totlInci                            # Wing incidence and CoG 
  ##
  apprFlag   = 0
  cruzFlag   = 0
  wingFlag   = 0
  wng1Flag   = 0
  hstabFlag  = 0
  vstabFlag  = 0
  vstabDone  = 0
  mstabFlag  = 0
  mstabDone  = 0
  ballFlag   = 0
  ballDone   = 0
  propFlag   = 0
  if ( pythVers < 3 ) :
    aCfgHndl  = open(tFID, 'w', 0)
  else :
    aCfgHndl  = open(tFID, 'w')
  # write auto file via yconfig template and subsVbls from Tix
  with open(yCfgFid, 'r') as yCfgHndl:
  # step each line in template yasim config file
    for line in yCfgHndl:
      # set / clear flags for each section
      if '<approach'  in line:
        apprFlag = 1
      if '</approach' in line:
        apprFlag = 0
      if '<cruise'    in line:
        cruzFlag = 1
      if '</cruise'   in line:
        cruzFlag = 0
      if '<wing'      in line:
        wingFlag = 1
      if '</wing'     in line:
        wingFlag = 0
        wng1Flag = 0
      if '<hstab'     in line:
        hstabFlag = 1
      if '</hstab'    in line:
        hstabFlag = 0
      if '<vstab'     in line:
        vstabFlag = 1
      if '</vstab'    in line:
        vstabDone = 1
        vstabFlag = 0
      if '<mstab'     in line:
        mstabFlag = 1
      if '</mstab'    in line:
        mstabDone = 1
        mstabFlag = 0
      if '<ballast' in line:
        ballFlag = 1
      if '</ballast'in line:
        ballFlag = 0
        ballDone = 1
      if '<propeller' in line:
        propFlag = 1
      if '</propeller'in line:
        propFlag = 0
      ### in each section substitute updated element values

      lineChrs = line.lstrip()
      if ( (lineChrs[0:4]) != "<!--" ) :
        ## approach
        if (apprFlag == 1):
          line = tuplSubs( 'speed',   line, Va ) 
          line = tuplSubs( 'aoa',     line, Aa ) 
          line = tuplSubs( 'fuel',    line, Ka ) 
          #print('subsLine: ', line)
          if ('throttle' in line):
            line   = tuplSubs( 'value', line, Ta ) 
          if ('flaps' in line):
            line   = tuplSubs( 'value', line, Fa ) 

        ## cruise
        if (cruzFlag == 1):
          if ('cruise speed' in line):
            # print ('Vc: ', Vc, ' Hc: ', Hc, ' Kc: ', Kc, ' Gc: ', Gc)  
            line = tuplSubs( 'speed',       line, Vc ) 
            line = tuplSubs( 'alt',         line, Hc ) 
          if ('fuel' in line):
            line = tuplSubs( 'fuel',        line, Kc ) 
          if ('glide-angle' in line):
            line = tuplSubs( 'glide-angle', line, Gc ) 
          if ('throttle' in line):
            line = tuplSubs( 'value',       line, Tc )

        ### wing sections parse camber and induced drag elements
        if ( (wingFlag  == 1)or (mstabFlag == 1) ) :
          if (  ( (wingFlag  == 1) and ( 'append=\"1\"' in line ) )  \
             or ( (mstabFlag == 1) and ( mstabDone == 0) ) ) :
            # first mstab uses wing1 settings 
            wng1Flag = 1
          if ( wng1Flag != 1 ) :          
            line = tuplSubs( 'camber',    line, Cw ) 
            line = tuplSubs( 'idrag',     line, Dw )
            line = tuplSubs( 'incidence', line, Iw )
            line = tuplSubs( 'twist',     line, Tw )
            line = tuplSubs( 'dihedral',  line, Hw )
            #print ('Wrt  Cw: ', Cw, 'Dw: ', Dw, ' Iw: ', Iw ,' Tw: ', Tw,' Hw: ', Hw)  
            #   
            if ('stall' in line):
             line = tuplSubs( 'aoa'  ,    line, Aw )
             line = tuplSubs( 'peak' ,    line, Pw ) 
             line = tuplSubs( 'width',    line, Ww ) 
            #  
            if ('flap0' in line):
              line = tuplSubs( 'lift',    line, Lf ) 
              line = tuplSubs( 'drag',    line, Df ) 
            #  
            if ('flap1' in line):
              line = tuplSubs( 'lift',    line, La ) 
              line = tuplSubs( 'drag',    line, Da )
            # end wing 
          else :   
            line = tuplSubs( 'camber',    line, Cm ) 
            line = tuplSubs( 'idrag',     line, Dm )
            line = tuplSubs( 'dihedral',  line, Hm )
            #print ('Wrt  Cw: ', Cw, 'Dw: ', Dw, ' Iw: ', Iw ,' Tw: ', Tw,' Hm: ', Hm)  
            #   
            if ('stall' in line):
              line = tuplSubs( 'aoa'  ,  line, Am )
              line = tuplSubs( 'peak' ,  line, Pm ) 
              line = tuplSubs( 'width',  line, Wm ) 
            #  
            if ('flap0' in line):
              line = tuplSubs( 'lift',   line, Lg ) 
              line = tuplSubs( 'drag',   line, Dg ) 
            #  
            if ('flap1' in line):
              line = tuplSubs( 'lift',   line, Lt ) 
              line = tuplSubs( 'drag',   line, Dt )
            # end wng1

        ## HStab     
        if (hstabFlag == 1):
          line = tuplSubs( 'camber', line, Ch ) 
          line = tuplSubs( 'idrag',  line, Dh )
          line = tuplSubs( 'effectiveness',  line, Eh )
          #
          if ('stall' in line):
            line = tuplSubs( 'aoa'  ,  line, Ah ) 
            line = tuplSubs( 'peak' ,  line, Ph )
            line = tuplSubs( 'width',  line, Wh ) 
          #   
          if ('flap0' in line):
            line = tuplSubs( 'lift',   line, Le ) 
            line = tuplSubs( 'drag',   line, De ) 
          # 

        ## Vstab   
        if ((vstabFlag == 1) and (vstabDone == 0)):
          line = tuplSubs( 'camber', line, Cv ) 
          line = tuplSubs( 'idrag',  line, Dv )
          line = tuplSubs( 'effectiveness', line, Ev )
          #
          line = tuplSubs( 'incidence', line, Iv )
          line = tuplSubs( 'twist', line, Tv )
          #print ('Wrt  Iv: ', Iv, 'Tv: ', Tv)  
            #   
          #
          if ('stall' in line):
            line = tuplSubs( 'aoa'  ,  line, Av ) 
            line = tuplSubs( 'peak' ,  line, Pv )
            line = tuplSubs( 'width',  line, Wv ) 
          #   
          if ('flap0' in line):
            line = tuplSubs( 'lift',   line, Lr ) 
            line = tuplSubs( 'drag',   line, Dr ) 
          # 
        #

        ## ballast ( Ensure input config does not enclose ballast in comments )
        if ((ballFlag == 1) and (ballDone == 0)):
          ## ballast section one line for all elements if present
          line = tuplSubs( 'mass',   line, Mb ) 
          line = tuplSubs( 'x',      line, Xb ) 
          line = tuplSubs( 'y',      line, Yb ) 
          line = tuplSubs( 'z',      line, Zb ) 
          ballFlag =  0
          ballDone =  1
        #

        ## prop 
        if (propFlag == 1):
          ## prop section parse elements if present
          line = tuplSubs( 'mass',   line, Mp ) 
          line = tuplSubs( 'radius', line, Rp ) 
          line = tuplSubs( 'moment', line, Ap ) 
          line = tuplSubs( 'min-rpm',line, Np ) 
          line = tuplSubs( 'max-rpm',line, Xp ) 
          line = tuplSubs( 'fine-stop',   line, Ip ) 
          line = tuplSubs( 'coarse-stop', line, Op ) 
          line = tuplSubs( 'cruise-speed',line, Vp ) 
          line = tuplSubs( 'cruise-rpm',  line, Cp ) 
          line = tuplSubs( 'takeoff-rpm', line, Tp ) 
          #

        ## Version string   
        # look for <airplane mass= to insert keyword for selected version
        if '<airplane mass="' in line:
          #
          metaLine =  strftime("<!-- %d%b%Y %H:%M:%S  auto generated by ysimi.py  -->\n", gmtime())
          #metaLine = '<!-- ysimi-outp {%i} {%i}:{%i}   -->\n'
          aCfgHndl.write(metaLine)
          #print('airplane kywd:', versKywd, '  todo: ', versToDo)
          # make an index list of double quotes in the line
          sepsList = []
          sepsChar = '"'
          lastIndx = 0
          while (lastIndx > -1):
            sepsIndx = line.find( sepsChar, (lastIndx +1))
            if (sepsIndx > 0) :
              sepsList.append(sepsIndx)
            lastIndx = sepsIndx
          #
          if ('version=' in line ):
            linePart = line[:line.find('version=')]  
            sepsIndx = line.find('version=')
            sepsIndx = line.find('"', (sepsIndx+1))
            sepsIndx = line.find('"', (sepsIndx+1))
            linePart = linePart + 'version="' + versKywd
            linePart = linePart + line[sepsIndx:]
            line = linePart
          else :  
            # Use index list to split line into text and numbers
            lineMass = line[0:(sepsList[1]+1)]
            line = lineMass + ' version="' + versKywd + '">'
          #
      # Write unchanged/modified line into auto.xml
      aCfgHndl.write(line)
  #close and sync files
  aCfgHndl.flush
  os.fsync(aCfgHndl.fileno())
  aCfgHndl.close
  yCfgHndl.close
  #print( 'Exit cfigFromVbls')
## 

# Make up command line and execuute external process call to YASim   
def spinYasim(tFid):
  #print( 'Entr spinYasim')
  global procPref, lvsdFid, iasaFid, iascFid, drgaFid, solnFid
  global solnDict, solnCDS, solnCols, solnDT, solnIter, solnElev, solnCgMC, solnCgWB
  global yCfgName, yCfgFid, aCfgFid, vCfgFid, versDict, versToDo, versKywd
  #
  global Mb, Xb, Yb, Zb, Hy,   Vy, Wx, Wb, Gx          # Ballast, Solver, Wh main, base, CG
  global fracInci, totlInci                            # Wing incidence and CoG 
  ##
  #
  ## update fileIDs with version selected from dropdown
  lvsdFid  = procPref + versToDo + '-lvsd.txt'
  drgaFid  = procPref + versToDo + '-drga.txt'
  iasaFid  = procPref + versToDo + '-iasa.txt'
  iascFid  = procPref + versToDo + '-iasc.txt'
  solnFid  = procPref + versToDo + '-soln.txt'
  #print('spinYasim tFid: ', tFid)
  ##
  spinFast = 0
  if ( spinFast < 1 ) :
    # run yasim external process to generate LvsD data table saved dataset file
    vDatHndl = open(lvsdFid, 'w')
    if  ( sys.platform.startswith('linux')):
      command_line = 'yasim {:s} --detailed-graph -a {:.2f} -s {:.2f}' \
                      .format(tFid,                 (Hy/3.3), (Vy))
    else:
      command_line = 'yasim {:s} -g     -a {:.2f} -s {:.2f}' \
                      .format(tFid,                 (Hy/3.3), (Vy))
    #    print(command_line)
    args = shlex.split(command_line)
    DEVNULL = open(os.devnull, 'wb')
    p = subprocess.run(args, stdout=vDatHndl, stderr=DEVNULL)
    DEVNULL.close()
    vDatHndl.close
    if  ( sys.platform.startswith('linux')):
      os.sync()
    #p.wait()
    ##
    # run yasim external process to generate min IAS data table saved dataset file
    vDatHndl = open(iasaFid, 'w')

    if  ( sys.platform.startswith('linux')):
      command_line = 'yasim {:s} --detailed-min-speed -a {:.2f}' \
                      .format(tFid,                 (Hy/3.3))
    else:
      command_line = 'yasim {:s} --min-speed -a {:.2f}' \
                      .format(tFid,                 (Hy/3.3))
    #    print(command_line)
    args = shlex.split(command_line)
    DEVNULL = open(os.devnull, 'wb')
    p = subprocess.run(args, stdout=vDatHndl, stderr=DEVNULL)
    DEVNULL.close()
    vDatHndl.close
    if  ( sys.platform.startswith('linux')):
      os.sync()
    #p.wait()
    ##
    ##  Perforamnce
    if (0) :
      # run yasim external process to generate min IAS data table saved dataset file
      vDatHndl = open(iascFid, 'w')
      if  ( sys.platform.startswith('linux')):
        command_line = 'yasim ' + tFid + ' --detailed-min-speed -cruise '
      else:
        command_line = 'yasim ' + tFid + '        --min-speed -cruise '
      #    print(command_line)
      args = shlex.split(command_line)
      DEVNULL = open(os.devnull, 'wb')
      p = subprocess.run(args, stdout=vDatHndl, stderr=DEVNULL)
      DEVNULL.close()
      vDatHndl.close
      if  ( sys.platform.startswith('linux')):
        os.sync()
      #p.wait()
      ##
      # run yasim external process to generate min IAS data table saved dataset file
      vDatHndl = open(drgaFid, 'w')
      if  ( sys.platform.startswith('linux')):
        command_line = 'yasim ' + tFid + ' --detailed-drag -approach '
      else:   
        command_line = 'yasim ' + tFid + ' -d -approach '
      #    print(command_line)
      args = shlex.split(command_line)
      DEVNULL = open(os.devnull, 'wb')
      p = subprocess.run(args, stdout=vDatHndl, stderr=DEVNULL)
      DEVNULL.close()
      vDatHndl.close
      if  ( sys.platform.startswith('linux')):
        os.sync()
      #p.wait()
      ##
  else :  
    # run yasim external process to generate LvsD data table saved dataset file
    vDatHndl = open(lvsdFid, 'w')
    command_line = 'yasim ' + tFid + ' -g            -a '+ str(Hy/3.3) + ' -s ' + str(Vy)
    #    print(command_line)
    args = shlex.split(command_line)
    DEVNULL = open(os.devnull, 'wb')
    p = subprocess.run(args, stdout=vDatHndl, stderr=DEVNULL)
    DEVNULL.close()
    vDatHndl.close
    if  ( sys.platform.startswith('linux')):
      os.sync()
    #p.wait()
    ##
    # run yasim external process to generate min IAS data table saved dataset file
    vDatHndl = open(iasaFid, 'w')
    command_line = 'yasim ' + tFid + '        --min-speed -approach '
    #    print(command_line)
    args = shlex.split(command_line)
    DEVNULL = open(os.devnull, 'wb')
    p = subprocess.run(args, stdout=vDatHndl, stderr=DEVNULL)
    DEVNULL.close()
    vDatHndl.close
    if  ( sys.platform.startswith('linux')):
      os.sync()
    #p.wait()
    ##
    ##  Perforamnce
    if (0) :
      # run yasim external process to generate min IAS data table saved dataset file
      vDatHndl = open(iascFid, 'w')
      command_line = 'yasim ' + tFid + '        --min-speed -cruise '
      #    print(command_line)
      args = shlex.split(command_line)
      DEVNULL = open(os.devnull, 'wb')
      p = subprocess.run(args, stdout=vDatHndl, stderr=DEVNULL)
      DEVNULL.close()
      vDatHndl.close
      if  ( sys.platform.startswith('linux')):
        os.sync()
      #p.wait()
      ##
      # run yasim external process to generate min IAS data table saved dataset file
      vDatHndl = open(drgaFid, 'w')
      command_line = 'yasim ' + tFid + '         -drag -approach '
      #    print(command_line)
      args = shlex.split(command_line)
      DEVNULL = open(os.devnull, 'wb')
      p = subprocess.run(args, stdout=vDatHndl, stderr=DEVNULL)
      DEVNULL.close()
      vDatHndl.close
      if  ( sys.platform.startswith('linux')):
        os.sync()
      #p.wait()
      ##
  # run yasim external process to create console output of solution
  vDatHndl = open(solnFid, 'w')
  command_line = 'yasim ' + tFid
  #    print(command_line)
  args = shlex.split(command_line)
  DEVNULL = open(os.devnull, 'wb')
  p = subprocess.run(args, stdout=vDatHndl, stderr=DEVNULL)
  DEVNULL.close()
  vDatHndl.flush
  vDatHndl.close
  if  ( sys.platform.startswith('linux')):
    os.sync()
  ##
  # Pull key values from yasim solution console output for dict, dataTable
  wingInci( aCfgFid)
  solnIter = scanSoln( solnFid, 'Iterations')
  solnDrgC = scanSoln( solnFid, 'Drag Coefficient')
  solnLftR = scanSoln( solnFid, 'Lift Ratio')
  solnAoAc = scanSoln( solnFid, 'CruiseAoA')
  solnTail = scanSoln( solnFid, 'Tail Incidence')
  solnElev = scanSoln( solnFid, 'Approach Elevator')
  solnCgMC = scanSoln( solnFid, 'CG-x rel. MAC')
  cofgXval = float(scanSoln( solnFid, 'CG-x    ').rstrip('m'))
  if ( Wb != 0 ) :
    solnCgWB = ( cofgXval - Wx ) / Wb
  # dunno how to update text boxes so output to console
  print( '#{:s}  HS:{:s}  ApElv:{:s}  CG@{:s}MC, {:3.0f}%WB  WInc:{:2.1f}d, {:.1f}% of ASt:{:.1f}d ' \
          .format( solnIter, solnTail, solnElev, solnCgMC, (100 * solnCgWB), totlInci, (100 * fracInci), Aw))
  solnDict = dict( 
              dNames  = [ 'Iterations', 'HStab Inci', 'Appr Elev', 'CG at MAC', 'CG on WB', 'Wing Inci', 'Stall AoA'],
              dValues = [  solnIter, solnTail, solnElev,    solnCgMC,   '{:3.0f}%'.format(100 * solnCgWB), '{:.1f}'.format(totlInci), Aw ])
  solnCDS  = ColumnDataSource ( solnDict)
  solnCols = [TableColumn( field="dNames", title="Starting" ),
              TableColumn( field="dValues", title="Values" ), ]
  solnDT   = DataTable(source=solnCDS, columns=solnCols, width=240, height=200)
  solnCDS.update()
  solnDT.update()
  ##  
  #print( 'Exit spinYasim')
#

# scan YASim solution file for given text eg for console print of elev, CofG
def scanSoln( tFid, tText) :
  #print( 'Entr scanSoln')
  with open(tFid, 'r') as solnHndl:
  # step each line in template yasim config file
    for tLine in solnHndl:
      if ( tText in tLine ) :
        # find the colon after the text
        tPosn = tLine.find( tText )
        tPosn = tLine.find( ':', (tPosn + 1))
        return ( tLine[ tPosn + 1 : ].strip('\n'))
##

# Given main, Seconary wheels x, z coords, return body incidence 
def bodyInci( Mx, Mz, Sx, Sz ) :  
  #
  Gx = Mx - Sx
  Gz = Mz - Sz
  # fiddle if wheels same distance on CL
  if ( Gz == 0 ) : Gz += 0.000001
  Ex = (Sz * Gx) / Gz
  inci = -1 * np.arctan ( Mz / ( Ex + Gx ) )
  inci = math.degrees ( inci ) 
  #
  return(inci)
##

# Given fileID figure wing + body incidence and stall margin
def wingInci( tFid) :
  global Mb, Xb, Yb, Zb, Hy,   Vy, Wx, Wb, Gx          # Ballast, Solver, Wh main, base, CG
  global fracInci, totlInci                            # Wing incidence and CoG 
  tree = ET.parse(tFid)
  root = tree.getroot()
  # Assume three wheels are specified, need z1, z2 verts from CL and (X1 - x2) separation
  x1 = y1 = z1 = x2 = y2 = z2 = 0
  for gearElem in root.iter('gear') :
    # Test if tail contact point is specified as 'ignored' 
    skipElem = gearElem.get( 'ignored-by-solver')
    if ( skipElem != '1') :
      # one of the wheels is both the same 
      xVal = float(gearElem.get('x'))
      yVal = float(gearElem.get('y'))
      zVal = float(gearElem.get('z'))
      if (( x1 == 0 ) & ( y1 == 0 ) & ( z1 == 0 )) :
        # found first wheel element, put in x1, y1, z1
        x1 = xVal
        y1 = yVal
        z1 = zVal
        #      print('First  x1: ', x1, ' y1: ', y1, 'z1: ', z1, 'x2: ', x2, ' y2: ', y2,  'z2: ', z2 )
      else :
        # not a new wheel1: then a non match is wheel2 
        if (( x1 != xVal ) ) :
          if (( x2 == xVal ) &                  ( z2 == zVal )) :
            # If newv == stored then swap mains into w1
            x2 = x1
            y2 = y1
            z2 = z1
            x1 = xVal
            y1 = yVal
            z1 = zVal
            #  print('  Swap x1: ', x1, ' y1: ', y1, 'z1: ', z1, 'x2: ', x2, ' y2: ', y2,  'z2: ', z2 )
          else:
            #  print('else xVal: ', xVal, ' yVal: ', yVal, 'zVal: ', zVal)
            x2 = xVal
            y2 = yVal
            z2 = zVal
            # print('NoSwap x1: ', x1, ' y1: ', y1, 'z1: ', z1, 'x2: ', x2, ' y2: ', y2,  'z2: ', z2 )
  ## mains in x1, y1, z1, wheelbase for CoG 
  Wx = x1
  Wb = (x2 - x1)
    #    print('Wx: ', Wx, ' Wb: ', Wb)
  #  print('Done, Main x1: ', x1, ' y1: ', y1, 'z1: ',   z1, 'x2: ', x2, ' y2: ', y2, ' z2: ', z2 )
  if  ( z1 <= z2 ) :
    clinInci = bodyInci(x1, z1, x2, z2 )
  else:   
    clinInci = bodyInci(x2, z2, x1, z1 )
  wingInci = wingAoaS = 0
  wingElem = root.find('wing')
  if ( wingElem.get('incidence') != None ) :
    wingInci = float(wingElem.get('incidence'))
  if ( wingElem.find('stall') != None ) :
    wingAoaS = float(wingElem.find('stall').get('aoa'))
  totlInci = clinInci + wingInci
  fracInci = totlInci / wingAoaS
##  
##  

#  main section: Run the calls to YASim ready for bokeh interface to browser 
pullArgs(sys.argv[1:])
presets()
vblsFromTplt()
cfigFromVbls( aCfgFid)
spinYasim( aCfgFid )

# use pandas to read sources and create bokeh dataframes
lvsdDfrm  = pd.read_csv(lvsdFid, sep='\t')
lvsdDsrc  = ColumnDataSource(lvsdDfrm)
#
iasaDfrm  = pd.read_csv(iasaFid, sep='\t')
iasaDsrc  = ColumnDataSource(iasaDfrm)
## 
if (0) :
  drgaDfrm  = pd.read_csv(drgaFid, sep='\t')
  drgaDsrc  = ColumnDataSource(drgaDfrm)
  #
  #
  iascDfrm  = pd.read_csv(iascFid, sep='\t')
  iascDsrc  = ColumnDataSource(iascDfrm)
  #
# Dropdown for selecting which YASim version to run 
versDrop = Dropdown(width=64, label='YASim VERSION', \
menu=['-vOrig', '-v2017-2', '-v32', '-vCurr'])
#
wingInci( aCfgFid)
#
# Set up plots
liftPlot  = figure(height=250, width=208, title="Acft Lift G  vs  AoA",
              tools="crosshair,pan,reset,save,wheel_zoom" )

dragPlot  = figure(height=250, width=208, title="Acft Drag G  vs  AoA",
              tools="crosshair,pan,reset,save,wheel_zoom" )

lvsdPlot  = figure(height=250, width=208, title="Acft L/D vs AoA @Appr",
              tools="crosshair,pan,reset,save,wheel_zoom" )

drgaPlot  = figure(height=250, width=208, title="Drag vs Kias @ Appr ",
              tools="crosshair,pan,reset,save,wheel_zoom" )

iasaPlot  = figure(height=250, width=208, title="VSzero IAS vs AoA @ Appr",
              tools="crosshair,pan,reset,save,wheel_zoom" )

iascPlot  = figure(height=250, width=208, title="VSzero IAS vs AoA @ Cruz",
              tools="crosshair,pan,reset,save,wheel_zoom" )

##
#if (0) :
if (1) :
# Enable for patched yasim-test else no LvsD column exists
  liftPlot.line( x='aoa', y='lift',  source=lvsdDsrc, line_width=3, line_alpha=0.6)
  dragPlot.line( x='aoa', y='drag',  source=lvsdDsrc, line_width=3, line_alpha=0.6)
  lvsdPlot.line( x='aoa', y='LD',    source=lvsdDsrc, line_width=3, line_alpha=0.6)
else : 
  liftPlot.line( x='aoa', y='lift',  source=lvsdDsrc, line_width=3, line_alpha=0.6)
  dragPlot.line( x='aoa', y='drag',  source=lvsdDsrc, line_width=3, line_alpha=0.6)
# 
iasaPlot.line( x='aoa', y='knots', source=iasaDsrc, line_width=3, line_alpha=0.6)
iasaPlot.line( x='aoa', y='lift',  source=iasaDsrc, line_width=3, line_alpha=0.6)
#
  ##
  ##  Perforamnce
if (0) :
  drgaPlot.line( x='knots', y='drag',  source=drgaDsrc, line_width=3, line_alpha=0.6)
  #
  iascPlot.line( x='aoa', y='knots', source=iascDsrc, line_width=3, line_alpha=0.6)
  iascPlot.line( x='aoa', y='lift',  source=iascDsrc, line_width=3, line_alpha=0.6)  
##
#
# Set up widgets, balance range / step size each affects re-calc
#   A smaller step size affects YASim spins: bigger step <==> faster response 
#
varyVa = Slider(bar_color='silver', width=132, title="Appr IAS      Va", value=Va, start=(20.0 ), end=(240 ), step=(1.0 ))
varyAa = Slider(bar_color='silver', width=132, title="Appr Acft AoA Aa", value=Aa, start=(-5.0 ), end=(20  ), step=(0.10))
varyTa = Slider(bar_color='silver', width=132, title="Appr Throttle Ta", value=Ta, start=(0.0  ), end=(1.0 ), step=(0.02))
varyKa = Slider(bar_color='silver', width=132, title="Appr Fuel     Ka", value=Ka, start=(0.0  ), end=(1.0 ), step=(0.02))
varyFa = Slider(bar_color='silver', width=132, title="Appr Flaps    Fa", value=Fa, start=(0.0  ), end=(1.0 ), step=(0.10))
#
varyVc = Slider(bar_color='silver', width=132, title="Cruz IAS Kt   Vc", value=Vc, start=(50   ), end=(650),  step=( 5.0))
varyHc = Slider(bar_color='silver', width=132, title="Cruz Alt Ft   Hc", value=Hc, start=(1000 ), end=(50000),step=(200 ))
varyTc = Slider(bar_color='silver', width=132, title="Cruz Throttle Tc", value=Tc, start=(0.0  ), end=(1.0 ), step=(0.05))
varyKc = Slider(bar_color='silver', width=132, title="Cruz Fuel     Kc", value=Kc, start=(0.0  ), end=(1.0 ), step=(0.05))
varyGc = Slider(bar_color='silver', width=132, title="Cruz Gl Angle Gc", value=Gc, start=(0.0  ), end=(20.0), step=(0.20))
#
varyAw = Slider(bar_color='silver', width=132, title="W0 AoA St     Aw", value=Aw, start=(-2.0 ), end=(24.0), step=(0.10))
varyDw = Slider(bar_color='silver', width=132, title="W0 iDrag--    Dw", value=Dw, start=( 0.1 ), end=(4.0 ), step=(0.005))
varyCw = Slider(bar_color='silver', width=132, title="W0 Camb  CL0/CLs", value=Cw, start=(0.000), end=(2.00), step=(0.005))
varyCm = Slider(bar_color='silver', width=132, title="WM Camb  CL0/CLs", value=Cm, start=(0.000), end=(2.00), step=(0.005))
varyLf = Slider(bar_color='silver', width=132, title="W0 Flap0 Lift Lf", value=Lf, start=( 0.01), end=(8.0 ), step=(0.01 ))
varyDf = Slider(bar_color='silver', width=132, title="W0 Flap0 Drag Df", value=Df, start=( 0.00), end=(20.0 ),step=(0.05))
#
varyWw = Slider(bar_color='silver', width=132, title="W0 Width St   Ww", value=Ww, start=(0.0  ), end=(32  ), step=(0.10))
varyPw = Slider(bar_color='silver', width=132, title="W0 Peak  St   Pw", value=Pw, start=(0.0  ), end=(10.0), step=(0.10))
varyIw = Slider(bar_color='silver', width=132, title="W0 Incidence  Iw", value=Iw, start=(-5.0 ), end=(10.0), step=(0.1 ))
varyLa = Slider(bar_color='silver', width=132, title="W0 Ailr Lift  La", value=La, start=( 0.00), end=(4.0 ), step=(0.02 ))
varyDa = Slider(bar_color='silver', width=132, title="W0 Ailr Drag  Da", value=Da, start=( 0.00), end=(4.0 ), step=(0.02))
#
varyAm = Slider(bar_color='silver', width=132, title="WM AoA St     Am", value=Am, start=(-2.0 ), end=(24.0), step=(0.10))
varyDm = Slider(bar_color='silver', width=132, title="WM iDrag--    Dm", value=Dm, start=( 0.1 ), end=(4.0 ), step=(0.10))
varyTw = Slider(bar_color='silver', width=132, title="W0 Twist      Tw", value=Tw, start=(-8.00), end=(12.0), step=(0.10))
varyHw = Slider(bar_color='silver', width=132, title="W0 Dihedral   Hw", value=Hw, start=(-8.00), end=(12.0), step=(0.05))
varyLg = Slider(bar_color='silver', width=132, title="WM Flap0 Lift Lg", value=Lg, start=( 0.00), end=(4.0 ), step=(0.01))
varyDg = Slider(bar_color='silver', width=132, title="WM Flap0 Drag Dg", value=Dg, start=( 0.00), end=(10.0 ),step=(0.01))
#
varyWm = Slider(bar_color='silver', width=132, title="WM Width St   Wm", value=Wm, start=(0.0  ), end=(32  ), step=(0.10))
varyPm = Slider(bar_color='silver', width=132, title="WM Peak  St   Pm", value=Pm, start=(0.0  ), end=(20.0), step=(0.10))
varyTm = Slider(bar_color='silver', width=132, title="WM Twist      Tm", value=Tm, start=(-8.00), end=(8.00), step=(0.10))
varyHm = Slider(bar_color='silver', width=132, title="WM Dihedral   Hm", value=Hm, start=(-8.00), end=(8.00), step=(0.05))
varyLt = Slider(bar_color='silver', width=132, title="WM Ailr Lift  Lt", value=Lt, start=( 0.00), end=(4.0 ), step=(0.10))
varyDt = Slider(bar_color='silver', width=132, title="WM Ailr Drag  Dt", value=Dt, start=( 0.00), end=(4.0 ), step=(0.01))
#
varyAh = Slider(bar_color='silver', width=132, title="HStab Aoa St  Ah", value=Ah, start=(-2.0 ), end=(24.0), step=(0.10))
varyDh = Slider(bar_color='silver', width=132, title="HStab IDrag-- Dh", value=Dh, start=( 0.1 ), end=(4.0 ), step=(0.10))
varyCh = Slider(bar_color='silver', width=132, title="HStab Camber  Ch", value=Ch, start=(0.00 ), end=(2.00), step=(0.01))
varyLe = Slider(bar_color='silver', width=132, title="Elev Lift     Le", value=Le, start=( 0.1 ), end=(8.0 ), step=(0.01))
varyCv = Slider(bar_color='silver', width=132, title="VStab Camber  Cv", value=Cv, start=(0.00 ), end=(2.50), step=(0.01))
#
varyWh = Slider(bar_color='silver', width=132, title="HStab Wdth St Wh", value=Wh, start=(0.0  ), end=(32  ), step=(0.20))
varyPh = Slider(bar_color='silver', width=132, title="HStab Peak St Ph", value=Ph, start=(0.0  ), end=(20.0), step=(0.20))
varyEh = Slider(bar_color='silver', width=132, title="HStab Effect  Eh", value=Eh, start=( 0.1 ), end=(4.0 ), step=(0.10))
varyDe = Slider(bar_color='silver', width=132, title="Elev Drag     De", value=De, start=(0.00 ), end=(4.0 ), step=(0.01))
varyDv = Slider(bar_color='silver', width=132, title="VStab IDrag-- Dv", value=Dv, start=(0.00 ), end=(8.0 ), step=(0.01))
#
varyAv = Slider(bar_color='silver', width=132, title="VStab AoA St  Av", value=Av, start=(-2.0 ), end=(24.0), step=(0.10))
varyEv = Slider(bar_color='silver', width=132, title="VStab Effect  Ev", value=Ev, start=( 0.1 ), end=(4.0 ), step=(0.10))
varyIv = Slider(bar_color='silver', width=132, title="VStab Incid   Iv", value=Iv, start=(-4.0 ), end=(4.0 ), step=(0.05))
varyTv = Slider(bar_color='silver', width=132, title="VStab Twist   Tv", value=Tv, start=(-4.0 ), end=(4.0 ), step=(0.10))
varyLr = Slider(bar_color='silver', width=132, title="Rudder Lift   Lr", value=Lr, start=(-4.0 ), end=(8.0 ), step=(0.02))
varyMb = Slider(bar_color='silver', width=132, title="Bllst Mass    Mb", value=Mb, start=(-5000), end=(50000),step=(20.0))
varyHy = Slider(bar_color='silver', width=132, title="Solve Alt ft  Hy", value=Hy, start=(   0 ), end=(40000),step=(100))
#
varyWv = Slider(bar_color='silver', width=132, title="VStab StWdth  Wv", value=Wv, start=(0.0  ), end=(32  ), step=(0.50))
varyPv = Slider(bar_color='silver', width=132, title="VStab StPeak  Pv", value=Pv, start=(0.2  ), end=(20.0), step=(0.20))
varyIu = Slider(bar_color='silver', width=132, title="VStab Incid   Iu", value=Iu, start=(-4.0 ), end=(4.0 ), step=(0.05))
varyTu = Slider(bar_color='silver', width=132, title="VStab Twist   Tu", value=Tu, start=(-4.0 ), end=(4.0 ), step=(0.05))
varyDr = Slider(bar_color='silver', width=132, title="Rudder Drag   Dr", value=Dr, start=( 0.0 ), end=(4.0 ), step=(0.05))
varyXb = Slider(bar_color='silver', width=132, title="Bllst Posn    Xb", value=Xb, start=(-200 ), end=(200 ), step=(0.25))
varyVy = Slider(bar_color='silver', width=132, title="Solve IAS kt  Vy", value=Vy, start=(40   ), end=(650 ), step=(20  ))
#

# called whenever a value is changed on browser interface
def update_elem(attrname, old, new):
  #  print( 'Entr update_elem')
  global procPref, lvsdFid, iasaFid, iascFid, drgaFid, solnFid
  global solnDict, solnCDS, solnCols, solnDT, solnIter, solnElev, solnCgMC, solnCgWB
  global yCfgName, yCfgFid, aCfgFid, vCfgFid, versDict, versToDo, versKywd
  #
  ## These vbles correspond to the elements in the config file: 
  global Va, Aa, Ka, Ta, Fa                            # Appr   Spd, Aoa, Thrt, Fuel, Flaps
  global Vc, Hc, Kc, Gc, Tc                            # Cruise Spd, Alt, Thrt, GlideAngle, Fuel
  global Iw, Aw, Cw, Lf, La,   Dw, Ww, Pw, Df, Da, Hw  # Wing, Flap, Ailr
  global Tm, Am, Cm, Lg, Lt,   Dm, Wm, Pm, Dg, Dt, Tw  # Wng1, Flap, Ailr
  global Ch, Ah, Eh, Le, Cv,   Dh, Wh, Ph, De, Dv, Hm  # HStab, Elev (incidence set by solver ) 
  global Av, Ev, Iv, Tv, Lr,   Wv, Pv, Iu, Tu, Dr      # VStab V0:'v' V1:'u', Rudder 
  global Mp, Rp, Ap, Np, Xp,   Ip, Op, Vp, Cp, Tp      # Prop
  global Mb, Xb, Yb, Zb, Hy,   Vy, Wx, Wb              # Ballast, Solver, Wheels 
  global fracInci, totlInci                            # Wing incidence and CoG 
  ##
  global fracInci, totlInci
  #
  # Put current slider values into global configuration values
  Va =  varyVa.value
  Aa =  varyAa.value
  Ta =  varyTa.value
  Ka =  varyKa.value
  Fa =  varyFa.value
  #
  Vc =  varyVc.value
  Hc =  varyHc.value
  Tc =  varyTc.value
  Kc =  varyKc.value
  Gc =  varyGc.value
  #
  Iw =  varyIw.value
  Aw =  varyAw.value
  Cw =  varyCw.value
  Lf =  varyLf.value
  La =  varyLa.value
  #
  Dw =  varyDw.value
  Ww =  varyWw.value
  Pw =  varyPw.value
  Df =  varyDf.value
  Da =  varyDa.value
  #
  Tw =  varyTw.value
  Tm =  varyTm.value
  Am =  varyAm.value
  Cm =  varyCm.value
  Lg =  varyLg.value
  Lt =  varyLt.value
  #
  Hw =  varyHw.value
  Hm =  varyHm.value
  Dm =  varyDm.value
  Wm =  varyWm.value
  Pm =  varyPm.value
  Dg =  varyDg.value
  Dt =  varyDt.value
  #
  Ch =  varyCh.value
  Ah =  varyAh.value
  Eh =  varyEh.value
  Le =  varyLe.value
  Cv =  varyCv.value
  #
  Dh =  varyDh.value
  Wh =  varyWh.value
  Ph =  varyPh.value
  De =  varyDe.value
  Dv =  varyDv.value
  #
  Av =  varyAv.value
  Ev =  varyEv.value
  Lr =  varyLr.value
  Mb =  varyMb.value
  Hy =  varyHy.value
  #
  Wv =  varyWv.value
  Pv =  varyPv.value
  Iv =  varyIv.value
  Tv =  varyTv.value
  Iu =  varyIu.value
  Tu =  varyTu.value
  Dr =  varyDr.value
  Xb =  varyXb.value
  Vy =  varyVy.value
  #
  cfigFromVbls( aCfgFid )
  spinYasim( aCfgFid )
  lvsdDfrm  = pd.read_csv( lvsdFid, sep='\t')
  lvsdDsrc.data  = lvsdDfrm
  iasaDfrm  = pd.read_csv( iasaFid, sep='\t')
  iasaDsrc.data  = iasaDfrm
  #
  ## performance
  if (0) :
    iascDfrm  = pd.read_csv( iascFid, sep='\t')
    iascDsrc.data  = iascDfrm
  # Here: figure wing incidence vs stall angle
  wingInci( aCfgFid)
#

# called if Version string is changed, duplicates actions cf above 
def dropHdlr(event) :
  global procPref, lvsdFid, iasaFid, iascFid, drgaFid, solnFid
  global solnDict, solnCDS, solnCols, solnDT, solnIter, solnElev, solnCgMC, solnCgWB
  global yCfgName, yCfgFid, aCfgFid, vCfgFid, versDict, versToDo, versKywd
  global Yb, Zb, Hy, Vy, fracInci, totlInci            # Ballast, Solver Result
  global     Aw                                        # Wing, Flap, Ailr
  ##
  # On dropdown action, record YASim version selected
  versToDo = event.item
  versKywd = versDict[versToDo]
  # cf update_elem
  cfigFromVbls( aCfgFid )
  spinYasim( aCfgFid )
  #lvsdDfrm  = pd.read_csv( lvsdFid, delimiter=', ')
  lvsdDfrm  = pd.read_csv( lvsdFid, delimiter='\t')
  lvsdDsrc.data  = lvsdDfrm
  #iasaDfrm  = pd.read_csv( iasaFid, delimiter=', ')
  iasaDfrm  = pd.read_csv( iasaFid, delimiter='\t')
  iasaDsrc.data  = iasaDfrm
  # performance  
  if (0) :
    iascDfrm  = pd.read_csv( iascFid, delimiter='\t')
    iascDsrc.data  = iascDfrm
  #
#
  
# listeners for interface slider changes 
for v in [\
          varyVa, varyAa, varyTa, varyKa, varyFa, \
          varyVc, varyHc, varyTc, varyKc, varyGc, \
          varyIw, varyAw, varyCw, varyLf, varyLa, \
          varyTw, varyDw, varyWw, varyPw, varyDf, varyDa, \
          varyTm, varyAm, varyCm, varyLg, varyLt, varyHw, varyHm, \
          varyDm, varyWm, varyPm, varyDg, varyDt, \
          varyCh, varyAh, varyEh, varyLe, varyCv, \
          varyDh, varyWh, varyPh, varyDe, varyDv, \
          varyAv, varyEv, varyIv, varyTv, varyLr, varyMb, varyHy, \
          varyWv, varyPv, varyIu, varyTu, varyDr, varyXb, varyVy  ]:
  v.on_change('value', update_elem)
#
versDrop.on_click( dropHdlr)
#
#
solnDT_callback = CustomJS(args=dict(source=solnDT), code="""
    source.change.emit()
""")
#source.js_on_change('data', solnDT_callback)
#
solnDT.js_on_change('source', solnDT_callback)
#
# Set up layouts for slider groups
ApprRack = column(varyVa,   varyAa, varyTa, varyKa, varyFa)
# Show Cruise Fuel CrzeRack = column(versDrop, varyVc, varyHc, varyTc, varyKc)
# Show Cruise Glide Angle
CrzeRack = column(versDrop, varyVc, varyHc, varyTc, varyGc)
#
W0AwRack = column(varyAw,   varyWw, varyPw, varyHw, varyTw)
W0CwRack = column(varyCw,   varyLf, varyDf, varyLa, varyDa)
#
WMAmRack = column(varyAm,   varyWm, varyPm, varyHm, varyDw)
WMWxRack = column(varyIw,   varyLg, varyDg, varyLt, varyDt)
#
HsAhRack = column(varyAh,   varyEh,  varyDh, varyLe, varyMb)
HsWhRack = column(varyWh,   varyPh,  varyCh, varyDe, varyXb)
#
VsAvRack = column(varyAv,   varyEv, varyIv, varyLr, varyHy)
VsWvRack = column(varyWv,   varyPv, varyCv, varyDr, varyVy )
##
presets()
vblsFromTplt()
cfigFromVbls(aCfgFid )
spinYasim(aCfgFid)
#
# plan overall interface layout 
#curdoc().title = yCfgName
curdoc().title = procPref
curdoc().add_root(row(ApprRack, W0AwRack, liftPlot, dragPlot, WMAmRack, width=400))
curdoc().add_root(row(CrzeRack, W0CwRack, iasaPlot, lvsdPlot, WMWxRack, width=400))
curdoc().add_root(row(HsAhRack, HsWhRack, VsAvRack, VsWvRack, solnDT,   width=400))
# Cannot get table of YASim output values to update, ergo console printout
#curdoc().add_root(row(solnDT, width=360))
#
## ysimi ends

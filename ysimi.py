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
import os, shlex, subprocess, sys, math
import csv, numpy as np, pandas as pd
#
from bokeh.io import curdoc      
from bokeh.models.callbacks import CustomJS
from bokeh.layouts  import column, row
from bokeh.models   import ColumnDataSource, Slider, Dropdown
from bokeh.models   import TextInput, DataTable, TableColumn
from bokeh.plotting import figure
from collections    import OrderedDict 
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
global procPref, lvsdFid, iasaFid, iascFid, drgaFid, solnFid
global solnDict, solnCDS, solnCols, solnDT, solnIter, solnElev, solnCgMC, solnCgWB
global yCfgName, yCfgFid, aCfgFid, vCfgFid, versDict, versToDo, versKywd
#
## These vbles correspond to the elements in the config file: 
global Va, Aa, Ka, Ta, Fa                            # Appr   Spd, Aoa, Thrt, Fuel, Flaps
global Vc, Hc, Kc, Tc                                # Cruise Spd, Alt, Thrt, Fuel
global Iw, Aw, Cw, Lf, La,   Dw, Ww, Pw, Df, Da      # Wing, Flap, Ailr
global Tx, Ax, Cx, Lg, Lt,   D1, W1, Px, Dg, Dt, Tw  # Wng1, Flap, Ailr
global Ch, Ah, Eh, Le, Cv,   Dh, Wh, Ph, De, Dv      # Hstab, Elev (incidence set by solver ) 
global Av, Ev, Iv, Tv, Lr,   Wv, Pv, Iu, Tu, Dr      # Vstab V0:'v' V1:'u', Rudder 
global Mp, Rp, Ap, Np, Xp,   Ip, Op, Vp, Cp, Tp      # Prop
global Mb, Xb, Yb, Zb, Hy,   Vy, Wx, Wb, Gx          # Ballast, Solver, Wh main, base, CG
global fracInci, totlInci                            # Wing incidence and CoG 
##
#  Set Defaults
def presets():
  global procPref, lvsdFid, iasaFid, iascFid, drgaFid, solnFid
  global yCfgName, yCfgFid, aCfgFid, vCfgFid, versDict, versToDo, versKywd
  global Hy, Vy                                      # Solver    parms
  #print( 'Entr presets')
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
  aCfgFid  = procPref + '-yasim-outp.xml'
  # yasim config xml file read input 
  yCfgFid  = procPref + '-yasim-inpt.xml'
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
  global Vc, Hc, Kc, Tc                                # Cruise Spd, Alt, Thrt, Fuel
  global Iw, Aw, Cw, Lf, La,   Dw, Ww, Pw, Df, Da      # Wing, Flap, Ailr
  global Tx, Ax, Cx, Lg, Lt,   D1, W1, Px, Dg, Dt, Tw  # Wng1, Flap, Ailr
  global Ch, Ah, Eh, Le, Cv,   Dh, Wh, Ph, De, Dv      # Hstab, Elev (incidence set by solver ) 
  global Av, Ev, Iv, Tv, Lr,   Wv, Pv, Iu, Tu, Dr      # Vstab V0:'v' V1:'u', Rudder 
  global Mp, Rp, Ap, Np, Xp,   Ip, Op, Vp, Cp, Tp      # Prop
  global Mb, Xb, Yb, Zb, Hy,   Vy, Wx, Wb, Gx          # Ballast, Solver, Wh main, base, CG
  global fracInci, totlInci                            # Wing incidence and CoG 
  ##
  # These flags indicate parsing has detected various sections of yasim config 
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
  # YASim 'Solve At' values for Speed and Altitude 
  Vy = 130
  Hy = 1000
  # 
  Va = Aa = Ka = Ta = Fa = Vc = Hc = Kc = Tc =           Wx = Wb = Gx = 0.00
  Iw = Aw = Tw = Tx = Ax = Ah = Cv = Av = Wv = Pv = Iv = Tv = Iu = Tu = Cw = Cx = Ch = 0.00
  Eh = Ev = La = Lf = Lg = Lt = Lh = Lv = Lr = Da = Df = Dg = Dt = Dh = Dr = Dw = D1 = Dv = 1.00
  Pw = Px = Ph = 1.50
  Ww = W1 = Wh = 2.00
  Mp = Rp = Ap = Np = Xp = Ip = Op = Vp = Cp = Tp = 0
  # in case ballast element is missing, fake with tiny value
  Mb = Xb = Yb = Zb = 0.001
  #
  # open base yasim config file and parse elements
  #print(yCfgFid)
  with open(yCfgFid, 'r') as yCfgHndl:
  # step each line in template yasim config file
    for line in yCfgHndl:
      # set / clear flags for each section
      # flag on approach section
      if '<approach' in line:
        apprFlag = 1
      if '</approach' in line:
        apprFlag = 0
      # flag on cruise section
      if '<cruise' in line:
        cruzFlag = 1
      if '</cruise' in line:
        cruzFlag = 0
      # flag on wing section
      if '<wing' in line:
        wingFlag = 1
        #print('fromTplt  <wing')
      if '</wing' in line:
        wingFlag = 0
        wng1Flag = 0
        #print('fromTplt  </wing')
      # flag on hstab section
      if '<hstab' in line:
        hstabFlag = 1
      if '</hstab' in line:
        hstabFlag = 0
      # flag on vstab section
      if '<vstab' in line:
        vstabFlag = 1
      if '</vstab' in line:
        vstabFlag = 0
        vstabDone = 1
      # flag on mstab section
      if '<mstab' in line:
        mstabFlag = 1
        #print('fromTplt  <mstab')
      if '</mstab' in line:
        mstabFlag = 0
        mstabDone = 1
        #print('fromTplt  </mstab')
      # flag on ballast section
      if '<ballast' in line:
        ballFlag = 1
      if '</ballast' in line:
        ballFlag = 0
        ballDone = 1
      # flag on prop section
      if '<propeller' in line:
        propFlag = 1
      if '</propeller' in line:
        propFlag = 0

      ### appr section parse approach speed and AoA elements
      if (apprFlag == 1):
        ##
        #in appr section, find elements
        if ('approach' in line):
          # find element names, save values to post in Tix gui
          if ( 'speed' in line):
            Va = tuplValu('speed', line)
          #
          if ( 'aoa' in line):
            Aa = tuplValu('aoa', line)
          #
          if ( 'fuel' in line):
            Ka = tuplValu('fuel', line)
          #
        #print ('Va: ', Va, ' Aa: ', Aa, ' Ka: ', Ka)  
        if ('throttle' in line):
          if ( 'value' in line):
            Ta = tuplValu('value', line)
            # print ('Ta: ', Ta)  
          #
        if ('flaps' in line):
          if ( 'value' in line):
            Fa = tuplValu('value', line)
          # print (' Fa: ', Fa,)  
          #

      ### cruise section parse cruise speed element
      if (cruzFlag == 1):
          # find element names, save values to post in Tix gui
          if ( 'speed' in line):
            Vc = tuplValu('speed', line)
          #
          if ( 'alt' in line):
            Hc = tuplValu('alt', line)
          #
          if ( 'fuel' in line):
            Kc = tuplValu('fuel', line)
          #
          #print ('Vc: ', Vc, ' Hc: ', Hc, ' Kc: ', Kc)  
          if ('throttle' in line):
            if ( 'value' in line):
              Tc = tuplValu('value', line)
          #
        ###

      ### wing sections parse camber and induced drag elements
      if ( (wingFlag  == 1)or  (mstabFlag == 1) ) :
        if (  ( (wingFlag  == 1) and ( 'append=\"1\"' in line ) )  \
           or ( (mstabFlag == 1) and ( mstabDone == 0) ) ) :
          # first mstab uses wing1 settings 
          wng1Flag = 1
        if ( wng1Flag != 1 ) :
          if ( 'camber' in line):
            Cw =  tuplValu('camber', line)
          #
          if ('idrag' in line):
            Dw = tuplValu('idrag', line)
          #  
          if ( 'incidence' in line):
            Iw = tuplValu('incidence', line)
          #
          if ( 'twist' in line):
            Tw = tuplValu('twist', line)
          #
          #     print ('Read Cw: ', Cw, 'Dw: ', Dw, ' Iw: ', Iw, ' Tw: ', Tw)  
          ##
          #in wing section, find stall element values
          if ('stall' in line):
            # find element names, save values to post in Tix gui
            if ( 'aoa' in line):
              Aw = tuplValu('aoa', line)
            #
            if ( 'peak' in line): 
              Pw = tuplValu('peak', line)
            #
            if ( 'width' in line):
              Ww = tuplValu('width', line)
            #
          # print (' read Aw: ', Aw, ' Ww: ', Ww, ' Pw: ', Pw)  
          ##
          #in wing section, find flap0 element values 
          if ('flap0' in line):
            # find element names, save values to post in Tix gui
            if ( 'lift' in line):
              Lf = tuplValu('lift', line)
            #
            if ( 'drag' in line):
              Df = tuplValu('drag', line)
            #
          #print ('Lf: ', Lf, ' Df: ', Df)  
          ##
          #in wing section, find flap1 element values 
          if ('flap1' in line):
            # find element names, save values to post in Tix gui
            if ( 'lift' in line):
              La = tuplValu('lift', line)
            #
            if ( 'drag' in line):
              Da = tuplValu('drag', line)
            #
          #print ('La: ', La, ' Da: ', Da)
          ## end wing 
        else :
          ## wing append 1  print('wng1')
          if ( 'camber' in line):
            Cx =  tuplValu('camber', line)
          #
          if ('idrag' in line):
            D1 = tuplValu('idrag', line)
          #  
          if ( 'twist' in line):
            Tx = tuplValu('twist', line)
          #
          # print ('Read Cx: ', Cx, 'D1: ', D1, ' Tx: ', Tx)  
          ##
          #in wing section, find stall element values
          if ('stall' in line):
            # find element names, save values to post in Tix gui
            if ( 'aoa' in line):
              Ax = tuplValu('aoa', line)
            #
            if ( 'peak' in line):
              Px = tuplValu('peak', line)
            #
            if ( 'width' in line):
              W1 = tuplValu('width', line)
            #
          #  print ('Ax: ', Ax, ' W1: ', W1, ' Px: ', Px)  
          ##
          #in wing section, find flap0 element values 
          if ('flap0' in line):
            # find element names, save values to post in Tix gui
            if ( 'lift' in line):
              Lg = tuplValu('lift', line)
            #
            if ( 'drag' in line):
              Dg = tuplValu('drag', line)
            #
          #print ('Lg: ', Lg, ' Dg: ', Dg)  
          ##
          #in wing section, find flap1 element values 
          if ('flap1' in line):
            # find element names, save values to post in Tix gui
            if ( 'lift' in line):
              Lt = tuplValu('lift', line)
            #
            if ( 'drag' in line):
              Dt = tuplValu('drag', line)
            #
          #print ('Lt: ', Lt, ' Dt: ', Dt)
          ## end wng1 

      ### hstab section parse camber, drag, stall and flap0 elements
      if (hstabFlag == 1):
        ## hstab section parse camber and induced drag elements if present
        if ('camber' in line):
          Ch =  tuplValu('camber', line)
        if ('idrag' in line):
          Dh = tuplValu('idrag', line)
        if ('effectiveness' in line):
          Eh = tuplValu('effectiveness', line)
        #  
        #print ('Ch: ', Ch, 'Dh: ', Dh, 'Eh: ', Eh)  
        ##
        #in hstab section, find stall elements
        if ('stall' in line):
          # find element names, save values to post in Tix gui
          if ( 'aoa' in line):
            Ah = tuplValu('aoa', line)
          #
          if ( 'peak' in line):
            Ph = tuplValu('peak', line)
          #
          if ( 'width' in line):
            Wh = tuplValu('width', line)
          #
        #print ('Ah: ', Ah, ' Wh: ', Wh, ' Ph: ', Ph)  
        ##
        #in hstab section, find flap0 elements
        if ('flap0' in line):
          # find element names, save values to post in Tix gui
          if ( 'lift' in line):
            Le = tuplValu('lift', line)
          #
          if ( 'drag' in line):
            De = tuplValu('drag', line)
          #
        #print ('Lh: ', Lh, ' Dh: ', Dh, 'Le: ', Le, ' De: ', De)  
 
      ### vstab section parse camber, idrag, stall and flap0 elements
      if ((vstabFlag == 1) and (vstabDone == 0)):
        ### vstab section parse camber and induced drag elements if present
        if ('camber' in line):
          Cv =  tuplValu('camber', line)
        #
        if ('idrag' in line):
          Dv = tuplValu('idrag', line)
        #  
        if ('effectiveness' in line):
          Ev = tuplValu('effectiveness', line)
        #  
        #print ('Cv: ', Cv, 'Dv: ', Dv, 'Ev: ', Ev)  
        if ( 'incidence' in line):
          Iv = tuplValu('incidence', line)
        #
        if ( 'twist' in line):
          Tv = tuplValu('twist', line)
        #
        #print ('Iv: ', Iv, 'Tv: ', Tv)  
        #in vstab section, find stall elements
        if ('stall' in line):
          # find element names, save values to post in Tix gui
          if ( 'aoa' in line):
            Av = tuplValu('aoa', line)
          #
          if ( 'width' in line):
            Wv = tuplValu('width', line)
          #
          if ( 'peak' in line):
            Pv = tuplValu('peak', line)
          #
        #print ('Av: ', Av, ' Wv: ', Wv, ' Pv: ', Pv)  
        #in vstab section, find flap0 elements
        if ('flap0' in line):
          # find element names, save values to post in Tix gui
          if ( 'lift' in line):
            Lr = tuplValu('lift', line)
          #
          if ( 'drag' in line):
            Dr = tuplValu('drag', line)
          #
        #print ('Lr: ', Lr, ' Dr: ', Dr)
      ###

      #ballast
      if ((ballFlag == 1) and (ballDone == 0)):
        ## ballast section single line for all elements
        if ('mass' in line):
          Mb =  tuplValu('mass', line)
        #
        if ('x=' in line):
          Xb =  tuplValu('x', line)
        #
        if ('y=' in line):
          Yb =  tuplValu('y', line)
        #
        if ('z=' in line):
          Zb =  tuplValu('z', line)
        #
        if ('/>' in line):
          ballDone =  1
          ballFlag =  0
        #
      ###

      #prop 
      if (propFlag == 1):
        ## prop section parse elements if present
        if ('mass' in line):
          Mp =  tuplValu('mass', line)
        #
        if ('radius' in line):
          Rp =  tuplValu('radius', line)
        #
        if ('moment' in line):
          Ap =  tuplValu('moment', line)
        #
        if ('min-rpm' in line):
          Np =  tuplValu('min-rpm', line)
        #
        if ('max-rpm' in line):
          Xp =  tuplValu('max-rpm', line)
        #
        if ('fine-stop' in line):
          Ip =  tuplValu('fine-stop', line)
        #
        if ('coarse-stop' in line):
          Op =  tuplValu('coarse-stop', line)
        #
        if ('cruise-speed' in line):
          Vp =  tuplValu('cruise-speed', line)
        #
        if ('cruise-rpm' in line):
          Cp =  tuplValu('cruise-rpm', line)
        #
        if ('takeoff-rpm' in line):
          Tp =  tuplValu('takeoff-rpm', line)
        #
        ###  
  #close and sync file
  yCfgHndl.close
  #print( 'Exit vblsFromTplt')
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
  global Vc, Hc, Kc, Tc                                # Cruise Spd, Alt, Thrt, Fuel
  global Iw, Aw, Cw, Lf, La,   Dw, Ww, Pw, Df, Da      # Wing, Flap, Ailr
  global Tx, Ax, Cx, Lg, Lt,   D1, W1, Px, Dg, Dt, Tw  # Wng1, Flap, Ailr
  global Ch, Ah, Eh, Le, Cv,   Dh, Wh, Ph, De, Dv      # Hstab, Elev (incidence set by solver ) 
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
          #print ('Vc: ', Vc, ' Hc: ', Hc, ' Kc: ', Kc)  
          line = tuplSubs( 'speed',   line, Vc ) 
          line = tuplSubs( 'alt',     line, Hc ) 
        if ('fuel' in line):
          line = tuplSubs( 'value',    line, Kc ) 
        if ('throttle' in line):
          line = tuplSubs( 'value',   line, Tc )

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
          #print ('Wrt  Cw: ', Cw, 'Dw: ', Dw, ' Iw: ', Iw ' Tw: ', Tw)  
          #   
          if ('stall' in line):
           line = tuplSubs( 'aoa'  ,  line, Aw )
           line = tuplSubs( 'peak' ,  line, Pw ) 
           line = tuplSubs( 'width',  line, Ww ) 
          #  
          if ('flap0' in line):
            line = tuplSubs( 'lift',   line, Lf ) 
            line = tuplSubs( 'drag',   line, Df ) 
          #  
          if ('flap1' in line):
            line = tuplSubs( 'lift',   line, La ) 
            line = tuplSubs( 'drag',   line, Da )
          # end wing 
        else :   
          line = tuplSubs( 'camber',  line, Cx ) 
          line = tuplSubs( 'idrag',   line, D1 )
          line = tuplSubs( 'twist',   line, Tx )
            #print ('Wrt  Cx: ', Cx, 'D1: ', D1, 'W1: ', W1, ' Tx: ', Tx)  
          #   
          if ('stall' in line):
            line = tuplSubs( 'aoa'  ,  line, Ax )
            line = tuplSubs( 'peak' ,  line, Px ) 
            line = tuplSubs( 'width',  line, W1 ) 
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
  print( '#{:s}  HS:{:s}  ApElv:{:s}  CG{:s} MC  {:3.0f}% WB  WngInc:{:2.1f}d {:.1f}% St @ {:.1f}d ' \
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
  #print( 'Exit scanSoln')
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
  x1 = y1 = z1 = x2 = y2 = z2 = 0
  # one of the wheels is both the same 
  for gearElem in root.iter('gear') :
    xVal = float(gearElem.get('x'))
    yVal = float(gearElem.get('y'))
    zVal = float(gearElem.get('z'))
    if (( x1 == 0 ) & ( y1 == 0 ) & ( z1 == 0 )) :
      # found first wheel element
      x1 = xVal
      y1 = yVal
      z1 = zVal
      #  print('1 x1: ', x1, ' y1: ', y1, 'z1: ', z1, 'x2: ', x2, 'z2: ', z2 )
    else :
      # not a new wheel1: then a non match is wheel2 
      if (( x1 != xVal ) ) :
        if (( x2 == xVal ) &                  ( z2 == zVal )) :
          # If newv == stored then swap mains into wx
          x2 = x1
          y2 = y1
          z2 = z1
          x1 = xVal
          y1 = yVal
          z1 = zVal
        else:
          #print('S xVal: ', xVal, ' yVal: ', yVal, 'zVal: ', zVal)
          x2 = xVal
          y2 = yVal
          z2 = zVal
    ## mains in x1, y1, z1, wheelbase for CoG 
    Wx = x1
    Wb = (x2 - x1)
    #    print('Wx: ', Wx, ' Wb: ', Wb)
  #  print('Main x1: ', x1, ' y1: ', y1, 'z1: ',   z1, 'x2: ', x2, ' y2: ', y2, ' z2: ', z2 )
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
liftPlot  = figure(plot_height=250, plot_width=208, title="Lift n100 vs AoA",
              tools="crosshair,pan,reset,save,wheel_zoom" )

dragPlot  = figure(plot_height=250, plot_width=208, title="Drag  n10 vs AoA",
              tools="crosshair,pan,reset,save,wheel_zoom" )

lvsdPlot  = figure(plot_height=250, plot_width=208, title="  L / D   vs AoA",
              tools="crosshair,pan,reset,save,wheel_zoom" )

drgaPlot  = figure(plot_height=250, plot_width=208, title="Drag vs Kias @ appr ",
              tools="crosshair,pan,reset,save,wheel_zoom" )

iasaPlot  = figure(plot_height=250, plot_width=208, title="Vs0, %Lift vs AoA @ appr",
              tools="crosshair,pan,reset,save,wheel_zoom" )

iascPlot  = figure(plot_height=250, plot_width=208, title="Vs0, %Lift vs AoA @ crse",
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
varyVa = Slider(width=132, title="Appr IAS      Va", value=Va, start=(40.0 ), end=(180 ), step=(2.0 ))
varyAa = Slider(width=132, title="Appr AoA      Aa", value=Aa, start=(-5.0 ), end=(20  ), step=(0.2 ))
varyTa = Slider(width=132, title="Appr Throttle Ta", value=Ta, start=(0.0  ), end=(1.0 ), step=(0.05))
varyKa = Slider(width=132, title="Appr Fuel     Ka", value=Ka, start=(0.0  ), end=(1.0 ), step=(0.05))
varyFa = Slider(width=132, title="Appr Flaps    Fa", value=Fa, start=(0.0  ), end=(1.0 ), step=(0.05))
#
varyVc = Slider(width=132, title="Crse IAS Kt   Vc", value=Vc, start=(50   ), end=(500 ), step=(10.0 ))
varyHc = Slider(width=132, title="Crse Alt Ft   Hc", value=Hc, start=(1000 ), end=(40000),step=(200 ))
varyTc = Slider(width=132, title="Crse Throttle Tc", value=Tc, start=(0.0  ), end=(1.0 ), step=(0.05))
varyKc = Slider(width=132, title="Crse Fuel     Kc", value=Kc, start=(0.0  ), end=(1.0 ), step=(0.05))
#
varyAw = Slider(width=132, title="AoA St    Wg0 Aw", value=Aw, start=(-2.0 ), end=(24.0), step=(0.1 ))
varyDw = Slider(width=132, title="iDrag--   Wg0 Dw", value=Dw, start=( 0.1 ), end=(4.0 ), step=(0.1 ))
varyCw = Slider(width=132, title="Camber    Wg0 Cw", value=Cw, start=(0.000), end=(1.00), step=(0.001))
varyCx = Slider(width=132, title="Camber    Wg1 Cx", value=Cx, start=(0.000), end=(1.00), step=(0.001))
varyLf = Slider(width=132, title="Lift  Fp0 Wg0 Lf", value=Lf, start=( 0.01), end=(8.0 ), step=(0.1 ))
varyDf = Slider(width=132, title="Drag  Fp0 Wg0 Df", value=Df, start=( 0.01), end=(8.0 ), step=(0.1))
#
varyWw = Slider(width=132, title="Width St  Wg0 Ww", value=Ww, start=(0.0  ), end=(32  ), step=(0.10))
varyPw = Slider(width=132, title="Peak  St  Wg0 Pw", value=Pw, start=(0.0  ), end=(20.0), step=(0.2 ))
varyIw = Slider(width=132, title="Incidence Wg0 Iw", value=Iw, start=(-5.0 ), end=(10.0), step=(0.1 ))
varyLa = Slider(width=132, title="Lift Ailr Wg0 La", value=La, start=( 0.01), end=(8.0 ), step=(0.1 ))
varyDa = Slider(width=132, title="Drag Ailr Wg0 Da", value=Da, start=( 0.01), end=(8.0 ), step=(0.1))
#
varyAx = Slider(width=132, title="AoA St    Wg1 Ax", value=Ax, start=(-2.0 ), end=(24.0), step=(0.1 ))
varyD1 = Slider(width=132, title="iDrag--   Wg1 D1", value=D1, start=( 0.1 ), end=(4.0 ), step=(0.1 ))
varyTw = Slider(width=132, title="Twist     Wg0 Tw", value=Tw, start=(-8.00), end=(8.00), step=(0.1 ))
varyLg = Slider(width=132, title="Lift Fp0  Wg1 Lg", value=Lg, start=( 0.01), end=(8.0 ), step=(0.1 ))
varyLt = Slider(width=132, title="Lift Ailr Wg1 Lt", value=Lt, start=( 0.01), end=(8.0 ), step=(0.1 ))
#
varyW1 = Slider(width=132, title="Width St  Wg1 W1", value=W1, start=(0.0  ), end=(32  ), step=(0.10))
varyPx = Slider(width=132, title="Peak  St  Wg1 Px", value=Px, start=(0.0  ), end=(20.0), step=(0.2 ))
varyTx = Slider(width=132, title="Twist     Wg1 Tx", value=Tx, start=(-8.00), end=(8.00), step=(0.1 ))
varyDg = Slider(width=132, title="Drag Fp0  Wg1 Dg", value=Dg, start=( 0.01), end=(8.0 ), step=(0.1))
varyDt = Slider(width=132, title="Drag Ai1r Wg1 Dt", value=Dt, start=( 0.01), end=(8.0 ), step=(0.1))
#
varyAh = Slider(width=132, title="Aoa St  Hstab Ah", value=Ah, start=(-2.0 ), end=(24.0), step=(0.1 ))
varyDh = Slider(width=132, title="IDrag-- Hstab Dh", value=Dh, start=( 0.1 ), end=(4.0 ), step=(0.1 ))
varyCh = Slider(width=132, title="Camber  Hstab Ch", value=Ch, start=(0.00 ), end=(2.00), step=(0.001))
varyLe = Slider(width=132, title="Lift     Elev Le", value=Le, start=( 0.1 ), end=(8.0 ), step=(0.01))
varyCv = Slider(width=132, title="Camber  Vstab Cv", value=Cv, start=(0.00 ), end=(2.50), step=(0.001))
#
varyWh = Slider(width=132, title="Wdth St Hstab Wh", value=Wh, start=(0.0  ), end=(32  ), step=(0.20))
varyPh = Slider(width=132, title="Peak St Hstab Ph", value=Ph, start=(0.0  ), end=(20.0), step=(0.2 ))
varyEh = Slider(width=132, title="Effect  Hstab Eh", value=Eh, start=( 0.1 ), end=(4.0 ), step=(0.1 ))
varyDe = Slider(width=132, title="Drag     Elev De", value=De, start=(0.01 ), end=(4.0 ), step=(0.1))
varyDv = Slider(width=132, title="IDrag-- Vstab Dv", value=Dv, start=(0.01 ), end=(8.0 ), step=(0.1))
#
varyAv = Slider(width=132, title="AoA St Vstab  Av", value=Av, start=(-2.0 ), end=(24.0), step=(0.1 ))
varyEv = Slider(width=132, title="Effect Vstab  Ev", value=Ev, start=( 0.1 ), end=(4.0 ), step=(0.1 ))
varyIv = Slider(width=132, title="Incid  Vstab  Iv", value=Iv, start=(-4.0 ), end=(4.0 ), step=(0.05))
varyTv = Slider(width=132, title="Twist  Vstab  Tv", value=Tv, start=(-4.0 ), end=(4.0 ), step=(0.1 ))
varyLr = Slider(width=132, title="Lift Rudder   Lr", value=Lr, start=(-4.0 ), end=(8.0 ), step=(0.01))
varyMb = Slider(width=132, title="Ballast Mass  Mb", value=Mb, start=(-5000), end=(15000),step=(10  ))
varyHy = Slider(width=132, title="Solve Alt ft  Hy", value=Hy, start=(   0 ), end=(40000),step=(100))
#
varyWv = Slider(width=132, title="Wdth St Vs0   Wv", value=Wv, start=(0.0  ), end=(32  ), step=(0.50))
varyPv = Slider(width=132, title="Pk   St Vs0   Pv", value=Pv, start=(0.2  ), end=(20.0), step=(0.2 ))
varyIu = Slider(width=132, title="Incid  ApVst  Iu", value=Iu, start=(-4.0 ), end=(4.0 ), step=(0.05))
varyTu = Slider(width=132, title="Twist  ApVst  Tu", value=Tu, start=(-4.0 ), end=(4.0 ), step=(0.05))
varyDr = Slider(width=132, title="Drag Rudder   Dr", value=Dr, start=( 0.0 ), end=(4.0 ), step=(0.05))
varyXb = Slider(width=132, title="Ballast Posn  Xb", value=Xb, start=(-200 ), end=(200 ), step=(0.10))
varyVy = Slider(width=132, title="Solve IAS kt  Vy", value=Vy, start=(40   ), end=(400 ), step=(20  ))
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
  global Vc, Hc, Kc, Tc                                # Cruise Spd, Alt, Thrt, Fuel
  global Iw, Aw, Cw, Lf, La,   Dw, Ww, Pw, Df, Da      # Wing, Flap, Ailr
  global Tx, Ax, Cx, Lg, Lt,   D1, W1, Px, Dg, Dt, Tw  # Wng1, Flap, Ailr
  global Ch, Ah, Eh, Le, Cv,   Dh, Wh, Ph, De, Dv      # Hstab, Elev (incidence set by solver ) 
  global Av, Ev, Iv, Tv, Lr,   Wv, Pv, Iu, Tu, Dr      # Vstab V0:'v' V1:'u', Rudder 
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
  Tx =  varyTx.value
  Ax =  varyAx.value
  Cx =  varyCx.value
  Lg =  varyLg.value
  Lt =  varyLt.value
  #
  D1 =  varyD1.value
  W1 =  varyW1.value
  Px =  varyPx.value
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
  #print('dropHdlr versToDo:',  versToDo, '  versKywd: ', versKywd)
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
          varyVc, varyHc, varyTc, varyKc, \
          varyIw, varyAw, varyCw, varyLf, varyLa, \
          varyTw, varyDw, varyWw, varyPw, varyDf, varyDa, \
          varyTx, varyAx, varyCx, varyLg, varyLt, \
          varyD1, varyW1, varyPx, varyDg, varyDt, \
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
CrzeRack = column(versDrop, varyVc, varyHc, varyTc, varyKc)
#
W0AwRack = column(varyAw,   varyWw, varyDw, varyPw, varyCw)
W0WwRack = column(varyTw,   varyLf, varyDf, varyLa, varyDa)
#
W1AxRack = column(varyAx,   varyW1, varyD1, varyPx, varyIw)
W1WxRack = column(varyTx,   varyLg, varyDg, varyLt, varyDt)
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
curdoc().add_root(row(ApprRack, W0AwRack, liftPlot, dragPlot, W1AxRack, width=400))
curdoc().add_root(row(CrzeRack, W0WwRack, iasaPlot, lvsdPlot, W1WxRack, width=400))
curdoc().add_root(row(HsAhRack, HsWhRack, VsAvRack, VsWvRack, solnDT,   width=400))
# Cannot get table of YASim output values to update, ergo console printout
#curdoc().add_root(row(solnDT, width=360))
#
## ysimi ends

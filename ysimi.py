#!/usr/bin/env python
#
##    ysimi.py: YASim Interactively Adjust Numbers: a pandas / bokeh testbench for YASim
#    takes a given YASim config file, offers a web based plotter for Lift, drag, L/D 
#    creates modified YASim configs for different YASim versions
#    offers slider control of various key YASim elements and re-plots interactively
#
#    yCfg.. Input   yasim config xml Original 
#    outp.. Auto    yasim config xml generated with eg modified varied elements
#   ..-LvsD.txt     yasim generated Lift / Drag tables    ( version specific )
#   ..-mias.txt     yasim generated IAS for 0vSpd vs AoA  ( version specific )
#   ..-soln.txt     yasim generated solution values       ( version specific )
#
#  install python3-bokeh, python3-pandas, numpy ( plus others ?? ) 
#  To run a local server: bokeh serve ysimi.py and then
#    browse to: http://localhost:5006/ysimi 
#
#  Suggested workflow ( various files are created / written ) 
#    Create a model-specific folder beneath this executable's folder:
#      mkdir [myModel]; cd [myModel]
#    Link or copy YASim configuration in Flightgear's Aircraft folder:
#      ln -s [fgaddon/Aircraft/[myModel] ysimi-yasim.xml
#      ( the executable's input YASim configuration file has a specific fileID )
#    Start bokeh server with this executable: 
#      bokeh serve [ --port 5006 ] ../ysimi.py
#    Browse to the interactive panel:   
#      http://localhost:5006/ysimi
#
#    If desired, copy this executable to a new name: ?simi.py with a differnt input 
#      and open on a different port: bokeh serve [ --port 5007 ] ../?simi.py
#      so that two models may be compared in side-by-side browser tabs
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
global yCfgName, yCfgFid, aCfgFid, vCfgFid, versDict, versToDo, versKywd
global solnDict, solnCDS, solnCols, solnDT, solnIter, solnElev, solnCofG
## These vbles correspond to the elements in the config file: 
global Va, Aa, Ka, Ra, Fa                            # Appr   Spd, Aoa, Thrt, Fuel, Flaps
global Vc, Hc, Kc, Rc                                # Cruise Spd, Alt, Thrt, Fuel
global Cw,     Dw, Iw, Aw, Pw, Ww, Lf, Df, La, Da    # Wing, Flap, Ailr
global Ch, Lh, Dh, Ah, Ph, Wh                        # Hstab, incidence is set by solver
global Cv, Lv, Dv, Av, Pv, Wv, Lr, Dr                # Vstab, Rudder
global Mp, Rp, Ap, Np, Xp, Ip, Op, Vp, Cp, Tp        # Prop
global Mb, Xb, Yb, Zb                                # Ballast
global Hy, Vy                                        # Solver

#  Set Defaults
def presets():
  global yCfgName, yCfgFid, aCfgFid, vCfgFid, versDict, versToDo, versKywd
  global procPref, lvsdFid, miasFid, solnFid
  global Hy, Vy                                      # Solver    parms
  global procPref, yCfgName, yCfgFid, aCfgFid, vCfgFid, lvsdFid, miasFid, solnFid, versDict
  #print( 'Entr presets')
  ## Default File IDs 
  procPref = "ysimi"
  # yasim config xml file read input 
  yCfgFid  = procPref + '-yasim.xml'
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
  # aCFig is output yasim config files with element(s) modified 
  aCfgFid  = procPref + '-outp-yasim.xml'
  #
  lvsdFid  = procPref + versToDo + '-LvsD.txt'
  miasFid  = procPref + versToDo + '-mias.txt'
  solnFid  = procPref + versToDo + '-soln.txt'
  #
  #print( 'Exit presets')
##

#  Return numeric value from 'name="nn.nnn"' tuple in config file
#
def tuplValu( tName, tText ):
  # opening quote is '="' chars beyond name 
  begnValu = tText.find( tName) + len(tName) + 2 
  endsValu = begnValu + (tText[begnValu:]).find('"')
  return( float( tText[(begnValu) : (endsValu) ] ))
##
#  Return given text with given value substituted at name="value" in config file
#
def tuplSubs( tName, tText, tValu ):
  # opening quote is '="' chars beyond name 
  begnValu = tText.find( tName) + len(tName) + 2 
  endsValu = begnValu + (tText[begnValu:]).find('"')
  resp = tText[ : begnValu] + str(tValu) + tText[endsValu :]
  return(resp)
##

# Scan original YASim config and extract numeric elements, save for tix menu
#
def vblsFromTplt():
  #print( 'Entr vblsFromTplt')
  global procPref, yCfgName, yCfgFid, aCfgFid, vCfgFid, lvsdFid, miasFid, solnFid
  global versDict, versToDo, versKywd
  ## These vbles correspond to the elements in the config file: 
  global Va, Aa, Ka, Ra, Fa                            # Appr   Spd, Aoa, Thrt, Fuel, Flaps
  global Vc, Hc, Kc, Rc                                # Cruise Spd, Alt, Thrt, Fuel
  global Cw,     Dw, Iw, Aw, Pw, Ww, Lf, Df, La, Da    # Wing, Flap, Ailr
  global Ch, Lh, Dh, Ah, Ph, Wh                        # Hstab, incidence is set by solver
  global Cv, Lv, Dv, Av, Pv, Wv, Lr, Dr                # Vstab, Rudder
  global Mp, Rp, Ap, Np, Xp, Ip, Op, Vp, Cp, Tp        # Prop
  global Mb, Xb, Yb, Zb                                # Ballast
  global Hy, Vy                                        # Solver
#
  # These flags indicate parsing has detected various sections of yasim config 
  apprFlag   = 0
  cruzFlag   = 0
  wingFlag   = 0
  hstabFlag  = 0
  vstabFlag  = 0
  ballFlag   = 0
  propFlag   = 0
  # YASim 'Solve At' values for Speed and Altitude 
  Vy = 130
  Hy = 4000
  # 
  Va = Aa = Ka = Ra = Fa = Vc = Hc = Kc = Rc = 0
  Iw = Aw = Ah = Cv = Av = Wv = Pv = 0
  Cw = Ch = 0.00
  Lh = Lv = Lr = Dw = Dh = Dh = Dr = 1.00
  Pw = Ph = 1.50
  Ww = Wh = 2.00
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
      if '</wing' in line:
        wingFlag = 0
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
      # flag on ballast section
      if '<ballast' in line:
        ballFlag = 1
      if '</ballast' in line:
        ballFlag = 0
      # flag on prop section
      if '<propeller' in line:
        propFlag = 1
      if '</propeller' in line:
        propFlag = 0
      ### appr section parse approach speed and AoA elements
      if (apprFlag == 1):
        ##
        #in appr section, find elements
        if ('approach speed' in line):
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
            Ra = tuplValu('value', line)
          #
        if ('flaps' in line):
          if ( 'value' in line):
            Fa = tuplValu('value', line)
          #
        #print ('Ra: ', Ra, ' Fa: ', Fa,)  
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
              Rc = tuplValu('value', line)
          #
        ###
      ### wing section parse camber and induced drag elements
      if (wingFlag == 1):
        # find element names, save values to post in Tix gui
        if ( 'camber' in line):
          Cw =  tuplValu('camber', line)
        #
        if ('idrag' in line):
          Dw = tuplValu('idrag', line)
        #  
        if ( 'incidence' in line):
          Iw = tuplValu('incidence', line)
        #
        #print ('Read Cw: ', Cw, 'Dw: ', Dw, ' Iw: ', Iw)  
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
        #print ('Aw: ', Aw, ' Ww: ', Ww, ' Pw: ', Pw)  
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
            Lf = tuplValu('lift', line)
          #
          if ( 'drag' in line):
            Df = tuplValu('drag', line)
          #
        #print ('Lr: ', Lr, ' Dr: ', Dr)  
      ### hstab section parse camber, idrag, stall and flap0 elements
      if (hstabFlag == 1):
        ## hstab section parse camber and induced drag elements if present
        if ('camber' in line):
          Ch =  tuplValu('camber', line)
        #
        if ('drag' in line):
          Dh = tuplValu('drag', line)
        #  
        #print ('Ch: ', Ch)  
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
            Lh = tuplValu('lift', line)
          #
          if ( 'drag' in line):
            Dh = tuplValu('drag', line)
          #
        #print ('Lh: ', Lh, ' Dh: ', Dh)  
      ### vstab section parse camber, idrag, stall and flap0 elements
      if (vstabFlag == 1):
        ### vstab section parse camber and induced drag elements if present
        if ('camber' in line):
          Cv =  tuplValu('camber', line)
        #
        if ('drag' in line):
          Dv = tuplValu('drag', line)
        #print ('Cv: ', Cv)  
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
      if (ballFlag == 1):
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
  global Va, Aa, Ka, Ra, Fa                            # Appr   Spd, Aoa, Thrt, Fuel, Flaps
  global Vc, Hc, Kc, Rc                                # Cruise Spd, Alt, Thrt, Fuel
  global Cw,     Dw, Iw, Aw, Pw, Ww, Lf, Df, La, Da    # Wing, Flap, Ailr
  global Ch, Lh, Dh, Ah, Ph, Wh                        # Hstab, incidence is set by solver
  global Cv, Lv, Dv, Av, Pv, Wv, Lr, Dr                # Vstab, Rudder
  global Mp, Rp, Ap, Np, Xp, Ip, Op, Vp, Cp, Tp        # Prop
  global Mb, Xb, Yb, Zb                                # Ballast
  global Hy, Vy                                        # Solver
  global versKywd
  #
  apprFlag   = 0
  cruzFlag   = 0
  wingFlag   = 0
  hstabFlag  = 0
  vstabFlag  = 0
  ballFlag   = 0
  propFlag   = 0
  aCfgFid  = tFID
  if ( pythVers < 3 ) :
    aCfgHndl  = open(aCfgFid, 'w', 0)
  else :
    aCfgHndl  = open(aCfgFid, 'w')
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
      if '<hstab'     in line:
        hstabFlag = 1
      if '</hstab'    in line:
        hstabFlag = 0
      if '<vstab'     in line:
        vstabFlag = 1
      if '</vstab'    in line:
        vstabFlag = 0
      if '<ballast' in line:
        ballFlag = 1
      if '</ballast'in line:
        propFlag = 0
      if '<propeller' in line:
        propFlag = 1
      if '</propeller'in line:
        propFlag = 0
      ### in each section substitute updated element values
      ## approach
      if (apprFlag == 1):
        if ('approach speed' in line):
          line = tuplSubs( 'speed',   line, Va ) 
          line = tuplSubs( 'aoa',     line, Aa ) 
          line = tuplSubs( 'fuel',    line, Ka ) 
          #print('subsLine: ', line)
        if ('throttle' in line):
          line   = tuplSubs( 'value', line, Ra ) 
        if ('flaps' in line):
          line   = tuplSubs( 'value', line, Fa ) 
      ## cruise
      if (cruzFlag == 1):
        if ('cruise speed' in line):
          line = tuplSubs( 'speed',   line, Vc ) 
          line = tuplSubs( 'alt',     line, Hc ) 
          line = tuplSubs( 'fuel',    line, Kc ) 
        if ('throttle' in line):
          line   = tuplSubs( 'value', line, Rc )
      ## wing
      if (wingFlag == 1):
        if ('camber' in line):
          line = tuplSubs( 'camber',  line, Cw ) 
        if ('idrag' in line):
          line = tuplSubs( 'idrag',   line, Dw )
        if ('incidence' in line):
          #print ('Wrt  Cw: ', Cw, 'Dw: ', Dw, ' Iw: ', Iw)  
          line = tuplSubs( 'incidence', line, Iw )
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
          line = tuplSubs( 'lift',   line, Lf ) 
          line = tuplSubs( 'drag',   line, Df )
        #
      ## HStab     
      if (hstabFlag == 1):
        if ('camber' in line):
          line = tuplSubs( 'camber', line, Ch ) 
        if ('drag' in line):
          line = tuplSubs( 'drag',   line, Dh )
        #
        if ('stall' in line):
          line = tuplSubs( 'aoa'  ,  line, Ah ) 
          line = tuplSubs( 'peak' ,  line, Ph )
          line = tuplSubs( 'width',  line, Wh ) 
        #   
        if ('flap0' in line):
          line = tuplSubs( 'lift',   line, Lh ) 
          line = tuplSubs( 'drag',   line, Dh ) 
        # 
      ## Vstab   
      if (vstabFlag == 1):
        if ('camber' in line):
          line = tuplSubs( 'lift',   line, Cv ) 
        if ('drag' in line):
          line = tuplSubs( 'drag',   line, Dv )
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
      if (ballFlag == 1):
        ## ballast section one line for all elements if present
        if ('mass' in line):
          line = tuplSubs( 'mass',   line, Mb ) 
        #
        if ('x=' in line):
          line = tuplSubs( 'x',      line, Xb ) 
        #
        if ('y=' in line):
          line = tuplSubs( 'y',      line, Yb ) 
        #
        if ('z=' in line):
          line = tuplSubs( 'z',      line, Zb ) 
        #
        if ('/>' in line):
          ballFlag =  0
        #
      #
      ## prop 
      if (propFlag == 1):
        ## prop section parse elements if present
        if ('mass' in line):
          line = tuplSubs( 'mass',   line, Mp ) 
        #
        if ('radius' in line):
          line = tuplSubs( 'radius', line, Rp ) 
        #
        if ('moment' in line):
          line = tuplSubs( 'moment', line, Ap ) 
        #
        if ('min-rpm' in line):
          line = tuplSubs( 'min-rpm',line, Np ) 
        #
        if ('max-rpm' in line):
          line = tuplSubs( 'max-rpm',line, Xp ) 
        #
        if ('fine-stop' in line):
          line = tuplSubs( 'fine-stop',   line, Ip ) 
        #
        if ('coarse-stop' in line):
          line = tuplSubs( 'coarse-stop', line, Op ) 
        #
        if ('cruise-speed' in line):
          line = tuplSubs( 'cruise-speed',line, Vp ) 
        #
        if ('cruise-rpm' in line):
          line = tuplSubs( 'cruise-rpm',  line, Cp ) 
        #
        if ('takeoff-rpm' in line):
          line = tuplSubs( 'takeoff-rpm', line, Tp ) 
        #
        #
      ## Version string   
      # look for <airplane mass="6175" to insert keyword for selected version
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
          line = lineMass + 'version="' + versKywd + '">'
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
  global procPref, yCfgName, yCfgFid, aCfgFid, vCfgFid, lvsdFid, miasFid, solnFid, versDict
  global Hy, Vy                                                # Solver    parms
  #
  ## update fileIDs with version selected from dropdown
  lvsdFid  = procPref + versToDo + '-LvsD.txt'
  miasFid  = procPref + versToDo + '-mias.txt'
  solnFid  = procPref + versToDo + '-soln.txt'
  #print('spinYasim tFid: ', tFid)
  ##
  # run yasim external process to generate LvsD data table saved dataset file
  vDatHndl = open(lvsdFid, 'w')
  command_line = 'yasim ' + tFid + ' -g -a '+ str(Hy/3.3) + ' -s ' + str(Vy)
  #    print(command_line)
  args = shlex.split(command_line)
  DEVNULL = open(os.devnull, 'wb')
  p = subprocess.run(args, stdout=vDatHndl, stderr=DEVNULL)
  DEVNULL.close()
  vDatHndl.close
  os.sync()
  #p.wait()
  ##
  # run yasim external process to generate min IAS data table saved dataset file
  vDatHndl = open(miasFid, 'w')
  command_line = 'yasim ' + tFid + ' --min-speed -a '+ str(Hy/3.3)
  #    print(command_line)
  args = shlex.split(command_line)
  DEVNULL = open(os.devnull, 'wb')
  p = subprocess.run(args, stdout=vDatHndl, stderr=DEVNULL)
  DEVNULL.close()
  vDatHndl.close
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
  os.sync()
  #p.wait()
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

# Given main, tail wheels x, z coords, return body incidence 
def bodyInci( Mx, Mz, Tx, Tz ) :  
  #
  Gx = Mx - Tx
  Ex = (Tz * Gx) / (Mz - Tz) 
  inci = -1 * np.arctan ( Mz / ( Ex + Gx ) )
  inci = math.degrees ( inci ) 
  #
  return(inci)
##

# Given fileID figure wing incidence and stall margin
def wingInci( tFid) :
  global totlInci, fracInci
  tree = ET.parse(tFid)
  root = tree.getroot()
  x1 = z1 = x2 = z2 = 0 
  for gearElem in root.iter('gear') :
    xVal = float(gearElem.get('x'))
    zVal = float(gearElem.get('z'))
    if (( x1 == 0 ) & ( z1 == 0 )) :
      x1 = xVal
      z1 = zVal
    else :
      if (( xVal != x1 ) & ( zVal != z1 )) :
        if (( x2 == 0 ) & ( z2 == 0 )) :
          x2 = xVal
          z2 = zVal
  #print('x1: ', x1, 'z1: ', z1, 'x2: ', x2, 'z2: ', z2 )
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
  




#  main section: Run the calls to YASim ready for bokeh interface to browser 
presets()
vblsFromTplt()
cfigFromVbls( aCfgFid)
spinYasim( aCfgFid )

# use pandas to read sources and create bokeh dataframes
lvsdDfrm  = pd.read_csv(lvsdFid, delimiter='\t')
lvsdDsrc  = ColumnDataSource(lvsdDfrm)
#
miasDfrm  = pd.read_csv(miasFid, delimiter='\t')
miasDsrc  = ColumnDataSource(miasDfrm)
#
# Dropdown for selecting which YASim version to run 
versDrop = Dropdown(label='Select YASim VERSION to Run', \
menu=['-vOrig', '-v2017-2', '-v32', '-vCurr'])
#
# Pull key values from yasim solution console output
solnIter = scanSoln( solnFid, 'Iterations')
solnElev = scanSoln( solnFid, 'Approach Elevator')
solnCofG = scanSoln( solnFid, 'CG-x rel. MAC')
# Did not work: Try a data table to live update soln values
solnDict = dict( 
            dNames  = [ 'Iterations', 'Approach Elevator', 'CG-x rel. MAC'],
            dValues = [  solnIter,     solnElev,            solnCofG      ])
solnCDS  = ColumnDataSource ( solnDict)
solnCols = [TableColumn( field="dNames", title="Solution Item" ),
            TableColumn( field="dValues", title="Value" ), ]
solnDT   = DataTable(source=solnCDS, columns=solnCols, width=240, height=120)
#
# Set up plots
liftPlot  = figure(plot_height=200, plot_width=256, title="Lift n100 vs AoA",
              tools="crosshair,pan,reset,save,wheel_zoom" )

dragPlot  = figure(plot_height=200, plot_width=256, title="Drag  n10 vs AoA",
              tools="crosshair,pan,reset,save,wheel_zoom" )

lvsdPlot  = figure(plot_height=200, plot_width=256, title="  L / D   vs AoA",
              tools="crosshair,pan,reset,save,wheel_zoom" )

miasPlot  = figure(plot_height=200, plot_width=256, title="Vs0 IAS, %Lift vs AoA",
              tools="crosshair,pan,reset,save,wheel_zoom" )

##
liftPlot.line( x='aoa', y='Lift',  source=lvsdDsrc, line_width=3, line_alpha=0.6)
dragPlot.line( x='aoa', y='Drag',  source=lvsdDsrc, line_width=3, line_alpha=0.6)
lvsdPlot.line( x='aoa', y='LvsD',  source=lvsdDsrc, line_width=3, line_alpha=0.6)
miasPlot.line( x='aoa', y='knots', source=miasDsrc, line_width=3, line_alpha=0.6)
miasPlot.line( x='aoa', y='lift',  source=miasDsrc, line_width=3, line_alpha=0.6)
#
# Set up widgets, balance range / step size each affects re-calc
#  Approach group
varyVa = Slider(title="Appr   IAS       Va", value=Va, start=(40.0 ), end=(160 ), step=(2.0 ))
varyAa = Slider(title="Appr   AoA       Aa", value=Aa, start=(-5.0 ), end=(20  ), step=(0.2 ))
varyKa = Slider(title="Appr   Throttle  Ka", value=Ka, start=(0.0  ), end=(1.0 ), step=(0.1 ))
varyRa = Slider(title="Appr   Fuel      Ra", value=Ra, start=(0.0  ), end=(1.0 ), step=(0.1 ))
varyFa = Slider(title="Appr   Flaps     Fa", value=Fa, start=(0.0  ), end=(1.0 ), step=(0.1 ))
#  Cruise
varyVc = Slider(title="Cruise IAS Kt    Vc", value=Vc, start=(40   ), end=(240 ), step=(2.0 ))
varyHc = Slider(title="Cruise Alt Ft    Hc", value=Hc, start=(1000 ), end=(40000),step=(200 ))
varyKc = Slider(title="Cruise Throttle  Kc", value=Kc, start=(0.0  ), end=(1.0 ), step=(0.1 ))
varyRc = Slider(title="Cruise Fuel      Rc", value=Rc, start=(0.0  ), end=(1.0 ), step=(0.1 ))
#  Wing
varyIw = Slider(title="Wing Icidence    Iw", value=Iw, start=(-4.0 ), end=(4   ), step=(0.1 ))
varyDw = Slider(title="Wing IDrag Less  Dw", value=Dw, start=( 0.1 ), end=(4.0 ), step=(0.1 ))
varyCw = Slider(title="Wing Camber      Cw", value=Cw, start=(0.00 ), end=(0.50), step=(0.01))
varyAw = Slider(title="Wing Stall Aoa   Aw", value=Aw, start=(-2.0 ), end=(24.0), step=(0.1 ))
varyPw = Slider(title="Wing Stall Peak  Pw", value=Pw, start=(0.2  ), end=(20.0), step=(0.2 ))
varyWw = Slider(title="Wing Stall Width Ww", value=Ww, start=(0.0  ), end=(32  ), step=(0.50))
#  Horiz Stab 
varyLh = Slider(title="Hstb Lift        Lh", value=Lh, start=( 0.1 ), end=(4.0 ), step=(0.1 ))
varyDh = Slider(title="Hstb Drag        Dh", value=Dh, start=( 0.1 ), end=(4.0 ), step=(0.1 ))
varyCh = Slider(title="Hstb Camber      Ch", value=Ch, start=(0.00 ), end=(0.50), step=(0.01))
varyAh = Slider(title="Hstb Stall Aoa   Ah", value=Ah, start=(-2.0 ), end=(24.0), step=(0.1 ))
varyPh = Slider(title="Hstb Stall Peak  Ph", value=Ph, start=(0.2  ), end=(20.0), step=(0.2 ))
varyWh = Slider(title="Hstb Stall Width Wh", value=Wh, start=(0.0  ), end=(32  ), step=(0.50))
#  Vert Stab 
varyLv = Slider(title="Vstb Lift        Lv", value=Lv, start=( 0.1 ), end=(4.0 ), step=(0.1 ))
varyDv = Slider(title="Vstb Drag        Dv", value=Dv, start=( 0.1 ), end=(4.0 ), step=(0.1 ))
varyCv = Slider(title="Vstb Camber      Cv", value=Cv, start=(0.00 ), end=(0.50), step=(0.01))
varyAv = Slider(title="Vstb Stall Aoa   Av", value=Av, start=(-2.0 ), end=(24.0), step=(0.1 ))
varyPv = Slider(title="Vstb Stall Peak  Pv", value=Pv, start=(0.2  ), end=(20.0), step=(0.2 ))
varyWv = Slider(title="Vstb Stall Width Wv", value=Wv, start=(0.0  ), end=(32  ), step=(0.50))
#  Rudder
varyLr = Slider(title="Rudder Lift      Lr", value=Lr, start=(0.10  ), end=(2.0), step=(0.10))
varyDr = Slider(title="Rudder Drag      Dr", value=Dr, start=( 0.1  ), end=(4.0), step=(0.1 ))
#  Ballast Mass, X Location 
varyMb = Slider(title="Ballast Mass     Mb", value=Mb, start=(-4000 ), end=(4000),step=(50  ))
varyXb = Slider(title="Ballast Posn     Xb", value=Xb, start=(-200  ), end=(200 ),step=(0.5 ))
#  Solver Altitude, Speed
varyHy = Slider(title="Solve for Alt ft Hy", value=Hy, start=(   0  ), end=(40000),step=(100))
varyVy = Slider(title="Solve for IAS kt Vc", value=Vy, start=(40    ), end=(400 ),step=(20  ))
#
# called whenever a value is changed on browser interface
def update_elem(attrname, old, new):
  #print( 'Entr update_elem')
  ## These vbles correspond to the elements in the config file: 
  global Va, Aa, Ka, Ra, Fa                            # Appr   Spd, Aoa, Thrt, Fuel, Flaps
  global Vc, Hc, Kc, Rc                                # Cruise Spd, Alt, Thrt, Fuel
  global Cw,     Dw, Iw, Aw, Pw, Ww, Lf, Df, La, Da    # Wing, Flap, Ailr
  global Ch, Lh, Dh, Ah, Ph, Wh                        # Hstab, incidence is set by solver
  global Cv, Lv, Dv, Av, Pv, Wv, Lr, Dr                # Vstab, Rudder
  global Mp, Rp, Ap, Np, Xp, Ip, Op, Vp, Cp, Tp        # Prop
  global Mb, Xb, Yb, Zb                                # Ballast
  global Hy, Vy                                        # Solver
  global solnDict, solnCDS, solnCols, solnDT, solnIter, solnElev, solnCofG
  global totlInci, fracInci
  # Get the current slider values
  Va =  varyVa.value
  Aa =  varyAa.value
  Ra =  varyRa.value
  Ka =  varyKa.value
  Fa =  varyFa.value
  #
  Vc =  varyVc.value
  Hc =  varyHc.value
  Kc =  varyKc.value
  Rc =  varyRc.value
  #
  Iw =  varyIw.value
  Cw =  varyCw.value
  Dw =  varyDw.value
  Iw =  varyIw.value
  Aw =  varyAw.value
  Pw =  varyPw.value
  Ww =  varyWw.value
  #
  Lh =  varyLh.value
  Ch =  varyCh.value
  Dh =  varyDh.value
  Ah =  varyAh.value
  Ph =  varyPh.value
  Wh =  varyWw.value
  #
  Lv =  varyLv.value
  Cv =  varyCh.value
  Dv =  varyDh.value
  Av =  varyAh.value
  Pv =  varyPh.value
  Wv =  varyWw.value
  #
  Lr =  varyLr.value
  Dr =  varyDw.value
  #
  Mb =  varyMb.value
  Xb =  varyXb.value
  #
  Hy =  varyHy.value
  Vy =  varyVy.value
  #
  cfigFromVbls( aCfgFid )
  spinYasim( aCfgFid )
  lvsdDfrm  = pd.read_csv( lvsdFid, delimiter='\t')
  lvsdDsrc.data  = lvsdDfrm
  miasDfrm  = pd.read_csv( miasFid, delimiter='\t')
  miasDsrc.data  = miasDfrm
  # Here: figure wing incidence vs stall angle
  wingInci( aCfgFid)
  # Pull key values from yasim solution console output
  solnIter = scanSoln( solnFid, 'Iterations')
  solnElev = scanSoln( solnFid, 'Approach Elevator')
  solnCofG = scanSoln( solnFid, 'CG-x rel. MAC')
  # dunno how to update text boxes so output to console
  print( 'Iter:{:s}  Appr Elev:{:s}   CG:{:s} MAC   Wing Inc {:2.1f}deg   Stall AoA {:.1f}deg   Margin {:.1f}% ' \
          .format( solnIter, solnElev, solnCofG, totlInci, Aw, (100 * ( 1 - fracInci))))
  solnDict = dict( 
              dNames  = [ 'Iterations', 'Approach Elevator', 'CG-x rel. MAC'],
              dValues = [  solnIter,     solnElev,            solnCofG      ])
  solnCDS  = ColumnDataSource ( solnDict)
  solnCols = [TableColumn( field="dNames", title="Solved" ),
              TableColumn( field="dValues", title="Value" ), ]
  solnDT   = DataTable(source=solnCDS, columns=solnCols, width=240, height=120)
  solnCDS.update()
  solnDT.update()
#

# called if Version string is changed, duplicates actions cf above 
def dropHdlr(event) :
  global yCfgName, yCfgFid, aCfgFid, vCfgFid, versDict, versToDo, versKywd
  global procPref, lvsdFid, miasFid, solnFid
  # On dropdown action, record YASim version selected
  versToDo = event.item
  versKywd = versDict[versToDo]
  #print('dropHdlr versToDo:',  versToDo, '  versKywd: ', versKywd)
  # cf update_elem
  cfigFromVbls( aCfgFid )
  spinYasim( aCfgFid )
  lvsdDfrm  = pd.read_csv( lvsdFid, delimiter='\t')
  lvsdDsrc.data  = lvsdDfrm
  miasDfrm  = pd.read_csv( miasFid, delimiter='\t')
  miasDsrc.data  = miasDfrm

  # Pull key values from yasim solution console output
  solnIter = scanSoln( solnFid, 'Iterations')
  solnElev = scanSoln( solnFid, 'Approach Elevator')
  solnCofG = scanSoln( solnFid, 'CG-x rel. MAC')
  # dunno how to update text input boxes so output to console 
  print( versToDo, ' : Iterations: ', solnIter, \
         '  Appr Elev:',  solnElev, '  CG-x rel. MAC', solnCofG )
  solnDict = dict( 
              dNames  = [ 'Iterations', 'Approach Elevator', 'CG-x rel. MAC'],
              dValues = [  solnIter,     solnElev,            solnCofG      ])
  solnCDS  = ColumnDataSource ( solnDict)
  solnCols = [TableColumn( field="dNames", title="Solved" ),
              TableColumn( field="dValues", title="Value" ), ]
  solnDT   = DataTable(source=solnCDS, columns=solnCols, width=240, height=120)
  solnCDS.update()
  solnDT.update()
#
  
# listeners for interface changes 
for v in [varyVa, varyAa, varyRa, varyKa, varyFa, \
          varyVc, varyHc, varyKc, varyRc, \
          varyIw, varyDw, varyCw, varyAw, varyPw, varyWw, \
          varyLh, varyDh, varyCh, varyAh, varyPh, varyWh, \
          varyLv, varyDv, varyCv, varyAv, varyPv, varyWv, \
          varyLr, varyDr, varyMb, varyXb, varyHy, varyVy]:
  v.on_change('value', update_elem)

versDrop.on_click( dropHdlr)

# Set up layouts for slider groups
varyAppr = column(varyVa, varyAa, varyRa, varyKa, varyFa)
varyCrze = column(varyVc, varyHc, varyKc, varyRc)
varyWHC1 = column(varyIw, varyCw, varyPw, varyLh, varyCh)
varyWHC2 = column(varyDw, varyAw, varyWw, varyDh, varyAh)
varyVstb = column(varyLv, varyCv, varyPv, varyLr)
varyRudd = column(varyDv, varyAv, varyWv, varyDr)
varyMisc = column(varyMb, varyXb, varyHy, varyVy)

##
presets()
vblsFromTplt()
cfigFromVbls(aCfgFid )
spinYasim(aCfgFid)
#
# plan overall interface layout 
curdoc().title = yCfgName
curdoc().add_root(row(varyAppr, liftPlot, varyCrze, width=480))
curdoc().add_root(row(varyWHC1, dragPlot, varyWHC2, width=480))
curdoc().add_root(row(varyVstb, lvsdPlot, varyRudd, width=480))
curdoc().add_root(row(varyMisc, miasPlot, versDrop, width=480))
# Cannot get table of YASim output values to update, ergo console printout
#curdoc().add_root(row(solnDT, width=480))
#
## ysimi ends

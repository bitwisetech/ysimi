#!/usr/bin/env python
#
## ysimi.py: Interactively Adjust Numbers: a pandass / bokeh testbench for YASim
#
#    takes a given yasim config file, offers a web based plotter for Lift, drag, L/D 
#    creates modified yasim configs for different yasim versions
#    offers slider control of various key yasim elements and re-plots interactively
#
#    yCfg.. Input   yasim config xml Original 
#    aCfg.. Auto    yasim config xml generated with eg modified varied elements
#    vCfg.. Version yasim config xml modified elements plus specific VERSION string
#   ..-LvsD.txt     yasim generated Lift / Drag tables  
#   ..-soln.txt     yasim generated solution values     
#
##  install python3-bokeh, python3-pandas, numpy ( plus others ?? ) 
#  To run a local server: bokeh serve yasimian.py and then
#    browse to: http://localhost:5006/yasimian 
#
#   https://www.pluralsight.com/guides/
#     importing-data-from-tab-delimited-files-with-python
#   https://pandas.pydata.org/docs/getting_started/intro_tutorials/
#      02_read_write.html#min-tut-02-read-write
#
##
##
import os, shlex, subprocess, sys
##
import csv, numpy as np, pandas as pd

from bokeh.io import curdoc      
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, Slider, Dropdown
from bokeh.models import   TextInput, DataTable, TableColumn
from bokeh.plotting import figure
##
#  Python Version
global pythVers
pythVers = sys.version_info[0]
#print('pythVers:', pythVers)
from collections import OrderedDict 
##
global yCfgName, yCfgFid, aCfgFid, vCfgFid, versDict, versToDo, versKywd
global procPref, lvsdFid, miasFid, solnFid
## These vbles correspond to the elements in the config file: 
global Va, Aa, Ka, Ra, Fa                      # App Spd, Aoa, Thrt, Fuel, Flaps
global Vc, Hc, Kc, Rc                          # Cruise Spd, Alt, Thrt, Fuel
global Cw, Iw, Aw, Ww, Pw, Lf, Df, Lr, Dr      # Wing/Ailr parms
global Ch, Ih, Ah, Wh, Ph, Lh, Dh              # Hstab     parms
global Cv, Iv, Av, Wv, Pv, Lv, Dv              # Vstab     parms 
global Mp, Rp, Ap, Np, Xp, Ip, Op, Vp, Cp, Tp  # Prop      parms 
global Mb, Xb, Yb, Zb                          # Ballast   parms 
global Hy, Vy                                  # Solver    parms

#  Set Defaults and parse cammand args 
def presets():
  ## Default File IDs 
  global yCfgName, yCfgFid, aCfgFid, vCfgFid, versDict, versToDo, versKywd
  global procPref, lvsdFid, miasFid, solnFid
  global Hy, Vy                                  # Solver    parms
  procPref = "zsimi"
  # yasim config xml file read input 
  yCfgFid  = procPref + '-yasim.xml'
  yCfgName = yCfgFid.find('.xml')
  yCfgName = yCfgFid[0:yCfgName]
  # AutoCFig are output yasim config files with element(s) modified 
  aCfgFid  = procPref + '-ACfg.xml'
  #
  ##   
  # output yasim config files with element(s) modified  acfg obsolete ?
  aCfgFid  = procPref + '-ACfg.xml'
  vCfgFid  = procPref + '-vCfg.xml'
  #
  lvsdFid  = procPref + '-LvsD.txt'
  miasFid  = procPref + '-mias.txt'
  solnFid  = procPref + '-soln.txt'
  #
  # Versions in Yasim configuration strings, OrderedDict
  # all versions 
  versDict =  OrderedDict([ ('-vOrig',   'YASIM_VERSION_ORIGINAL'), \
                            ('-v2017-2', '2017.2'),   \
                            ('-v32',     'YASIM_VERSION_32',), \
                            ('-vCurr',   'YASIM_VERSION_CURRENT',  )])
   
  versToDo = '-vCurr'
  versKywd = versDict[versToDo]
  #print('presets versKywd:', versKywd)
# # Yasim 'Solve At' values for Speed and Altitude 
  Vy = 130
  Hy = 4000
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
# Scan original Yyasim config and extract numeric elements
#
def vblsFromTplt():
  global yCfgName, yCfgFid, aCfgFid, vCfgFid, versDict, versToDo, versKywd
  global solnDict, solnCDS, solnCols, solnDT, solnIter, solnElev, solnCofG
  ## These vbles correspond to the elements in the config file: 
  global Va, Aa, Ka, Ra, Fa                                    # Approach  parms
  global Vc, Hc, Kc, Rc                                        # Cruise    parms 
  global Cw, Iw, Aw, Ww, Pw, Lf, Df, Lr, Dr                    # Wing/Ailr parms
  global Ch, Ih, Ah, Wh, Ph, Lh, Dh                            # Hstab     parms
  global Cv, Iv, Av, Wv, Pv, Lv, Dv                            # Vstab     parms 
  global Mp, Rp, Ap, Np, Xp, Ip, Op, Vp, Cp, Tp                # Prop      parms 
  global Mb, Xb, Yb, Zb                                        # Ballast   parms 
  global Hy, Vy                                                # Solver    parms
#
  # These flags indicate parsing has detected various sections of yasim config 
  apprFlag   = 0
  cruzFlag   = 0
  wingFlag   = 0
  hstabFlag  = 0
  vstabFlag  = 0
  ballFlag   = 0
  propFlag   = 0
  # 
  Va = Aa = Ka = Ra = Fa = Vc = Hc = Kc = Rc = 0
  Cw = Aw = Ww = Pw = Lf = Df = Lr = Dr = 0
  Ch = Ah = Wh = Ph = Lh = Dh = Cv = Iv = Av = Wv = Pv = Lv = Dv = 0
  Iw = Ih = 1.00
  Mp = Rp = Ap = Np = Xp = Ip = Op = Vp = Cp = Tp = 0
  # in case ballast element is missing, fake with tiny value
  Mb = Xb = Yb = Zb = 0.001
#
  ## # open Yasim config file
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
          Iw = tuplValu('idrag', line)
        #print ('Cw: ', Cw, ' Iw: ', Iw)  
        ##
        #in wing section, find stall element values
        if ('stall' in line):
          # find element names, save values to post in Tix gui
          if ( 'aoa' in line):
            Aw = tuplValu('aoa', line)
          #
          if ( 'width' in line):
            Ww = tuplValu('width', line)
          #
          if ( 'peak' in line):
            Pw = tuplValu('peak', line)
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
            Lr = tuplValu('lift', line)
          #
          if ( 'drag' in line):
            Dr = tuplValu('drag', line)
          #
        #print ('Lr: ', Lr, ' Dr: ', Dr)  
      ### hstab section parse camber, idrag, stall and flap0 elements
      if (hstabFlag == 1):
        ## hstab section parse camber and induced drag elements if present
        if ('camber' in line):
          Ch =  tuplValu('camber', line)
        else:
          # camber is not specified so deflt values to satisfy menu
          Ch = 0
        #
        if ('idrag' in line):
          Ih = tuplValu('idrag', line)
        else:
          # camber is not specified so deflt values to satisfy menu
          Ih = 1
        #print ('Ch: ', Ch, ' Ih: ', Ih)  
        ##
        #in hstab section, find stall elements
        if ('stall' in line):
          # find element names, save values to post in Tix gui
          if ( 'aoa' in line):
            Ah = tuplValu('aoa', line)
          #
          if ( 'width' in line):
            Wh = tuplValu('width', line)
          #
          if ( 'peak' in line):
            Ph = tuplValu('peak', line)
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
        else:
          # camber is not specified so deflt values to satisfy menu
          Cv = 0
        #
        if ('idrag' in line):
          Iv = tuplValu('idrag', line)
        else:
          # camber is not specified so deflt values to satisfy menu
          Iv = 1
        #print ('Cv: ', Cv, ' Iv: ', Iv)  
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
            Lv = tuplValu('lift', line)
          #
          if ( 'drag' in line):
            Dv = tuplValu('drag', line)
          #
        #print ('Lv: ', Lv, ' Dv: ', Dv)
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
##
# Write named YASim config file to output with new elements
#
def cfigFromVbls( tFID):
  global yCfgName, yCfgFid, aCfgFid, vCfgFid, versDict, versToDo, versKywd
  global solnDict, solnCDS, solnCols, solnDT, solnIter, solnElev, solnCofG
  global Va, Aa, Ka, Ra, Fa                                    # Approach  parms
  global Vc, Hc, Kc, Rc                                        # Cruise    parms 
  global Cw, Iw, Aw, Ww, Pw, Lf, Df, Lr, Dr                    # Wing/Ailr parms
  global Ch, Ih, Ah, Wh, Ph, Lh, Dh                            # Hstab     parms
  global Cv, Iv, Av, Wv, Pv, Lv, Dv                            # Vstab     parms 
  global Mp, Rp, Ap, Np, Xp, Ip, Op, Vp, Cp, Tp                # Prop      parms 
  global Mb, Xb, Yb, Zb                                        # Ballast   parms 
  global Hy, Vy                                                # Solver    parms
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
  # write auto file via yconfig template and changed elements
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
          line = tuplSubs( 'idrag',   line, Iw )
        #   
        if ('stall' in line):
          line = tuplSubs( 'aoa'  ,   line, Aw )
          line = tuplSubs( 'width',   line, Ww ) 
          line = tuplSubs( 'peak' ,   line, Pw ) 
        #  
        if ('flap0' in line):
          line = tuplSubs( 'lift',    line, Lf ) 
          line = tuplSubs( 'drag',    line, Df ) 
        #  
        if ('flap1' in line):
          line = tuplSubs( 'lift',    line, Lr ) 
          line = tuplSubs( 'drag',    line, Dr )
        #
      ## HStab     
      if (hstabFlag == 1):
        if ('camber' in line):
          line = tuplSubs( 'camber',  line, Ch ) 
        if ('idrag' in line):
          line = tuplSubs( 'idrag',   line, Ih )
        #
        if ('stall' in line):
          line = tuplSubs( 'aoa'  ,   line, Ah ) 
          line = tuplSubs( 'width',   line, Wh ) 
          line = tuplSubs( 'peak' ,   line, Ph )
        #   
        if ('flap0' in line):
          line = tuplSubs( 'lift',    line, Lh ) 
          line = tuplSubs( 'drag',    line, Dh ) 
        # 
      ## Vstab   
      if (vstabFlag == 1):
        if ('camber' in line):
          line = tuplSubs( 'lift',    line, Cv ) 
          line = tuplSubs( 'idrag',   line, Iv )
        #
        if ('stall' in line):
          line = tuplSubs( 'aoa'  ,   line, Av ) 
          line = tuplSubs( 'width',   line, Wv ) 
          line = tuplSubs( 'peak' ,   line, Pv )
        #   
        if ('flap0' in line):
          line = tuplSubs( 'lift',    line, Lv ) 
          line = tuplSubs( 'drag',    line, Dv ) 
        # 
      ###
      #ballast
      if (ballFlag == 1):
        ## ballast section one line for all elements if present
        if ('mass' in line):
          line = tuplSubs( 'mass',    line, Mb ) 
        #
        if ('x=' in line):
          line = tuplSubs( 'x',    line, Xb ) 
        #
        if ('y=' in line):
          line = tuplSubs( 'y',    line, Yb ) 
        #
        if ('z=' in line):
          line = tuplSubs( 'z',    line, Zb ) 
        #
        ballFlag =  0
        #
      ###
      #prop 
      if (propFlag == 1):
        ## prop section parse elements if present
        if ('mass' in line):
          line = tuplSubs( 'mass',    line, Mp ) 
        #
        if ('radius' in line):
          line = tuplSubs( 'radius',    line, Rp ) 
        #
        if ('moment' in line):
          line = tuplSubs( 'moment',    line, Ap ) 
        #
        if ('min-rpm' in line):
          line = tuplSubs( 'min-rpm',    line, Np ) 
        #
        if ('max-rpm' in line):
          line = tuplSubs( 'max-rpm',    line, Xp ) 
        #
        if ('fine-stop' in line):
          line = tuplSubs( 'fine-stop',    line, Ip ) 
        #
        if ('coarse-stop' in line):
          line = tuplSubs( 'coarse-stop',    line, Op ) 
        #
        if ('cruise-speed' in line):
          line = tuplSubs( 'cruise-speed',    line, Vp ) 
        #
        if ('cruise-rpm' in line):
          line = tuplSubs( 'cruise-rpm',    line, Cp ) 
        #
        if ('takeoff-rpm' in line):
          line = tuplSubs( 'takeoff-rpm',    line, Tp ) 
        #
      # graft for ?simi versions where YASim Version is menu selection 
      # look for eg <airplane mass="6175" version="YASIM_VERSION_CURRENT" mtow-lbs="7500">  
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

##
# Create individual Yasim config file for testing each desired Yasim version 
#   Files contain 'YASIM_VERSION_XXX string to trigger various execution paths in yasim
# Call Yasim as external process to create console output and data tables 
# Obs ? Call Yasim as external process to generate Lift, Drag ( LvsD ? ) data tables 
## 
def spinVersions(tFid):
  global yCfgName, yCfgFid, aCfgFid, vCfgFid, versDict, versToDo, versKywd
  global procPref, lvsdFid, miasFid, solnFid
  #
  ## No need to Iterate through each version, dropdown selects version to run
  #versSfix = versDict[versKywd]
  ## use version selected in dropdown
  versSfix = versToDo
  # find keyword for inserting into vCfg 
  versKywd = versDict[versSfix]
  vCfgFid  = yCfgName + versSfix + '.xml'
  print ('spinVers tFid:', tFid,  ' vCfgFid: ', vCfgFid )
  lvsdFid  = procPref + '-LvsD' + versSfix + '.txt'
  miasFid  = procPref + '-mias' + versSfix + '.txt'
  solnFid  = procPref + '-soln' + versSfix + '.txt'
  ##
  ## # open version - yasim config file, apply version string 
  if (pythVers < 3):
    vCfgHndl  = open(vCfgFid, 'w', 0)
  else :
    vCfgHndl  = open(vCfgFid, 'w')
  #  write modified elements and version string file via yconfig template
  with open(tFid, 'r') as aCfgHndl:
  # step each line in template yasim config file
    for line in aCfgHndl:
      # look for eg <airplane mass="6175" version="YASIM_VERSION_CURRENT" mtow-lbs="7500">  
      if '<airplane mass="' in line:
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
      # Write unchanged/modified line into versioned xml 
      vCfgHndl.write(line)
  #close and sync files
  vCfgHndl.flush
  os.fsync(vCfgHndl.fileno())
  vCfgHndl.close
  #os.sync()
  aCfgHndl.close
  ## busy work, without this yasim executes too soon and throws error 
  lc = 0   
  with open(vCfgFid, 'r') as vCfgHndl:
  # step each line in template yasim config file
    for line in vCfgHndl:
      lc += 1
  vCfgHndl.close
  #
  ##
  #end step through version dictionary
#
## 
def spinYasim(tFid):
  global yCfgName, yCfgFid, aCfgFid, vCfgFid, versDict, versToDo, versKywd
  global lvsdFid, miasFid, solnFid
  global Hy, Vy
  #
  ## use version selected in dropdown
  ## Obs ? Think these not needed 
  ##versSfix = versToDo
  ##vCfgFid  = yCfgName + versSfix + '.xml'
  ##lvsdFid  = procPref + '-LvsD' + versSfix + '.txt'
  ##miasFid  = procPref + '-mias' + versSfix + '.txt'
  ##solnFid  = procPref + '-soln' + versSfix + '.txt'
  #print('spinYasim tFid: ', tFid)
  ##
  # run yasim external process to generate LvsD data table saved dataset file
  vDatHndl = open(lvsdFid, 'w')
  command_line = 'yasim ' + tFid + ' -g -a '+ str(Hy/3.3) + ' -s ' + str( (Vy))
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
#

def scanSoln( tFid, tText) :
  with open(tFid, 'r') as solnHndl:
  # step each line in yasim config file
    for tLine in solnHndl:
      if ( tText in tLine ) :
        # find the colon after the text
        tPosn = tLine.find( tText )
        tPosn = tLine.find( ':', (tPosn + 1))
        return ( tLine[ tPosn + 1 : ].strip('\n'))

#
def update_elem(attrname, old, new):
## These vbles correspond to the elements in the config file: 
  global Va, Aa, Ka, Ra, Fa                                    # Approach  parms
  global Vc, Hc, Kc, Rc                                        # Cruise    parms 
  global Cw, Iw, Aw, Ww, Pw, Lf, Df, Lr, Dr                    # Wing/Ailr parms
  global Ch, Ih, Ah, Wh, Ph, Lh, Dh                            # Hstab     parms
  global Cv, Iv, Av, Wv, Pv, Lv, Dv                            # Vstab     parms 
  global Mp, Rp, Ap, Np, Xp, Ip, Op, Vp, Cp, Tp                # Prop      parms 
  global Mb, Xb, Yb, Zb                                        # Ballast   parms 
  global Hy, Vy                                                # Solver    parms
  global solnDict, solnCDS, solnCols, solnDT, solnIter, solnElev, solnCofG
  global yCfgName, yCfgFid, aCfgFid, vCfgFid, versDict, versToDo, versKywd
  global procPref, lvsdFid, miasFid, solnFid
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
  Aw =  varyAw.value
  Ww =  varyWw.value
  Pw =  varyPw.value
  #
  Mb =  varyMb.value
  Xb =  varyXb.value
  Hy =  varyHy.value
  Vy =  varyVy.value
  #
  cfigFromVbls( vCfgFid )
  #spinVersions( vCfgFid )
  spinYasim( vCfgFid )
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

def dropHdlr(event) :
  global yCfgName, yCfgFid, aCfgFid, vCfgFid, versDict, versToDo, versKywd
  global procPref, lvsdFid, miasFid, solnFid
  # On dropdown action, record YASim version selected  
  versToDo = event.item
  versKywd = versDict[versToDo]
  #print('dropHdlr versToDo:',  versToDo, '  versKywd: ', versKywd)
  # cf update_elem
  cfigFromVbls( vCfgFid )
  #spinVersions( vCfgFid )
  spinYasim( vCfgFid )
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
  
##
presets()
vblsFromTplt()
cfigFromVbls( vCfgFid)
#spinVersions( vCfgFid )
spinYasim( vCfgFid )

# sources for bokeh dataframe and readout data 
lvsdDfrm  = pd.read_csv(lvsdFid, delimiter='\t')
lvsdDsrc  = ColumnDataSource(lvsdDfrm)

miasDfrm  = pd.read_csv(miasFid, delimiter='\t')
miasDsrc  = ColumnDataSource(miasDfrm)

# Dropdown for selecting which YASim version to run 
versDrop = Dropdown(label='Select YASim VERSION to Run', \
menu=['-vOrig', '-v2017-2', '-v32', '-vCurr'])

# Pull key values from yasim solution console output
solnIter = scanSoln( solnFid, 'Iterations')
solnElev = scanSoln( solnFid, 'Approach Elevator')
solnCofG = scanSoln( solnFid, 'CG-x rel. MAC')
# Try a data table to live update soln values
solnDict = dict( 
            dNames  = [ 'Iterations', 'Approach Elevator', 'CG-x rel. MAC'],
            dValues = [  solnIter,     solnElev,            solnCofG      ])
solnCDS  = ColumnDataSource ( solnDict)
solnCols = [TableColumn( field="dNames", title="Solution Item" ),
            TableColumn( field="dValues", title="Value" ), ]
solnDT   = DataTable(source=solnCDS, columns=solnCols, width=240, height=120)

# Set up plots
liftPlot  = figure(plot_height=200, plot_width=256, title="Lift G vs AoA",
              tools="crosshair,pan,reset,save,wheel_zoom" )

dragPlot  = figure(plot_height=200, plot_width=256, title="Drag G vs AoA",
              tools="crosshair,pan,reset,save,wheel_zoom" )

lvsdPlot  = figure(plot_height=200, plot_width=256, title="L / D  vs AoA",
              tools="crosshair,pan,reset,save,wheel_zoom" )

miasPlot  = figure(plot_height=200, plot_width=256, title="Vs0 IAS, %Lift vs AoA",
              tools="crosshair,pan,reset,save,wheel_zoom" )

#7 #plot_i.line(x='x', 'y', source=source, line_width=3, line_alpha=0.6)
liftPlot.line( x='aoa', y='Lift',  source=lvsdDsrc, line_width=3, line_alpha=0.6)
dragPlot.line( x='aoa', y='Drag',  source=lvsdDsrc, line_width=3, line_alpha=0.6)
lvsdPlot.line( x='aoa', y='LvsD',  source=lvsdDsrc, line_width=3, line_alpha=0.6)
miasPlot.line( x='aoa', y='knots', source=miasDsrc, line_width=3, line_alpha=0.6)
miasPlot.line( x='aoa', y='lift',  source=miasDsrc, line_width=3, line_alpha=0.6)

# Set up widgets, balance range / step size each affects re-calc
#  Approach group
varyVa    = Slider(title="Appr IAS  Va",         value= Va, start=(40.0  ), end=(160 ),  step=(2.0   ))
varyAa    = Slider(title="Appr AoA  Aa",         value= Aa, start=(-5.0  ), end=(20  ),  step=(0.2   ))
varyKa    = Slider(title="Appr Thrt  Ka",        value= Ka, start=(0.0   ), end=(1.0 ),  step=(0.1   ))
varyRa    = Slider(title="Appr Fuel  Ra",        value= Ra, start=(0.0   ), end=(1.0 ),  step=(0.1   ))
varyFa    = Slider(title="Appr Flap  Fa",        value= Fa, start=(0.0   ), end=(1.0 ),  step=(0.1   ))
#  Cruise
varyVc    = Slider(title="Cruise IAS  Vc",       value= Vc, start=(40    ), end=(240 ),  step=(2.0   ))
varyHc    = Slider(title="Cruise Alt  Hc",       value= Hc, start=(1000  ), end=(40000), step=(500   ))
varyKc    = Slider(title="Cruise Thrt  Kc",      value= Kc, start=(0.0   ), end=(1.0 ),  step=(0.1   ))
varyRc    = Slider(title="Cruise Fuel  Rc",      value= Rc, start=(0.0   ), end=(1.0 ),  step=(0.1   ))
#  Wing
varyIw    = Slider(title="Wing Incidence   Iw",  value= Iw, start=(-8.0  ), end=(24  ),  step=(0.2   ))
varyAw    = Slider(title="Wing Stall Aoa   Aw",  value= Aw, start=(-2.0  ), end=(24.0),  step=(0.1   ))
varyWw    = Slider(title="Wing Stall Width Ww",  value= Ww, start=(0.0   ), end=(32  ),  step=(0.50  ))
varyPw    = Slider(title="Wing Stall Peak  Pw",  value= Pw, start=(0.2   ), end=(20.0),  step=(0.2   ))
#
varyMb    = Slider(title="Ballast Mass     Mb",  value= Mb, start=(-4000 ), end=(4000),  step=(200   ))
varyXb    = Slider(title="Ballast Posn     Xb",  value= Xb, start=(-200  ), end=(200 ),  step=(0.5   ))
varyHy    = Slider(title="Solve at Alt Ft  Hy",  value= Hy, start=(500   ), end=(40000), step=(500   ))
varyVy    = Slider(title="Solve at IAS Kt  Vy",  value= Vy, start=(40    ), end=(300  ), step=(50    ))


for v in [varyVa, varyAa, varyRa, varyKa, varyFa, varyVc, varyHc, varyKc, varyRc, \
          varyIw, varyAw, varyWw, varyPw, varyMb, varyXb, varyHy, varyVy ]:
  v.on_change('value', update_elem)
  
versDrop.on_click( dropHdlr)


# Set up layouts and add to document
varyAppr = column(varyVa, varyAa, varyRa, varyKa, varyFa)
varyCrze = column(varyVc, varyHc, varyKc, varyRc)
varyWing = column(varyIw, varyAw, varyWw, varyPw)
varyBlst = column(varyMb, varyXb, varyHy, varyVy)

##
presets()
vblsFromTplt()
cfigFromVbls( vCfgFid )
#spinVersions(vCfgFid)
spinYasim(vCfgFid)
#
curdoc().title = yCfgName
curdoc().add_root(row(versDrop, width=480))
curdoc().add_root(row(varyAppr, liftPlot, width=480))
curdoc().add_root(row(varyCrze, dragPlot, width=480))
curdoc().add_root(row(varyWing, lvsdPlot, width=480))
curdoc().add_root(row(varyBlst, miasPlot, width=480))
#curdoc().add_root(row(solnDT, width=480))

## simi ends

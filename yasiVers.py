#!/usr/bin/env python
#
## yasiVers.py tix menu driven yasim version explorer with gnuplot displays
#    takes a given yasim config file, tix menus display/alter element values
#    creates altered yasim configs for different yasim versions
#    gnuplots Lift, Drag and Lift vs Drag for each yasim version 
#
#    yCfg.. Input   yasim cofig xml Original 
#    aCfg.. Auto    yasim cofig xml generated with eg varied elements
#    vCfg.. Version yasim cofig xml elements plus specific VERSION string
##
## Tix tix for python 3  import getopt, os, shlex, subprocess, sys, Tix
import getopt, os, shlex, subprocess, sys
from collections import OrderedDict 
##
#  Python Version
global pythVers
pythVers = sys.version_info[0]
#print('pythVers:', pythVers)
if (pythVers < 3):
  import Tix
  import Tkinter as tk
else:  
  import tkinter as tk
  from tkinter import tix
##
#  Set Defaults and parse cammand args 
def normArgs(argv):
  ## Default File IDs 
  ##
  global yCfgNam, yCfgFid, dataFid, aCfgFid, atptFid, tpltFid
  # yasim config xml file read input 
  yCfgFid   = 'yvers-yasim.xml'
  yCfgNam = yCfgFid.find('.xml')
  yCfgNam = yCfgFid[0:yCfgNam]
  # AutoCFig are output yasim config files with element(s) modified 
  aCfgFid   = 'yvers-ACfg.xml'
  # tabbed text yasim -g enerated 
  dataFid = "yvers-outp-yGen.txt"
  #
  ##   
  # Tabulated yasim -g data using Tix Menu modified elements for GNU Plot 
  # yasim config xml file read input 
  yCfgFid   = 'yvers-YCfg.xml'
  # AutoCFig are output yasim config files with element(s) modified 
  aCfgFid   = 'yvers-ACfg.xml'
  #
  # template p is the base gnuplot command file
  tpltFid    = 'yvers-ldld-spec.p'
  # atp      p is retitled gnuplot command file
  atptFid    = 'yvers-outp-spec.p'
  ## 
  # get yasim config FileID from args
  try: 
    opts, args = getopt.getopt(argv, "f:p:", ["file=", "plot="])
  except getopt.GetoptError:
     print ('sorry, args do not make sense ')
     sys.exit(2)
  #
  #
  for opt, arg in opts:
    if   opt in ("-f", "--file"):
      yCfgFid = arg
      yCfgNam = yCfgFid.find('.xml')
      yCfgNam = yCfgFid[0:yCfgNam]
  #
  for opt, arg in opts:
    if   opt in ("-p", "--plot"):
      if (( arg == 'l') or (arg == 'L'  )) :
        tpltFid  = 'yvers-l-spec.p'
      if (( arg == 'd') or (arg == 'D'  )) :
        tpltFid  = 'yvers-d-spec.p'
      if (( arg == 'l') or (arg == 'L'  )) :
        tpltFid  = 'yvers-l-spec.p'
      if (( arg == 'ld') or (arg == 'LD')) :
        tpltFid  = 'yvers-ld-spec.p'
      # defaults to l, d, l/d spec  
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
# Scan original Yyasim config and extract numeric elements, save for tix menu
#
def vblsFromTplt():
  global yCfgNam, yCfgFid, dataFid, aCfgFid, atptFid, tpltFid
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
# # Yasim 'Solve At' values for Speed and Altitude 
  Vy = 130
  Hy = 4000
  # 
  Va = Aa = Ka = Ra = Fa = Vc = Hc = Kc = Rc = 0
  Cw = Aw = Ww = Pw = Lf = Df = Lr = Dr = 0
  Ch = Ah = Wh = Ph = Lh = Dh = Cv = Iv = Av = Wv = Pv = Lv = Dv = 0
  Iw = Ih = 1.00
  Mp = Rp = Ap = Np = Xp = Ip = Op = Vp = Cp = Tp = 0
  Mb = Xb = Yb = Zb = 0
#
  ## # open Yasim config file
  ## aCfgHndl  = open(aCfgFid, 'w', 0)
  # Phase 1 open base yasim config file and parse elements
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
# After tix menu changes, copy input yasim config file to output with new elements
#
def cfigFromVbls( tFID):
  global yCfgNam, yCfgFid, dataFid, aCfgFid, atptFid, tpltFid
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
  print( tFID)
  ###ab smite yDatFid  = yCfgNam + '-tix.txt'
  ## # open auto yasim config file
  ## Tix tix for python 3
  if ( pythVers < 3 ) :
    aCfgHndl  = open(aCfgFid, 'w', 0)
  else :
    aCfgHndl  = open(aCfgFid, 'w')
  # Phase 3 write auto file via yconfig template and subsVbls from Tix
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
# Call GNUPlot as external process to create Lift-Drag-L/D curves
## 
def callPlot(tFid):
  global yCfgNam, yCfgFid, dataFid, aCfgFid, atptFid, tpltFid
  global Va, Aa, Ka, Ra, Fa                                    # Approach  parms
  global Vc, Hc, Kc, Rc                                        # Cruise    parms 
  global Cw, Iw, Aw, Ww, Pw, Lf, Df, Lr, Dr                    # Wing/Ailr parms
  global Ch, Ih, Ah, Wh, Ph, Lh, Dh                            # Hstab     parms
  global Cv, Iv, Av, Wv, Pv, Lv, Dv                            # Vstab     parms 
  global Mp, Rp, Ap, Np, Xp, Ip, Op, Vp, Cp, Tp                # Prop      parms 
  global Mb, Xb, Yb, Zb                                        # Ballast   parms 
  global Hy, Vy                                                # Solver    parms
#
# Versions in Yasim configuration strings, OrderedDict
## single plot 
  versDict =             OrderedDict([ ('YASIM_VERSION_CURRENT',  '-vCurr'), ])
## all versions 
##versDict =             OrderedDict([ ('YASIM_VERSION_ORIGINAL', '-vOrig'), \
##                                     ('YASIM_VERSION_32',       '-v32'),   \
##                                     ('YASIM_VERSION_CURRENT',  '-vCurr'), \
##                                     ('2017.2',                 '-v2017-2') ])
  ## Iterate through each version in dictionary
  for versKywd in versDict.keys():
    versSfix = versDict[versKywd]
    vCfgFid  = yCfgNam + versSfix + '.xml'
    vdatFid  = yCfgNam +  '-dat' + versSfix + '.txt'
    ##
    ## # open version - yasim config file, apply version string 
    ## Tix tix for python 3
    if (pythVers < 3):
      vCfgHndl  = open(vCfgFid, 'w', 0)
    else :
      vCfgHndl  = open(vCfgFid, 'w')
    #  write auto file via yconfig template and subsVbls from Tix
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
    #
    os.sync()
    aCfgHndl.close
    ##
    ## GNUPlot needs specification files: auto create gnuplot spec file
    if ( pythVers < 3 ) :
      apltHndl  = open(atptFid, 'w', 0)
    else :
      apltHndl  = open(atptFid, 'w')
    #create common annotation test parsed / menu-altered values, big version: all menu parms 
    commNota = ' set title "' + tFid + ' Parms:\\nAp:' + str(Va)  \
      + ' ' + str(Aa) + ' ' + str(Ka) + ' ' + str(Ra) + ' ' + str(Fa) +'\\n'   \
      + ' Cz:'  + str(Vc) + ' ' + str(Hc) + ' ' + str(Kc) + ' '                \
      + str(Rc) + '\\nWi:' + str(Cw) + ' ' + str(Iw) + ' ' + str(Aw)           \
      + ' ' + str(Ww) + ' ' + str(Pw) + ' ' + str(Lf) + ' ' + str(Df)          \
      + ' ' + str(Lr) + ' ' + str(Dr)                                          \
      + '\\nHs:' + str(Ch) + ' ' + str(Ih) + ' ' + str(Ah)                     \
      + ' ' + str(Wh) + ' ' + str(Ph) + ' '   + str(Lh) + ' ' + str(Dh)        \
      + '\\nVs:' + str(Cv) + ' ' + str(Iv) + ' ' + str(Av)                     \
      + ' ' + str(Wv) + ' ' + str(Pv) + ' '   + str(Lv) + ' ' + str(Dv)        \
      + 'Ys:'+ str(Vy) + ' ' + str(Hy) + '" \n'
    # uncomment a line below to have gnuplot show shortened legend 
    #commNota = ' set title "yasiVers.py ' + yCfgNam + versSfix + ' : ' + str(Vy) + 'kTAS at ' + str(Hy) + 'ft" \n'
    #commNota = ' set title "' + yCfgNam + ' ' + versSfix + ' : ' + str(Vy) + 'kTAS at ' + str(Hy) + 'ft" \n'
    commNota = ' set title "'+ tFid +' Va:'+str(Va)+' Aa:'+str(Aa) + ' Vc:'+str(Vc)+' Cw:'+str(Cw)+' Aw:'+str(Aw)+' Ww:'+str(Ww)+'"\n'
    with open(tpltFid, 'r') as tplt:
      plotFlag = 0
      for line in tplt:
        # set flag near end when 'plot' string is found
        if (' plot ' in line ): plotFlag = 1
        # find the title line in template config
        if ('set title' in line ):
          line  = commNota
        if ( plotFlag < 1):
          # Write line into auto.xml
          apltHndl.write(line)
      # At EOF append plot lines with proper data file name
#     line = ' plot "' + vdatFid +'" every ::2        using '            \
#          + '1:2 with lines title \'lift\', \\\n'
#     apltHndl.write(line)
#     line = '      "' + vdatFid +'" every ::2        using '            \
#          + '1:3 with lines title \'drag\''
#     apltHndl.write(line)
### ab 2020Jan23  L/D only 
      line = ' plot "' + vdatFid +'" every ::2        using '            \
           + '1:4 with lines title \'LvsD\''
      apltHndl.write(line)
      apltHndl.close
      tplt.close
    #
    ## auto create gnuplot config file
    apltHndl  = open(atptFid, 'w')
    with open(tpltFid, 'r') as tplt:
      plotFlag = 0
      for line in tplt:
        # find the title line in template config
        if ('set title' in line ):
          line  = commNota
        apltHndl.write(line)
      apltHndl.close
      tplt.close
    ## python3 Need to open/close file to flush it ?
    vCfgHndl  = open(vCfgFid, 'r')
    vCfgHndl.close()
    ##    
    if (0) :
      # run yasim external process to show console output
      command_line = 'yasim ' + vCfgFid + ' -a ' + str(Hy) + ' -s ' + str(Vy)
      command_line = 'yasim ' + vCfgFid                                        
      args = shlex.split(command_line)
      DEVNULL = open(os.devnull, 'wb')
      p = subprocess.run(args, stdout=DEVNULL, stderr=DEVNULL)
      DEVNULL.close()
      #p.communicate()
      #p.wait()
      #
    # run yasim external process for auto dataset, name used in .p spec
    ###ab smite yDatHndl = open(yDatFid, 'w')
    ###ab smite command_line = 'yasim ' + vCfgFid + ' -g -a ' + str(Hy) + ' -s ' + str(Vy)
    ###ab smite args = shlex.split(command_line)
    ###ab smite p = subprocess.run(args, stdout=yDatHndl)
    ###ab smite yDatHndl.close
    ###ab smite p.wait()
    #
    ##
    # run yasim external process for saved dataset file
    print ('here')
    vDatHndl = open(vdatFid, 'w')
    command_line = 'yasim ' + vCfgFid + ' -g -a '+ str(Hy) + ' -s ' + str(Vy)
    print(command_line)
    args = shlex.split(command_line)
    DEVNULL = open(os.devnull, 'wb')
    p = subprocess.run(args, stdout=vDatHndl, stderr=DEVNULL)
    DEVNULL.close()
    vDatHndl.close
    #p.wait()
    ##
    # run gnuplot with command file to plot dataset
    apltHndl  = open(atptFid, 'w')
    apltHndl.close()
    command_line = "gnuplot -p " + atptFid
    args = shlex.split(command_line)
    DEVNULL = open(os.devnull, 'wb')
    p = subprocess.run(args, stdout=DEVNULL, stderr=DEVNULL)
    #p.communicate()
    DEVNULL.close()
  #end step through version dictionary
#

##
# Tix Interface Menu #
##
class PropertyField:
  def __init__(self, parent, prop, label):
    self.prop = prop
    ## Tix tix for python 3
    if (pythVers < 3):
      self.field = Tix.LabelEntry( parent, label=label,
        options='''
        label.width 12
        label.anchor e
        entry.width 12
        ''' )
    else :  
      self.field = tix.LabelEntry( parent, label=label,
        options='''
        label.width 12
        label.anchor e
        entry.width 12
        ''' )
    ## Tix tix for python 3
    if (pythVers < 3):
      self.field.pack( side=Tix.TOP, padx=8, pady=2 )    
    else :
      self.field.pack( side=tix.TOP, padx=8, pady=2 )
  # Pull numeric vals from menu entries and store into variables
  def eval_field(self):
    global Va, Aa, Ka, Ra, Fa                                    # Approach  parms
    global Vc, Hc, Kc, Rc                                        # Cruise    parms 
    global Cw, Iw, Aw, Ww, Pw, Lf, Df, Lr, Dr                    # Wing/Ailr parms
    global Ch, Ih, Ah, Wh, Ph, Lh, Dh                            # Hstab     parms
    global Cv, Iv, Av, Wv, Pv, Lv, Dv                            # Vstab     parms 
    global Mp, Rp, Ap, Np, Xp, Ip, Op, Vp, Cp, Tp                # Prop      parms 
    global Mb, Xb, Yb, Zb                                        # Ballast   parms 
    global Hy, Vy                                                # Solver    parms
    #
    #
    val = self.field.entry.get()
    lbl = self.field.label.cget('text')
    self.prop = val
    if 'ApprSpd'    in lbl: Va = val
    if 'ApprAoA'    in lbl: Aa = val
    if 'ApprFuel'   in lbl: Ka = val
    if 'ApprThrt'   in lbl: Ra = val
    if 'ApprFlap'   in lbl: Fa = val
    if 'SolveAtSpd' in lbl: Vy = val
    if 'SolveAtAlt' in lbl: Hy = val
    if 'CruiseSpd'  in lbl: Vc = val
    if 'CruiseAlt'  in lbl: Hc = val
    if 'CruiseFuel' in lbl: Kc = val
    if 'CruiseThrt' in lbl: Rc = val
    if 'WingCambr'  in lbl: Cw = val
    if 'WingIDrag'  in lbl: Iw = val
    if 'WingStAoA'  in lbl: Aw = val
    if 'WingStWid'  in lbl: Ww = val
    if 'WingStlPk'  in lbl: Pw = val
    if 'WFlapLift'  in lbl: Lf = val
    if 'WFlapDrag'  in lbl: Df = val
    if 'AilrnLift'  in lbl: Lr = val
    if 'AilrnDrag'  in lbl: Dr = val
    if 'HstbCambr'  in lbl: Ch = val
    if 'HstbIDrag'  in lbl: Ih = val
    if 'HstbStAoA'  in lbl: Ah = val
    if 'HstbStWid'  in lbl: Wh = val
    if 'HstbStlPk'  in lbl: Ph = val
    if 'HFlapLift'  in lbl: Lh = val
    if 'HFlapDrag'  in lbl: Dh = val
    if 'VstbCambr'  in lbl: Ch = val
    if 'VstbIDrag'  in lbl: Ih = val
    if 'VstbStAoA'  in lbl: Ah = val
    if 'VstbStWid'  in lbl: Wh = val
    if 'VstbStlPk'  in lbl: Ph = val
    if 'VFlapLift'  in lbl: Lh = val
    if 'VFlapDrag'  in lbl: Dh = val
    if 'BallMass'   in lbl: Mb = val
    if 'BallXloc'   in lbl: Xb = val
    if 'BallYloc'   in lbl: Yb = val
    if 'BallZloc'   in lbl: Zb = val
    if 'PropMass'   in lbl: Mp = val
    if 'PropRadi'   in lbl: Rp = val
    if 'PropMomt'   in lbl: Ap = val
    if 'PropMinR'   in lbl: Np = val
    if 'PropMaxR'   in lbl: Xp = val
    if 'PropFine'   in lbl: Ip = val
    if 'PropCoar'   in lbl: Op = val
    if 'PropCSpd'   in lbl: Vp = val
    if 'PropCRpm'   in lbl: Cp = val
    if 'PropTRpm'   in lbl: Tp = val

  def update_field(self):
    val = self.prop
    self.field.entry.delete(0,'end')
    self.field.entry.insert(0, val)

## Tix tix for python 3
class PropertyPage(tix.Frame):
  ## class PropertyPage(Tix.Frame):
  def __init__(self,parent):
    ## Tix tix for python 3
    if (pythVers < 3):
      Tix.Frame.__init__(self,parent)
      self.pack( side=Tix.TOP, padx=2, pady=2, fill=Tix.BOTH, expand=1 )
    else :  
      tix.Frame.__init__(self,parent)
      self.pack( side=tix.TOP, padx=2, pady=2, fill=tix.BOTH, expand=1 )
    ## Tix tix for python 3
    self.fields = []

  def addField(self, prop, label):
    f = PropertyField(self, prop, label)
    self.fields.append(f)

  def eval_fields(self):
    for f in self.fields:
      f.eval_field()

  def update_fields(self):
    for f in self.fields:
      #f.update_field(self.fgfs)
      f.update_field()
      ## Tix tix for python 3
      if (pythVers < 3):
        Tix.Frame.update(self)
      else :  
        tix.Frame.update(self)

## Tix tix for python 3   class ycTix(Tix.Frame):
class ycTix(tix.Frame):
  def __init__(self,root=None):
    ## Tix tix for python 3
    if (pythVers < 3):
      Tix.Frame.__init__(self,root)
    else :  
      tix.Frame.__init__(self,root)
    z = root.winfo_toplevel()
    z.wm_protocol("WM_DELETE_WINDOW", lambda self=self: self.quitCmd())
    #self.fgfs = fgfs
    self.pack()
    self.pages = {}
    self.after_id = None
    self.createWidgets()
    self.update()

  def createWidgets(self):
    ## Tix tix for python 3
    if (pythVers < 3):
      self.nb = Tix.NoteBook(self)
    else :  
      self.nb = tix.NoteBook(self)
    self.nb.add( 'appr', label='APPR',
           raisecmd= lambda self=self: self.update_page() )
    self.nb.add( 'cruz', label='CRSE',
           raisecmd= lambda self=self: self.update_page() )
    self.nb.add( 'wing', label='WING',
           raisecmd= lambda self=self: self.update_page() )
    self.nb.add( 'hstb', label='HSTB',
           raisecmd= lambda self=self: self.update_page() )
    self.nb.add( 'vstb', label='VSTB',
           raisecmd= lambda self=self: self.update_page() )
    self.nb.add( 'ball', label='BALL',
           raisecmd= lambda self=self: self.update_page() )
    self.nb.add( 'prop', label='PROP',
           raisecmd= lambda self=self: self.update_page() )
    #
    page = PropertyPage( self.nb.appr )
    self.pages['appr'] = page
    page.addField( Va,    'ApprSpd:')
    page.addField( Aa,    'ApprAoA:')
    page.addField( Ka,    'ApprFuel:')
    page.addField( Ra,    'ApprThrt:')
    page.addField( Fa,    'ApprFlap:')
    page.addField( Vy,  'SolveAtSpd:')
    page.addField( Hy,  'SolveAtAlt:')
    #
    page = PropertyPage( self.nb.cruz )
    self.pages['cruz'] = page
    page.addField( Vc,    'CruiseSpd:')
    page.addField( Hc,    'CruiseAlt:')
    page.addField( Kc,   'CruiseFuel:')
    page.addField( Rc,   'CruiseThrt:')
    #
    page = PropertyPage( self.nb.wing )
    self.pages['wing'] = page
    page.addField( Cw,    'WingCambr:')
    page.addField( Iw,    'WingIDrag:')
    page.addField( Aw,    'WingStAoA:')
    page.addField( Ww,    'WingStWid:')
    page.addField( Pw,    'WingStlPk:')
    page.addField( Lf,    'WFlapLift:')
    page.addField( Df,    'WFlapDrag:')
    page.addField( Lr,    'AilrnLift:')
    page.addField( Dr,    'AilrnDrag:')
    #
    page = PropertyPage( self.nb.hstb )
    self.pages['hstb'] = page
    page.addField( Ch,    'HstbCambr:')
    page.addField( Ih,    'HstbIDrag:')
    page.addField( Ah,    'HstbStAoA:')
    page.addField( Wh,    'HstbStWid:')
    page.addField( Ph,    'HstbStlPk:')
    page.addField( Lh,    'HFlapLift:')
    page.addField( Dh,    'HFlapDrag:')
    #
    page = PropertyPage( self.nb.vstb )
    self.pages['vstb'] = page
    page.addField( Cv,    'VstbCambr:')
    page.addField( Iv,    'VstbIDrag:')
    page.addField( Av,    'VstbStAoA:')
    page.addField( Wv,    'VstbStWid:')
    page.addField( Pv,    'VstbStlPk:')
    page.addField( Lv,    'VFlapLift:')
    page.addField( Dv,    'VFlapDrag:')
    #
    page = PropertyPage( self.nb.ball )
    self.pages['ball'] = page
    page.addField( Mb,    'BallMass :')
    page.addField( Xb,    'BallXloc :')
    page.addField( Yb,    'BallYloc :')
    page.addField( Zb,    'BallZloc :')
    #
    page = PropertyPage( self.nb.prop )
    self.pages['prop'] = page
    page.addField( Mp,    'PropMass :')
    page.addField( Rp,    'PropRadi :')
    page.addField( Ap,    'PropMomt :')
    page.addField( Np,    'PropMinR :')
    page.addField( Xp,    'PropMaxR :')
    page.addField( Ip,    'PropFine :')
    page.addField( Op,    'PropCoar :')
    page.addField( Vp,    'PropCSpd :')
    page.addField( Cp,    'PropCRpm :')
    page.addField( Tp,    'PropTRpm :')
    #
    ## Tix tix for python 3
    if (pythVers < 3):
      self.nb.pack( expand=1, fill=Tix.BOTH, padx=5, pady=5, side=Tix.TOP )
    else :  
      self.nb.pack( expand=1, fill=tix.BOTH, padx=5, pady=5, side=tix.TOP )

    ## Tix tix for python 3
    if (pythVers < 3):
      self.PLOT = Tix.Button(self)
    else :  
      self.PLOT = tix.Button(self)
    self.PLOT['text'] = 'Plot'
    self.PLOT['command'] = self.plotCmd
    self.PLOT.pack({"side": "left"})
    ## Tix tix for python 3
    if (pythVers < 3):
      self.QUIT = Tix.Button(self)
    else :  
      self.QUIT = tix.Button(self)
    self.QUIT['text'] = 'Quit'
    self.QUIT['command'] = self.quitCmd
    self.QUIT.pack({"side": "right"})
    ## Tix tix for python 3
    if (pythVers < 3):
      self.SAVE = Tix.Button(self)
    else :  
      self.SAVE = tix.Button(self)
    self.SAVE['text'] = 'Save'
    self.SAVE['command'] = self.saveCmd
    self.SAVE.pack({"side": "right"})
    ## Tix tix for python 3
    if (pythVers < 3):
      self.RELOAD = Tix.Button(self)
    else :  
      self.RELOAD = tix.Button(self)
    self.RELOAD['text'] = 'ReLoad'
    self.RELOAD['command'] = self.reloadCmd
    self.RELOAD.pack({"side": "right"})
  #
  def plotCmd(self):
    page = self.pages[ self.nb.raised() ]
    page.eval_fields()
    #vblsFromTplt()
    #aCfgFid = yCfgNam + '-tix.txt'
    cfigFromVbls( aCfgFid )
    callPlot( aCfgFid )
  #
  def reloadCmd(self):
    page = self.pages[ self.nb.raised() ]
    ##for k in self.pages.keys():
      ##p = self.pages[k]
      ##print ('p: ', p)
      ##p.eval_fields()
    page.eval_fields()
    #autoFromVbls()
    vblsFromTplt()
    self.update_page()
    self.update()
  #
  def saveCmd(self):
    page = self.pages[ self.nb.raised() ]
    ##for k in self.pages.keys():
      ##p = self.pages[k]
      ##print ('p: ', p)
      ##p.eval_fields()
    page.eval_fields()
    #autoFromVbls()
    cfigFromVbls( yCfgNam + '-save.xml' )
    self.update()
    self.update_page()
  #
  def quitCmd(self):
    if self.after_id:
      self.after_cancel(self.after_id)
    self.quit()
    self.destroy()
  #
  def update_page(self):
    page = self.pages[ self.nb.raised() ]
    page.update_fields()
    self.update()
    ###self.after_id = self.after( 1000, lambda self=self: self.update_page() )
#
def main():
  normArgs(sys.argv[1:])
  ## Tix tix for python 3
  if ( pythVers < 3 ) :
    root = Tix.Tk()  
  else :
    root = tix.Tk()
  vblsFromTplt()
  cfigFromVbls( aCfgFid )
  app = ycTix( root )
  app.mainloop()

if __name__ == '__main__':
  main()

##### ycTixPlot Ends

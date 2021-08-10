#!/usr/bin/env python
#
#### tixyPlot : Tix Menu driven yasim element explorer with yasim - gnuplot displays
#  Python Version
import getopt, os, shlex, subprocess, sys
global pythVers
pythVers = sys.version_info[0]
#print('pythVers:', pythVers)
if (pythVers < 3):
  import Tix
  import Tkinter as tk
else:  
  import tkinter as tk
  from tkinter import tix
from collections import OrderedDict 
from collections import OrderedDict 
##
# default yasim config under test
def normArgs(argv):
  global ycIpFid
  ycIpFid   = 'yasimCfg.xml'
  global ycIpNam
  global ycOpFid
  ycOpFid   = 'ytixOutp.xml'
  global yDatFid
  # template gnuplot spec files for 2, 3 variables plot
  global tpt2Fid
  tpt2Fid   = 'tplt2arg.p'
  global tpt3Fid
  tpt3Fid   = 'tplt3arg.p'
  global vpt2Fid
  vpt2Fid   = 'outp2arg.p'
  global vpt3Fid
  vpt3Fid   = 'outp3arg.p'
  # get yasim config FileID from args
  try:
    opts, args = getopt.getopt(argv, "f:", "file=")
  except getopt.GetoptError:
     print ('sorry, I need -f or file= yasim config  fileID ')
     sys.exit(2)
    #
  for opt, arg in opts:
    if   opt in ("-f", "--file"):
      ycIpFid = arg
      ycIpNam = ycIpFid.find('.')
      ycIpNam = ycIpFid[0:ycIpNam]

##
# Scan template yasim cfig and extract numeric elements, copy for tix menu
#
def vblsFromTplt():
  global ycIpFid
  global ycIpNam
  global tpt2Fid
  global tpt2Fid
  global vpt2Fid
  global vpt3Fid
  global Hy
  global Vy
  global Va
  global Aa
  global Ka
  global Ra
  global Fa
  global Vc
  global Hc
  global Kc
  global Rc
  global Cw
  global Iw
  global Aw
  global Ww
  global Pw
  global Lw
  global Dw
  global Lr
  global Dr
  global Ch
  global Ih
  global Ah
  global Wh
  global Ph
  global Lh
  global Dh
  global Cv
  global Iv
  global Av
  global Wv
  global Pv
  global Lv
  global Dv
#
  global textVa
  global textAa
  global textKa
  global textRa
  global textFa
  global textVc
  global textHc
  global textKc
  global textRc
  global textCw
  global textIw
  global textAw
  global textWw
  global textPw
  global textLw
  global textDw
  global textLr
  global textDr
  global textCh
  global textIh
  global textAh
  global textWh
  global textPh
  global textLh
  global textDh
  global textCv
  global textIv
  global textAv
  global textWv
  global textPv
  global textLv
  global textDv
  global txtZa
  global txtZZa
  global txtZZZa
  global txtZc
  global txtZZc
  global txtZw
  global txtZZw
  global txtZZZw
  global txtZh
  global txtZZh
  global txtZZZh
  global txtZv
  global txtZZv
  global txtZZZv
  global txtZr
#
  apprFlag   = 0
  cruzFlag   = 0
  wingFlag   = 0
  hstabFlag  = 0
  vstabFlag  = 0
#
  Vy = 75
  Hy = 0
  Va = Aa = Ka = Ra = Fa = Vc = Hc = Kc = Rc = 0
  Cw = Iw = Aw = Ww = Pw = Lw = Dw = Lr = Dr = 0
  Ch = Ih = Ah = Wh = Ph = Lh = Dh = Cv = Iv = Av = Wv = Pv = Lv = Dv = 0
#
  ## # open auto yasim config file
  ## ycOpHndl  = open(ycOpFid, 'w', 1)
  # Phase 1 open base yasim config file and parse elements
  with open(ycIpFid, 'r') as ycIp:
  # step each line in template yasim config file
    for line in ycIp:
      # flag on appr section
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
      if '<vstab' in line:
        vstabFlag = 1
      if '</vstab' in line:
        vstabFlag = 0
      ### appr section parse approach speed and AoA elements
      if (apprFlag == 1):
        #in appr section, find elements
        if ('approach speed' in line):
          # make an index list of double quotes in the line
          sepsList = []
          sepsChar = '"'
          lastIndx = 0
          while (lastIndx > -1):
            sepsIndx = line.find( sepsChar, (lastIndx +1))
            if (sepsIndx > 0) :
              sepsList.append(sepsIndx)
            lastIndx = sepsIndx
          # Use index list to split line into text and numbers
          textVa = line[0:(sepsList[0]+1)]
          Va     = float ( (line[(sepsList[0]+1):(sepsList[1])]))
          textAa = line[(sepsList[1]):(sepsList[2]+1)]
          Aa     = float(line[(sepsList[2]+1):(sepsList[3])])
          textKa = line[(sepsList[3]):(sepsList[4]+1)]
          Ka     = float(line[(sepsList[4]+1):(sepsList[5])])
          txtZa  = line[(sepsList[5]):]
          line   = textVa + str(Va) + textAa + str(Aa) + textKa + str(Ka)   \
                 + txtZa
        if ('throttle' in line):
          # make an index list of double quotes in the line
          sepsList = []
          sepsChar = '"'
          lastIndx = 0
          while (lastIndx > -1):
            sepsIndx = line.find( sepsChar, (lastIndx +1))
            if (sepsIndx > 0) :
              sepsList.append(sepsIndx)
            lastIndx = sepsIndx
          # Use index list to split line into text and numbers
          textRa = line[0:(sepsList[2]+1)]
          Ra     = float ( (line[(sepsList[2]+1):(sepsList[3])]))
          txtZZa = line[(sepsList[3]):]
          line   = textRa + str(Ra) + txtZZa
        if ('flaps' in line):
          # make an index list of double quotes in the line
          sepsList = []
          sepsChar = '"'
          lastIndx = 0
          while (lastIndx > -1):
            sepsIndx = line.find( sepsChar, (lastIndx +1))
            if (sepsIndx > 0) :
              sepsList.append(sepsIndx)
            lastIndx = sepsIndx
          # Use index list to split line into text and numbers
          textFa  = line[0:(sepsList[2]+1)]
          Fa      = float ( (line[(sepsList[2]+1):(sepsList[3])]))
          txtZZZa = line[(sepsList[3]):]
          line    = textFa + str(Fa) + txtZZZa
        ###
      ### cruise section parse cruise speed element
      if (cruzFlag == 1):
        #in cruise section, find element
        if ('cruise speed' in line):
          # make an index list of double quotes in the line
          sepsList = []
          sepsChar = '"'
          lastIndx = 0
          while (lastIndx > -1):
            sepsIndx = line.find( sepsChar, (lastIndx +1))
            if (sepsIndx > 0) :
              sepsList.append(sepsIndx)
            lastIndx = sepsIndx
          # Use index list to split line into text and numbers
          textVc = line[0:(sepsList[0]+1)]
          Vc     = float ( (line[(sepsList[0]+1):(sepsList[1])]))
          textHc = line[(sepsList[1]):(sepsList[2]+1)]
          Hc     = float ( (line[(sepsList[2]+1):(sepsList[3])]))
          textKc = line[(sepsList[3]):(sepsList[4]+1)]
          Kc     = float ( (line[(sepsList[4]+1):(sepsList[5])]))
          txtZc  = line[(sepsList[5]):]
          line   = textVc + str(Vc) + textHc + str(Hc) + textKc + str(Kc)   \
                 + txtZc
        if ('throttle' in line):
          # make an index list of double quotes in the line
          sepsList = []
          sepsChar = '"'
          lastIndx = 0
          while (lastIndx > -1):
            sepsIndx = line.find( sepsChar, (lastIndx +1))
            if (sepsIndx > 0) :
              sepsList.append(sepsIndx)
            lastIndx = sepsIndx
          # Use index list to split line into text and numbers
          textRc = line[0:(sepsList[2]+1)]
          Rc     = float ( (line[(sepsList[2]+1):(sepsList[3])]))
          txtZZc = line[(sepsList[3]):]
          line   = textRc + str(Rc) + txtZZc
        ###
      ### wing section parse camber and induced drag elements
      # Be Sure length, chord ... camber, idrag elements are on a single line
      if (wingFlag == 1):
        #in wing section, find elements
        if ('camber' in line):
          # make an index list of double quotes in the line
          sepsList = []
          sepsChar = '"'
          lastIndx = 0
          while (lastIndx > -1):
            sepsIndx = line.find( sepsChar, (lastIndx +1))
            if (sepsIndx > 0) :
              sepsList.append(sepsIndx)
            lastIndx = sepsIndx
          # Use index list to split line into text and numbers
          print(line)
          textCw = line[0:(sepsList[8]+1)]
          Cw     = float ( (line[(sepsList[8]+1):(sepsList[9])]))
          textIw = line[(sepsList[9]):(sepsList[10]+1)]
          Iw     = float(line[(sepsList[10]+1):(sepsList[11])])
          txtZw  = line[(sepsList[11]):]
          # overwrite line with substituted elements
          line   = textCw + str(Cw) + textIw + str(Iw) + txtZw
        ###
        #in wing section, find stall elements
        if ('stall' in line):
          # make an index list of double quotes in the line
          sepsList = []
          sepsChar = '"'
          lastIndx = 0
          while (lastIndx > -1):
            sepsIndx = line.find( sepsChar, (lastIndx +1))
            if (sepsIndx > 0) :
              sepsList.append(sepsIndx)
            lastIndx = sepsIndx
          # Use index list to split line into text and numbers
          textAw = line[0:(sepsList[0]+1)]
          Aw     = float ( (line[(sepsList[0]+1):(sepsList[1])]))
          textWw = line[(sepsList[1]):(sepsList[2]+1)]
          Ww     = float(line[(sepsList[2]+1):(sepsList[3])])
          textPw = line[(sepsList[3]):(sepsList[4]+1)]
          Pw     = float(line[(sepsList[4]+1):(sepsList[5])])
          txtZZw = line[(sepsList[5]):]
          line   = textAw + str(Aw) + textWw + str(Ww) + textPw + str(Pw)  \
                 + txtZZw
        ###
        #in wing section, find flap0 elements
        if ('flap0' in line):
          # make an index list of double quotes in the line
          sepsList = []
          sepsChar = '"'
          lastIndx = 0
          while (lastIndx > -1):
            sepsIndx = line.find( sepsChar, (lastIndx +1))
            if (sepsIndx > 0) :
              sepsList.append(sepsIndx)
            lastIndx = sepsIndx
          # Use index list to split line into text and numbers
          textLw = line[0:(sepsList[4]+1)]
          Lw     = float ( (line[(sepsList[4]+1):(sepsList[5])]))
          textDw = line[(sepsList[5]):(sepsList[6]+1)]
          Dw     = float( line[(sepsList[6]+1):(sepsList[7])])
          txtZZZw = line[(sepsList[7]):]
          line    = textLw + str(Lw) + textDw + str(Dw) + txtZZZw
        if ('flap1' in line):
          # make an index list of double quotes in the line
          sepsList = []
          sepsChar = '"'
          lastIndx = 0
          while (lastIndx > -1):
            sepsIndx = line.find( sepsChar, (lastIndx +1))
            if (sepsIndx > 0) :
              sepsList.append(sepsIndx)
            lastIndx = sepsIndx
          # Use index list to split line into text and numbers
          textLr = line[0:(sepsList[4]+1)]
          Lr     = float ( (line[(sepsList[4]+1):(sepsList[5])]))
          textDr = line[(sepsList[5]):(sepsList[6]+1)]
          Dr     = float( line[(sepsList[6]+1):(sepsList[7])])
          txtZr  = line[(sepsList[7]):]
          line    = textLr + str(Lr) + textDr + str(Dr) + txtZr
      ### hstab section parse camber, idrag, stall and flap0 elements
      if (hstabFlag == 1):
        ### hstab section parse camber and induced drag elements if present
        #    If camber element is present then idrag dflt 1 must be present
        # Be Sure length,chord...camber, idrag are in order on a single line
        if ('camber' in line):
          # make an index list of double quotes in the line
          sepsList = []
          sepsChar = '"'
          lastIndx = 0
          while (lastIndx > -1):
            sepsIndx = line.find( sepsChar, (lastIndx +1))
            if (sepsIndx > 0) :
              sepsList.append(sepsIndx)
            lastIndx = sepsIndx
          # Use index list to split line into text and numbers
          textCh = line[0:(sepsList[8]+1)]
          Ch     = float ( (line[(sepsList[8]+1):(sepsList[9])]))
          textIh = line[(sepsList[9]):(sepsList[10]+1)]
          Ih     = float(line[(sepsList[10]+1):(sepsList[11])])
          txtZh  = line[(sepsList[11]):]
          # overwrite line with substituted elements
          line   = textCh + str(Ch) + textIh + str(Ih) + txtZh
        else:
          # camber is not specified so deflt values to satisfy menu
          Ch = 0
          Ih = 1
        #in hstab section, find stall elements
        if ('stall' in line):
          # make an index list of double quotes in the line
          sepsList = []
          sepsChar = '"'
          lastIndx = 0
          while (lastIndx > -1):
            sepsIndx = line.find( sepsChar, (lastIndx +1))
            if (sepsIndx > 0) :
              sepsList.append(sepsIndx)
            lastIndx = sepsIndx
          # Use index list to split line into text and numbers
          textAh = line[0:(sepsList[0]+1)]
          Ah     = float ( (line[(sepsList[0]+1):(sepsList[1])]))
          textWh = line[(sepsList[1]):(sepsList[2]+1)]
          Wh     = float(line[(sepsList[2]+1):(sepsList[3])])
          textPh = line[(sepsList[3]):(sepsList[4]+1)]
          Ph     = float(line[(sepsList[4]+1):(sepsList[5])])
          txtZZh = line[(sepsList[5]):]
          line   = textAh + str(Ah) + textWh + str(Wh) + textPh + str(Ph)    \
                 + txtZZh
        #in hstab section, find flap0 elements
        if ('flap0' in line):
          # make an index list of double quotes in the line
          sepsList = []
          sepsChar = '"'
          lastIndx = 0
          while (lastIndx > -1):
            sepsIndx = line.find( sepsChar, (lastIndx +1))
            if (sepsIndx > 0) :
              sepsList.append(sepsIndx)
            lastIndx = sepsIndx
          # Use index list to split line into text and numbers
          textLh = line[0:(sepsList[4]+1)]
          Lh     = float ( (line[(sepsList[4]+1):(sepsList[5])]))
          textDh = line[(sepsList[5]):(sepsList[6]+1)]
          Dh     = float( line[(sepsList[6]+1):(sepsList[7])])
          txtZZZh = line[(sepsList[7]):]
          line   = textLh + str( Lh) + textDh + str(Dh) + txtZZZh
      ### vstab section parse camber, idrag, stall and flap0 elements
      if (vstabFlag == 1):
        ### vstab section parse camber and induced drag elements if present
        #    If camber element is present then idrag dflt 1 must be present
        # Be Sure length,chord...camber, idrag are in order on a single line
        if ('camber' in line):
          # make an index list of double quotes in the line
          sepsList = []
          sepsChar = '"'
          lastIndx = 0
          while (lastIndx > -1):
            sepsIndx = line.find( sepsChar, (lastIndx +1))
            if (sepsIndx > 0) :
              sepsList.append(sepsIndx)
            lastIndx = sepsIndx
          # Use index list to split line into text and numbers
          textCv = line[0:(sepsList[8]+1)]
          Cv     = float ( (line[(sepsList[8]+1):(sepsList[9])]))
          textIv = line[(sepsList[9]):(sepsList[10]+1)]
          Iv     = float(line[(sepsList[10]+1):(sepsList[11])])
          txtZv  = line[(sepsList[11]):]
          # overwrite line with substituted elements
          line   = textCv + str(Cv) + textIv + str(Iv) + txtZv
        else:
          # camber is not specified so deflt values to satisfy menu
          Cv = 0
          Iv = 1
        #in vstab section, find stall elements
        if ('stall' in line):
          # make an index list of double quotes in the line
          sepsList = []
          sepsChar = '"'
          lastIndx = 0
          while (lastIndx > -1):
            sepsIndx = line.find( sepsChar, (lastIndx +1))
            if (sepsIndx > 0) :
              sepsList.append(sepsIndx)
            lastIndx = sepsIndx
          # Use index list to split line into text and numbers
          textAv = line[0:(sepsList[0]+1)]
          Av     = float ( (line[(sepsList[0]+1):(sepsList[1])]))
          textWv = line[(sepsList[1]):(sepsList[2]+1)]
          Wv     = float(line[(sepsList[2]+1):(sepsList[3])])
          textPv = line[(sepsList[3]):(sepsList[4]+1)]
          Ph     = float(line[(sepsList[4]+1):(sepsList[5])])
          txtZZv  = line[(sepsList[5]):]
          line   = textAv + str(Av) + textWv + str(Wv) + textPv + str(Pv)    \
                 + txtZZv
        #in vstab section, find flap0 elements
        if ('flap0' in line):
          # make an index list of double quotes in the line
          sepsList = []
          sepsChar = '"'
          lastIndx = 0
          while (lastIndx > -1):
            sepsIndx = line.find( sepsChar, (lastIndx +1))
            if (sepsIndx > 0) :
              sepsList.append(sepsIndx)
            lastIndx = sepsIndx
          # Use index list to split line into text and numbers
          textLv = line[0:(sepsList[4]+1)]
          Lv     = float ( (line[(sepsList[4]+1):(sepsList[5])]))
          textDv = line[(sepsList[5]):(sepsList[6]+1)]
          Dv     = float( line[(sepsList[6]+1):(sepsList[7])])
          txtZZZv = line[(sepsList[7]):]
          line   = textLv + str( Lv) + textDv + str(Dv) + txtZZZv
  #close and sync file
    ycIp.flush
    os.fsync(ycIp.fileno())
  ycIp.close
##
# After tix menu changes, create temp yasim config file woth new elements
#
def autoFromVbls():
  global ycIpFid
  global ycIpNam
  global ycOpFid
  global yDatFid
  global tpt2Fid
  global tpt2Fid
  global vpt2Fid
  global vpt3Fid
  global Va
  global Aa
  global Ka
  global Ra
  global Fa
  global Vc
  global Hc
  global Kc
  global Rc
  global Cw
  global Iw
  global Aw
  global Ww
  global Pw
  global Lw
  global Dw
  global Lr
  global Dr
  global Ch
  global Ih
  global Ah
  global Wh
  global Ph
  global Lh
  global Dh
  global Cv
  global Iv
  global Av
  global Wv
  global Pv
  global Lv
  global Dv
#
  global textVa
  global textAa
  global textKa
  global textRa
  global textFa
  global textVc
  global textHc
  global textKc
  global textRc
  global textCw
  global textIw
  global textAw
  global textWw
  global textPw
  global textLw
  global textDw
  global textLr
  global textDr
  global textCh
  global textIh
  global textAh
  global textWh
  global textPh
  global textLh
  global textDh
  global textCv
  global textIv
  global textAv
  global textWv
  global textPv
  global textLv
  global textDv
  global txtZa
  global txtZZa
  global txtZZZa
  global txtZc
  global txtZZc
  global txtZw
  global txtZZw
  global txtZZZw
  global txtZh
  global txtZZh
  global txtZZZh
  global txtZv
  global txtZZv
  global txtZZZv
  global txtZr
#
  apprFlag   = 0
  cruzFlag   = 0
  wingFlag   = 0
  hstabFlag  = 0
  vstabFlag  = 0
  ycOpFid  = ycIpNam + '-tix.xml'
  yDatFid  = ycIpNam + '-tix.txt'
  ## # open auto yasim config file
  ycOpHndl  = open(ycOpFid, 'w', 1)
  # Phase 3 write auto file via yconfig template and subsVbls from Tix
  with open(ycIpFid, 'r') as ycIp:
  # step each line in template yasim config file
    for line in ycIp:
      # flag on appr section
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
      if '<vstab' in line:
        vstabFlag = 1
      if '</vstab' in line:
        vstabFlag = 0
      ### in each section write saved text fields and updated element values
      if (apprFlag == 1):
        if ('approach speed' in line):
          line   = textVa + str(Va) + textAa + str(Aa) + textKa + str(Ka)   \
                 + txtZa
        if ('throttle' in line):
          line   = textRa + str(Ra) + txtZZa
        if ('flaps' in line):
          line    = textFa + str(Fa) + txtZZZa
      if (cruzFlag == 1):
        if ('cruise speed' in line):
          line   = textVc + str(Vc) + textHc + str(Hc) + textKc + str(Kc)   \
                 + txtZc
        if ('throttle' in line):
          line   = textRc + str(Rc) + txtZZc
      if (wingFlag == 1):
        if ('camber' in line):
          line   = textCw + str(Cw) + textIw + str(Iw) + txtZw
        if ('stall' in line):
          line   = textAw + str(Aw) + textWw + str(Ww) + textPw + str(Pw)  \
                 + txtZZw
        if ('flap0' in line):
          line    = textLw + str(Lw) + textDw + str(Dw) + txtZZZw
        if ('flap1' in line):
          line    = textLr + str(Lr) + textDr + str(Dr) + txtZr
      if (hstabFlag == 1):
        if ('camber' in line):
          line   = textCh + str(Ch) + textIh + str(Ih) + txtZh
        if ('stall' in line):
          line   = textAh + str(Ah) + textWh + str(Wh) + textPh + str(Ph)    \
                 + txtZZh
        if ('flap0' in line):
          line   = textLh + str( Lh) + textDh + str(Dh) + txtZZZh
      if (vstabFlag == 1):
        if ('camber' in line):
          line   = textCv + str(Cv) + textIv + str(Iv) + txtZv
        if ('stall' in line):
          line   = textAv + str(Av) + textWv + str(Wv) + textPv + str(Pv)    \
                 + txtZZv
        if ('flap0' in line):
          line   = textLv + str( Lv) + textDv + str(Dv) + txtZZZv
      # Write unchanged/modified line into auto.xml
      ycOpHndl.write(line)
    #close and sync files
    ycOpHndl.flush
    os.fsync(ycOpHndl.fileno())
    ycOpHndl.close
    ycIp.flush
    os.fsync(ycIp.fileno())
  ycIp.close

  ## auto create 2 vble gnuplot config file
  apltHndl  = open(vpt2Fid, 'w', 1)
  with open(tpt2Fid, 'r') as tplt:
    plotFlag = 0
    for line in tplt:
      # set flag near end when 'plot' string is found
      if (' plot ' in line ): plotFlag = 1
      # find the title line in template config
      if ('set title' in line):
          #create title using parsed / substituted values
          line = ' set title "'+ 'A:'   + str(Va) + ' ' + str(Aa)             \
            + ' '     + str(Ka) + ' ' + str(Ra) + ' ' + str(Fa)               \
            + ' C:'  + str(Vc) + ' ' + str(Hc) + ' ' + str(Kc) + ' '          \
            + str(Rc) + '\\nW:' + str(Cw) + ' ' + str(Iw) + ' ' + str(Aw)     \
            + ' ' + str(Ww) + ' ' + str(Pw) + ' ' + str(Lw) + ' ' + str(Dw)   \
            + ' ' + str(Lr) + ' ' + str(Dr)                                   \
            + '\\nH:' + str(Ch) + ' ' + str(Ih) + ' ' + str(Ah)               \
            + ' ' + str(Wh) + ' ' + str(Ph) + ' '   + str(Lh) + ' ' + str(Dh) \
            + '\\nV:' + str(Cv) + ' ' + str(Iv) + ' ' + str(Av)               \
            + ' ' + str(Wv) + ' ' + str(Pv) + ' '   + str(Lv) + ' ' + str(Dv) \
            + ' At:'+ str(Vy) + ' ' + str(Hy) + '" \n'
      if ( plotFlag < 1):
        # Write line into auto.xml
        apltHndl.write(line)
    # At EOF append plot lines with proper data file name
    line = ' plot "' + yDatFid +'" every ::155::210 using '            \
         + '1:2 with lines title \'lift\', \\\n'
    apltHndl.write(line)
    line = '      "' + yDatFid +'" every ::155::210 using '            \
         + '1:3 with lines title \'drag\''
    apltHndl.write(line)
    apltHndl.close
  #  tplt.flush
  #  os.fsync(tplt.fileno())
    tplt.close
  #
  ## auto create 3 vble gnuplot config file
  apltHndl  = open(vpt3Fid, 'w', 1)
  with open(tpt2Fid, 'r') as tplt:
    plotFlag = 0
    for line in tplt:
      # set flag near end when 'plot' string is found
      if (' plot ' in line ): plotFlag = 1
      # find the title line in template config
      if ('set title' in line):
          #create title using parsed / substituted values
          line = ' set title "'+ 'A:'   + str(Va) + ' ' + str(Aa)             \
            + ' '     + str(Ka) + ' ' + str(Ra) + ' ' + str(Fa)               \
            + ' C:'  + str(Vc) + ' ' + str(Hc) + ' ' + str(Kc) + ' '          \
            + str(Rc) + '\\nW:' + str(Cw) + ' ' + str(Iw) + ' ' + str(Aw)     \
            + ' ' + str(Ww) + ' ' + str(Pw) + ' ' + str(Lw) + ' ' + str(Dw)   \
            + ' ' + str(Lr) + ' ' + str(Dr)                                   \
            + '\\nH:' + str(Ch) + ' ' + str(Ih) + ' ' + str(Ah)               \
            + ' ' + str(Wh) + ' ' + str(Ph) + ' '   + str(Lh) + ' ' + str(Dh) \
            + '\\nV:' + str(Cv) + ' ' + str(Iv) + ' ' + str(Av)               \
            + ' ' + str(Wv) + ' ' + str(Pv) + ' '   + str(Lv) + ' ' + str(Dv) \
            + ' At:'+ str(Vy) + ' ' + str(Hy) + '" \n'
      if ( plotFlag < 1):
        # Write line into auto.xml
        apltHndl.write(line)
    # At EOF append plot lines with proper data file name
    line = ' plot "' + yDatFid +'" every ::155::210 using '            \
         + '1:2 with lines title \'lift\', \\\n'
    apltHndl.write(line)
    line = '      "' + yDatFid +'" every ::155::210 using '            \
         + '1:3 with lines title \'drag\', \\\n'
    apltHndl.write(line)
    line = '      "' + yDatFid +'" every ::155::210 using '             \
         + '1:4 with lines title \'L-D\''
    apltHndl.write(line)
    apltHndl.close
  #  tplt.flush
  #  os.fsync(tplt.fileno())
    tplt.close

##
# Call yasim data and gnuplot with auto-created config and plot spec files
def callPlot():
  global ycOpFid
  global yDatFid
  global Vy
  global Hy
  # run yasim external process to show console output
  command_line = 'yasim ' + ycOpFid + ' -a ' + str(Hy) + ' -s ' + str(Vy)
  args = shlex.split(command_line)
  p = subprocess.Popen(args)
  p.communicate()
  p.wait()
  #
  ## # run yasim external process for saved dataset file
  ## yDatFid = ycIpNam + '.dat'
  ## yDatHndl = open(yDatFid, 'w')
  ## command_line = "yasim auto.xml -g "
  ## args = shlex.split(command_line)
  ## p = subprocess.Popen(args, stdout=yDatHndl)
  ## #yDatHndl.flush
  ## #os.fsync(yDatHndl.fileno())
  ## yDatHndl.close
  ## p.wait()
  #
  # run yasim external process to create auto dataset
  yDatHndl = open(yDatFid, 'w')
  command_line = 'yasim ' + ycOpFid + ' -g -a ' + str(Hy) + ' -s ' + str(Vy)
  args = shlex.split(command_line)
  p = subprocess.Popen(args, stdout=yDatHndl)
  #yDatHndl.flush
  #os.fsync(yDatHndl.fileno())
  yDatHndl.close()
  p.wait()
  #
  # run gnuplot with 2 vble command file to plot dataset
  command_line = "gnuplot -p " + vpt2Fid
  args = shlex.split(command_line)
  DEVNULL = open(os.devnull, 'wb')
  p = subprocess.Popen(args, stdout=DEVNULL, stderr=DEVNULL)
  p.communicate()
  DEVNULL.close()
  #
  # run gnuplot with 3 vble command file to plot dataset
  command_line = "gnuplot -p " + vpt3Fid
  args = shlex.split(command_line)
  DEVNULL = open(os.devnull, 'wb')
  p = subprocess.Popen(args, stdout=DEVNULL, stderr=DEVNULL)
  p.communicate()
  DEVNULL.close()
#

##
# Tix Interface Menu #
##
class PropertyField:
  def __init__(self, parent, prop, label):
    self.prop = prop
    self.field = tix.LabelEntry( parent, label=label,
       options='''
       label.width 12
       label.anchor e
       entry.width 12
       ''' )
    self.field.pack( side=tix.TOP, padx=8, pady=2 )

  # Pull numeric vals from menu entries and store into variables
  def eval_field(self):
    global Vy
    global Hy
    global Va
    global Aa
    global Ka
    global Ra
    global Fa
    global Vc
    global Hc
    global Kc
    global Rc
    global Cw
    global Iw
    global Aw
    global Ww
    global Pw
    global Lw
    global Dw
    global Lr
    global Dr
    global Ch
    global Ih
    global Ah
    global Wh
    global Ph
    global Lh
    global Dv
    global Cv
    global Iv
    global Av
    global Wv
    global Pv
    global Lv
    global Dv
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
    if 'WFlapLift'  in lbl: Lw = val
    if 'WFlapDrag'  in lbl: Dw = val
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

  def update_field(self):
    val = self.prop
    self.field.entry.delete(0,'end')
    self.field.entry.insert(0, val)

class PropertyPage(tix.Frame):
  def __init__(self,parent):
    tix.Frame.__init__(self,parent)
    #self.fgfs = fgfs
    self.pack( side=tix.TOP, padx=2, pady=2, fill=tix.BOTH, expand=1 )
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
      tix.Frame.update(self)

class ycTix(tix.Frame):
  def __init__(self,root=None):
    tix.Frame.__init__(self,root)
    z = root.winfo_toplevel()
    z.wm_protocol("WM_DELETE_WINDOW", lambda self=self: self.quitcmd())
    #self.fgfs = fgfs
    self.pack()
    self.pages = {}
    self.after_id = None
    self.createWidgets()
    self.update()

  def createWidgets(self):
    self.nb = tix.NoteBook(self)
    self.nb.add( 'appr', label='APPR',
           raisecmd= lambda self=self: self.update_page() )
    self.nb.add( 'cruz', label='CRUISE',
           raisecmd= lambda self=self: self.update_page() )
    self.nb.add( 'wing', label='WING',
           raisecmd= lambda self=self: self.update_page() )
    self.nb.add( 'hstb', label='HSTAB',
           raisecmd= lambda self=self: self.update_page() )
    self.nb.add( 'vstb', label='VSTAB',
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
    page.addField( Lw,    'WFlapLift:')
    page.addField( Dw,    'WFlapDrag:')
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
    self.nb.pack( expand=1, fill=tix.BOTH, padx=5, pady=5, side=tix.TOP )
    #
    self.QUIT = tix.Button(self)
    self.QUIT['text'] = 'Quit'
    self.QUIT['command'] = self.quitCmd
    self.QUIT.pack({"side": "right"})
    #
    self.PLOT = tix.Button(self)
    self.PLOT['text'] = 'Solve'
    self.PLOT['command'] = self.plotCmd
    self.PLOT.pack({"side": "left"})
  #
  def plotCmd(self):
    page = self.pages[ self.nb.raised() ]
    ##for k in self.pages.keys():
      ##p = self.pages[k]
      ##print ('p: ', p)
      ##p.eval_fields()
    page.eval_fields()
    autoFromVbls()
    callPlot()
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
  root = tix.Tk()
  vblsFromTplt()
  app = ycTix( root )
  app.mainloop()

if __name__ == '__main__':
  main()

##### ycTixPlot Ends

#!/usr/bin/env python
#
### autoPlot.py : Auto run yasim plots stepping wing/hstab elements
##
##  order of elements in yasimCfg.xml <wing> and <hstab> must be e.g:
##     <stall aoa="15" width="18.0" peak="1.5"/>
##     <flap0 start="0.00" end="0.54" lift="1.1" drag="1.7"/>
##
###
import getopt, os, shlex, subprocess, sys
##
#  Python Version
global pythVers
pythVers = sys.version_info[0]
#print('pythVers:', pythVers)
if (pythVers < 3):
  import xml.etree.ElementTree as ET
else:  
  import xml.etree.ElementTree as ET
  #from lxml import html
  import requests
#
##

#  Set Defaults and parse cummand args 
def normArgs(argv):
  ##
  global yCfgFID, yCfgName, yCfgUrl, todo
  # file for input 
  yCfgFID  = 'bc18/model18-yasim-h.xml'
  yCfgName = 'model18-yasim-h.xml'
  yCfgUrl  = 'https://sourceforge.net/p/flightgear/fgaddon/HEAD/tree/trunk/Aircraft/14bis/14bis-yasim.xml'
  ## 
  # get options
  try: 
    opts, args = getopt.getopt(argv, "f:p:u:", ["file=", "path=", "url="])
  except getopt.GetoptError:
     print ('sorry, args: ', args, '  opts: ', opts, '   do not make sense ')
     sys.exit(2)
  #
  #
  todo = 'todoFile' 
  for opt, arg in opts:
    if   opt in ("-f", "--file"):
      todo = 'todoFile' 
      yCfgFID = arg
      #yCfgNam = yCfgFID.find('.xml')
      #yCfgNam = yCfgFID[0:yCfgNam]
  #
    if   opt in ("-u", "--url"):
      todo = 'todoUrl' 
      yCfgUrl = arg
  #
    if   opt in ("-p", "--path"):
      print('--path: noOp')
      
  #yCfgNam = yCfgFid.find('.xml')
  #yCfgNam = yCfgFid[0:yCfgNam]
  #
  yCfgName = yCfgFID
  lastSlsh = yCfgName.rfind('/')
  if ( lastSlsh > 0 ) :
    yCfgName = yCfgName[(lastSlsh +1):] 
      
##

def scanYCfg():
  global yCfgFID, yCfgName, yCfgUrl, todo
  #
  currStep   = 0
  # open base yasim config file
  with open(yCfgFID, 'r') as yCfg:
    # step each line in template yasim config file
    for line in yCfg:
      currStep += 1
      print ('Step: ', currStep , 'Line: ', line)
    # done with step
  # done with open(yCfgFID, 'r')
  yCfg.close
##

def wingAoa( Mx, Mz, Tx, Tz ) :  
  import math, numpy
  #
  Gx = Mx - Tx
  Gz = Mz - Tz
  # fiddle if wheels same distance on CL
  if ( Gz == 0 ) : Gz += 0.000001
  Ex = (Tz * Gx) / Gz
  Aoa = -1 * numpy.arctan ( Mz / ( Ex + Gx ) )
  Aoa = math.degrees ( Aoa ) 
  #
  return(Aoa)
  
def xetrYCfg():
  global yCfgFID, yCfgName, yCfgUrl, todo
  #
  if ( todo == 'todoFile' ) :
    tree = ET.parse(yCfgFID)
  if  ( todo == 'todoUrl' ) :
    resp = requests.get(yCfgUrl)
    tree = ET.parse(resp.content)
  root = tree.getroot()
  x1 = y1 = z1 = x2 = y2 = z2 = 0
  # one of the wheels is both the same 
  for gearElem in root.iter('gear') :
    xVal = float(gearElem.get('x'))
    yVal = float(gearElem.get('y'))
    zVal = float(gearElem.get('z'))
    if (( x1 == 0 ) & ( z1 == 0 )) :
      #print('0 xv: ', xVal, ' yv: ', yVal, 'zv: ', zVal )
      # found first wheel element
      x1 = xVal
      y1 = yVal
      z1 = zVal
      #print('1 x1: ', x1, ' y1: ', y1, 'z1: ', z1, 'x2: ', x2, 'z2: ', z2 )
    else :
      x2 = xVal
      y2 = yVal
      z2 = zVal
      # next wheel 
      if (( x2 != x1 ) & ( y2 != y1 )) :
        if (( x2 == 0 ) & ( z2 == 0 )) :
          x2 = xVal
          y2 = yVal
          z2 = zVal
  #  print('2 x1: ', x1, ' y1: ', y1, 'z1: ', z1, 'x2: ', x2, ' y2: ', y2, ' z2: ', z2 )
  if  ( z1 <= z2 ) :
    clinInci = wingAoa(x1, z1, x2, z2 )
  else:   
    clinInci = wingAoa(x2, z2, x1, z1 )
  wingInci = wingAoaS = 0
  wingElem = root.find('wing')
  if ( wingElem.get('incidence') != None ) :
    wingInci = float(wingElem.get('incidence'))
  if ( wingElem.find('stall') != None ) :
    wingAoaS = float(wingElem.find('stall').get('aoa'))
  totlInci = clinInci + wingInci
  fracInci = totlInci / wingAoaS
  print ( '{:s}   CL incidence: {:.3f}  Wing incidence: {:.3f}  Total Incidence : {:.3f}  \
  Wing AoaStall: {:.3f}   % Margin: {:.3f} ' \
  .format( yCfgName, clinInci, wingInci, totlInci, wingAoaS, (100 * ( 1 - fracInci))))
##

def main():
  global yCfgFID
  normArgs(sys.argv[1:])
  #scanYCfg()
  xetrYCfg()
##

if __name__ == '__main__':
  main()

### yCfgArgs Ends

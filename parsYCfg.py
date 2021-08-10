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
#
##

#  Set Defaults and parse cummand args 
def normArgs(argv):
  ##
  global skelFID
  # file for input 
  skelFID = 'bc18/model18-yasim-h.xml'
  ## 
  # get options
  try: 
    opts, args = getopt.getopt(argv, "f:p:", ["file=", "path="])
  except getopt.GetoptError:
     print ('sorry, args: ', args, '  opts: ', opts, '   do not make sense ')
     sys.exit(2)
  #
  #
  for opt, arg in opts:
    if   opt in ("-f", "--file"):
      skelFID = arg
      skelNam = skelFID.find('.xml')
      #skelNam = skelFID[0:skelNam]
  #
  for opt, arg in opts:
    if   opt in ("-p", "--path"):
      print('--path: noOp')
##

def scanSkel():
  global skelFID
#
  currStep   = 0
  # open base yasim config file
  with open(skelFID, 'r') as skel:
    # step each line in template yasim config file
    for line in skel:
      currStep += 1
      print ('Step: ', currStep , 'Line: ', line)
    # done with step
  # done with open(skelFID, 'r')
  skel.close
##

def wingAoa( Mx, Mz, Tx, Tz ) :  
 import math, numpy
 #
 Gx = Mx - Tx
 Ex = (Tz * Gx) / (Mz - Tz) 
 Aoa = -1 * numpy.arctan ( Mz / ( Ex + Gx ) )
 Aoa = math.degrees ( Aoa ) 
 #
 return(Aoa)
  
def xetrSkel():
  global skelFID
#
  tree = ET.parse(skelFID)
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
  print('x1: ', x1, 'z1: ', z1, 'x2: ', x2, 'z2: ', z2 )
  if  ( z1 <= z2 ) :
    clinInci = wingAoa(x1, z1, x2, z2 )
  else:   
    clinInci = wingAoa(x2, z2, x1, z1 )
  wingInci = 0
  wingElem = root.find('wing')
  if ( wingElem.get('incidence') != None ) :
    wingInci = float(wingElem.get('incidence'))
  totlInci = clinInci + wingInci
  print ( 'CL incidence: ', clinInci, \
          '  wing incidence: ', wingInci, \
          ' Total : ', totlInci )

    
    
#;#

def main():
  global skelFID
  normArgs(sys.argv[1:])
  #scanSkel()
  xetrSkel()
##

if __name__ == '__main__':
  main()

### skelArgs Ends

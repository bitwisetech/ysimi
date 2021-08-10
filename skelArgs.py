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
  from collections import OrderedDict 
else:  
  from collections import OrderedDict 
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

def scanskel():
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

def main():
  global skelFID
  normArgs(sys.argv[1:])
  scanskel()
##

if __name__ == '__main__':
  main()

### skelArgs Ends

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
  import Tix
  import Tkinter as tk
else:  
  import tkinter as tk
  from tkinter import tix
#
from collections import OrderedDict 
##

#  Set Defaults and parse cummand args 
def normArgs(argv):
  # range of steps for element increments must be integers
  # Columns stepping [ Start End+1, Step] element 'A'
  # Rows    stepping [ Start End+1, Step] element 'B'
  global colsLgnd, colsRnge,rowsLgnd, rowsRnge
  ## bc18 
  #Cols: Appr aoa  
  colsLgnd = 'Aa'
  colsRnge = range(8, 13, 4 )
  #Rows: Appr Spd
  rowsLgnd = 'Va'
  rowsRnge = range(75, 86, 5 )
  ##
  global yCfgNam, yCfgFid, dataFid, aCfgFid, atptFid, tpltFid
  # yasim config xml file read input 
  yCfgFid   = 'multi-YCfg.xml'
  # AutoCFig are output yasim config files with element(s) modified 
  aCfgFid   = 'multi-ACfg.xml'
  #
  dataFid = "multi-outp-yGen.txt"
  #
  # Template gnuplot spec files for 2, 3 variables plot
  global tpt2Fid, atp2Fid, tpt3Fid, atp3Fid
  # 
  ## 2-Arg plot hacked to do single L/D plotis 
  # template p is the base gnuplot command file
  tpltFid    = 'multi-ldld-spec.p'
  # atp      p is retitled gnuplot command file
  atptFid    = 'multi-outp-spec.p'
  ## 
  # get yasim config FileID from args
  try: 
    opts, args = getopt.getopt(argv, "f:p:", ["file=", "plot="])
  except getopt.GetoptError:
     print ('sorry, args: ', args, '  opts: ', opts, '   do not make sense ')
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
        tpltFid  = 'multi-l-spec.p'
      if (( arg == 'd') or (arg == 'D'  )) :
        tpltFid  = 'multi-d-spec.p'
      if (( arg == 'l') or (arg == 'L'  )) :
        tpltFid  = 'multi-l-spec.p'
      if (( arg == 'ld') or (arg == 'LD')) :
        tpltFid  = 'multi-ld-spec.p'
      # defaults to l, d, l/d spec  
  ##

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


def scanYCfg():
  global colsLgnd, colsRnge,rowsLgnd, rowsRnge

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
  # open base yasim config file
  with open(yCfgFid, 'r') as ycfg:
    # step each line in template yasim config file
    for line in ycfg:
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
      # propFlag
    # with line  
  # done with input yCfg
  ycfg.close

def stepACfg() :
  #
  global colsLgnd, colsRnge,rowsLgnd, rowsRnge
  global ycIpFid, ycIpNam, ycOpFid
  global spc2Fid, spc3Fid, vbl2Fid, vbl3Fid
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
  # for each element varied: open YCfg, mod/write to ACfg
  for colsStep in colsRnge:
    for rowsStep in rowsRnge:
      # open auto yasim config file
      aCfgHndl  = open(aCfgFid, 'w', 1)
      #print('rowsStep, colsStep1')
      # actual element value to be substitued on each run
      subsColV    = float(colsStep)
      # actual element value to be substitued on each run
      subsRowV    = float(rowsStep)
      # open base yasim config file
      with open(yCfgFid, 'r') as ycfg:
        for line in ycfg:
          # These flags indicate parsing has detected various sections of yasim config 
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
            ### Element Substitution: uncomment whichever is desired
            # 
            if 'Aa' in colsLgnd: Aa = subsColV
            if 'Aa' in rowsLgnd: Aa = subsRowV
            if 'Va' in colsLgnd: Va = subsColV
            if 'Va' in rowsLgnd: Va = subsRowV
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
            ### Element Substitution: uncomment whichever is desired
            # 
            if 'Vc' in colsLgnd: Vc = subsColV
            if 'Vc' in rowsLgnd: Vc = subsRowV
            if 'Hc' in colsLgnd: Hc = subsColV
            if 'Hc' in rowsLgnd: Hc = subsRowV
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
      # done with input yCfg lines
      ycfg.close
      #close and sync
      aCfgHndl.flush
      os.fsync(aCfgHndl.fileno())
      aCfgHndl.close
      # autoCfig with substituted vales done, call the plot
      aCfgPlot( colsStep, rowsStep )

def aCfgPlot( colsStep, rowsStep ) :
  ## auto create gnuplot config file
  apltHndl  = open(atptFid, 'w', 1)
  with open(tpltFid, 'r') as tplt:
    for line in tplt:
      # find the title line in template config
      if (line.find('set title') > 0):
          #create title using parsed / substituted values
          line = ' set title "' + colsLgnd + ': ' + str(colsStep)    \
                          + ' ' + rowsLgnd + ': ' + str(rowsStep) + '" \n'
      #print(line)
      # Write unchanged/modified line into auto.xml
      apltHndl.write(line)
  #  apltHndl.flush
  #  os.fsync(apltHndl.fileno())
    apltHndl.close
  #  tplt.flush
  #  os.fsync(tplt.fileno())
    tplt.close
  # print (rowsStep, colsStep)
  if 0 :
    # run yasim external process to show console output
    command_line = 'yasim ' + aCfgFid
    args = shlex.split(command_line)
    #print args
    p = subprocess.run(args)
    #p.communicate()
    #p.wait()
  #
  # run yasim external process to create dataset
  #dataFid = "auto.dat"
  dataHndl = open(dataFid, 'w')
  command_line = 'yasim ' + aCfgFid + ' -g'
  args = shlex.split(command_line)
  #print args
  p = subprocess.run(args, stdout=dataHndl)
  #dataHndl.flush
  #os.fsync(dataHndl.fileno())
  dataHndl.close
  #p.wait()
  #
  # run gnuplot with command file to plot dataset
  command_line = 'gnuplot -p ' + atptFid 
  args = shlex.split(command_line)
  #    print (rowsStep, colsStep, args)
  #p = subprocess.Popen(args)
  p = subprocess.run(args)
  #p.communicate()

def main():
  normArgs(sys.argv[1:])
  ## Tix tix for python 3
  if ( pythVers < 3 ) :
    root = Tix.Tk()  
  else :
    root = tix.Tk()
  scanYCfg()
  stepACfg()
#  vblsFromTplt()
#  app = ycTix( root )
#  app.mainloop()

if __name__ == '__main__':
  main()

### multiPlot Ends



#!/usr/bin/env python
#
### autoPlot.py : Auto run yasim plots stepping wing/hstab elements
##
##  order of elements in yasimCfg.xml <wing> and <hstab> must be e.g:
##     <stall aoa="15" width="18.0" peak="1.5"/>
##     <flap0 start="0.00" end="0.54" lift="1.1" drag="1.7"/>
##
###
###
import os, shlex, subprocess
# yasim config template xml file under test
global ycfgFid
ycfgFid   = 'yasimCfg.xml'
global ycfgNam
# auto files are generated while running
global acfgFid
acfgFid   = 'outpYCfg.xml'
global dataFid
dataFid = "outpData.txt"
# template gnuplot spec files for 2, 3 variables plot
global plt3Fid
# template p is the base gnuplot command file
plt3Fid   = 'tplt3arg.p'
global var3Fid
var3Fid   = 'outp3arg.p'
# range of steps for element increments must be integers
# Columns stepping [ Start End+1, Step] element 'A'
# Rows    stepping [ Start End+1, Step] element 'B'
# bc18 
#Cols: Appr aoa  
colsRnge = range(4, 13, 4 )
colsLgnd = 'apprAoA'
#Rows: Appr Spd  
rowsRnge = range(75, 86, 5 )
rowsLgnd = 'apprSpd'
for rowsStep in rowsRnge:
  for colsStep in colsRnge:
    # actual element value to be substitued on each run
    subsColV    = float(colsStep)
    # actual element value to be substitued on each run
    subsRowV    = float(rowsStep)
    # These flags indicate parsing has detected various sections of yasim config 
    apprFlag   = 0
    cruzFlag   = 0
    wingFlag   = 0
    hstabFlag  = 0
    # open auto yasim config file
    acfgHndl  = open(acfgFid, 'w', 1)
    # open base yasim config file
    with open(ycfgFid, 'r') as ycfg:
      # step each line in template yasim config file
      for line in ycfg:
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
        if '/wing' in line:
          wingFlag = 0
        # flag on hstab section
        if '<hstab' in line:
          hstabFlag = 1
        if '</hstab' in line:
          hstabFlag = 0
        ### approach section parse in order: speed, aoa, fuel elements
        if (apprFlag == 1):
          #in approach section first line 
          if '<approach' in line :
            # make an index list of double quotes in the line
            sepsList = []
            sepsChar = '"'
            lastIndx = 0
            while (lastIndx > -1):
              sepsIndx = line.find( sepsChar, (lastIndx +1))
              #print(sepsIndx)
              if (sepsIndx > 0) :
                sepsList.append(sepsIndx)
              lastIndx = sepsIndx
            #print(sepsList)
            # Use index list to spli line into text and numbers
            textApS = line[0:(sepsList[0]+1)]
            numbApS = float ( (line[(sepsList[0]+1):(sepsList[1])]))
            textApA = line[(sepsList[1]):(sepsList[2]+1)]
            numbApA = float(line[(sepsList[2]+1):(sepsList[3])])
            textApF = line[(sepsList[3]):(sepsList[4]+1)]
            numbApF = float(line[(sepsList[4]+1):(sepsList[5])])
            textApT = line[(sepsList[5]):]
            ### Element Substitution: uncomment whichever is desired
            # 
            numbApA = subsColV
            numbApS = subsRowV
            # overwrite line with substituted elements
            line = textApS + str(numbApS) + textApA + str(numbApA) \
                 + textApF + str(numbApF) + textApT
        ### cruise section  parse in order: speed, alt, fuel elements
        if (cruzFlag == 1):
          #in cruz section, first line
          if '<cruise' in line :
            # make an index list of double quotes in the line
            sepsList = []
            sepsChar = '"'
            lastIndx = 0
            while (lastIndx > -1):
              sepsIndx = line.find( sepsChar, (lastIndx +1))
              #print(sepsIndx)
              if (sepsIndx > 0) :
                sepsList.append(sepsIndx)
              lastIndx = sepsIndx
            #print(sepsList)
            # Use index list to spli line into text and numbers
            textCzS = line[0:(sepsList[0]+1)]
            numbCzS = float ( (line[(sepsList[0]+1):(sepsList[1])]))
            textCzA = line[(sepsList[1]):(sepsList[2]+1)]
            numbCzA = float(line[(sepsList[2]+1):(sepsList[3])])
            textCzF = line[(sepsList[3]):(sepsList[4]+1)]
            numbCzF = float(line[(sepsList[4]+1):(sepsList[5])])
            textCzT = line[(sepsList[5]):]
            ### Element Substitution: uncomment whichever is desired
            #            numbCzS = subsRowV
            # overwrite line with substituted elements
            line = textCzS + str(numbCzS) + textCzA + str(numbCzA) \
                 + textCzF + str(numbCzF) + textCzT
        ### wing section parse stall and flap0 elements
        if (wingFlag == 1):
          #in wing section, find stall elements
          if (line.find('<stall') > 0):
            # make an index list of double quotes in the line
            sepsList = []
            sepsChar = '"'
            lastIndx = 0
            while (lastIndx > -1):
              sepsIndx = line.find( sepsChar, (lastIndx +1))
              #print(sepsIndx)
              if (sepsIndx > 0) :
                sepsList.append(sepsIndx)
              lastIndx = sepsIndx
            #print(sepsList)
            # Use index list to spli line into text and numbers
            textWsA = line[0:(sepsList[0]+1)]
            numbWsA = float ( (line[(sepsList[0]+1):(sepsList[1])]))
            textWsW = line[(sepsList[1]):(sepsList[2]+1)]
            numbWsW = float(line[(sepsList[2]+1):(sepsList[3])])
            textWsP = line[(sepsList[3]):(sepsList[4]+1)]
            numbWsP = float(line[(sepsList[4]+1):(sepsList[5])])
            textWsT = line[(sepsList[5]):]
            ### Element Substitution: uncomment whichever is desired
            #numbWsA = subsColV
            # overwrite line with substituted elements
            line = textWsA + str(numbWsA) + textWsW + str(numbWsW) \
                 + textWsP + str(numbWsP) + textWsT
          ###
          #in wing section, find flap0 elements
          if (line.find('<flap0') > 0):
            # make an index list of double quotes in the line
            sepsList = []
            sepsChar = '"'
            lastIndx = 0
            while (lastIndx > -1):
              sepsIndx = line.find( sepsChar, (lastIndx +1))
              #print(sepsIndx)
              if (sepsIndx > 0) :
                sepsList.append(sepsIndx)
              lastIndx = sepsIndx
            #print(sepsList)
            # Use index list to spli line into text and numbers
            textWfL = line[0:(sepsList[4]+1)]
            numbWfL = float ( (line[(sepsList[4]+1):(sepsList[5])]))
            textWfD = line[(sepsList[5]):(sepsList[6]+1)]
            numbWfD = line[(sepsList[6]+1):(sepsList[7])]
            textWfT = line[(sepsList[7]):]
            ### Element Substitution: uncomment whichever is desired
            # numbWfL = subsColV
            # overwrite line with substituted elements
            line = textWfL + str(numbWfL)           \
                 + textWfD + str(numbWfD) + textWfT
        ### hstab section parse stall and flap0 elements
        if (hstabFlag == 1):
          #in hstab section, find stall elements
          if (line.find('<stall') > 0):
            # make an index list of double quotes in the line
            sepsList = []
            sepsChar = '"'
            lastIndx = 0
            while (lastIndx > -1):
              sepsIndx = line.find( sepsChar, (lastIndx +1))
              #print(sepsIndx)
              if (sepsIndx > 0) :
                sepsList.append(sepsIndx)
              lastIndx = sepsIndx
            #print(sepsList)
            # Use index list to spli line into text and numbers
            textHsA = line[0:(sepsList[0]+1)]
            numbHsA = float ( (line[(sepsList[0]+1):(sepsList[1])]))
            textHsW = line[(sepsList[1]):(sepsList[2]+1)]
            numbHsW = float(line[(sepsList[2]+1):(sepsList[3])])
            textHsP = line[(sepsList[3]):(sepsList[4]+1)]
            numbHsP = float(line[(sepsList[4]+1):(sepsList[5])])
            textHsT = line[(sepsList[5]):]
            ### Element Substitution: uncomment whichever is desired
            #numbHsA = subsRowV
            # overwrite line with substituted elements
            line = textHsA + str(numbHsA) + textHsW + str(numbHsW) \
                 + textHsP + str(numbHsP) + textHsT
          ###
          #in hstab section, find flap0 elements
          if (line.find('<flap0') > 0):
            # make an index list of double quotes in the line
            sepsList = []
            sepsChar = '"'
            lastIndx = 0
            while (lastIndx > -1):
              sepsIndx = line.find( sepsChar, (lastIndx +1))
              #print(sepsIndx)
              if (sepsIndx > 0) :
                sepsList.append(sepsIndx)
              lastIndx = sepsIndx
            #print(sepsList)
            # Use index list to spli line into text and numbers
            textHfL = line[0:(sepsList[4]+1)]
            numbHfL = float ( (line[(sepsList[4]+1):(sepsList[5])]))
            textHfD = line[(sepsList[5]):(sepsList[6]+1)]
            numbHfD = line[(sepsList[6]+1):(sepsList[7])]
            textHfT = line[(sepsList[7]):]
            ### Element Substitution: uncomment whichever is desired
            #numbHfL = subsRowV
            # overwrite line with substituted elements
            line = textHfL + str(numbHfL)           \
                 + textHfD + str(numbHfD) + textHfT
        # Write unchanged/modified line into auto xml
        acfgHndl.write(line)
      #close and sync files
      acfgHndl.flush
      os.fsync(acfgHndl.fileno())
      acfgHndl.close
      ycfg.flush
      os.fsync(ycfg.fileno())
      ycfg.close
    ## auto create gnuplot config file
    apltHndl  = open(var3Fid, 'w', 1)
    with open(plt3Fid, 'r') as tplt:
      for line in tplt:
        # find the title line in template config
        if (line.find('set title') > 0):
            #create title using parsed / substituted values
          # line = ' set title "Aw:' + str(numbWsA)    \
          #      + ' Ww:' + str(numbWsW) + 'Pw:' + str(numbWsP) \
          #      + '  Lw:' + str(numbWfL) + 'Dw:' + str(numbWfD) \
          #      + '\\nAh:' + str(numbHsA) + ' Wh:' + str(numbHsW) \
          #      + ' Ph:' + str(numbHsP) + '  Lh:' + str(numbHfL) \
          #      + ' Dh:' + str(numbHfD) + '" \n'
            line = ' set title "' + colsLgnd +  ': ' + str(colsStep)    \
                 + '  ' + rowsLgnd + ': ' + str(rowsStep) + '" \n'
          #  line = ' set title "Row:' + str(rowsStep)    \
          #       + '  Col: :' + str(colsStep) + '" \n'
        #print(line)
        # Write unchanged/modified line into auto.xml
        apltHndl.write(line)
    #  apltHndl.flush
    #  os.fsync(apltHndl.fileno())
      apltHndl.close
    #  tplt.flush
    #  os.fsync(tplt.fileno())
      tplt.close
    #    
    print (rowsStep, colsStep)
    if 0 :
      # run yasim external process to show console output
      command_line = 'yasim ' + acfgFid
      args = shlex.split(command_line)
      #print args
      p = subprocess.Popen(args)
      p.communicate()
      p.wait()
    #
    # run yasim external process to create dataset
    #dataFid = "auto.dat"
    dataHndl = open(dataFid, 'w')
    command_line = 'yasim ' + acfgFid + ' -g'
    args = shlex.split(command_line)
    #print args
    p = subprocess.Popen(args, stdout=dataHndl)
    #dataHndl.flush
    #os.fsync(dataHndl.fileno())
    dataHndl.close
    p.wait()
    #
    # run gnuplot with command file to plot dataset
    command_line = 'gnuplot -p ' + var3Fid 
    args = shlex.split(command_line)
    #    print (rowsStep, colsStep, args)
    #p = subprocess.Popen(args)
    p = subprocess.run(args)
    #p.communicate()
### runYasim Ends

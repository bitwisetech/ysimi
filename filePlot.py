#!/usr/bin/env python
#
#### runYasim.py : Auto run yasim plots stepping wing/hstab elements
import getopt, os, shlex, subprocess, sys
# default yasim config under test
def normArgs(argv):
  global ycfgFid
  ycfgFid  = 'yasimCfg.xml'
  global acfgFid
  acfgFid  = 'outpYCfg.xml'
  global dataFid
  dataFid  = "outpData.txt"
  global ycfgNam
  # template gnuplot spec files for 2, 3 variables plot
  global plt2Fid
  plt2Fid  = 'tplt2arg.p'
  global plt3Fid
  plt3Fid  = 'tplt3arg.p'
  global var2Fid
  var2Fid  = 'outp2arg.p'
  global var3Fid
  var3Fid  = 'outp3arg.p'
  # get yasim config FileID from args
  try:
    opts, args = getopt.getopt(argv, "f:", "file=")
  except getopt.GetoptError:
     print 'sorry, I need -f or file= yasim config  fileID '
     sys.exit(2)
    #
    #print(opts)
  for opt, arg in opts:
    if   opt in ("-f", "--file"):
      #print'fileID oride'
      ycfgFid = arg
      ycfgNam = ycfgFid.find('.xml')
      ycfgNam = ycfgFid[0:ycfgNam]
      #print('Fid, Fnam: ',  ycfgFid,  ycfgNam)

##
def plotMill():
  global dataFid
  global ycfgFid
  global ycfgNam
  global acfgFid
  global plt2Fid
  global plt3Fid
  global var2Fid
  global var3Fid
  # range of steps for element increments must be integers
  # 3 Columns stepping [ Start End+1, Step] element 'A'
  colsRnge = range(0, 1, 2 )
  # 5 Rows    stepping [ Start End+1, Step] element 'B'
  rowsRnge = range(0, 1, 2 )
  for colsStep in colsRnge:
    for rowsStep in rowsRnge:
      #print(colsStep, rowsStep)
      # actual element value to be substitued on each run
      subsWw     = float(colsStep) / 1
      # actual element value to be substitued on each run
      subsLw     = float(rowsStep) / 10
      wingFlag   = 0
      hstabFlag  = 0
      # open auto yasim config file
      acfgHndl  = open(acfgFid, 'w', 0)
      # open base yasim config file
      with open(ycfgFid, 'r') as ycfg:
      # step each line in template yasim config file
        for line in ycfg:
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
          ### wing section parse stall and flap0 elements
          if (wingFlag == 1):
            #in wing section, find stall elements
            if (line.find('stall') > 0):
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
              #numbWsA = subsAw
              #numbWsW = subsWw
              #numbWsP = subsValu
              # overwrite line with substituted elements
              line = textWsA + str(numbWsA) + textWsW + str(numbWsW) \
                   + textWsP + str(numbWsP) + textWsT
            ###
            #in wing section, find flap0 elements
            if (line.find('flap0') > 0):
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
              # Use index list to spli line into text and numbers
              textWfL = line[0:(sepsList[4]+1)]
              numbWfL = float ( (line[(sepsList[4]+1):(sepsList[5])]))
              textWfD = line[(sepsList[5]):(sepsList[6]+1)]
              numbWfD = line[(sepsList[6]+1):(sepsList[7])]
              textWfT = line[(sepsList[7]):]
              ### Element Substitution: uncomment whichever is desired
              #numbWfL = subsLw
              #numbWfD = subsDw
              # overwrite line with substituted elements
              line = textWfL + str(numbWfL)           \
                   + textWfD + str(numbWfD) + textWfT
          ### hstab section parse stall and flap0 elements
          if (hstabFlag == 1):
            #in hstab section, find stall elements
            if (line.find('stall') > 0):
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
              #numbHsA = subsAh
              #            numbHsW = subsWh
              #            numbHsP = subsPh
              # overwrite line with substituted elements
              line = textHsA + str(numbHsA) + textHsW + str(numbHsW) \
                   + textHsP + str(numbHsP) + textHsT
            ###
            #in hstab section, find flap0 elements
            if (line.find('flap0') > 0):
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
              #numbHfL = subsValu
              #numbHfD = subsValu
              # overwrite line with substituted elements
              line = textHfL + str(numbHfL)           \
                   + textHfD + str(numbHfD) + textHfT
          # Write unchanged/modified line into auto.xml
          acfgHndl.write(line)
        #close and sync files
        acfgHndl.flush
        os.fsync(acfgHndl.fileno())
        acfgHndl.close
        ycfg.flush
        os.fsync(ycfg.fileno())
        ycfg.close
      ## auto create 2 vble gnuplot config file
      apltHndl  = open(var2Fid, 'w', 0)
      with open(plt2Fid, 'r') as tplt:
        for line in tplt:
          # find the title line in template config
          if (line.find('set title') > 0):
              #create title using parsed / substituted values
            line = ' set title "'+ ycfgFid + '\\nAw:' + str(numbWsA)    \
                 + ' Ww:' + str(numbWsW) + 'Pw:' + str(numbWsP) \
                 + '  Lw:' + str(numbWfL) + 'Dw:' + str(numbWfD) \
                 + '\\nAh:' + str(numbHsA) + ' Wh:' + str(numbHsW) \
                 + ' Ph:' + str(numbHsP) + '  Lh:' + str(numbHfL) \
                 + ' Dh:' + str(numbHfD) + '" \n'
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
      ## auto create 3 vble gnuplot config file
      apltHndl  = open(var3Fid, 'w', 0)
      with open(plt3Fid, 'r') as tplt:
        for line in tplt:
          # find the title line in template config
          if (line.find('set title') > 0):
              #create title using parsed / substituted values
            line = ' set title "'+ ycfgFid + '\\nAw:' + str(numbWsA)    \
                 + ' Ww:' + str(numbWsW) + 'Pw:' + str(numbWsP) \
                 + '  Lw:' + str(numbWfL) + 'Dw:' + str(numbWfD) \
                 + '\\nAh:' + str(numbHsA) + ' Wh:' + str(numbHsW) \
                 + ' Ph:' + str(numbHsP) + '  Lh:' + str(numbHfL) \
                 + ' Dh:' + str(numbHfD) + '" \n'
          #print(line)
          # Write unchanged/modified line into auto.xml
          apltHndl.write(line)
      #  apltHndl.flush
      #  os.fsync(apltHndl.fileno())
        apltHndl.close
      #  tplt.flush
      #  os.fsync(tplt.fileno())
        tplt.close
      # run yasim external process to show console output
      command_line = 'yasim ' + acfgFid
      args = shlex.split(command_line)
      #print args
      p = subprocess.Popen(args)
      p.communicate()
      p.wait()
      #
      # run yasim external process to create auto dataset
      dataHndl = open(dataFid, 'w')
      command_line = 'yasim ' + acfgFid + ' -g'
      args = shlex.split(command_line)
      #print args
      p = subprocess.Popen(args, stdout=dataHndl)
      dataHndl.close
      p.wait()
      #
      # change filname for data file and run yasim external process for saved dataset file
      dataFid = ycfgNam + '.dat'
      dataHndl = open(dataFid, 'w')
      print(dataFid)
      command_line = 'yasim ' + acfgFid + ' -g'
      args = shlex.split(command_line)
      p = subprocess.Popen(args, stdout=dataHndl)
      #dataHndl.flush
      #os.fsync(dataHndl.fileno())
      dataHndl.close
      p.wait()
      #
      # run gnuplot with 2 vble command file to plot dataset
      command_line = "gnuplot -p " + var2Fid
      args = shlex.split(command_line)
      #print args
      p = subprocess.Popen(args)
      p.communicate()
      #
      # run gnuplot with 3 vble command file to plot dataset
      command_line = "gnuplot -p " + var3Fid
      args = shlex.split(command_line)
      #print args
      p = subprocess.Popen(args)
      p.communicate()
#
if __name__ == "__main__":
  normArgs(sys.argv[1:])
  plotMill()
##### runYasim Ends

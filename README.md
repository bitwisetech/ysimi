YASIPLOT  Diagnostic tools for FlightGear's YASIM Flight Dynamics Model yasimi.py, inciMarg.py

  Yasim FDM uses a configuration file to creatre its FDM and can supply tabulated
Lift, Drag Tables and a solution summary text. The python tools from here automatically
generate configuration files and plotting data while key elements of the configuration 
files are manually altered. 

  YASim Simulator Interactive  ysimi.py is the fullest function latest 

## ysimi.py 
  ysimi.py uses python's bokeh package, it serves a live control / plotting
interface shown on a web browser.  Key elements in a YASim configuration file may 
be altered by sliders in the web app while Lift / Drag curves are updated with live plots. 
  At the same time an updated yasim conguration file is re-written so that a flightgear session 
may instantly update its configuration and the modifications tested.

  ysimi.py requires bokeh, pandas python packages, perhaps more depending on what's installed
  
  It needs a copy of the flightgear YASim configuration named ysimi-yasim.xml 
  It is started by commnd: bokeh serve ysimi.py
    shown on a web browser at URL:  http://localhost:5006/ysimi
  On the browser Lift, Drag, MIas plots are updated live with slider input  
  On the console are updated key YASim solution results that affect the model's motion.     

  An example workflow details are commented at the start of file: ysimi.py 

  Buckaroo's Yasim Reference :  
    https://buckarooshangar.com/flightgear/yasimtut.html  
  
  Running Real-Time Plots:
  
  Use a working directory in a folder below the executables: 
cd somePath/ysmi; mkdir mymodel; cd mymodel

  create base configuration file from the YASim configuration file(s) of interest :
    cp /pathTo/fgaddon/Aircraft/Beechcraft-C18S/Systems/FDM/model18-yasim.xml ysimi-yasim.xml

  pathToEnv/bokeh serve ysimi.py 
  (The standard bokeh port is 5006 ) 
  
  open a web browser and in a new tab: 
  http://localhost:5006/ysimi 

  To see the effect on Lift and Drag curves slowly adjust any pointer. Each step will 
trigger a yasim re-run and re-plot of the three curves while on the console a brief message
reports key results: Elevator on Approach  and  Center of Gravity relative to Wing's MAC.

  A new YASim configuration is created as adjustments are made at the browser,  the new file 
is named: ysimi-yasim-outp.xml.   


## inciMarg.py 
  A command line logout of Wing Incidence, derived from wheel / cenreline geometry, compared to 
wing stall AoA values read from a named YASim configuration file: 
  
> inciMarg.py -f t6/t6-yasim.xml
 t6-yasim.xml   CL incidence: 11.294  Wing incidence: 2.000  Total Incidence : 13.294    Wing AoaStall: 15.000   % Margin: 11.374


YASIPLOT  Diagnostic tools for FlightGear's YASIM Flight Dynamics Model

  Yasim FDM uses a configuration file to creatre its FDM and can supply tabulated
Lift, Drag Tables and a solution summary text. The python tools from here automatically
generate configuration files and plotting data while key elements of the configuration 
files are manually altered. 

  ysimi.py, xsimi.py  both use python's bokeh package which serves a live control / plotting
interface showing on a web browser.  Sliders for key yasim elements automatically alter
the yasim conguration file to real-time generate Lift / Drag LvsD plots. 

  inciMarg.py takes a named yasim configuration file and, using the landing gear's heights 
to figure the wing's inclination while on the ground and compares this with wing's stall angle.

  aoaStatic.py command line utility for incidence, stall margin with console output.


VVV Older Utilities /  Versions may not be pyhon3 ready   !!!    VVV

yasiVers.py  is a utility to automatically create gnuplot displays from FlightGear Yasim
  configuration files. Lift, Drag, L/D plots are created using different Yasim 'Version' 
 specifications so that the effect of version changes in the FDM can be inspected. 
 A menu interface allows for the various key Yasim parameters to be adjusted; such adjustments
 are saved separately from the original yasim xml configuration file. 

The python script depends on Tkinter being available for import and gnuplot should be installed.
 It's a work in process, it's likely the parser will throw errors depending on the line-by-line 
 form of the input configuration file: most likely the 'wing', 'hstab' and 'vstab' definitions
 will need to be unsplit into single long line definitions. 
 
For both compVers.py and dspdVers.py the plotted line styles are chosen to highlight differences
  between Yasim versions: 
  YASIM_VERSION_ORIGINAL data are shown as solid Violet 'line' style 
  YASIM_VERSION_32       data are shown as green 'impulse' style, vertical strokes from Y=0 to datapoints
  YASIM_VERSION_CURRENT  data are shown as 'dot' style seen as asterisks, '*'
  2017.2                 data are shown as 'line-dot' style seen as amber line with small boxes
  
  Versions CURRENT and 2017.2 should match exactly sine 2017.2 is the current version. Any mismatch 
  between the vertical green strokes and amber lines is significant, indicating that the new, 2017.2
  version has a different solution from the previous version. Other deviations from the solid violet line
  highlight changes from Original due to versin 32 fixes. 
 
examples: 
  cd/theClonedDir/t6;    python ../yasiVers.py -f t6-yasim.xml    ( adjust as desired, press 'Plot' ) 
  cd/theClonedDir/772E;  python ../yasiVers.py -f 772E.xml        ( adjust as desired, press 'Plot' ) 
  cd/theClonedDir/772E;  python ../compVers.py -f 772E.xml        ( adjust as desired, press 'Plot' ) 
  cd/theClonedDir/772E;  python ../dspdVers.py -f 772E.xml        ( adjust as desired, press 'Plot' ) 
  cd/theClonedDir/; mkdir MyNewModel; cp ../*Tplt.p .; copy pathTo/Aircraft/MyNewModel/yasimConfig.xml; 
                         python ../dspdVers.py -f yasimConfig.xml ( adjust as desired, press 'Plot' ) 

<!-- autoPlot.py  -->
<!-- multiPlot.py  -->
 2021Jl17 autoPlot.py: Now is yasiPlot/multiPlot.py
 This program makes repeated automatic runs of yasim to create gnuplots of Lift, Drag, L/D.
Two different elements in the yasim config file are stepped in a nested colums rows fashion.  

  Before running, edit the script to cutomise column, row, range and text legend.
In the section of code after each section's parsing: set up a conditional to substitute 
stepped values for the tyasim elemnts of interest. 

For example: to explore approach Speed and AoA :
  
    #Cols: Appr aoa  
    colsLgnd = 'ApA'
    colsRnge = range(4, 17, 4 )
    #Rows: Appr Spd  
    rowsLgnd = 'ApS'
    rowsRnge = range(72, 89, 8 )
    ##
    
    and, in the <approach> section: 
 
    # 
    if 'ApS' in colsLgnd: numbApS = subsColV
    if 'ApS' in rowsLgnd: numbApS = subsRowV
    if 'ApA' in colsLgnd: numbApA = subsColV
    if 'ApA' in rowsLgnd: numbApA = subsRowV

 The code does not do an exhaustive name=value parsing of the various sections. Elements 
in each section must be in a particular order. Symlink the yasim config xml from your 
model to file: yasimCfighas those elements described in the same order as in the template xml file, sections are
copied here:   
 
  <wing x="-2.755"     y="0.5"    z="-0.53"     taper="0.48" incidence="4.00" twist="-3"
    length="4.3" chord="2.25" sweep="-2.0" dihedral="6.00" camber="0.068" idrag="0.95">
    <stall aoa="15" width="18.0" peak="1.5"/>
    <flap0 start="0.00" end="0.54" lift="1.1" drag="1.7"/>

  <hstab x="-7.0" y="0.0" z="0.31" taper="0.72"
        length="1.72" chord="1.06" sweep="0" dihedral="30" >
    <stall aoa="24.0" width="4.0" peak="1.5"/>
    <flap0 start="0.05" end="1.0" lift="2.25" drag="1.7" />
    
 The python program substitutes in the <stall> and <flap0> sections for both <wing> and
 for <hstab>    



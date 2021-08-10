# Gnuplot script file for "outpData.txt"
 # This file is based on tplt2arg.p
 set   autoscale                        # scale axes automatically
 unset log                              # remove any log-scaling
 unset label                            # remove any previous labels
 # 
 set term qt size 340, 256
 # set term qt size 360, 200
 # set term wxt size 240, 200
 # set term wxt size 380, 150
 # set term wxt size 500, 180
 set xtic auto                          # set xtics automatically
 set ytic auto                          # set ytics automatically
 set  grid xtics ytics
 show grid
 set title "WsA:12 Wsw:4.0 WsP:1.4 WfL:1.0 WfD:1.7 HsA:8.0 Hsw:4.0 HsP:1.5 HfL:2.3 HfD:1.7 "
# set xlabel "AoA (Deg)"
# set ylabel "Force (G)"
 plot  "outpData.txt" every ::155::210 using 1:4 with lines title 'LvsD'

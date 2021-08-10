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
 set title "./Citation-II-yasim-p-vCurr Va:107.0 Aa:5.0 Vc:368.0 Cw:0.0 Aw:10.0 Ww:3.0"
# set xlabel "AoA (Deg)"
# set ylabel "Force (G)"
 plot "./Citation-II-yasim-p-dat-vCurr.txt" every ::2        using 1:4 with lines title 'LvsD'
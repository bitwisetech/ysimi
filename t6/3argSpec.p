# Gnuplot script file for "outpData.txt"
 # This file is based on tplt3arg.p
 set   autoscale                        # scale axes automatically
 unset log                              # remove any log-scaling
 unset label                            # remove any previous labels
 # 
 set term qt size 340, 256
 # set term qt size 360, 200
 #  set term wxt size 240, 200
 # set term wxt size 380, 150
 # set term wxt size 500, 180
 set xtic auto                          # set xtics automatically
 set ytic auto                          # set ytics automatically
 set  grid xtics ytics
 show grid
 set title "t6-yasim-p-vCurr Va:80.0 Aa:2.0 Vc:130.0 Cw:0.001 Aw:16.0 Ww:1.0"
# set xlabel "AoA (Deg)"
# set ylabel "Force (G)"
#plot  "outpData.txt" every ::155::210 using 1:2 with lines title 'lift', \
#      "outpData.txt" every ::155::210 using 1:3 with lines title 'drag', \
#      "outpData.txt" every ::155::210 using 1:4 with lines title 'LD'
 plot "t6-yasim-p-dat-vCurr.txt" every ::2        using 1:2 with lines title 'lift', \
      "t6-yasim-p-dat-vCurr.txt" every ::2        using 1:3 with lines title 'drag', \
      "t6-yasim-p-dat-vCurr.txt" every ::2        using 1:4 with lines title 'L-D' 

# Gnuplot script file for "outpData.txt"
 # This file is based on tplt2arg.p
 set   autoscale                        # scale axes automatically
 unset log                              # remove any log-scaling
 unset label                            # remove any previous labels
 # 
 set term qt size 240, 200
 # set term wxt size 240, 200
 # set term wxt size 380, 150
 # set term wxt size 500, 180
 set xtic auto                          # set xtics automatically
 set ytic auto                          # set ytics automatically
 set  grid xtics ytics
 show grid
 set title "A:60.0 4.0 0.2 0.4 1.0 C:180.0 15000.0 0.5 1.0\nW:7.241 0.3 16.0 1.0 1.5 1.4 1.6 1.2 1.1\nH:0 1 14.0 1.0 1.5 2.0 1.0\nV:0 1 12.0 1.0 0 1.8 1.5 At:75 0" 
# set xlabel "AoA (Deg)"
# set ylabel "Force (G)"
# below likely ::155::210 is wrong, data files no longer have extreme AOA lines 
 plot "multi-yasim-tix.txt" every ::155::210 using 1:2 with lines title 'lift', \
      "multi-yasim-tix.txt" every ::155::210 using 1:3 with lines title 'drag', \
      "multi-yasim-tix.txt" every ::155::210 using 1:4 with lines title 'L-D'
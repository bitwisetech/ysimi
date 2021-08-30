#!/usr/bin/env python
#
import math, numpy
# Figure wing incidence from gear heights 
# Figure wing incidence from gear heights 
Mx = float (input ( 'Mains (x) posn   ? '))
Mz = float (input ( 'Mains (z) height ? '))
Tx = float (input ( 'Tail  (x) posn   ? '))
Tz = float (input ( 'Tail  (z) height ? '))
#
Gx = Mx - Tx
Ex = (Tz * Gx) / (Mz - Tz) 
Aoa = -1 * numpy.arctan ( Mz / ( Ex + Gx ) )
Aoa = math.degrees ( Aoa ) 
#
print ( 'Add centre line incidence of ', Aoa, 'deg to wing incedence from config')   
  

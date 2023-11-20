import matplotlib.pyplot as plt
import numpy as np
import matplotlib.animation as animation
import h5py
import meep as mp

#Airmode(Higher Q then dielecmode): a= 0.538, w=0.54, t=0.220, r=0.172, lattice defect factor=0.83, radius defect factor=0.51, 4 mirror holes each side, 9 defect holes each side
#Dielecmode: a= 0.538, w=0.54, t=0.220, r=0.173, lattice defect factor=0.70, radius defect factor=0.87, 4 mirror holes each side, 9 defect holes each side




# Measured parameters from fab by Milan:
eps = 11.9   # dielectric constant of silcon
h = 0.22  # height of unit  

a = 0.538  # lattice constant 
r = 0.172  # radius of holes  (biggest at r=(a*n_silicon)/(n_air+n_silicon))

A = 0.72    # defect factor of a
B = 0.85    # defec factor of r
N1=6   #number of holes in the mirror
N2=7   #number of holes in defect (9holes=8spacing)
pad = 0.3    # padding between pml layer and last hole
dpml = 0.5   # PML thickness

fcen = 0.649    # pulse center frequency
df = 0.6       # pulse freq. width
mp.filename_prefix = ''

def d(x):
    l = (A*a*x)+((x*(x+1)*((2*x)+1))/6)*(1-A)*a/(N2**2) #length of half of the defect
    return l 

# The cell dimensions
sx = 2*(pad+N1*a+d(N2)+A*a+dpml)  # size of cell in x direction
sy = h+(0.5+dpml)*2  # size of cell in y direction
#sz = t+(0.5+dpml)*2  # size of cell in z direction 


cell = mp.Vector3(sx, sy,0)

blk = mp.Block(size=mp.Vector3(mp.inf, h, mp.inf), material=mp.Medium(epsilon=eps))
geometry = [blk]

for i in range(N1):
    geometry.append(mp.Block(size=mp.Vector3(r, h, mp.inf), center=mp.Vector3(A*a + d(N2) + a/2 + i*a), material=mp.air))
    geometry.append(mp.Block(size=mp.Vector3(r, h, mp.inf), center=mp.Vector3(-(A*a + d(N2) + a/2 + i*a)), material=mp.air))
for i in range(N2+1):
    geometry.append(mp.Block(size=mp.Vector3((B*r+r*(1-B)*(i*i)/(N2*N2)), h, mp.inf), center=mp.Vector3(A*a + d(i)-(A*a+(1-A)*a*(i**2)/(N2**2))/2), material=mp.air))
    geometry.append(mp.Block(size=mp.Vector3((B*r+r*(1-B)*(i*i)/(N2*N2)), h, mp.inf), center=mp.Vector3(-(A*a + d(i)-(A*a+(1-A)*a*(i**2)/(N2**2))/2)), material=mp.air))

s = mp.Source(
    src=mp.GaussianSource(fcen, fwidth=df),
    component=mp.Hz,
    center=mp.Vector3(),
)

sym = [mp.Mirror(mp.Z,+1),mp.Mirror(mp.Y,+1)]

sim = mp.Simulation(cell_size=cell,
                    geometry=geometry,
                    sources=[s],
                    symmetries=sym,
                    boundary_layers=[mp.PML(dpml)],
                    resolution=100,
                   )
#sim.use_output_directory('/home/qlin/return_message/')
sim.run(mp.after_sources(mp.Harminv(mp.Hz, mp.Vector3(0, 0, 0), fcen, df)),
        until_after_sources=800)
sim.run(mp.to_appended("res",mp.at_every(1/fcen/20, mp.output_efield_x),mp.at_end(mp.output_epsilon)), until=3/fcen) 
#sim.run(mp.to_appended("res",mp.at_every(1/fcen/20, mp.output_efield_z), until=1/fcen))      
#sim.run(mp.after_sources(mp.Harminv(mp.Hz, mp.Vector3(0, 0, 0), fcen, df)), #mp.synchronized_magnetic(mp.after_sources_and_time(1000, mp.output_tot_pwr)),
#        until_after_sources=400)

# In[ ]:





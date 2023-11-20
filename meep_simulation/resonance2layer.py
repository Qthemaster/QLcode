
import matplotlib.pyplot as plt
import numpy as np
import numpy.matlib
import math
import meep as mp
from meep.materials import cSi, Y2O3

#Dielecmode: a= 0.538, w=0.54, t=0.220, Y2O3thickness=0.100, r=0.181, lattice defect factor=0.70, radius defect factor=0.85, 4 mirror holes each side, 9 defect holes each side

# Some parameters to describe the geometry:
eps = 11.8   # dielectric constant of silcon
w = 0.540  # width of unit  (for bigger gap not centered at 1.545um wavelength: 0.4 ~ 0.41)  
           # 0.533 for gap to centered at 1.545um wavelength
t = 0.220  # thickness of unit
a = 0.538  #lattice constant 
r = 0.173  # radius of holes  (biggest at r=(a*n_silicon)/(n_air+n_silicon))

A = 0.70    # defect factor of a
B = 0.87    # defec factor of r
# N1=4number of holes in the mirror
# N2=9number of holes in defect (9holes=8spacing)
pad = 1    # padding between pml layer and last hole
dpml = 0.5   # PML thickness

fcen = 0.650    # pulse center frequency
df = 0.4 # pulse freq. width

Yrcenter = mp.Vector3(0, 0, 0)

tt = t    #toplayer thickness
mt = 0.10    #middlelayer thickness
lt = t    #lowerlayer thickness

def sim_cavity(N1, N2):

    def d(x):
        l = (A*a*x)+((x*(x+1)*((2*x)+1))/6)*(1-A)*a/(N2**2) #length of half of the defect
        return l 
    
    # The cell dimensions
    sx = 2*(pad+N1*a+d(N2)+A*a+dpml)  # size of cell in x direction
    sy = w+(1+dpml)*2  # size of cell in y direction (perpendicular to wvg.)\
    sz = tt+mt+lt+(1+dpml)*2
    

    cell = mp.Vector3(sx, sy, sz)
    
    u = mp.Block(size=mp.Vector3(mp.inf, w, tt), center=mp.Vector3(0, 0, 0.5*(mt+tt)), material=cSi)
    y = mp.Block(size=mp.Vector3(mp.inf, w, mt), center=Yrcenter, material=Y2O3)
    s = mp.Block(size=mp.Vector3(mp.inf, w, lt), center=mp.Vector3(0, 0, -0.5*(mt+lt)), material=cSi)
    geometry = [u, y, s]

    for i in range(N1):
        geometry.append(mp.Cylinder(r, height=tt, center=mp.Vector3((A*a/2 + d(N2) + a + i*a), 0, 0.5*(mt+tt)), material=mp.Medium(epsilon=1.0006)))
        geometry.append(mp.Cylinder(r, height=tt, center=mp.Vector3((-(A*a/2 + d(N2) + a + i*a)), 0, 0.5*(mt+tt)), material=mp.Medium(epsilon=1.0006)))
        geometry.append(mp.Cylinder(r, height=lt, center=mp.Vector3((A*a/2 + d(N2) + a + i*a), 0, -0.5*(mt+lt)), material=mp.Medium(epsilon=1.0006)))
        geometry.append(mp.Cylinder(r, height=lt, center=mp.Vector3((-(A*a/2 + d(N2) + a + i*a)), 0, -0.5*(mt+lt)), material=mp.Medium(epsilon=1.0006)))
    for i in range(N2+1):
        geometry.append(mp.Cylinder((B*r+r*(1-B)*(i*i)/(N2*N2)), height=tt, center=mp.Vector3((A*a/2 + d(i)), 0, 0.5*(mt+tt)), material=mp.Medium(epsilon=1.0006)))
        geometry.append(mp.Cylinder((B*r+r*(1-B)*(i*i)/(N2*N2)), height=tt, center=mp.Vector3((-(A*a/2 + d(i))), 0, 0.5*(mt+tt)), material=mp.Medium(epsilon=1.0006)))
        geometry.append(mp.Cylinder((B*r+r*(1-B)*(i*i)/(N2*N2)), height=lt, center=mp.Vector3((A*a/2 + d(i)), 0, -0.5*(mt+lt)), material=mp.Medium(epsilon=1.0006)))
        geometry.append(mp.Cylinder((B*r+r*(1-B)*(i*i)/(N2*N2)), height=lt, center=mp.Vector3((-(A*a/2 + d(i))), 0, -0.5*(mt+lt)), material=mp.Medium(epsilon=1.0006)))

    s = mp.Source(
        src=mp.GaussianSource(fcen, fwidth=df),
        component=mp.Ey,
        center=mp.Vector3(0, 0, 0),
    )

    sym = [mp.Mirror(mp.Y, phase=-1), mp.Mirror(mp.X, phase=+1), mp.Mirror(mp.Z, phase=-1)]
   

    sim = mp.Simulation(
        cell_size=cell,
        geometry=geometry,
        default_material=mp.Medium(epsilon=1.0006),
        sources=[s],
        symmetries=sym,
        boundary_layers=[mp.PML(dpml)],
        resolution=100,
        split_chunks_evenly = False
    )
    return sim
    


sim = sim_cavity(6, 8)     # cavity

sim.run(mp.after_sources(mp.Harminv(mp.Ey, mp.Vector3(), fcen, df)),
        until_after_sources=400)

E_yr = sim.field_energy_in_box(mp.Volume(center=Yrcenter, size=(0, w, mt)))
E_tot = sim.field_energy_in_box(mp.Volume(center=(0, 0, 0.5*(mt+tt+lt)-0.5*(mt+2*lt)), size=(0, w, (mt+tt+lt))))
print("Percentage of tot energy in Yr: {}".format(100*E_yr/E_tot))
        


# In[ ]:





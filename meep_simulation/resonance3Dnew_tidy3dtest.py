
import numpy as np
import tidy3d as td
import tidy3d.web as web

# Define the original parameters from MEEP code
eps = 11.9   # Dielectric constant of silicon
w = 0.540    # Width of the waveguide
t = 0.22     # Thickness of the waveguide
a = 0.538    # Lattice constant
r = 0.172    # Radius of the holes

A = 0.72     # Lattice defect factor
B = 0.85     # Radius defect factor
N1 = 6       # Number of holes in the mirror
N2 = 7       # Number of holes in the defect region
pad = 0.3    # Padding between PML layer and last hole
dpml = 0.5   # Thickness of the PML layers
fcen = 0.649 # Center frequency of the source
df = 0.6     # Frequency width of the source

# Function to calculate the length of the defect region
def d(x):
    return (A * a * x) + ((x * (x + 1) * ((2 * x) + 1)) / 6) * (1 - A) * a / (N2 ** 2)

# Define the size of the simulation domain
sx = 2 * (pad + N1 * a + d(N2) + A * a + dpml)
sy = w + (0.5 + dpml) * 2
sz = t + (0.5 + dpml) * 2

# Create the simulation domain
sim_domain = td.Box(size=(sx, sy, sz))

# Define the material for the waveguide (silicon)
silicon = td.Medium(epsilon=eps)

# Create the geometric structures
geometry = []
# Add an infinite silicon block
geometry.append(td.Structure(
    geometry=td.Box(size=(td.inf, w, t)),
    material=silicon
))

# Add cylinders for the mirror and defect regions
for i in range(N1):
    geometry.append(td.Structure(
        geometry=td.Cylinder(
            radius=r, 
            axis='x', 
            center=(A * a + d(N2) + a / 2 + i * a, 0, 0),
            length= td.inf
        ),
        material=td.Air
    ))
    geometry.append(td.Structure(
        geometry=td.Cylinder(
            radius=r, 
            axis='x', 
            center=(-(A * a + d(N2) + a / 2 + i * a), 0, 0),
            length= td.inf
        ),
        material=td.Air
    ))

for i in range(N2 + 1):
    radius = B * r + r * (1 - B) * (i * i) / (N2 * N2)
    geometry.append(td.Structure(
        geometry=td.Cylinder(
            radius=radius, 
            axis='x', 
            center=(A * a + d(i) - (A * a + (1 - A) * a * (i ** 2) / (N2 ** 2)) / 2, 0, 0),
            length= td.inf
        ),
        material=td.Air
    ))
    geometry.append(td.Structure(
        geometry=td.Cylinder(
            radius=radius, 
            axis='x', 
            center=(-(A * a + d(i) - (A * a + (1 - A) * a * (i ** 2) / (N2 ** 2)) / 2), 0, 0),
            length= td.inf
        ),
        material=td.Air
    ))

# Create the source
source = td.PointSource(
    position=(0, 0, 0),
    frequency=fcen,
    pulse_width=df,
    amplitude=1,
    polarization='Hz'
)

# Setup the simulation
sim = td.Simulation(
    domain=sim_domain,
    structures=geometry,
    sources=[source],
    resolution=40,
    boundary_layers=[td.PML(thickness=dpml)]
)

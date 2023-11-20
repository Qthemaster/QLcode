import matplotlib.pyplot as plt
import numpy as np
import matplotlib.cm as cm
import meep as mp
import math
import os
import matplotlib.colors as mcolors
#Airmode(Higher Q then dielecmode): a= 0.538, w=0.54, t=0.220, r=0.172, lattice defect factor=0.83, radius defect factor=0.51, 4 mirror holes each side, 9 defect holes each side
#Dielecmode: a= 0.538, w=0.54, t=0.220, r=0.173, lattice defect factor=0.70, radius defect factor=0.87, 4 mirror holes each side, 9 defect holes each side

total_scales = np.linspace(0.98, 1.02, 10) 
filename = 'test0'
path = '/home/qlin/return_message'
harminv_data = {}

 

def save_harminv_results(harminv_data, path, base_filename):
    rank = mp.my_global_rank()
    unique_filename = f"{base_filename}_rank_{rank}.txt"
    full_path = f"{path}/{unique_filename}"
    with open(full_path, 'w') as file:
        for scale, modes in harminv_data.items():
            for mode in modes:
                freq, Q = mode
                file.write(f"Scale: {scale}, freq: {freq}, Q: {Q}\n")


def run_simulation(scale):
    # Measured parameters from fab by Milan:
    eps = 11.9   # dielectric constant of silcon
    w = 0.540 * scale  # width of unit  (for bigger gap not centered at 1.545um wavelength: 0.4 ~ 0.41)  
            # 0.533 for gap to centered at 1.545um wavelength
    t = 0.22 
    a = 0.538 * scale # lattice constant 
    r = 0.172 * scale # radius of holes  (biggest at r=(a*n_silicon)/(n_air+n_silicon))

    A = 0.72    # defect factor of a
    B = 0.85    # defec factor of r
    N1=6   #number of holes in the mirror
    N2=7   #number of holes in defect (9holes=8spacing)
    pad = 0.3    # padding between pml layer and last hole
    dpml = 0.5   # PML thickness

    fcen = 0.649    # pulse center frequency
    df = 0.1       # pulse freq. width
    mp.filename_prefix = ''

    def d(x):
        l = (A*a*x)+((x*(x+1)*((2*x)+1))/6)*(1-A)*a/(N2**2) #length of half of the defect
        return l

    # The cell dimensions
    sx = 2*(pad+N1*a+d(N2)+A*a+dpml)  # size of cell in x direction
    sy = w+(0.5+dpml)*2  # size of cell in y direction
    sz = t+(0.5+dpml)*2  # size of cell in z direction 


    cell = mp.Vector3(sx, sy, sz)

    blk = mp.Block(size=mp.Vector3(mp.inf, w, t), material=mp.Medium(epsilon=eps))
    geometry = [blk]

    for i in range(N1):
        geometry.append(mp.Cylinder(r, height = mp.inf, center=mp.Vector3(A*a + d(N2) + a/2 + i*a), material=mp.air))
        geometry.append(mp.Cylinder(r, height = mp.inf, center=mp.Vector3(-(A*a + d(N2) + a/2 + i*a)), material=mp.air))
    for i in range(N2+1):
        geometry.append(mp.Cylinder((B*r+r*(1-B)*(i*i)/(N2*N2)), height = mp.inf, center=mp.Vector3(A*a + d(i)-(A*a+(1-A)*a*(i**2)/(N2**2))/2), material=mp.air))
        geometry.append(mp.Cylinder((B*r+r*(1-B)*(i*i)/(N2*N2)), height = mp.inf, center=mp.Vector3(-(A*a + d(i)-(A*a+(1-A)*a*(i**2)/(N2**2))/2)), material=mp.air))

    s = mp.Source(
        src=mp.GaussianSource(fcen, fwidth=df),
        component=mp.Ey,
        center=mp.Vector3(),
    )

    sym = [mp.Mirror(mp.Z,+1),mp.Mirror(mp.X,+1),mp.Mirror(mp.Y,-1)]

    sim = mp.Simulation(cell_size=cell,
                        geometry=geometry,
                        sources=[s],
                        symmetries=sym,
                        boundary_layers=[mp.PML(dpml)],
                        resolution=40,
                    )
    #sim.use_output_directory('/home/qlin/return_message/')
    # Create a Harminv object for monitoring
    harminv_monitor = mp.Harminv(mp.Ey, mp.Vector3(0, 0, 0), fcen, df)

    # Run the simulation, including Harminv analysis after the sources are off
    sim.run(mp.after_sources(harminv_monitor), until_after_sources=400)

    # Retrieve the results from the Harminv analysis
    
    
    harminv_results = harminv_monitor.modes
    # Save the Harminv results to a file
    

    # Add the Harminv results to the data dictionary for later use
    harminv_data[scale] = [(mode.freq, mode.Q) for mode in harminv_results]
    


def distribute_tasks(scales, total_progress, max_ranks_per_task=224):
    # Determine the number of tasks for the first round of distribution.
    # It ensures that the number of remaining scales is at least equal to total_ranks.
    num_tasks= math.ceil(total_progress / max_ranks_per_task)
    while (len(scales) % num_tasks != 0 and num_tasks < len(scales)) :
        num_tasks += 1
   
    # Split the scales for the first round, leaving out the last 'total_ranks' scales.
    scales_per_task = np.array_split(scales, num_tasks)
    
    
    return num_tasks, scales_per_task

def merge_and_delete_temp_files(path, base_filename, group_master_ranks):
    all_data = {}
    
    # Merge the contents of each temporary file created by group masters
    for rank in group_master_ranks:
        temp_filename = f"{path}/{base_filename}_rank_{rank}.txt"
        with open(temp_filename, 'r') as file:
            for line in file:
                scale, freq, Q = parse_line(line)
                if scale not in all_data:
                    all_data[scale] = []
                all_data[scale].append((freq, Q))
                #print(all_data)
                #print(temp_filename)
        
        # Delete the temporary file after reading its contents
        os.remove(temp_filename)

    # Write the merged data into a single output file
    output_path = f"{path}/{base_filename}.txt"
    with open(output_path, 'w') as file:
        for scale, modes in all_data.items():
            for freq, Q in modes:
                file.write(f"Scale: {scale}, freq: {freq}, Q: {Q}\n")
                

    return all_data

def parse_line(line):
    # Parse each line of the file to extract scale, frequency, and Q-factor
    parts = line.strip().split(',')
    scale = float(parts[0].split(': ')[1])
    freq = float(parts[1].split(': ')[1])
    Q = float(parts[2].split(': ')[1])
    return scale, freq, Q


total_ranks = mp.count_processors()  # Total number of available processes
ranks, scales_per_task = distribute_tasks(total_scales, total_ranks)
#print (scales_per_task)
n = mp.divide_parallel_processes(ranks)
group_masters =mp.get_group_masters()
for scale in scales_per_task[n]:
    run_simulation(scale)
    mp.all_wait()


if mp.am_master():
    save_harminv_results(harminv_data, path, filename)

mp.all_wait()
mp.begin_global_communications()
mp.all_wait()
mp.end_global_communications()

if mp.am_really_master():
    merged_data = merge_and_delete_temp_files(path, filename, group_masters)
    cmap = cm.get_cmap('viridis') 

    fig, ax = plt.subplots()
    all_Q_factors = [mode[1] for modes in merged_data.values() for mode in modes]
    min_Q, max_Q = min(all_Q_factors), max(all_Q_factors)
    norm = mcolors.Normalize(vmin=min_Q, vmax=max_Q)

    for scale, modes in merged_data.items():
        frequencies = [mode[0] for mode in modes]
        Q_factors = [mode[1] for mode in modes]

        colors = cmap(norm(np.array(Q_factors)))
        ax.scatter([scale]*len(frequencies), frequencies, color=colors)

    ax.set_xlabel("Scale")
    ax.set_ylabel("Frequency")
    cb = plt.colorbar(cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax, label='Q Factor')
    fig.savefig('/home/qlin/return_message/modestructure.png')
    #sim.run(mp.to_appended("res",mp.at_every(1/fcen/20, mp.output_efield_y),mp.at_end(mp.output_epsilon)), until=3/fcen) 
    #sim.run(mp.to_appended("res",mp.at_every(1/fcen/20, mp.output_efield_z), until=1/fcen))      
    #sim.run(mp.after_sources(mp.Harminv(mp.Hz, mp.Vector3(0, 0, 0), fcen, df)), #mp.synchronized_magnetic(mp.after_sources_and_time(1000, mp.output_tot_pwr)),
    #        until_after_sources=400)

    # In[ ]:





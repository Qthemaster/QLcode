#!/bin/bash

#SBATCH --job-name=res
#SBATCH --account=pi-tzh
#SBATCH --output=/home/qlin/return_message/res.out
#SBATCH --error=/home/qlin/return_message/res.err
#SBATCH --partition=broadwl  # accessible partitions listed by the sinfo command
#SBATCH --nodes=8
#SBATCH --ntasks-per-node=1  # number of tasks per node
#SBATCH --cpus-per-task=28
#SBATCH --time=1:00:00
#SBATCH --mail-type=ALL  # Mail events (NONE, BEGIN, END, FAIL, ALL)
#SBATCH --mail-user=qlin@rcc.uchicago.edu  # Where to send email



# Load the require module(s)
module load python/anaconda-2020.02
module load meep/1.16+intelmpi-5.1+intel-16.0
source activate meep

export OMP_NUM_THREADS=28
# Load the require module(s)
mpirun -np 8 python /home/qlin/sim_code/resonance2D.py

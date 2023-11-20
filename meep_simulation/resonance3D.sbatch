#!/bin/bash

#SBATCH --job-name=res
#SBATCH --account=pi-tzh
#SBATCH --output=/home/qlin/return_message/res.out
#SBATCH --error=/home/qlin/return_message/res.err
#SBATCH --partition=broadwl  # accessible partitions listed by the sinfo command
#SBATCH --nodes=8
#SBATCH --ntasks-per-node=4  # number of tasks per node
#SBATCH --cpus-per-task=6
#SBATCH --time=3:00:00
#SBATCH --mail-type=ALL  # Mail events (NONE, BEGIN, END, FAIL, ALL)
#SBATCH --mail-user=qlin@rcc.uchicago.edu  # Where to send email


n=$(( SLURM_NNODES * SLURM_NTASKS_PER_NODE ))

export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK

module load meep/1.27.0+oneapi-2023.1
source activate meep
mpirun -np $n python3 /home/qlin/sim_code/resonance3Dnew.py
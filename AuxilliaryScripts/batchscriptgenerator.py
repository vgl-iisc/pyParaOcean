import sys
import os

lognametype = "streamlinesfive_bigdataset_np_"
paraviewscriptpath="/home/toshitjain/scripts/streamtracer_big_fivetimes.py"
numnodes = 5
numcores = [2,4,8,16,32,48,64,80,96,112,128,144,160]
pathtologs = "/home/toshitjain/logs/"
filenames = []

for numcore in numcores:
    filename=lognametype+str(numcore)+".sh"
    with open(filename, 'w') as f:
        lines=['#!/bin/bash\n', '#SBATCH --job-name='+lognametype+'exp'+str(numcore)+'\n', '#SBATCH --ntasks-per-node=32\n', '#SBATCH --nodes='+str(numnodes)+'\n', '\n', '#SBATCH --time=00:10:00\n', '#SBATCH -o testslurm_job%j.out\n', '#SBATCH -e '+lognametype+'exp'+str(numcore)+'.out'+'\n', '##SBATCH --gres=gpu:1\n', '#SBATCH --partition=debug\n', '\n', 'echo "Number of Nodes Allocated      = $SLURM_JOB_NUM_NODES"\n', 'echo "Number of Tasks Allocated      = $SLURM_NTASKS"\n', 'echo "Number of Cores/Task Allocated = $SLURM_CPUS_PER_TASK"\n', '\n', 'export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH\n', 'export LD_LIBRARY_PATH=/home/toshitjain/paraview_build/lib64:/home/toshitjain/lib:/apps/installed/openmpi/41/lib:/home/toshitjain/paraview_build/lib64:/home/toshitjain/lib:$LD_LIBRARY_PATH\n', '\n', 'export PATH=/home/toshitjain/paraview-bins/ParaView-5.11.0-osmesa-MPI-Linux-Python3.9-x86_64/bin:/usr/local/Qt-5.15.8/bin:/home/toshitjain/bin:/opt/xcat/bin:/opt/xcat/sbin:/opt/xcat/share/xcat/tools:/apps/installed/openmpi/41/bin:/usr/local/Qt-5.15.8/bin:/home/toshitjain/bin:/opt/xcat/bin:/opt/xcat/sbin:/opt/xcat/share/xcat/tools:/apps/installed/module/v52/bin:/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/usr/local/texlive/2023/bin/x86_64-linux:/usr/local/texlive/2023/bin/x86_64-linux:/home/toshitjain/.local/bin:/home/toshitjain/bin:/usr/local/texlive/2023/bin/x86_64-linux:$PATH\n\n']
        f.writelines(lines)

        command = "mpiexec -np "+str(numcore)+" pvbatch -v MAX -l MAX " +paraviewscriptpath+" &> "+pathtologs + lognametype +str(numcore)

        f.write(command)
    
    os.system("chmod +x "+filename)
    filenames.append(filename)

scriptname="runthis_"+lognametype+".sh"
with open(scriptname, 'w') as f:
    f.write('#!/bin/bash\n')
    for filename in filenames:
        f.write('sbatch '+filename+'\n')

os.system("chmod +x "+scriptname)





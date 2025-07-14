#assumes paraview version 5.11.0
#import paraview
#paraview.compatibility.major = 5
#paraview.compatibility.minor = 11

from paraview.simple import *

##############################
### USER INPUT PARAMAETERS ###
##############################
'''run the script for all timesteps in dataset'''
_flagRunForAllTimesteps = 0 

'''set to zero if eddy detection has already run once for your data'''
_flagComputeSeeds = 1

'''path to directory where (pre)computed point data from eddy detection is stored, end with slash'''
_pvdfolderpath = "/home/toshit/Downloads/varun/scratch/points/"

'''tTKScalarFieldSmoother1.IterationNumber'''
_numSmoothingIterations = 5

'''topological simplification persistence threshold, between 0 and 1'''
_persistenceThreshold = 0.1

'''(vertical) display scale along the z-axis, between 0 and 1'''
_zDisplayScale = 0.01

################################################
### SETTING UP PIPELINE FOR SEED COMPUTATION ###
################################################

#assumes data file is selected in pipeline view
#fetches current timestamp and extents
netcdf4Datafile = GetActiveSource()
_xmin,_xmax,_ymin,_ymax,_zmin,_zmax = netcdf4Datafile.GetDataInformation().GetExtent()
_time = netcdf4Datafile.GetDataInformation().DataInformation.GetTime()

#extracts depth slice
extractSubset1 = ExtractSubset(registrationName='ExtractSubset1', Input=netcdf4Datafile)
extractSubset1.VOI = [_xmin, _xmax, _ymin, _ymax, _zmin, _zmin]
UpdatePipeline(time=_time, proxy=extractSubset1)

#veloicty in depth slice
calculator1 = Calculator(registrationName='Calculator1', Input=extractSubset1)
calculator1.ResultArrayName = 'velocitySlice'
calculator1.Function = 'uo*iHat + vo*jHat'
UpdatePipeline(time=_time, proxy=calculator1)

#speed in depth slice
calculator2 = Calculator(registrationName='Calculator2', Input=calculator1)
calculator2.ResultArrayName = 'speedSlice'
calculator2.Function = 'mag(velocitySlice)'
UpdatePipeline(time=_time, proxy=calculator2)

#need cube grid for TTK Scalar field filters
resampleToImage1 = ResampleToImage(registrationName='ResampleToImage1', Input=calculator2)
resampleToImage1.SamplingDimensions = [(_xmax-_xmin+1), (_ymax-_ymin+1), 1]
UpdatePipeline(time=_time, proxy=resampleToImage1)

#smooth the velocity magnitude field
tTKScalarFieldSmoother1 = TTKScalarFieldSmoother(registrationName='TTKScalarFieldSmoother1', Input=resampleToImage1)
tTKScalarFieldSmoother1.IterationNumber = _numSmoothingIterations
UpdatePipeline(time=_time, proxy=tTKScalarFieldSmoother1)

#simplification
tTKTopologicalSimplificationByPersistence1 = TTKTopologicalSimplificationByPersistence(registrationName='TTKTopologicalSimplificationByPersistence1', Input=tTKScalarFieldSmoother1)
tTKTopologicalSimplificationByPersistence1.PairType = 'Minimum-Saddle'
tTKTopologicalSimplificationByPersistence1.PersistenceThreshold = _persistenceThreshold
UpdatePipeline(time=_time, proxy=tTKTopologicalSimplificationByPersistence1)

#find critical points
tTKScalarFieldCriticalPoints1 = TTKScalarFieldCriticalPoints(registrationName='TTKScalarFieldCriticalPoints1', Input=tTKTopologicalSimplificationByPersistence1)
UpdatePipeline(time=_time, proxy=tTKScalarFieldCriticalPoints1)

#keep only local minima
programmableFilter1 = ProgrammableFilter(registrationName='ProgrammableFilter1', Input=tTKScalarFieldCriticalPoints1)
programmableFilter1.Script = """import paraview.util.vtkAlgorithm
 
from vtkmodules.numpy_interface import algorithms as algs
from vtkmodules.vtkCommonDataModel import vtkDataSet,vtkPolyData
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtkmodules.numpy_interface import dataset_adapter as dsa
from vtkmodules.vtkFiltersCore import vtkAppendPolyData, vtkCleanPolyData

import vtk
import numpy as np
import random

C = inputs[0].PointData["CriticalType"]
pids = algs.where(C == 0)
coords = inputs[0].GetPoints()[pids]


pts = vtk.vtkPoints()
pts.SetData(dsa.numpyTovtkDataArray(coords, "Points"))
output.SetPoints(pts)
numPts = pts.GetNumberOfPoints()
ptIds = vtk.vtkIdList()
ptIds.SetNumberOfIds(numPts)
for a in range(numPts):
    ptIds.SetId(a, a)

output.Allocate(1)
output.InsertNextCell(vtk.VTK_POLY_VERTEX, ptIds)
"""
UpdatePipeline(time=_time, proxy=programmableFilter1)

#detect potential eddy centres and their width
programmableFilter2 = ProgrammableFilter(registrationName='ProgrammableFilter2', Input=[tTKTopologicalSimplificationByPersistence1, programmableFilter1])
programmableFilter2.OutputDataSetType = 'vtkPolyData'
programmableFilter2.Script = """#!/usr/bin/python
# -*- coding: utf-8 -*-
import paraview.util.vtkAlgorithm 
from vtkmodules.numpy_interface import algorithms as algs
from vtkmodules.vtkCommonDataModel import vtkDataSet, vtkPolyData
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtkmodules.numpy_interface import dataset_adapter as dsa
from vtkmodules.vtkFiltersCore import vtkAppendPolyData, \\
    vtkCleanPolyData
from vtkmodules.util import numpy_support
import vtk
import numpy as np
import random

input0 = inputs[0]
input1 = inputs[1]

(  # structured coordinates
    xmin,
    xmax,
    ymin,
    ymax,
    zmin,
    zmax,
    ) = input0.GetExtent()
(  # coordinates
    coordXmin,
    coordXmax,
    coordYmin,
    coordYmax,
    coordZmin,
    coordZmax,
    ) = input0.GetBounds()

v = input0.PointData[\'velocitySlice\']
seeds = input1.GetPoints()


    

def in_bounds(p, B):
    for i in range(3):
        if p[i] < B[2 * i]:
            return False
        if p[i] > B[2 * i + 1]:
            return False
    return True


dim2pid = lambda x: x[0] + (1 + xmax) * x[1] + (1 + xmax) * (1 + ymax) * x[2]


def find_nearest_point(p):
    (x, y, z) = (p[0], p[1], p[2])
    dx = x - coordXmin
    dy = y - coordYmin
    dz = z - coordZmin
    ix = int(dx / (coordXmax - coordXmin) * xmax)
    iy = int(dy / (coordYmax - coordYmin) * ymax)
    iz = (0 if zmax == 0 else int(dz / (coordZmax - coordZmin) * zmax))

    return (ix, iy, iz)


def get_quadrant(p):
    (x, y, z) = (p[0], p[1], p[2])
    if x >= 0 and y > 0:
        return 1
    elif x <= 0 and y > 0:
        return 2
    elif x <= 0 and y < 0:
        return 3
    else:
        return 4

def is_valid_qseq(q):
    if q == [0,1,2,3,4,1]:
        return True
    if q == [0,4,3,2,1,4]:
        return True
    return False

def integ(centre, offset, h):
    r = np.zeros((nsteps, 3))
    r[0] = centre + offset

    numPts = 1
    qseq = [0]

    for i in range(nsteps - 1):

        if not in_bounds(r[i], input0.GetBounds()):
            #print (centre, \'went out of bounds\')
            break

        tpid = dim2pid(find_nearest_point(r[i]))
        r[i + 1] = r[i] + v[tpid] * h
        numPts += 1

        q = get_quadrant(r[i + 1] - centre)
        if qseq[-1] != q:
            qseq.append(q)

        if len(qseq) == 6:
            #print (centre, qseq)
            break

    return r[0:numPts], is_valid_qseq(qseq) and np.linalg.norm(r[numPts-1] - r[0]) < dc


# print(input0.GetPoint(dim2pid(find_nearest_point(88,10, -0.5))))

nsteps = 10000
h = 0.01
max_xoffset = 1
dc = 0.4
goodseeds = []
xoffsets = []

#r, q = integ(seeds[1],[3,0,0], h)
for seedidx in range(len(seeds)):
    valid = False
    for xoffset in np.arange(0.1, 3, 0.1):
        _ , qfv = integ(seeds[seedidx], [xoffset,0,0], h)
        _ , qbv = integ(seeds[seedidx], [xoffset,0,0], -h)
        if qfv or qbv:
            if not valid:
                goodseeds.append(seeds[seedidx])
                xoffsets.append(xoffset)
                valid = True
            else:
                xoffsets[-1] = xoffset
        else:
            break

print(goodseeds, xoffsets)

output.Points = goodseeds
pointIds = vtk.vtkIdList()
pointIds.SetNumberOfIds(len(goodseeds))
for i in range(len(goodseeds)):
    pointIds.SetId(i, i)
output.Allocate(1, 1) 
output.InsertNextCell(vtk.VTK_POLY_VERTEX, pointIds)
output.PointData.append(np.array(xoffsets), "xoffset")"""
UpdatePipeline(time=_time, proxy=programmableFilter2)

#create seeds for generating streamlines 
programmableFilter3 = ProgrammableFilter(registrationName='ProgrammableFilter3', Input=programmableFilter2)
programmableFilter3.Script = """#!/usr/bin/python
# -*- coding: utf-8 -*-
import paraview.util.vtkAlgorithm 

from vtkmodules.numpy_interface import algorithms as algs
from vtkmodules.vtkCommonDataModel import vtkDataSet, vtkPolyData
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtkmodules.numpy_interface import dataset_adapter as dsa
from vtkmodules.vtkFiltersCore import vtkAppendPolyData, \\
    vtkCleanPolyData
from vtkmodules.util import numpy_support
import vtk
import numpy as np
import random

input0 = inputs[0]

centres = input0.GetPoints()
xoffsets = input0.PointData["xoffset"]

n = 9

seeds = []

for i in range(len(centres)):
    a = centres[i]
    b = centres[i] + [xoffsets[i],0,0]
    seeds.append(a)
    for j in range(n):
        seeds.append(a + (b-a) / n * (j))

pts = vtk.vtkPoints()
pts.SetData(dsa.numpyTovtkDataArray(seeds, "seeds"))
output.SetPoints(pts)
numPts = pts.GetNumberOfPoints()
ptIds = vtk.vtkIdList()
ptIds.SetNumberOfIds(numPts)
for a in range(numPts):
    ptIds.SetId(a, a)

output.Allocate(1)
output.InsertNextCell(vtk.VTK_POLY_VERTEX, ptIds)
output.PointData.append(np.arange(numPts), "num")"""
UpdatePipeline(time=_time, proxy=programmableFilter3)

#############################################################
## EXECUTING SEED COMPUTATION PIPELINE IF REQUIRED BY USER ##
#############################################################

if _flagComputeSeeds:
    for _z in range(_zmin,_zmax+1):
        # Properties modified on extractSubset1
        extractSubset1.VOI = [_xmin, _xmax, _ymin, _ymax, _z, _z]
        UpdatePipeline(time=_time, proxy=extractSubset1)
        # save data
        SaveData(_pvdfolderpath+str(_z)+'.pvd', proxy=programmableFilter3, PointDataArrays=['num'],
            FieldDataArrays=['time_calendar', 'time_units', 'uo_units', 'vo_units'], WriteTimeSteps=_flagRunForAllTimesteps)

########################################
## DELETING SEED COMPUTATION PIPELINE ##
########################################

Delete(programmableFilter3)
del programmableFilter3
Delete(programmableFilter2)
del programmableFilter2
Delete(programmableFilter1)
del programmableFilter1
Delete(tTKScalarFieldCriticalPoints1)
del tTKScalarFieldCriticalPoints1
Delete(tTKTopologicalSimplificationByPersistence1)
del tTKTopologicalSimplificationByPersistence1
Delete(tTKScalarFieldSmoother1)
del tTKScalarFieldSmoother1
Delete(resampleToImage1)
del resampleToImage1
Delete(calculator2)
del calculator2
Delete(calculator1)
del calculator1
Delete(extractSubset1)
del extractSubset1


################################################
## SETTING UP PIPELINE FOR EDDY VISUALIZATION ##
################################################

#calculate velocity in whole domain
calculator1 = Calculator(registrationName='Calculator1', Input=netcdf4Datafile)
calculator1.ResultArrayName = 'veocity'
calculator1.Function = 'uo*iHat + vo*jHat'
UpdatePipeline(time=_time, proxy=calculator1)

#load seeds for each depth slice
_pvdlist = []
for _z in range(_zmin,_zmax+1):
    _pvd = PVDReader(registrationName=str(_z)+'.pvd', FileName=_pvdfolderpath+str(_z)+'.pvd')
    _pvdlist.append(_pvd)

#collate seeds from all depth slices
appendDatasets1 = AppendDatasets(registrationName='AppendDatasets1', Input=_pvdlist)
UpdatePipeline(time=_time, proxy=appendDatasets1)

renderView1 = GetActiveViewOrCreate('RenderView')
Hide(netcdf4Datafile,renderView1)

# stream tracer 
'''
Stream Tracer filter generates streamlines in a vector field from a collection of seed points. Production of streamlines terminates if a streamline crosses the exterior boundary of the input dataset (ReasonForTermination=1). Other reasons for termination include an initialization issue (ReasonForTermination=2), computing an unexpected value (ReasonForTermination=3), reached the Maximum Streamline Length input value (ReasonForTermination=4), reached the Maximum Steps input value (ReasonForTermination=5), and velocity was lower than the Terminal Speed input value (ReasonForTermination=6). This filter operates on any type of dataset, provided it has point-centered vectors. The output is polygonal data containing polylines.
'''
streamTracerWithCustomSource1 = StreamTracerWithCustomSource(registrationName='StreamTracerWithCustomSource1', Input=calculator1,
    SeedSource=appendDatasets1)
streamTracerWithCustomSource1.Vectors = ['POINTS', 'veocity']
streamTracerWithCustomSource1.MaximumStreamlineLength = (_xmax-_xmin)/2

# keeping only certain streamlines, see earlier comment
threshold1 = Threshold(registrationName='Threshold1', Input=streamTracerWithCustomSource1)
threshold1.Scalars = ['CELLS', 'ReasonForTermination']
threshold1.LowerThreshold = 3
threshold1.UpperThreshold = 6
threshold1Display = Show(threshold1, renderView1, 'UnstructuredGridRepresentation')
ColorBy(threshold1Display, ('POINTS', 'veocity', 'Magnitude'))
threshold1Display.Scale = [1.0, 1.0, _zDisplayScale]



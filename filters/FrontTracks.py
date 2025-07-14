import numpy as np
import vtk
import os
import sys
import time
import math
import errno
import multiprocessing as mp
import datetime
import networkx as nx
from scipy import ndimage

from paraview.util.vtkAlgorithm import *
from vtkmodules.numpy_interface import algorithms as algs
from vtkmodules.vtkCommonDataModel import vtkDataSet, vtkPolyData, vtkUnstructuredGrid
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtkmodules.numpy_interface import dataset_adapter as dsa
   
from vtk import vtkPolyDataWriter, vtkMutableDirectedGraph, vtkPoints, vtkGraphToPolyData, vtkXMLPolyDataWriter


@smproxy.filter(label="Front Tracks")
@smproperty.input(name="Input")
@smproperty.xml("""
  <Hints>
    <ShowInMenu category='pyParaOcean Filters'/>
  </Hints>""")
class FrontTracks(VTKPythonAlgorithmBase):
    # the rest of the code here is unchanged.
    def __init__(self):
        self.datafilepath = ""
        self.v_limit = 35
        self.lt_origin = 5
        self.ln_origin = 75
        self.lt_clip = 6
        self.ln_clip = 80
        self.v_name = "so"
        self.bound_lon = 84,88
        self.bound_lat = 14,19
        super().__init__(nInputPorts=1, nOutputPorts=1, outputType="vtkPolyData")

    def RequestDataObject(self, request, inInfo, outInfo):
        inData = self.GetInputData(inInfo, 0, 0)
        outData = self.GetOutputData(outInfo, 0)

        assert inData is not None
        if outData is None or (not outData.IsA(inData.GetClassName())):
            outData = inData.NewInstance()
            outInfo.GetInformationObject(0).Set(outData.DATA_OBJECT(), outData)
        return super().RequestDataObject(request, inInfo, outInfo)

    # text box indicating which file
    @smproperty.stringvector(name="NetCDF file Path",
                             default_values='home/ocean-visualization-dashboard/scripts/')
    def SetPath(self, filename):
        if filename is None:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), filename)
        else:
            self.datafilepath = filename
        self.Modified()
        
        
    @smproperty.intvector(name="Salinity upper bound (psu)", default_values="35")
    @smdomain.intrange(min=0, max=100)
    def Set_v_limit(self, x):
        self.v_limit = x
        self.Modified()
        
    @smproperty.intvector(name="Origin Latitude", default_values="5")
    def Set_lt_origin(self, x):
        self.lt_origin = x
        self.Modified()
        
    @smproperty.intvector(name="Origin Longitude", default_values="75")
    def Set_ln_origin(self, x):
        self.ln_origin = x
        self.Modified()
        
    @smproperty.stringvector(name="Longitude Boundaries",
                             default_values='84,88')
    def SetBoundLon(self, x):
        self.bound_lon = x
        self.Modified()
        
    @smproperty.stringvector(name="Latitude Boundaries",
                             default_values='14,19')
    def SetBoundLat(self, x):
        self.bound_lat = x
        self.Modified()

    def RequestData(self, request, inInfo, outInfo):

        # input0 = dsa.WrapDataObject(vtkUnstructuredGrid.GetData(inInfo[0]))
        output = dsa.WrapDataObject(vtkPolyData.GetData(outInfo))
        pdi = self.GetInputData(inInfo, 0, 0)
        pdo = self.GetOutputData(outInfo, 0)

        wpdi = dsa.WrapDataObject(pdi)
        # pts = wpdi.Points

        CODE_PATH = 'home/ocean-visualization-dashboard/scripts/FrontTracks/'
        
        parametersStr = """
v_limit = """ + str(self.v_limit) + """
lt_origin = """ + str(self.lt_origin) + """
ln_origin = """ + str(self.ln_origin) + """
lt_clip = 6
ln_clip = 80
TrackGraph input =""" + self.datafilepath + """
TrackGraph_output = alltracks_clipped
d_max = 200
resolution = 1.0/12.0
neighborhood = 70
interpolation = 1
v_name = so
depth_name = depth
set_bound_lon = """ + self.bound_lon + """
set_bound_lat = """ + self.bound_lat + """
paths = 5
"""

        with open('parameter.txt', 'w') as f:
            f.write(parametersStr)


        cmd = 'python3 ComputeTrackGraph.py'
        print("DEBUG: ", cmd)
        os.system(cmd)
        
        file_name = CODE_PATH+"computedTracks.vtp"
        reader = vtk.vtkXMLPolyDataReader()
        reader.SetFileName(file_name)
        reader.Update()
        tracksPolyData = reader.GetOutput()
        output.ShallowCopy(tracksPolyData)
	
	
	
        return 1

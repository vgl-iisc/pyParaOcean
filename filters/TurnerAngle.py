from paraview.util.vtkAlgorithm import *
import numpy as np
import vtk

from vtkmodules.numpy_interface import algorithms as algs
from vtkmodules.vtkCommonDataModel import vtkDataSet, vtkPolyData
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtkmodules.numpy_interface import dataset_adapter as dsa
from vtkmodules import vtkCommonCore
import os
from paraview.simple import GetActiveViewOrCreate, GetDisplayProperties
import sys
import time

@smproxy.filter(label="Turner Angle")
@smproperty.input(name="Input")
@smproperty.xml("""
    <OutputPort index="0" name='Slice'/>
    <OutputPort index="1" name='Slice_2'/>
    <Hints>
        <ShowInMenu category="pyParaOcean Filters"/>
    </Hints>
""")

class TurnerAngle(VTKPythonAlgorithmBase):
    def __init__(self):
        super().__init__(nInputPorts = 1, nOutputPorts = 2)

        self.z1 = 70
        self.z2 = 72

        self.salinity_variable_name = "so"
        self.temperature_variable_name = "thetao"
        self.gsw_path = ''

    def get_slice(self, pdi, depth):
        plane = vtk.vtkPlane()
        plane.SetOrigin(0, 0, depth)
        plane.SetNormal(0, 0, 1)
        cutter = vtk.vtkCutter()
        cutter.SetCutFunction(plane)
        cutter.SetInputData(pdi)
        cutter.Update()

        return cutter
        
    @smproperty.doublevector(name = "Set Depth Levels", default_values = [70, 72])
    def SetDepths(self, x, y):
        self.z1 = x
        self.z2 = y
        self.Modified()

    @smproperty.stringvector(name = "Salinity Variable Name", default_values = "so")
    def SetSalinityName(self, x):
        self.salinity_variable_name = x
        self.Modified()

    @smproperty.stringvector(name = "Temperature Variable Name", default_values = "thetao")
    def SetTemperatureName(self, x):
        self.temperature_variable_name = x
        self.Modified()

    @smproperty.stringvector(name = "gsw Library Path", default_values = "/home/user-name/.local/lib/python3.10/site-packages")
    def SetGswPath(self, x):
        self.gsw_path = x
        self.Modified()

    def RequestData(self, request, inInfo, outInfo):

        if self.gsw_path not in sys.path:
            sys.path.append(self.gsw_path)   

        import gsw
     
        input0 = dsa.WrapDataObject(vtkDataSet.GetData(inInfo[0]))

        # -------------------------------------------------------
        print("Appending Longitude values to dataset...")

        longitude_data = vtk.vtkDoubleArray()
        longitude_data.SetName("Longitude")

        for i in range(input0.GetNumberOfPoints()):
            x_coord = input0.GetPoint(i)[0]
            longitude_data.InsertNextValue(x_coord)

        input0.GetPointData().AddArray(longitude_data)

        print("----- DONE! -----")
        # -------------------------------------------------------
        print("\nAppending Latitude values to dataset...")

        latitude_data = vtk.vtkDoubleArray()
        latitude_data.SetName("Latitude")

        for i in range(input0.GetNumberOfPoints()):
            y_coord = input0.GetPoint(i)[1]
            latitude_data.InsertNextValue(y_coord)
        
        input0.GetPointData().AddArray(latitude_data)

        print("----- DONE! -----")
        # -------------------------------------------------------
        print("\nCalculating 2 slices at given depths...")

        output1 = dsa.WrapDataObject(vtkPolyData.GetData(outInfo, 0))
        output2 = dsa.WrapDataObject(vtkPolyData.GetData(outInfo, 1))

        pdi = self.GetInputData(inInfo, 0, 0)

        start = time.time()

        slice_1 = self.get_slice(pdi, -1*self.z1)
        slice_2 = self.get_slice(pdi, -1*self.z2)

        print("----- DONE! -----")
        # -------------------------------------------------------
        print("\nMaking list of variables: Salinity, Temperature, Longitude and Latitude values...")

        salinity_at_slice_1 = slice_1.GetOutput().GetPointData().GetScalars(self.salinity_variable_name)
        salinity_at_slice_1_list = []
        for i in range(0, salinity_at_slice_1.GetSize()):
            salinity_at_slice_1_list.append(salinity_at_slice_1.GetValue(i))

        temperature_at_slice_1 = slice_1.GetOutput().GetPointData().GetScalars(self.temperature_variable_name)
        temperature_at_slice_1_list = []
        for i in range(0, temperature_at_slice_1.GetSize()):
            temperature_at_slice_1_list.append(temperature_at_slice_1.GetValue(i))

        salinity_at_slice_2 = slice_2.GetOutput().GetPointData().GetScalars(self.salinity_variable_name)
        salinity_at_slice_2_list = []
        for i in range(0, salinity_at_slice_2.GetSize()):
            salinity_at_slice_2_list.append(salinity_at_slice_2.GetValue(i))

        temperature_at_slice_2 = slice_2.GetOutput().GetPointData().GetScalars(self.temperature_variable_name)
        temperature_at_slice_2_list = []
        for i in range(0, temperature_at_slice_2.GetSize()):
            temperature_at_slice_2_list.append(temperature_at_slice_2.GetValue(i))

        longitude_at_slices = slice_1.GetOutput().GetPointData().GetScalars("Longitude")
        longitude_at_slices_list = []
        for i in range(0, longitude_at_slices.GetSize()):
            longitude_at_slices_list.append(longitude_at_slices.GetValue(i))

        latitude_at_slices = slice_2.GetOutput().GetPointData().GetScalars("Latitude")
        latitude_at_slices_list = []
        for i in range(0, latitude_at_slices.GetSize()):
            latitude_at_slices_list.append(latitude_at_slices.GetValue(i))

        print("----- DONE! -----")
        # -------------------------------------------------------
        print("\nCalculating Pressure based on given Latitude...")

        pressure_at_slice_1_list = []
        for i in range(0, len(latitude_at_slices_list)):
            p = gsw.p_from_z(-1*self.z1, latitude_at_slices_list[i])
            pressure_at_slice_1_list.append(p)

        pressure_at_slice_2_list = []
        for i in range(0, len(latitude_at_slices_list)):
            p = gsw.p_from_z(-1*self.z2, latitude_at_slices_list[i])
            pressure_at_slice_2_list.append(p)

        print("----- DONE! -----")
        # -------------------------------------------------------
        print("\nCalculating Absolute Salinity and Conservative Temperature...")

        absolute_salinity_at_slice_1_list = []
        conservative_temperature_at_slice_1_list = []

        absolute_salinity_at_slice_1_list = []
        conservative_temperature_at_slice_2_list = []

        absolute_salinity_at_slice_1_list = gsw.SA_from_SP(salinity_at_slice_1_list, pressure_at_slice_1_list, longitude_at_slices, latitude_at_slices)
        conservative_temperature_at_slice_1_list = gsw.CT_from_pt(absolute_salinity_at_slice_1_list, temperature_at_slice_1_list)

        absolute_salinity_at_slice_2_list = gsw.SA_from_SP(salinity_at_slice_2_list, pressure_at_slice_2_list, longitude_at_slices, latitude_at_slices)
        conservative_temperature_at_slice_2_list = gsw.CT_from_pt(absolute_salinity_at_slice_2_list, temperature_at_slice_2_list)

        print("----- DONE! -----")
        # -------------------------------------------------------
        print("\nCalculating Turner Angle...")

        S = [0, 0]
        T = [0, 0]
        D = [0, 0]
        j = 0
        Tu_list = np.zeros(salinity_at_slice_1.GetSize())
        for i in range(0, salinity_at_slice_1.GetSize()):
            S[j] = absolute_salinity_at_slice_1_list[i]
            S[j+1] = absolute_salinity_at_slice_2_list[i]

            T[j] = conservative_temperature_at_slice_1_list[i]
            T[j+1] = conservative_temperature_at_slice_2_list[i]

            D[j] = pressure_at_slice_1_list[i]
            D[j+1] = pressure_at_slice_2_list[i]

            Tu, Rsubrho, p_mid = gsw.Turner_Rsubrho(S, T, D)
            Tu_list[i] = Tu[0]

        print("----- DONE! -----")
        # -------------------------------------------------------
        print("\nAppending Turner Angle to Dataset...")


        point_data_array = vtk.vtkDoubleArray()
        point_data_array.SetName("Turner_Angle")  # Set the name of the array

        for i in range(0, len(Tu_list)):
            point_data_array.InsertNextValue(Tu_list[i])

        slice_1.GetOutput().GetPointData().AddArray(point_data_array)
        print("----- DONE! -----")
        # -------------------------------------------------------    

        output1.ShallowCopy(slice_1.GetOutput())
        output2.ShallowCopy(slice_2.GetOutput())

        end = time.time()

        print(f"------------------------Time: {end - start}------------------------")
       
        return 1



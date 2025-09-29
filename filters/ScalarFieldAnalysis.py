import vtk
import numpy as np

from vtkmodules.vtkCommonDataModel import vtkPolyData, vtkImageData
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtkmodules.numpy_interface import dataset_adapter as dsa
from vtkmodules.vtkCommonTransforms import vtkTransform
from vtkmodules.vtkCommonDataModel import vtkDataObject
from paraview.util.vtkAlgorithm import smproxy, smproperty

@smproxy.filter(label="Scalar Field Profile")
@smproperty.input(name="Input")
@smproperty.xml("""
<OutputPort index="0" name='VerticalSliceImage'/>
<OutputPort index="1" name='DepthProfileLine'/>
<OutputPort index="2" name='LandMass'/>
<Hints>
    <ShowInMenu category="pyParaOcean Filters"/>
</Hints>
""")
class DepthSalinityImage(VTKPythonAlgorithmBase):
    def __init__(self):
        super().__init__(nInputPorts=1, nOutputPorts=3)
        self.axis = 1
        self.x = 85.5
        self.y = 13.0
        self.z1 = -222.4752
        self.z2 = -0.4940
        self.variable_name = "so"

    @smproperty.doublevector(name="Set Coordinates", default_values=[85.5, 13.0])
    def SetLinePos(self, x, y):
        self.x = x
        self.y = y
        self.Modified()

    @smproperty.doublevector(name="Set Depth Levels", default_values=[-222.4752, -0.4940])
    def SetLineLen(self, z1, z2):
        self.z1 = z1
        self.z2 = z2
        self.Modified()

    @smproperty.stringvector(name="Variable Array Name", default_values=["so"])
    def SetSalinityArray(self, name):
        self.variable_name = name
        self.Modified()

    def FillOutputPortInformation(self, port, info):
        if port == 0:
            info.Set(vtkDataObject.DATA_TYPE_NAME(), "vtkImageData")
        elif port == 1:
            info.Set(vtkDataObject.DATA_TYPE_NAME(), "vtkPolyData")
        elif port == 2:
            info.Set(vtkDataObject.DATA_TYPE_NAME(), "vtkPolyData")
        return 1

    def get_slice(self, pdi):
        plane = vtk.vtkPlane()
        plane.SetOrigin(self.x, self.y, 0)
        plane.SetNormal(self.axis, 0, 0)
        cutter = vtk.vtkCutter()
        cutter.SetCutFunction(plane)
        cutter.SetInputData(pdi)
        cutter.Update()
        return cutter

    def createLine(self, numPoints):
        line = vtk.vtkLineSource()
        line.SetResolution(numPoints)
        line.SetPoint1([self.x, self.y, self.z1])
        line.SetPoint2([self.x, self.y, self.z2])
        line.Update()
        return line

    def RequestData(self, request, inInfo, outInfo):
        from vtkmodules.util.numpy_support import numpy_to_vtk
        from vtkmodules.vtkFiltersCore import vtkThreshold

        reader = self.GetInputAlgorithm(0, 0)
        reader.UpdateInformation()
        info0 = reader.GetOutputInformation(0)
        vtk_times = info0.Get(vtk.vtkStreamingDemandDrivenPipeline.TIME_STEPS())
        if not vtk_times:
            return 0
        times = list(vtk_times)
        nT = len(times)

        nD = 200
        depths = np.linspace(self.z1, self.z2, nD)
        sal_data = np.zeros((nT, nD), dtype=np.float32)

        # Process landmass from first timestep
        info0.Set(vtk.vtkStreamingDemandDrivenPipeline.UPDATE_TIME_STEP(), times[0])
        reader.Update()
        grid0 = reader.GetOutputDataObject(0)

        threshold = vtkThreshold()
        threshold.SetInputData(grid0)
        threshold.SetInputArrayToProcess(0, 0, 0, 0,"so")
        threshold.SetLowerThreshold(-1e9)
        threshold.SetUpperThreshold(0.0)
        threshold.SetThresholdFunction(vtkThreshold.THRESHOLD_BETWEEN)
        threshold.Update()

        land_output = vtkPolyData.GetData(outInfo, 2)
        geo_filter = vtk.vtkGeometryFilter()
        geo_filter.SetInputData(threshold.GetOutput())
        geo_filter.Update()
        land_output.ShallowCopy(geo_filter.GetOutput())

        # Process each time step for salinity
        for ti, t in enumerate(times):
            info0.Set(vtk.vtkStreamingDemandDrivenPipeline.UPDATE_TIME_STEP(), t)
            reader.Update()
            grid = reader.GetOutputDataObject(0)

            cutter = self.get_slice(grid).GetOutput()
            line = self.createLine(nD)
            probe = vtk.vtkProbeFilter()
            probe.SetInputData(line.GetOutput())
            probe.SetSourceData(cutter)
            probe.Update()
            pd = probe.GetOutput()

            sal = pd.GetPointData().GetArray(self.variable_name)
            for di in range(nD):
                sal_data[ti, di] = sal.GetTuple1(di)

            if ti == 0:
                depth_profile = vtkPolyData.GetData(outInfo, 1)
                depth_profile.ShallowCopy(probe.GetOutput())

        img = vtkImageData()
        img.SetDimensions(nT, nD, 1)
        dx = (times[-1] - times[0]) / max(1, nT - 1)
        dy = (depths[-1] - depths[0]) / max(1, nD - 1)
        img.SetOrigin(times[0], depths[0], 0.0)
        img.SetSpacing(dx, dy, 1.0)

        flat = sal_data.flatten(order='F')
        vtkarr = numpy_to_vtk(num_array=flat, deep=True, array_type=vtk.VTK_FLOAT)
        if self.variable_name == "so":
         vtkarr.SetName("Salinity")
        elif  self.variable_name == "thetao":
         vtkarr.SetName("Temperature")
        elif self.variable_name == "uo":
         vtkarr.SetName(" Horizontal velocity")
        else:
         vtkarr.SetName(" Vertical velocity")
            
        img.GetPointData().SetScalars(vtkarr)

        out_img = vtkImageData.GetData(outInfo, 0)
        out_img.ShallowCopy(img)
        return 1

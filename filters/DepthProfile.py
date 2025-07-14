import vtk

from vtkmodules.vtkCommonDataModel import vtkPolyData
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtkmodules.numpy_interface import dataset_adapter as dsa
from vtkmodules.vtkCommonTransforms import vtkTransform
from vtkmodules.vtkCommonDataModel import vtkDataObject
from paraview.util.vtkAlgorithm import smproxy, smproperty

@smproxy.filter(label="Depth Profile")
@smproperty.input(name="Input")
@smproperty.xml("""
<OutputPort index="0" name='Landmass' />
<OutputPort index="1" name='ResampleToImage_Water'/>
<OutputPort index="2" name='LinePlot' />
<Hints>
    <View type="ParallelCoordinatesChartView" port="2" />
    <ShowInMenu category="pyParaOcean Filters"/>
</Hints>
""")

class DepthProfile(VTKPythonAlgorithmBase):
    # the rest of the code here is unchanged.
    def __init__(self):
        # CONSTANTS
        self.VTK_UNSTRUCTURED_GRID_PORTS = [0]
        self.VTK_IMAGE_DATA_PORTS = [1]
        self.VTK_POLY_DATA_PORTS = [2]
        self.PORT_LANDMASS = 0
        self.PORT_RESAMPLE_TO_IMAGE_WATER = 1
        self.PORT_LINEPLOT = 2

        self.INPUT_PORTS = 1
        self.OUTPUT_PORTS = 3

        super().__init__(nInputPorts = self.INPUT_PORTS, nOutputPorts = self.OUTPUT_PORTS)

        #variables set through UI elements
        self.inputVectorStr= "" # default value of the input vector field for vector weighted seeding
        self.inputScalarStr= "" # default value of scalar
        self.seedingStrategy = 1 # default value of seeding strategy  
        self.numSeeds = 300 # default number of seeds
        self.salinity_variable_name = "so"
        self.axis = 1
        self.x = 85.5
        self.y = 13
        self.z1 = -222.47520446777344
        self.z2 = -0.49402499198913574
        self.longitude_dimension = 253
        self.latitude_dimension = 241
        self.depth_dimension = 27

        self.request_data_count = 1

    @smproperty.stringvector(name = "Salinity Variable Name", default_values = "so")
    def SetSalinityName(self, x):
        self.salinity_variable_name = x
        self.Modified()

    @smproperty.intvector(name = "Longitude Dimension", default_values = 253)
    def SetLongitudeDimension(self, x):
        self.longitude_dimension = x
        self.Modified()

    @smproperty.intvector(name = "Latitude Dimension", default_values = 241)
    def SetLatitudeDimension(self, x):
        self.latitude_dimension = x
        self.Modified()

    @smproperty.intvector(name = "Depth Dimension", default_values = 27)
    def SetDepthDimension(self, x):
        self.depth_dimension = x
        self.Modified()

    @smproperty.doublevector(name="Set Coordinates",default_values=[85, 13])
    def SetLinePos(self,x,y):
        self.x = x
        self.y = y
        self.Modified()
        
    @smproperty.doublevector(name="Set Depth Levels",default_values=[0, 200])
    def SetLineLen(self,x,y):
        self.z1 = -1 * x/10.0
        self.z2 = -1 * y/10.0
        # self.z1 = -1 * x/10.0
        # self.z2 = -1 * y/10.0
        #self.z1 = x // original
        #self.z2 = y // original
        self.Modified()
    
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
        # Create the line along which you want to sample
        line = vtk.vtkLineSource()
        line.SetResolution(numPoints)
        line.SetPoint1([self.x, self.y, self.z1])
        line.SetPoint2([self.x, self.y, self.z2])
        line.Update()

        return line

    def FillOutputPortInformation(self, port, info):
        if port in self.VTK_UNSTRUCTURED_GRID_PORTS:
            info.Set(vtkDataObject.DATA_TYPE_NAME(), "vtkUnstructuredGrid") 
        elif port in self.VTK_IMAGE_DATA_PORTS:
            info.Set(vtkDataObject.DATA_TYPE_NAME(), "vtkImageData")
        elif port in self.VTK_POLY_DATA_PORTS:
            info.Set(vtkDataObject.DATA_TYPE_NAME(), "vtkPolyData")

        return 1
    
    def RequestDataObject(self, request, inInfo, outInfo):
        from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid, vtkImageData, vtkStructuredGrid

        for i in range(self.GetNumberOfOutputPorts()):
            if i in self.VTK_UNSTRUCTURED_GRID_PORTS:
                outInfo.GetInformationObject(i).Set(vtkDataObject.DATA_OBJECT(), vtkUnstructuredGrid())
            elif i in self.VTK_IMAGE_DATA_PORTS:
                outInfo.GetInformationObject(i).Set(vtkDataObject.DATA_OBJECT(), vtkImageData())
            elif i in self.VTK_POLY_DATA_PORTS:
                outInfo.GetInformationObject(i).Set(vtkDataObject.DATA_OBJECT(), vtkPolyData())

        return 1
    
    def RequestData(self, request, inInfo, outInfo):
        from vtkmodules.vtkCommonDataModel import vtkRectilinearGrid, vtkStructuredGrid
        from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid, vtkImageData
        from vtkmodules.vtkFiltersCore import vtkThreshold
        from vtkmodules.vtkFiltersGeneral import vtkTransformFilter

        # print(f"RequestData() called: {self.request_data_count}")
        # self.request_data_count += 1

        # Get input/output objects
        input_data = vtkRectilinearGrid.GetData(inInfo[0])
        
        output_data_land = vtkUnstructuredGrid.GetData(outInfo, self.PORT_LANDMASS)
        output_resample_to_image_water = vtkImageData.GetData(outInfo, self.PORT_RESAMPLE_TO_IMAGE_WATER)
        output_lineplot = vtkPolyData.GetData(outInfo, self.PORT_LINEPLOT)

        if output_data_land is None:
            raise RuntimeError("Output object is None. ParaView did not allocate it.")

        # Apply Transform
        transform = vtkTransform()
        transform.Scale(1.0, 1.0, 0.1)  # example translation

        transform_filter = vtkTransformFilter()
        transform_filter.SetTransform(transform)
        transform_filter.SetInputData(input_data)
        transform_filter.Update()
        transformed = transform_filter.GetOutput()

        output_transformed_z_np = dsa.WrapDataObject(transformed)

        longitude_data = vtk.vtkDoubleArray()
        longitude_data.SetName("Depth")

        for i in range(output_transformed_z_np.GetNumberOfPoints()):
            z_coord = output_transformed_z_np.GetPoint(i)[2]
            longitude_data.InsertNextValue(-1 * z_coord * 10)

        output_transformed_z_np.GetPointData().AddArray(longitude_data)

        # Apply Threshold
        threshold_land = vtkThreshold()
        threshold_land.SetInputData(transformed)
        threshold_land.SetInputArrayToProcess(0, 0, 0, 0, self.salinity_variable_name)
        threshold_land.SetLowerThreshold(-100)
        threshold_land.SetUpperThreshold(0.0)
        threshold_land.SetThresholdFunction(threshold_land.THRESHOLD_BETWEEN)
        threshold_land.Update()

        threshold_water = vtkThreshold()
        threshold_water.SetInputData(transformed)
        threshold_water.SetInputArrayToProcess(0, 0, 0, 0, self.salinity_variable_name)
        threshold_water.SetLowerThreshold(0.0)
        threshold_water.SetUpperThreshold(100.0)
        threshold_water.SetThresholdFunction(threshold_water.THRESHOLD_BETWEEN)
        threshold_water.Update()

        # Output
        output_data_land.ShallowCopy(threshold_land.GetOutput())

        Resampler = vtk.vtkResampleToImage()
        Resampler.SetSamplingDimensions(self.longitude_dimension, self.latitude_dimension, self.depth_dimension)
        Resampler.SetInputDataObject(threshold_water.GetOutput())
        # self.Resampler.SetSamplingBounds(xmin, xmax, ymin, ymax, zmin, zmax)
        Resampler.Update()
        output_resample_to_image_water.ShallowCopy(Resampler.GetOutput())

        pdi = transformed
        cutter = self.get_slice(pdi)
        line1 = self.createLine(1000)

        pl = vtk.vtkProbeFilter()
        pl.SetInputData(line1.GetOutput())
        pl.SetSourceData(cutter.GetOutput())
        pl.Update()
        
        output_lineplot.ShallowCopy(pl.GetOutput())

        return 1


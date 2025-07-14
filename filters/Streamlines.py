import numpy as np

from vtkmodules.numpy_interface import algorithms as algs
from vtkmodules.vtkCommonDataModel import vtkPolyData
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtkmodules.numpy_interface import dataset_adapter as dsa
from vtkmodules.vtkCommonTransforms import vtkTransform
from vtkmodules.vtkFiltersGeneral import vtkTransformFilter
from vtkmodules.vtkFiltersCore import vtkAppendPolyData
from vtkmodules.vtkCommonDataModel import vtkDataObject
from vtkmodules.vtkFiltersSources import vtkPointSource

from paraview.util.vtkAlgorithm import smproxy, smproperty
import random

@smproxy.filter(label="Streamlines")
@smproperty.input(name="Input")
@smproperty.xml("""
<OutputPort index="0" name='Landmass' />
<OutputPort index="1" name='Streamlines' />
<Hints>
    <ShowInMenu category="pyParaOcean Filters"/>
</Hints>
""")

class Streamlines(VTKPythonAlgorithmBase):
    # the rest of the code here is unchanged.
    def __init__(self):

        # CONSTANTS
        self.VTK_UNSTRUCTURED_GRID_PORTS = [0]
        self.VTK_POLY_DATA_PORTS = [1]
        self.PORT_LANDMASS = 0
        self.PORT_STREAM_LINES = 1

        self.INPUT_PORTS = 1
        self.OUTPUT_PORTS = 2

        super().__init__(nInputPorts = self.INPUT_PORTS, nOutputPorts = self.OUTPUT_PORTS)

        #variables set through UI elements
        self.inputVectorStr= "" # default value of the input vector field for vector weighted seeding
        self.inputScalarStr= "" # default value of scalar
        self.seedingStrategy = 1 # default value of seeding strategy  
        self.numSeeds = 300 # default number of seeds
        self.salinity_variable_name = "so"

    # textbox to enter flow field vector
    @smproperty.stringvector(name ="Enter Flow Vector Components (comma separated)",
                             default_values='uo,vo')
    def SetVectorField(self, name):
        self.inputVectorStr = name.split(",")
        self.Modified()

    # dropdown to select seeding strategy
    @smproperty.xml("""
          <IntVectorProperty
                        name="Seeding Strategy"
                        command="SetSeedingStrategy"
                        number_of_elements="1"
                        default_values="1">
        <EnumerationDomain name="enum">
          <Entry value="1" text="Uniform"/>
          <Entry value="2" text="Chosen Scalar's Magnitude"/>
          <Entry value="3" text="Curl"/>
          <Entry value="4" text="Vorticity"/>
          <Entry value="5" text="Okubo-Weiss"/>
          <Entry value="6" text="Flow Magnitude"/>
          
        </EnumerationDomain>
        <Documentation>
          This property indicates which seeding strategy will be used.
        </Documentation>
         </IntVectorProperty>
         """)
    def SetSeedingStrategy(self, n):
        self.seedingStrategy = n
        self.Modified()

    @smproperty.stringvector(name = "Salinity Variable Name", default_values = "so")
    def SetSalinityName(self, x):
        self.salinity_variable_name = x
        self.Modified()

    def Tranform_z(self, data):
        t = vtkTransform()
        t.Scale(1, 1, 0.01)

        tf = vtkTransformFilter()
        tf.SetTransform(t)
        tf.SetInputData(data)
        tf.Update()

        return tf
    
    # textbox to enter number of seeding points
    @smproperty.intvector(name ="Number of seeds", default_values=300)
    def SetNumSeeds(self, n):
        self.numSeeds = n
        self.Modified()

    #TODO: deprecate this helper function
    def point_generate(self,input0,id,n):
        ip = vtkPolyData()
        ps1 = vtkPointSource()
        pt = input0.GetPoint(int(id))
        ps1.SetCenter(pt)
        ps1.SetNumberOfPoints(n)
        ps1.SetRadius(0.4)
        ps1.Update()
        ip.ShallowCopy(ps1.GetOutput())
        return ip

    def FillOutputPortInformation(self, port, info):
        if port in self.VTK_UNSTRUCTURED_GRID_PORTS:
            info.Set(vtkDataObject.DATA_TYPE_NAME(), "vtkUnstructuredGrid") 
        elif port in self.VTK_POLY_DATA_PORTS:
            info.Set(vtkDataObject.DATA_TYPE_NAME(), "vtkPolyData")

        return 1
    
    def RequestDataObject(self, request, inInfo, outInfo):
        from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid, vtkRectilinearGrid

        for i in range(self.GetNumberOfOutputPorts()):
            if i in self.VTK_UNSTRUCTURED_GRID_PORTS:
                outInfo.GetInformationObject(i).Set(vtkDataObject.DATA_OBJECT(), vtkUnstructuredGrid())
            elif i in self.VTK_POLY_DATA_PORTS:
                outInfo.GetInformationObject(i).Set(vtkDataObject.DATA_OBJECT(), vtkPolyData())

        return 1
    
    def RequestData(self, request, inInfo, outInfo):
        from vtkmodules.vtkCommonDataModel import vtkRectilinearGrid
        from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid, vtkDataSet
        from vtkmodules.vtkFiltersCore import vtkThreshold
        from vtkmodules.vtkFiltersGeneral import vtkTransformFilter, vtkRectilinearGridToPointSet
        from vtkmodules.vtkFiltersFlowPaths import vtkStreamTracer

        # Get input/output objects
        input_data = vtkRectilinearGrid.GetData(inInfo[0])
        output_data_land = vtkUnstructuredGrid.GetData(outInfo, self.PORT_LANDMASS)
        stream_lines = vtkPolyData.GetData(outInfo, self.PORT_STREAM_LINES)

        if output_data_land is None:
            raise RuntimeError("Output object is None. ParaView did not allocate it.")

        # Convert to vtkPointSet using vtkRectilinearGridToPointSet
        converter = vtkRectilinearGridToPointSet()
        converter.SetInputData(input_data)
        converter.Update()
        pointset = converter.GetOutput()

        # Apply Transform
        transform = vtkTransform()
        transform.Scale(1.0, 1.0, 0.01)  # example translation

        transform_filter = vtkTransformFilter()
        transform_filter.SetTransform(transform)
        transform_filter.SetInputData(pointset)
        transform_filter.Update()
        transformed = transform_filter.GetOutput()

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

        input_data_np = dsa.WrapDataObject(vtkDataSet.GetData(inInfo[0]))
        output_data_water_np = dsa.WrapDataObject(threshold_water.GetOutput())
        
        # Put vector field in velocity
        vec  = []
        for i in self.inputVectorStr:
            vec.append(output_data_water_np.PointData[i])
        try:
            velocity = algs.make_vector(vec[0],vec[1],vec[2])   
        except:
            velocity = algs.make_vector(vec[0],vec[1],np.zeros(len(vec[0])))

        # Compute jacobian
        J = algs.gradient(velocity) # Jacobian
        ux, uy, uz = J[:,0,0], J[:,0,1], J[:,0,2]
        vx, vy, vz = J[:,1,0], J[:,1,1], J[:,1,2]
        wx, wy, wz = J[:,2,0], J[:,2,1], J[:,2,2]

        # Compute seeding distribution
        criterion = None
        if self.seedingStrategy == 1:
                criterion = None
        elif self.seedingStrategy == 2:
                scalarMag = algs.abs(output_data_water_np.PointData[self.inputScalarStr])
                criterion = scalarMag
        elif self.seedingStrategy == 3:
                curlSqrMag = (wy - vz)**2 + (uz - wx)**2 + (vx - uy)**2 
                criterion = curlSqrMag
        elif self.seedingStrategy == 4:
                vorSqrMag = (vx - uy)**2
                criterion = vorSqrMag
        elif self.seedingStrategy == 5:
                okuboWeiss = np.abs((ux - vy)**2 + (vx + uy)**2 - (vx - uy)**2)
                criterion = okuboWeiss
        elif self.seedingStrategy == 6:
                flowMag = algs.mag(velocity)
                criterion = flowMag
        else:
                criterion = None

        # Mask unviable points
        validPointIds = np.where((vx - uy)**2 > 0)[0]
        if criterion is not None:
                criterion = criterion[validPointIds]

        # Sample from set of valid points in domain
        seedPointIds = random.choices(validPointIds, weights=criterion, k=self.numSeeds)
        newSeedPoints = vtkAppendPolyData()

        for idval in seedPointIds:
                newSeedPoints.AddInputData(self.point_generate(output_data_water_np, idval, 1))
        newSeedPoints.Update()

        output_velocity_field = dsa.WrapDataObject(vtkUnstructuredGrid())
        # Populate output ports for velocity and seeds
        output_velocity_field.ShallowCopy(output_data_water_np.VTKObject)
        output_velocity_field.PointData.append(velocity, "velocity")

        #output_seeds.ShallowCopy(newSeedPoints.GetOutput())

        # Create the stream tracer
        streamTracer = vtkStreamTracer()
        streamTracer.SetInputData(output_velocity_field.VTKObject)      # vector field input
        streamTracer.SetSourceData(newSeedPoints.GetOutput())      # seed source
        streamTracer.SetIntegrationDirectionToForward()
        streamTracer.SetMaximumPropagation(500)
        streamTracer.SetInitialIntegrationStep(0.1)
        streamTracer.SetIntegrationStepUnit(2)     # Cell length unit
        streamTracer.SetComputeVorticity(False)

        # Set the velocity field array name
        streamTracer.SetInputArrayToProcess(0, 0, 0, 0, "velocity")  # change as needed

        # Run it
        streamTracer.Update()

        output = streamTracer.GetOutput()
        if output is None:
             raise RuntimeError("StreamTracer failed to produce output.")
        
        stream_lines.ShallowCopy(output)

        return 1


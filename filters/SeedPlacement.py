from paraview.util.vtkAlgorithm import *

from vtkmodules.numpy_interface import algorithms as algs
from vtkmodules.vtkCommonDataModel import vtkDataSet,vtkPolyData
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtkmodules.numpy_interface import dataset_adapter as dsa
from vtkmodules.vtkFiltersCore import vtkAppendPolyData, vtkCleanPolyData

import vtk
import numpy as np
import random

@smproxy.filter(label="Seed Placement")
@smproperty.input(name="Input")
@smproperty.xml("""
<OutputPort index="0" name='Velocity Field'/> #names of output fields in pipeline
<OutputPort index="1" name='Seeds' />
  <Hints>
    <View type="None" port="0" />
    <View type="RenderView" port="1" /> #types of output fields in pipeline
    <ShowInMenu category="pyParaOcean Filters"/>
  </Hints>
                """)
class SeedPlacement(VTKPythonAlgorithmBase):

    def __init__(self):
    
        #variables set through UI elements
        self.inputVectorStr="" # default value of the input vector field for vector weighted seeding
        self.inputScalarStr="" # default value of scalar
        self.seedingStrategy=1 # default value of seeding strategy  
        self.numSeeds=300 # default number of seeds
        
        #not used (yet)
        self.Cache = None
        self.time_index=0
        
        super().__init__(nInputPorts=1, nOutputPorts=2) # initializing with one input port and two output ports


    def FillOutputPortInformation(self, port, info):
        if port==0:
            info.Set(vtk.vtkDataObject.DATA_TYPE_NAME(), "vtkDataSet") # the type for velocity field is vtkDataSet
        else:
            info.Set(vtk.vtkDataObject.DATA_TYPE_NAME(), "vtkPolyData") # the type for seeds is vtkPolyData; vtkPolyData is specialized for unstructured geometric data, while vtkDataSet is more general.
        return 1


    # invoked automatically by ParaView's execution pipeline before the RequestData function, which performs the actual data processing.
    # it retrieves information about the input data using GetInputData;
    # it creates/updates and then sets output data object 
    def RequestDataObject(self, request, inInfo, outInfo): 
        inData = self.GetInputData(inInfo, 0, 0)
        outData0 = self.GetOutputData(outInfo, 0)
        outData1 = self.GetOutputData(outInfo, 1)

        assert inData is not None
        
        #preserve the input dataset type
        if outData0 is None or (not outData0.IsA(inData.GetClassName())):
            outData0 = inData.NewInstance()
            outInfo.GetInformationObject(0).Set(outData0.DATA_OBJECT(), outData0)            
        if outData1 is None or (not outData1.IsA(inData.GetClassName())):
            outData1 = inData.NewInstance()
            outInfo.GetInformationObject(1).Set(outData1.DATA_OBJECT(), outData1)

        return super().RequestDataObject(request, inInfo, outInfo)

    # textbox to enter number of seeding points
    @smproperty.intvector(name ="Number of seeds",default_values=300)
    def SetNumSeeds(self, n):
        self.numSeeds = n
        self.Modified()

    # textbox to enter input scalar field name
    @smproperty.stringvector(name ="Enter Scalar Field",
                             default_values='v')
    def SetScalarField(self, name):
        self.inputScalarStr = name
        self.Modified()

    # textbox to enter flow field vector
    @smproperty.stringvector(name ="Enter Flow Vector Components (comma separated)",
                             default_values='u,v')
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

    #TODO: deprecate this helper function
    def point_generate(self,input0,id,n):
        ip = vtkPolyData()
        ps1 = vtk.vtkPointSource()
        pt = input0.GetPoint(int(id))
        ps1.SetCenter(pt)
        ps1.SetNumberOfPoints(n)
        ps1.SetRadius(0.4)
        ps1.Update()
        ip.ShallowCopy(ps1.GetOutput())
        return ip

    # Central function where the actual data processing and output generation happen within a Python plugin. 
    def RequestData(self, request, inInfo, outInfo):

        input0 = dsa.WrapDataObject(vtkDataSet.GetData(inInfo[0]))

        #put vector field in velocity
        vec  = []
        for i in self.inputVectorStr:
            vec.append(input0.PointData[i])
        try:
            velocity = algs.make_vector(vec[0],vec[1],vec[2])
        except:
            velocity = algs.make_vector(vec[0],vec[1],np.zeros(len(vec[0])))

        #compute jacobian
        J = algs.gradient(velocity) #Jacobian
        ux, uy, uz = J[:,0,0], J[:,0,1], J[:,0,2]
        vx, vy, vz = J[:,1,0], J[:,1,1], J[:,1,2]
        wx, wy, wz = J[:,2,0], J[:,2,1], J[:,2,2]

        #compute seeding distribution
        criterion = None
        if self.seedingStrategy == 1:
                criterion = None
        elif self.seedingStrategy == 2:
                scalarMag = algs.abs(input0.PointData[self.inputScalarStr])
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

        #mask unviable points
        validPointIds = np.where((vx - uy)**2 > 0)[0]
        if criterion is not None:
                criterion = criterion[validPointIds]
                
        #sample from set of valid points in domain
        seedPointIds = random.choices(validPointIds, weights=criterion, k=self.numSeeds)
        newSeedPoints = vtkAppendPolyData()
        for idval in seedPointIds:
                newSeedPoints.AddInputData(self.point_generate(input0, idval, 1))
        newSeedPoints.Update()

        #populate output ports for velocity and seeds
        outputFlowField =  dsa.WrapDataObject(vtkDataSet.GetData(outInfo, 0))
        outputFlowField.ShallowCopy(input0.VTKObject)
        outputFlowField.PointData.append(velocity,"velocity")

        outputSeeds = dsa.WrapDataObject(vtkPolyData.GetData(outInfo,1))
        outputSeeds.ShallowCopy(newSeedPoints.GetOutput())

        return 1

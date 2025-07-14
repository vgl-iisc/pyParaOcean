from paraview.util.vtkAlgorithm import *
import numpy as np
import vtk

from vtkmodules.numpy_interface import algorithms as algs
from vtkmodules.vtkCommonDataModel import vtkDataSet,vtkPolyData
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtkmodules.numpy_interface import dataset_adapter as dsa

import paraview
# new module for ParaView-specific decorators.
from paraview.util.vtkAlgorithm import smproxy, smproperty, smdomain

import warnings
warnings.filterwarnings('ignore')
import errno
import os

from paraview.simple import GetActiveViewOrCreate,GetDisplayProperties


@smproxy.filter(label="pyParaOcean:AnalysisFilter")
@smproperty.input(name="Input")
@smproperty.xml("""  <OutputPort index="0" name='Slice'/>
<OutputPort index="1" name='LinePlot'/>
<Hints>
<View type="ParallelCoordinatesChartView" port="1" also_show_in_current_view="1" />
<ShowInMenu category="pyParaOcean Filters"/>
  </Hints>""")
class AnalysisFilter(VTKPythonAlgorithmBase):
    # the rest of the code here is unchanged.
    def __init__(self):
        # VTKPythonAlgorithmBase.__init__(self)
        self.axis = 1
        self.x = 0
        self.y = 0
        self.z1=-222.47520446777344
        self.z2= -0.49402499198913574
        self.path=""

        # self.fs = GetActiveViewOrCreate('XYChartView')
        # self.fs.BottomAxisTitle = 'Depth'
        self.fs = GetActiveViewOrCreate('PythonView')

        super().__init__(nInputPorts=1, nOutputPorts=2)



    def RequestDataObject(self, request, inInfo, outInfo):
        inData = self.GetInputData(inInfo, 0, 0)
        outData1 = self.GetOutputData(outInfo, 0)
        outData2 = self.GetOutputData(outInfo, 1)
        # outData3 = self.GetOutputData(outInfo, 2)
        assert inData is not None
        if outData1 is None or (not outData1.IsA(inData.GetClassName())):
            outData1 = inData.NewInstance()
            outInfo.GetInformationObject(0).Set(outData1.DATA_OBJECT(), outData1)
        if outData2 is None or (not outData2.IsA(inData.GetClassName())):
            outData2 = inData.NewInstance()
            outInfo.GetInformationObject(1).Set(outData2.DATA_OBJECT(), outData2)

        return super().RequestDataObject(request, inInfo, outInfo)
        

    
    def get_slice(self,pdi):
        plane = vtk.vtkPlane()
        plane.SetOrigin(self.x,self.y,0)
        plane.SetNormal(self.axis,0,0)
        cutter = vtk.vtkCutter()
        cutter.SetCutFunction(plane)
        cutter.SetInputData(pdi)
        cutter.Update()
        return cutter
                




    @smproperty.doublevector(name="Set Coordinates",default_values=[0,0])
    def SetLinePos(self,x,y):
        self.x = x
        self.y= y
        self.Modified()
        
    @smproperty.doublevector(name="Set Depth Levels",default_values=[0,5])
    def SetLineLen(self,x,y):
        self.z1 = x
        self.z2 = y
        self.Modified()


    def createLine(self,numPoints):
        # Create the line along which you want to sample
        line = vtk.vtkLineSource()
        line.SetResolution(numPoints)
        line.SetPoint1([self.x,self.y,self.z1])
        line.SetPoint2([self.x,self.y,self.z2])
        line.Update()
        return line


    def RequestData(self, request, inInfo, outInfo):

        input0 = dsa.WrapDataObject(vtkDataSet.GetData(inInfo[0]))
        output1 = dsa.WrapDataObject(vtkPolyData.GetData(outInfo,0))
        output2 = dsa.WrapDataObject(vtkPolyData.GetData(outInfo,1))
        pdi = self.GetInputData(inInfo,0,0)

        cutter = self.get_slice(pdi)
        output2.ShallowCopy(input0.VTKObject)
        output2.ShallowCopy(cutter.GetOutput())


        line1 = self.createLine(1000)
        pl = vtk.vtkProbeFilter()
        pl.SetInputData(line1.GetOutput())
        pl.SetSourceData(cutter.GetOutput())
        pl.Update()
        output2.ShallowCopy(pl.GetOutput())
        output1.ShallowCopy(cutter.GetOutput())
        script="""
from matplotlib.pyplot import cm
import numpy as np
import paraview.numpy_support
def setup_data(view):
  # Iterate over visible data objects
  for i in range(view.GetNumberOfVisibleDataObjects()):
    # You need to use GetVisibleDataObjectForSetup(i) in setup_data to access the data object.
    dataObject = view.GetVisibleDataObjectForSetup(i)

    # The data object has the same data type and structure as the data object that
    # sits on the server. You can query the size of the data, for instance, or do anything
    # else you can do through the Python wrapping.
    
    # Clean up from previous calls here. We want to unset any of the arrays requested
    # in previous calls to this function.
    view.EnableAllAttributeArrays()
    
    

      

def render(view,width,height):
    from paraview import python_view
    figure = python_view.matplotlib_figure(width,height)
    numObjects = view.GetNumberOfVisibleDataObjects()
    for i in range(numObjects):
        dataObject = view.GetVisibleDataObjectForRendering(i)
        

        if dataObject:
            pd = dataObject.GetPointData()
            n_arr = pd.GetNumberOfArrays()


            vtk_points = dataObject.GetPoints()
            
            if vtk_points:
                vtk_points_data = vtk_points.GetData()
                pts = paraview.numpy_support.vtk_to_numpy(vtk_points_data)

                x, y,z = pts[:,0], pts[:,1],pts[:,2]
                names=[]
                for j in range(n_arr):
                    name = pd.GetArrayName(j)

                    if name!="vtkValidPointMask":
                        names.append(name)

                col=2
                nn=len(names)
                row = (nn)//col
                row += (nn)%col
                pos = range(1,nn+1)
                color = iter(cm.rainbow(np.linspace(0, 1, nn)))
                for j in range(nn):
                    c=next(color)
                    name = pd.GetArrayName(j)

                    tmp = dataObject.GetPointData().GetArray(name)
                    ax = figure.add_subplot(row,col,pos[j])
                    ax.plot(z,tmp,c=c)
                    ax.set_xlabel('Depth')
                    ax.set_ylabel(name)                      
                                    
    return python_view.figure_to_image(figure)   
        """
        self.fs.Script = script

        return 1



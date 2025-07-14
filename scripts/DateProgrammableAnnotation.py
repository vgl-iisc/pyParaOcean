'''
to = self.GetTableOutput()
arr = vtk.vtkStringArray()
arr.SetName("Text")
arr.SetNumberOfComponents(1)
arr.InsertNextValue("YourString")
to.AddColumn(arr)
'''

import datetime

to = self.GetTableOutput()

hoursSince1950 = float(inputs[0].RowData["Text"].GetValue(0)[6:])
start = datetime.date.fromisoformat('1950-01-01')
td = datetime.timedelta( hoursSince1950 / 24)
now = start + td
nowStr = now.strftime("%d. %B %Y")

vtkStr = vtk.vtkStringArray()
vtkStr.SetName("Time")
vtkStr.SetNumberOfComponents(1)
vtkStr.InsertNextValue(nowStr)

to.AddColumn(vtkStr)

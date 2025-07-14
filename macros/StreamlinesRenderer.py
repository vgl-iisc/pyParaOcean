from paraview.simple import *

# Constants
PORT_LANDMASS = 0
PORT_STREAMLINES = 1

sources = GetSources()
filters_creation = False
for(key, src) in sources.items():
    if "AnnotateTimeFilter1" in key[0] or "ProgrammableAnnotation1" in key[0] or "TimeStepProgressBar1" in key[0]:
        filters_creation = True

if not filters_creation:
    for (key, src) in sources.items():
        if "Streamlines1" in key[0]:
            try:
                view = GetActiveViewOrCreate("RenderView")

                # Streamlines
                streamlines = OutputPort(src, PORT_STREAMLINES)

                display = Show(streamlines)

                # Safely extract array names from point data
                point_data = streamlines.GetPointDataInformation()
                array_names = [point_data.GetArray(i).GetName()
                                for i in range(point_data.GetNumberOfArrays())]

                if "velocity" in array_names:
                    ColorBy(display, ("POINTS", "velocity"))
                else:
                    print(f"No 'velocity' array found in {key[0]} port 5")

                display.LineWidth = 2
                display.PointSize = 2
                display.RenderLinesAsTubes = 0

                # Show scalar bar (color legend)
                display.SetScalarBarVisibility(view, True)

                # Landmass
                Landmass = OutputPort(src, PORT_LANDMASS)
                display = Show(Landmass)
                display.DiffuseColor = [0.46, 0.46, 0.46]

                #if time_annotation_done is False:
                # --- Create an AnnotateTimeFilter to display time information ---
                timeAnnot = AnnotateTimeFilter(Input = Landmass)
                timeAnnot.Format = "Time: {time:f}"

                # --- Create a ProgrammableAnnotation for custom annotation  ---
                progAnnot = ProgrammableAnnotation(Input = timeAnnot)
                progAnnot.Script = '''
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
                '''
                Show(progAnnot, view)

                # Create TimeStepProgressBar
                tspb = TimeStepProgressBar(Input = Landmass)

                # Display in the render view
                Show(tspb, view)

                Render()

                print(f"Styled Streamlines on {key}")

            except Exception as e:
                print(f"Failed to style Streamlines on {key}: {e}")
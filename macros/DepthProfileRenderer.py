from paraview.simple import *

# Constants
PORT_LANDMASS = 0
PORT_RESAMPLE_TO_IMAGE_WATER = 1
PORT_LINEPLOT = 2

sources = GetSources()
filters_creation = False
for(key, src) in sources.items():
    if "AnnotateTimeFilter1" in key[0] or "ProgrammableAnnotation1" in key[0] or "TimeStepProgressBar1" in key[0]:
        filters_creation = True

if not filters_creation:
    for (key, src) in sources.items():
        if "DepthProfile1" in key[0]:
            try:
                layout = GetLayout()
                views = GetViews()

                render_view = None
                for view in views:
                    if view.GetXMLName() == 'RenderView':
                        render_view = view
                        break

                if render_view:
                    SetActiveView(render_view)
                    print("Render view found and set as active.")
                else:
                    print("No Render View found.")

                # Get specific output ports by name or index
                # Adjust port indices as needed for your filter
                lineplot_output = OutputPort(src, PORT_LINEPLOT)  # Line plot output (polydata with scalar info)

                display_lineplot_output = Show(lineplot_output)
                display_lineplot_output.LineWidth = 3

                resampled_image_output = OutputPort(src, PORT_RESAMPLE_TO_IMAGE_WATER)
                display_resampled_image_output = Show(resampled_image_output)
                ColorBy(display_resampled_image_output, ("POINTS", "thetao"))

                lut = GetColorTransferFunction('thetao')  # retrieves the LUT in use
                lut.ApplyPreset('Black, Blue and White', True)  # apply a color preset
                opacity = GetOpacityTransferFunction('thetao')
                opacity.Points = [0.0, 0.0, 0.5, 0.0, 
                                  7.2424, 0.0, 0.5, 0.0,
                                  16.689, 0.880435, 0.5, 0.0,
                                  26.4505, 0.0, 0.5, 0.0,
                                  33.378, 0.0, 0.5, 0.0]

                display_resampled_image_output.Representation = 'Volume'

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
                Show(progAnnot, render_view)

                # Create TimeStepProgressBar
                tspb = TimeStepProgressBar(Input = Landmass)

                # Display in the render view
                Show(tspb, render_view)

                line = OutputPort(src, PORT_LINEPLOT)
                Show(line, render_view)

                # Find the Parallel Coordinates View
                pc_view = None
                for view in views:
                    if view.GetXMLName() == 'ParallelCoordinatesChartView':
                        pc_view = view
                        break

                cell_id = layout.GetViewLocation(pc_view)

                layout_proxy = layout.SMProxy
                layout_proxy.SplitVertical(cell_id, 0.5)

                chart_view = GetActiveViewOrCreate('XYChartView')

                layout_proxy.AssignView(cell_id, None)
                AssignViewToLayout(view = chart_view, layout = layout, hint = cell_id)

                line_display = Show(line, chart_view)
                line_display.SeriesVisibility = ['so', 'thetao'] 
                line_display.XArrayName = "Depth"
                line_display.UseIndexForXAxis = 0

                SetViewProperties(
                    chart_view,
                    BottomAxisUseCustomRange    = 1,
                    BottomAxisRangeMinimum      = 0.0,
                    BottomAxisRangeMaximum      = 220.0,
                    LeftAxisUseCustomRange      = 1,
                    LeftAxisRangeMinimum        = 8.0,
                    LeftAxisRangeMaximum        = 38.0
                )

                SetActiveView(render_view)

                Render()

                print(f"Styled Depth Profile on {key}")

            except Exception as e:
                print(f"Failed to style Depth Profile on {key}: {e}")
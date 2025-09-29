from paraview.simple import *

# Constants
PORT_1 = 1
PORT_2 = 2
FILTER_NAME = "ScalarFieldProfile1"  # <-- updated name based on your pipeline

# Setup a session-level filter-specific split tracker
if not hasattr(servermanager, 'macro_filter_tracker'):
    servermanager.macro_filter_tracker = {}

# Locate the filter in the pipeline
filter = FindSource(FILTER_NAME)

if not filter:
    print("Filter not found. Please load the filter named:", FILTER_NAME)
else:
    # Check if already processed this filter
    if servermanager.macro_filter_tracker.get(filter, 0) >= 1:
        print("Layout already split for this filter. Reload it to enable again.")
    else:
        renderView1 = GetActiveViewOrCreate('RenderView')
        layout1 = GetLayout()

        try:
            layout1.SplitHorizontal(0, 0.5)
        except:
            print("Layout split failed or already done.")
            servermanager.macro_filter_tracker[filter] = 1
            exit()

        AssignViewToLayout(view=renderView1, layout=layout1, hint=0)

        # Show main filter in left view as slice
        display_main = Show(filter, renderView1, 'UniformGridRepresentation')
        display_main.Representation = 'Slice'
        display_main.SetScalarBarVisibility(renderView1, True)

        # Hide main dataset if exists
        dataset = FindSource('BoB_July_2020_uvst.nc')
        if dataset:
            Hide(dataset, renderView1)

        # Show ports in left view
        Show(OutputPort(filter, PORT_1), renderView1)
        Show(OutputPort(filter, PORT_2), renderView1)

        # Create and assign right render view
        renderView2 = CreateRenderView()
        AssignViewToLayout(view=renderView2, layout=layout1, hint=2)

        # Port 2 in right view with scalar field coloring
        port2_display = Show(OutputPort(filter, PORT_2), renderView2)
        port2_display.Representation = 'Surface'
        ColorBy(port2_display, ('POINTS', 'so'))
        port2_display.RescaleTransferFunctionToDataRange(True)
        port2_display.SetScalarBarVisibility(renderView2, True)

        GetColorTransferFunction('so')
        GetOpacityTransferFunction('so')

        Show(OutputPort(filter, PORT_1), renderView2)

        # Hide previous displays
        Hide(OutputPort(filter, PORT_1), renderView1)
        Hide(OutputPort(filter, PORT_2), renderView1)
        Hide(filter, renderView1)

        # Final visible representation with coordinates
        final_display = Show(filter, renderView1, 'UniformGridRepresentation')
        final_display.SetRepresentationType('Surface')
        final_display.SetScalarBarVisibility(renderView1, True)
        final_display.DataAxesGrid.GridAxesVisibility = 1
        final_display.DataAxesGrid.XTitle = "Time Steps"
        final_display.DataAxesGrid.YTitle = "Depth"
        final_display.DataAxesGrid.ZTitle = ""

        layout1.SetSize(1272, 695)

        renderView1.CameraPosition = [618348.0, -111.4846, 1581.8808017858303]
        renderView1.CameraFocalPoint = [618348.0, -111.4846, 0.0]
        renderView1.CameraParallelScale = 411.66868053724795

        renderView2.CameraPosition = [85.5, 14.0, 359.2317551512789]
        renderView2.CameraFocalPoint = [85.5, 14.0, -111.48461472988129]
        renderView2.CameraParallelScale = 122.51015080438218

        Render()

        servermanager.macro_filter_tracker[filter] = 1
        print(" Macro executed and layout split for the filter.")

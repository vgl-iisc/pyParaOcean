from paraview.simple import *

# Constants
PORT_LANDMASS = 0
PORT_VELOCITY_FIELD = 1
PORT_SEEDS = 2

sources = GetSources()

filters_creation = False

for(key, src) in sources.items():
    if "ParticleTracer1" in key[0] or "TemporalParticlesToPathlines1" in key[0]:
        filters_creation = True

if not filters_creation:
    for (key, src) in sources.items():
        if "Pathlines1" in key[0]:
            try:
                view = GetActiveViewOrCreate("RenderView")

                velocity_field = OutputPort(src, PORT_VELOCITY_FIELD)
                seeds = OutputPort(src, PORT_SEEDS)

                # create a new 'ParticleTracer'
                particleTracer1 = ParticleTracer(registrationName='ParticleTracer1', Input=velocity_field, SeedSource=seeds)
                particleTracer1.SelectInputVectors = ['POINTS', 'velocity']

                Hide(particleTracer1, view)
                Hide(velocity_field, view)
                Hide(seeds, view)

                # Create a new 'Temporal Particles To Pathlines'
                temporalParticlesToPathlines1 = TemporalParticlesToPathlines(registrationName='TemporalParticlesToPathlines1', Input=particleTracer1,
                    Selection=None)

                # Properties modified on temporalParticlesToPathlines1
                temporalParticlesToPathlines1.MaskPoints = 1
                temporalParticlesToPathlines1.MaxTrackLength = 5
                temporalParticlesToPathlines1.IdChannelArray = 'ParticleId'

                display = Show(temporalParticlesToPathlines1)

                # Safely extract array names from point data
                point_data = temporalParticlesToPathlines1.GetPointDataInformation()
                array_names = [point_data.GetArray(i).GetName()
                                for i in range(point_data.GetNumberOfArrays())]

                if "vo" in array_names:
                    ColorBy(display, ("POINTS", "vo"))
                else:
                    print(f"No 'vo' array found")

                display.PointSize = 2
                display.LineWidth = 2
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
                # If desired, you can assign an input. For example:
                # progAnnot.Input = streamlinesOutputs
                Show(progAnnot, view)

                # Create TimeStepProgressBar
                tspb = TimeStepProgressBar(Input = Landmass)

                # Display in the render view
                Show(tspb, view)

                Render()

                print(f"Styled Pathlines on {key}")

            except Exception as e:
                print(f"Failed to style Pathlines on {key}: {e}")
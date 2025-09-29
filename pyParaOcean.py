import sys
import os
sys.path.append(os.getcwd())
#print(sys.path)
import warnings
warnings.filterwarnings('ignore')
sys.path.append(os.path.dirname(__file__))


if(sys.platform == 'linux'):
    #REPLACE THIS LIST WITH YOUR PYTHON PATH/IF SERVER REPLACE WITH SERVER PATH/Conda based python paths are recommended
  PATH=['', '/usr/lib/python310.zip', '/usr/lib/python3.10', '/usr/lib/python3.10/lib-dynload', '/home/ravindra/.local/lib/python3.10/site-packages', '/usr/local/lib/python3.10/dist-packages', '/usr/lib/python3/dist-packages']
    #######
    #PATH=['', '/usr/lib/python310.zip', '/usr/lib/python3.10', '/usr/lib/python3.10/lib-dynload', '/home/ravindra/.local/lib/python3.10/site-packages', '/usr/local/lib/python3.10/dist-packages', '/usr/lib/python3/dist-packages']
  sys.path.extend(PATH)


#from filters.Analysis import *
from filters.DepthProfile import *
#from filters.UniformSeed import *
#from filters.VortexSeeds import * 
#from filters.trackGraph import *
#from filters.FrontTracks import *
from filters.SeedPlacement import *
from filters.Streamlines import *
from filters.Pathlines import *
from filters.ScalarFieldAnalysis import *

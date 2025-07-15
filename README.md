# pyParaOcean : A Paraview Plugin for Ocean Data Visualization

pyParaOcean provides a dashboard for visualizing ocean data.
The system is available as a plugin to [ParaView](https://paraview.org/) and is hence able to leverage its distributed computing capabilities and its rich set of generic analysis and visualization functionalities. pyParaOcean provides modules to support different visual analysis tasks specific to ocean data, such as eddy identification and salinity movement tracking. These modules are available as Paraview filters and the seamless integration results in a system that is easy to install and use.


## Installation:

1. Navigate to this directory

1. Run ```$bash MakeFile.sh```

1. Open Paraview, go to Tools > Manage Plugins > Load New

1. Navigate to this directory and select pyParaOcean.py

InteractiveFrontPath needs to run in the server since it requires parallel computation. If the plugin is loaded in server, then run MakeFile.sh again.


> Use powershell on windows to run the makefile.

> Prerequisites: python3, pip3

> Tested on Paraview v5.11.0

## Documentation
[Sample dataset can be found here.](https://indianinstituteofscience-my.sharepoint.com/:f:/g/personal/vijayn_iisc_ac_in/Ehc8X74KBl1Au85q88AlBg8BcrOMEyW3FypTccIsjwfFrg?e=BzhyJ8)

Other relevant documentation can be found in the ```./Documentaion``` folder.

## References
For more information about this system, refer to the following papers. Please cite the following publication if you use this software in your work.

```
@article{JainpyScalableOcean2025, 
title = {A scalable system for visual analysis of ocean data}, 
author = {Jain, Toshit and Singh, Upkar and Singh, Varun and Boda, Vijay Kumar and Hotz, Ingrid and Vadhiyar, Sathish S. and Vinayachandran, P.N. and Natarajan, Vijay}, 
year = {2025},
pages = 1–18, 
journal = {Computer Graphics Forum}, 
DOI = {10.1111/cgf.15279} 
}
```

```
@inproceedings{JainpyParaOcean2023, 
booktitle = {Workshop on Visualisation in Environmental Sciences (EnvirVis)}, 
editor = {Dutta, Soumya and Feige, Kathrin and Rink, Karsten and Zeckzer, Dirk}, 
title = {{pyParaOcean: A system for visual analysis of ocean data}}, 
author = {Jain, Toshit and Singh, Varun and Boda, Vijay Kumar and Singh, Upkar and Hotz, Ingrid and Vinayachandran, P.N. and Natarajan, Vijay}, 
year = {2023},
pages = 1–8, 
publisher = {The Eurographics Association}, 
ISBN = {978-3-03868-223-3}, 
DOI = {10.2312/envirvis.20231100} 
}
```

## Acknowledgements
This research was funded by a grant from SERB, Govt. of India (CRG/2021/005278), partial support from National Supercomputing Mission, DST, the J. C. Bose Fellowship awarded by the SERB, DST, Govt. of India, and a scholarship from MoE, Govt. of India.

## Copyright
Program: *pyParaOcean*

Copyright (c) 2024 Visualization & Graphics Lab (VGL), Indian Institute of Science. All rights reserved.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.


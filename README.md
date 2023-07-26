# glance-vtr 
Rectilinear Grid is not supported by VTK.js.  
Read vtkRectilinearGrid into Kitware Glance.
- vtkRectilinearGrid to vtkImageData using vtkResampleToImage
- write vtkImageData as VTI files
- use vtkJSONSceneExporter to generate a glance scene

Usage:
```bash
python -m venv .venv
pip install vtk
python app.py data
```

from vtkmodules.vtkIOExport import vtkJSONSceneExporter
from vtkmodules.vtkIOXML import vtkXMLImageDataWriter, vtkXMLImageDataReader, vtkXMLRectilinearGridReader
from vtkmodules.vtkFiltersCore import vtkResampleToImage, vtkArrayCalculator

from vtkmodules.vtkCommonCore import vtkLookupTable

from vtkmodules.vtkCommonDataModel import vtkPiecewiseFunction

from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkPolyDataMapper,
    vtkRenderer,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
    vtkImageMapper,
    vtkVolume,
    vtkColorTransferFunction
)

from vtkmodules.vtkCommonColor import (
    vtkNamedColors
)

from vtkmodules.vtkRenderingVolume import (
    vtkVolumeMapper
)
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleSwitch  # noqa

from vtkmodules.vtkRenderingVolumeOpenGL2 import (
    vtkSmartVolumeMapper
)

from vtkjs_helper import zipAllTimeSteps

import sys, os, shutil, zipfile, logging

try:
    import zlib

    compression = zipfile.ZIP_DEFLATED
except:
    compression = zipfile.ZIP_STORED

logger = logging.getLogger("")

def make_lut():
    ctf = vtkColorTransferFunction()

    ctf.SetNanColor(1, 1, 0)
    ctf.AddRGBPoint(0, 0.23137254902, 0.298039215686, 0.752941176471)
    ctf.AddRGBPoint(0.5, 0.865, 0.865, 0.865)
    ctf.AddRGBPoint(1, 0.705882352941, 0.0156862745098, 0.149019607843)

    return ctf

def convert(folder_path: str):
    output_datasets = []

    func_scale = "\"E-Field\"*10000000000000"
    func_mag = "mag(\"E-Field_Scaled\")"

    for vtr_file_name in os.listdir(folder_path):
        reader = vtkXMLRectilinearGridReader()
        reader.SetFileName(folder_path + '/' + vtr_file_name)
        reader.Update()

        rectilinear_grid = reader.GetOutput()

        input_dimensions = rectilinear_grid.GetDimensions()
        logger.debug(vtr_file_name + ":")
        logger.debug("Dimensions: " + str(input_dimensions))

        resample = vtkResampleToImage()
        resample.SetInputConnection(reader.GetOutputPort())
        resample.SetSamplingDimensions(100, 100, 100)
        resample.Update()

        calc_scale = vtkArrayCalculator()
        calc_scale.AddVectorArrayName("E-Field")
        calc_scale.SetFunction(func_scale)
        calc_scale.SetResultArrayName("E-Field_Scaled")
        calc_scale.SetInputConnection(resample.GetOutputPort())
        calc_scale.SetAttributeTypeToPointData()
        calc_scale.Update()
        
        calc_mag = vtkArrayCalculator()
        calc_mag.AddVectorArrayName("E-Field_Scaled")
        calc_mag.SetFunction(func_mag)
        calc_mag.SetResultArrayName("E-Field_Scaled_Magnitude")
        calc_mag.SetInputConnection(calc_scale.GetOutputPort())
        calc_mag.SetAttributeTypeToPointData()
        calc_mag.Update()

        output_datasets.append((
            vtr_file_name, calc_mag.GetOutput()
        ))

        ### write
        writer = vtkXMLImageDataWriter()
        output_file = "outputs/images/" + os.path.splitext(vtr_file_name)[0] + ".vti"
        writer.SetFileName(output_file)
        writer.SetInputConnection(calc_mag.GetOutputPort())
        writer.Update()
        ###

    return output_datasets


def export(datasets, render: bool):
    rw = vtkRenderWindow()
    renderer = vtkRenderer()
    rw.AddRenderer(renderer)

    renderer.SetBackground(0.5, 0.5, 0.5)

    rwi = vtkRenderWindowInteractor()
    rwi.SetRenderWindow(rw)
    rwi.GetInteractorStyle().SetCurrentStyleToTrackballCamera()

    volumes = []

    for name, dataset in datasets:
        mapper = vtkSmartVolumeMapper()
        mapper.DebugOn()
        mapper.SetInputData(dataset)

        mapper.SetScalarModeToUsePointFieldData()
        mapper.SelectScalarArray("E-Field_Scaled_Magnitude")

        volume = vtkVolume()
        pwf = vtkPiecewiseFunction()
        lut = make_lut()
        volume.GetProperty().SetColor(lut)
        volume.GetProperty().SetScalarOpacity(pwf)

        volume.GetProperty().ShadeOn()
        volume.GetProperty().SetInterpolationTypeToLinear()

        volume.SetMapper(mapper)
        renderer.AddVolume(volume)

        renderer.ResetCamera()

        rw.Render()

        exporter = vtkJSONSceneExporter()
        exporter.SetRenderWindow(rw)
        dirname = "outputs/json/exports/" + name

        if os.path.isdir(dirname):
            shutil.rmtree(dirname)

        exporter.SetFileName(dirname)
        exporter.Write()

        renderer.RemoveVolume(volume)
        volumes.append(volume)

        archive_path = "outputs/json/archives/" + os.path.splitext(name)[0]  + ".vtkjs"

        shutil.make_archive(archive_path, "zip", dirname)
        os.rename(archive_path + ".zip", archive_path)

    shutil.copy("template_index.json", "outputs/json/exports/index.json")

    zipAllTimeSteps("outputs/json/exports/", "outputs/json/archives/timesteps.zip")

    os.rename("outputs/json/archives/timesteps.zip", "outputs/json/archives/timesteps.vtkjs")

    if render:
        renderer.AddVolume(volumes[-1])
        renderer.ResetCamera()
        rw.Render()
        rwi.Start()

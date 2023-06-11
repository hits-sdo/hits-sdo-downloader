import argparse

import matplotlib.pyplot as plt
import numpy as np
from astropy import units as u
from astropy.visualization import ImageNormalize, AsinhStretch, SqrtStretch, PowerStretch
from iti.data.editor import LoadMapEditor, NormalizeRadiusEditor, AIAPrepEditor
from sunpy.visualization.colormaps import cm

sdo_cmaps = {171: cm.sdoaia171, 193: cm.sdoaia193, 211: cm.sdoaia211, 304: cm.sdoaia304}

sdo_asinh_norms = {94: ImageNormalize(vmin=0, vmax=340, stretch=AsinhStretch(0.02), clip=False),
             131: ImageNormalize(vmin=0, vmax=1400, stretch=AsinhStretch(0.02), clip=False),
             171: ImageNormalize(vmin=0, vmax=1400, stretch=AsinhStretch(0.02), clip=False),
             193: ImageNormalize(vmin=0, vmax=9800, stretch=AsinhStretch(0.02), clip=False),
             211: ImageNormalize(vmin=0, vmax=1500, stretch=AsinhStretch(0.02), clip=False),
             304: ImageNormalize(vmin=0, vmax=600, stretch=AsinhStretch(0.04), clip=False),
             335: ImageNormalize(vmin=0, vmax=600, stretch=AsinhStretch(0.02), clip=False),
             1600: ImageNormalize(vmin=0, vmax=4000, stretch=AsinhStretch(0.02), clip=False),
             1700: ImageNormalize(vmin=0, vmax=4000, stretch=AsinhStretch(0.02), clip=False)
             }

sdo_linear_norms = {94: ImageNormalize(vmin=0, vmax=2.41, clip=False),
             131: ImageNormalize(vmin=0, vmax=11.6, clip=False),
             171: ImageNormalize(vmin=0, vmax=305, clip=False),
             193: ImageNormalize(vmin=0, vmax=417, clip=False),
             211: ImageNormalize(vmin=0, vmax=151, clip=False),
             304: ImageNormalize(vmin=0, vmax=83.1, clip=False),
             335: ImageNormalize(vmin=0, vmax=7.80, clip=False),
             1600: ImageNormalize(vmin=0, vmax=94.5, clip=False),
             1700: ImageNormalize(vmin=0, vmax=94.5, clip=False)
             }

sdo_power_norms = {94: ImageNormalize(vmin=0, vmax=2.41, stretch=PowerStretch(0.5), clip=False),
             131: ImageNormalize(vmin=0, vmax=11.6, stretch=PowerStretch(0.5), clip=False),
             171: ImageNormalize(vmin=0, vmax=305, stretch=PowerStretch(0.5), clip=False),
             193: ImageNormalize(vmin=0, vmax=417, stretch=PowerStretch(0.5), clip=False),
             211: ImageNormalize(vmin=0, vmax=151, stretch=PowerStretch(0.5), clip=False),
             304: ImageNormalize(vmin=0, vmax=83.1, stretch=PowerStretch(0.5), clip=False),
             335: ImageNormalize(vmin=0, vmax=7.80, stretch=PowerStretch(0.5), clip=False),
             1600: ImageNormalize(vmin=0, vmax=94.5, stretch=PowerStretch(0.5), clip=False),
             1700: ImageNormalize(vmin=0, vmax=94.5, stretch=PowerStretch(0.5), clip=False)
             }



def loadAIAMap(file_path, calibration='auto', fix_radius_padding=None, resolution=None):
    """Load and preprocess AIA file to make them compatible to ITI.


    Parameters
    ----------
    file_path: path to the FTIS file.
    calibration: calibration mode for AIAPrepEditor
    fix_radius_padding: how far from the solar limb to place the edge of the image
    resolution: target resolution in pixels of 2*(1+fix_radius_padding) solar radii.

    NOTE: both fix_radius_padding and resolution need to be set for radius normalization to take place

    Returns
    -------
    the preprocessed SunPy Map
    """

    s_map, _ = LoadMapEditor().call(file_path)
    assert s_map.meta['QUALITY'] == 0, f'Invalid quality flag while loading AIA Map: {s_map.meta["QUALITY"]}'

    if fix_radius_padding is not None and resolution is not None:
        s_map = NormalizeRadiusEditor(resolution, padding_factor=fix_radius_padding).call(s_map)
    try:
        s_map = AIAPrepEditor(calibration=calibration).call(s_map)
    except:
        s_map = AIAPrepEditor(calibration='aiapy').call(s_map)

    return s_map


def loadMap(file_path, resolution=None, fix_radius_padding=None, calibration=None):
    """Load and resample a FITS file (no pre-processing).


    Parameters
    ----------
    file_path: path to the FTIS file.
    resolution: target resolution in pixels of 2*(1+fix_radius_padding) solar radii.
    fix_radius_padding: dummy parameter so that we can exchange this function for loadAIAMap
    calibration: dummy parameter so that we can exchange this function for loadAIAMap

    Returns
    -------
    the preprocessed SunPy Map
    """
    s_map, _ = LoadMapEditor().call(file_path)
    if resolution is not None:
        s_map = s_map.resample((resolution, resolution) * u.pix)
    return s_map


def loadMapStack(file_paths,
                 aia_preprocessing=True,
                 calibration='auto',
                 normalization='asinh',
                 fix_radius_padding=None,
                 resolution=None,
                 remove_nans=True,
                 percentile_clip=0.25):
    """Load a stack of FITS files, resample ot specific resolution, and stackt hem.


    Parameters
    ----------
    file_paths: list of files to stack.
    aia_preprocessing: Whether to pre-process AIA or simply load the image
    calibration: calibration mode for AIAPrepEditor
    normalization: whether to use 'asinh', 'power' or 'linear' normalization
    fix_radius_padding: how far from the solar limb to place the edge of the image
    resolution: target resolution in pixels of 2*(1+fix_radius_padding) solar radii.
    remove_nans: change nans and inf for zero
    percentile_clip: clipping of the hottest pixels to the 100-percentile_clip percentile


    Returns
    -------
    numpy array with AIA stack
    """
    load_func = loadAIAMap if aia_preprocessing else loadMap
    s_maps = [load_func(file, resolution=resolution, calibration=calibration, fix_radius_padding=fix_radius_padding) for file in file_paths]
    if normalization == 'linear':
        sdo_norms = sdo_linear_norms
    elif normalization == 'power':
        sdo_norms = sdo_power_norms
    else:
        sdo_norms = sdo_asinh_norms
    
    stack = np.stack([sdo_norms[s_map.wavelength.value](s_map.data) for s_map in s_maps]).astype(np.float32)

    if remove_nans:
        stack[np.isnan(stack)] = 0
        stack[np.isinf(stack)] = 0

    if percentile_clip:
        for i in range(stack.shape[0]):
            percentiles = np.percentile(stack[i,:,:].reshape(-1), [percentile_clip,100-percentile_clip])
            stack[i,:,:][stack[i,:,:]<percentiles[0]] = percentiles[0]
            stack[i,:,:][stack[i,:,:]>percentiles[1]] = percentiles[1]

    return stack.data


if __name__ == '__main__':
    # test code
    o_map = loadAIAMap('/mnt/aia-jsoc/171/aia171_2010-05-13T00:00:07.fits')
    o_map.plot()
    plt.savefig('/home/robert_jarolim/results/original_map.jpg')
    plt.close()

    s_map = loadAIAMap('/mnt/aia-jsoc/171/aia171_2010-05-13T00:00:07.fits')
    s_map.plot(**o_map.plot_settings)
    plt.savefig('/home/robert_jarolim/results/projected_map.jpg')
    plt.close()
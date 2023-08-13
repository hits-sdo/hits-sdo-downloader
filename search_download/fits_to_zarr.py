import argparse
import logging
import os
from os.path import exists

from functools import partial
import matplotlib.image

import numpy as np
import pandas as pd
from tqdm import tqdm

from search_download.utils.utils import loadMapStack, loadMap
import zarr
from numcodecs import Blosc

# Initialize Python Logger
logging.basicConfig(format='%(levelname)-4s '
                           '[%(module)s:%(funcName)s:%(lineno)d]'
                           ' %(message)s')

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)


def parse_args():
    # Commands 
    p = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument('--aia_path', dest='aia_path', type=str, default="/mnt/aia_data",
                   help='aia path')
    p.add_argument('--hmi_path', dest='hmi_path', type=str, default="/mnt/hmi_data",
                   help='hmi path')
    p.add_argument('--matches', dest='matches', type=str,
                   default="/mnt/data/aia_matches_171_211_304.csv",
                   help='multi-wavelength matches')
    p.add_argument('--zarr_outpath', dest='zarr_outpath', type=str,
                   default="/mnt/data_out",
                   help='Zarr out path')
    p.add_argument('--aia_preprocessing', dest='aia_preprocessing', action='store_true', 
                   help='Whether to pre-process AIA or simply load the image')
    p.add_argument('--aia_calibration', dest='aia_calibration', type=str,
                   default="aiapy",
                   help="calibration mode for AIAPrepEditor")
    p.add_argument('--aia_normalization', dest='aia_normalization', type=str,
                   default="asinh",
                   help="whether to use 'asinh', 'power', 'linear', or 'none' normalization for aia")    
    p.add_argument('--fix_radius_padding', dest='fix_radius_padding', type=float, default=None, 
                   help='How far from the solar limb to place the edge of the image')
    p.add_argument('--resolution', dest='resolution', type=int, default=None, 
                   help='Target resolution in pixels of 2*(1+fix_radius_padding) solar radii')
    p.add_argument('--remove_nans', action='store_true', 
                   help='change nans and inf for zero')
    p.add_argument('--percentile_clip', dest='percentile_clip', type=float, default=None, 
                   help='clipping of the hottest pixels to the 100-percentile_clip percentile')
    p.add_argument('--debug', action='store_true',
                   help='Only process a few files (10)')
    args = p.parse_args()
    return args


if __name__ == "__main__":
    # Parser
    args = parse_args()
    hmi_path = args.hmi_path
    aia_path = args.aia_path
    matches = args.matches
    zarr_outpath = args.zarr_outpath
    aia_preprocessing = args.aia_preprocessing
    aia_calibration = args.aia_calibration
    aia_normalization = args.aia_normalization
    fix_radius_padding = args.fix_radius_padding
    resolution = args.resolution
    remove_nans = args.remove_nans
    percentile_clip = args.percentile_clip
    debug = args.debug
    

    # Load indices
    matches = pd.read_csv(matches)
    if debug:
        matches = matches.loc[0:10, :]

    # Extract filenames for stacks
    aia_columns = []
    for col in matches.columns:
        if 'aia' in col:
            aia_columns.append(col)

    aia_files = None
    if len(aia_columns) > 0:
        aia_files = []
        for index, row in tqdm(matches.iterrows(), total=matches.shape[0], desc='Turning aia dataframe columns into stacks'):
            aia_files.append(row[aia_columns].tolist())  # (channel, files)    

    hmi_columns = []
    for col in matches.columns:
        if 'hmi' in col:
            hmi_columns.append(col)            

    hmi_files = None
    if len(hmi_columns) > 0:
        hmi_files = []
        for index, row in tqdm(matches.iterrows(), total=matches.shape[0], desc='Turning hmi dataframe columns into stacks'):
            hmi_files.append(row[hmi_columns].tolist())

    # Initialize zarr
    store = zarr.DirectoryStore(zarr_outpath)
    compressor = Blosc(cname='zstd', clevel=5, shuffle=Blosc.BITSHUFFLE)
    root = zarr.group(store=store, overwrite=True)

    if len(aia_columns) > 0:
        dataset_name = 'aia_' + '_'.join([column.split('files_aia')[1] for column in aia_columns])
        if len(hmi_columns) > 0:
            dataset_name = dataset_name + '_hmilos'
    elif len(hmi_columns) > 0:
        dataset_name = 'hmilos'

    sdo_stacks = root.create_dataset(dataset_name, 
                            shape=(matches.shape[0], len(aia_columns) + len(hmi_columns), resolution, resolution), 
                            chunks=(1, None, None, None), 
                            dtype='f4',
                            compressor=compressor)

    # Processing AIA stacks
    partial_load_map_stack = partial(loadMapStack,
                            aia_preprocessing=aia_preprocessing,
                            calibration=aia_calibration,
                            normalization=aia_normalization,
                            fix_radius_padding=fix_radius_padding,
                            resolution=resolution,
                            remove_nans=remove_nans,
                            percentile_clip=percentile_clip,
                            return_meta=True)

    for i, file_stack in tqdm(enumerate(aia_files), total=len(aia_files), desc='Processing AIA stacks'):
        try:
            # open file
            aia_stack, aia_meta = partial_load_map_stack(file_stack)
            # for key in data.meta:
            #     if key not in HEADER_FIELD_IGNORE:
            #         vars()[key].append(data.meta[key])

            sdo_stacks[i, 0:len(aia_columns), :, :] = aia_stack  
        except Exception as e:
            print(e)

    for i, file_stack in tqdm(enumerate(hmi_files), total=len(hmi_files), desc='Processing HMI stacks'):
        try:
            # open file
            hmi_map = loadMap(file_stack[0], resolution=resolution, fix_radius_padding=fix_radius_padding, zero_outside_disk=True)

            if remove_nans:
                hmi_map.data[np.isnan(hmi_map.data)] = 0
                hmi_map.data[np.isinf(hmi_map.data)] = 0                

            sdo_stacks[i, len(aia_columns), :, :] = hmi_map.data

        except Exception as e:
            print(e)              
    
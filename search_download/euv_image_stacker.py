import argparse
import logging
import os
from os.path import exists

from functools import partial
import matplotlib.image

import numpy as np
import pandas as pd
from tqdm import tqdm
from tqdm.contrib.concurrent import process_map

from search_download.utils.utils import loadMapStack

# Initialize Python Logger
logging.basicConfig(format='%(levelname)-4s '
                           '[%(module)s:%(funcName)s:%(lineno)d]'
                           ' %(message)s')

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)

# Order seems to be:  [0:94, 1:131, 2:171, 3:193, 4:211, 5:304, 6:335, 7:1600]


def load_map_stack(aia_stack,
                    aia_preprocessing=True,
                    calibration='auto',
                    normalization='asinh',
                    fix_radius_padding=None,
                    resolution=None,
                    remove_nans=True,
                    percentile_clip=0.25,
                    stack_outpath=None,
                    file_format=None):
    # Extract filename from index_aia_i (remove aia_path)

    filename = aia_stack[0].replace('\\', '/').split('/')[-1].split('aia')[0]+'aia'
    for file in aia_stack:
        filename = filename + '_' + file.replace('\\', '/').split('/')[-1].split('_')[3]
    filename = filename + '.' + file_format

    output_file = stack_outpath + '/' + filename

    if exists(output_file):
        LOG.info(f'{filename} exists.')
    else:
        aia_stack = loadMapStack(aia_stack,
                            aia_preprocessing=aia_preprocessing,
                            calibration=calibration,
                            normalization=normalization,
                            fix_radius_padding=fix_radius_padding,
                            resolution=resolution,
                            remove_nans=remove_nans,
                            percentile_clip=percentile_clip)
        # Save stack
        if file_format=='npy':
            np.save(output_file, aia_stack)
        if file_format=='jpg':
            aia_stack = aia_stack.transpose(1, 2, 0)
            aia_stack[aia_stack<0] = 0
            aia_stack[aia_stack>1] = 1
            matplotlib.image.imsave(output_file, aia_stack, vmin=0, vmax=1)


    return output_file


def parse_args():
    # Commands 
    p = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument('--aia_path', dest='aia_path', type=str, default="/mnt/data",
                   help='aia_path')
    p.add_argument('--matches', dest='matches', type=str,
                   default="/mnt/data/aia_matches_171_211_304.csv",
                   help='multi-wavelength matches')
    p.add_argument('--stack_outpath', dest='stack_outpath', type=str,
                   default="/mnt/data_out",
                   help='out_path')
    p.add_argument('--file_format', dest='file_format', type=str,
                   default="npy",
                   help='format to save the stack in')
    p.add_argument('--wavelength_order', type=str,
                        nargs='+', default=None,
                        help='Order in which to stack the files, needs to contain only available wavelengths')
    p.add_argument('--aia_preprocessing', dest='aia_preprocessing', action='store_true', 
                   help='Whether to pre-process AIA or simply load the image')
    p.add_argument('--calibration', dest='calibration', type=str,
                   default="aiapy",
                   help="calibration mode for AIAPrepEditor")
    p.add_argument('--normalization', dest='normalization', type=str,
                   default="asinh",
                   help="whether to use 'asinh', 'power' or 'linear' normalization")
    p.add_argument('--fix_radius_padding', dest='fix_radius_padding', type=float, default=None, 
                   help='How far from the solar limb to place the edge of the image')
    p.add_argument('--resolution', dest='resolution', type=int, default=None, 
                   help='Target resolution in pixels of 2*(1+fix_radius_padding) solar radii')
    p.add_argument('--remove_nans', action='store_true', 
                   help='change nans and inf for zero')
    p.add_argument('--percentile_clip', dest='percentile_clip', type=float, default=0.25, 
                   help='clipping of the hottest pixels to the 100-percentile_clip percentile')
    p.add_argument('--debug', action='store_true',
                   help='Only process a few files (10)')
    args = p.parse_args()
    return args


if __name__ == "__main__":
    # Parser
    args = parse_args()
    # eve_path = args.eve_path
    aia_path = args.aia_path
    matches = args.matches
    stack_outpath = args.stack_outpath
    file_format = args.file_format
    wavelength_order = args.wavelength_order
    aia_preprocessing = args.aia_preprocessing
    calibration = args.calibration
    normalization = args.normalization
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
    for wl in wavelength_order:
        for col in matches.columns:
            if wl in col:
                aia_columns.append(col)

    aia_files = []
    for index, row in tqdm(matches.iterrows()):
        aia_files.append(row[aia_columns].tolist())  # (channel, files)

    # Path for output
    os.makedirs(stack_outpath, exist_ok=True)

    # Stacks
    print('Saving stacks')
    partial_load_map_stack = partial(load_map_stack,
                                    aia_preprocessing=aia_preprocessing,
                                    calibration=calibration,
                                    normalization=normalization,
                                    fix_radius_padding=fix_radius_padding,
                                    resolution=resolution,
                                    remove_nans=remove_nans,
                                    percentile_clip=percentile_clip,
                                    stack_outpath=stack_outpath,
                                    file_format=file_format)
    converted_file_paths = process_map(partial_load_map_stack, aia_files, max_workers=16, chunksize=5)

    # Save
    if debug:
        matches = matches.loc[0:len(converted_file_paths), :]

    print('Saving Matches')
    matches['aia_stack'] = converted_file_paths
    matches_output = args.matches.replace('\\','/').split('/')[-1].replace('.csv','_processed.csv')
    matches_output = f'{stack_outpath}/{matches_output}'
    matches.to_csv(matches_output, index=False)

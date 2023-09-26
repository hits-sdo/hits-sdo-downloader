import argparse
import logging
import os
from os.path import exists

import matplotlib.image

from functools import partial
import matplotlib.image

import numpy as np
import pandas as pd
from tqdm import tqdm

import xarray as xr

# Initialize Python Logger
logging.basicConfig(
    format="%(levelname)-4s " "[%(module)s:%(funcName)s:%(lineno)d]" " %(message)s"
)

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)


class ZarrToJpg:
    """ """

    def __init__(
        self,
        aia_path="/d0/euv/aia/preprocessed/aia_hmi_stacks_2010_2023_1d_full.zarr",
        stack_outpath="/d0/euv/aia/preprocessed",
        wavelength_order=[211, 193, 171],
        debug=False,
    ):
        self.aia_path = aia_path
        self.stack_outpath = (
            stack_outpath + "/AIA_" + "_".join([str(wl) for wl in wavelength_order])
        )
        self.channel_index = ["aia" + str(wl).zfill(3) for wl in wavelength_order]
        self.debug = debug
        self.data = xr.open_zarr(self.aia_path)
        self.aia_slice = self.data.aia_hmi.loc[:, self.channel_index, :, :]
        self.wavelength_order = wavelength_order

        if self.debug:
            self.aia_slice = self.aia_slice[0:10, :, :, :]

        if not os.path.exists(self.stack_outpath):
            os.mkdir(self.stack_outpath)

    def save_jpg(self, index):
        aia_stack = np.arcsinh(self.aia_slice[index, :, :, :].load().data)
        aia_stack = aia_stack.transpose(1, 2, 0)
        aia_stack[aia_stack < 0] = 0
        aia_stack[aia_stack > 1] = 1
        output_file = (
            pd.to_datetime(self.aia_slice.t_obs[index].data).strftime(
                "%Y%m%d_%H%M%S_aia_"
            )
            + "_".join([str(wl) for wl in self.wavelength_order])
            + ".jpg"
        )
        matplotlib.image.imsave(
            os.path.join(self.stack_outpath, output_file), aia_stack, vmin=0, vmax=1
        )


def parse_args():
    # Commands
    p = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument(
        "--aia_path", dest="aia_path", type=str, default="/mnt/data", help="aia_path"
    )
    p.add_argument(
        "--stack_outpath",
        dest="stack_outpath",
        type=str,
        default="/mnt/data_out",
        help="out_path",
    )
    p.add_argument(
        "--file_format",
        dest="file_format",
        type=str,
        default="npy",
        help="format to save the stack in",
    )
    p.add_argument(
        "--wavelength_order",
        type=str,
        nargs="+",
        default=None,
        help="Order in which to stack the files, needs to contain only available wavelengths",
    )
    p.add_argument("--debug", action="store_true", help="Only process a few files (10)")
    args = p.parse_args()
    return args


if __name__ == "__main__":
    # Parser
    args = parse_args()
    aia_path = args.aia_path
    stack_outpath = args.stack_outpath
    wavelength_order = args.wavelength_order
    debug = args.debug

    # open zarr

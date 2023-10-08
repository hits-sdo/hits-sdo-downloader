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
import dask
import dask.array as da

from astropy.visualization import ImageNormalize, AsinhStretch

from tqdm.dask import TqdmCallback

# Initialize Python Logger
logging.basicConfig(
    format="%(levelname)-4s " "[%(module)s:%(funcName)s:%(lineno)d]" " %(message)s"
)

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)


class ZarrToJpg:
    """
    Class containing the methods necessary to create jpgs out of AIA data. It includes means
    for automatically setting asinh normalization

    Parameters
    ----------
    aia_path : str
        Path pointing to Zarr array
    stack_outpath : str
        Path to place the folder containing output
    wavelength_order : list, optional
        List with wavelengths to place in the red, green, and blue channels, by default [211, 193, 171]
    debug : bool, optional
        flag that uses a reduced version of the array, only 10 samples, by default False
    hist_low_lim : float, optional
        Low limit in histogram calucation, by default 0
    hist_high_lim : float, optional
        High limit in histogram calculation, by default 1000
    hist_delta : float, optional
        Size of the histogram bin, by default 0.1
    vmax_percentile : float, optional
        Max percentile to be used to set vmax in the archsinstretch, by default 99
    vmax_factor : float, optional
        Additional stretch that can help with very bright active regions, by default 2.5
    stretch_percentile : float, optional
        Percentile that will be pegged to a stretch position after stretch, by default 40
    stretch_position : float, optional
        Stretch position to wich the percentile above will be mapped, by default 0.4
    """

    def __init__(
        self,
        aia_path: str,
        stack_outpath: str,
        wavelength_order: list = [211, 193, 171],
        debug: bool = False,
        hist_low_lim: float = 0,
        hist_high_lim: float = 1000,
        hist_delta: float = 0.1,
        vmax_percentile: float = 99,
        vmax_factor: float = 2.5,
        stretch_percentile: float = 40,
        stretch_position: float = 0.4,
    ):
        assert (
            len(wavelength_order) == 3
        ), "Three channels need to be provided to generate jpgs."
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

        # Calculate histogram of pixel values for each channel in the slice
        histogram_dict = {}
        histogram_dict["bins"] = np.arange(hist_low_lim, hist_high_lim, hist_delta)
        for i, channel in enumerate(self.aia_slice.channel):
            histogram_dict[str(channel.data)], _ = da.histogram(
                self.aia_slice.loc[:, str(channel.data), :, :].data,
                bins=histogram_dict["bins"],
            )

        with TqdmCallback(desc="Calculating data histogram"):
            self.histogram_dict = dask.compute(histogram_dict)[0]

        # Calculate cumulative distribution for each channel in the slice to calculate percentiles
        self.cumsum_dict = {}
        for i, channel in enumerate(self.aia_slice.channel):
            self.cumsum_dict[str(channel.data)] = (
                np.cumsum(self.histogram_dict[str(channel.data)])
                / np.sum(self.histogram_dict[str(channel.data)])
                * 100
            )

        # Calculate channel percentiles to set normalization
        percentile_list = [stretch_percentile, vmax_percentile]
        self.percentile_dict = get_percentiles(
            self.cumsum_dict,
            self.histogram_dict["bins"],
            percentile_list=percentile_list,
        )

        self.sdo_asinh_norms = {}
        for i, channel in enumerate(self.aia_slice.channel):
            test_stretch = 0.25
            for n in range(3, 15):
                test_norm = ImageNormalize(
                    vmin=0,
                    vmax=self.percentile_dict[str(channel.data)][1],
                    stretch=AsinhStretch(test_stretch),
                    clip=False,
                )
                test_val = test_norm(self.percentile_dict[str(channel.data)][0])
                if test_val < stretch_position:
                    test_stretch = test_stretch - 1 / 2**n
                else:
                    test_stretch = test_stretch + 1 / 2**n

            self.sdo_asinh_norms[str(channel.data)] = ImageNormalize(
                vmin=0,
                vmax=self.percentile_dict[str(channel.data)][1] * vmax_factor,
                stretch=AsinhStretch(test_stretch),
                clip=False,
            )

    def save_jpg(self, index: int):
        """Functin that saves a jpg for a given index of the Zarr array

        Parameters
        ----------
        index : int
            numerical index to save
        """
        aia_stack = self.aia_slice[index, :, :, :].load()
        for i, channel in enumerate(aia_stack.channel):
            aia_stack.loc[channel, :, :] = self.sdo_asinh_norms[str(channel.data)](
                aia_stack.loc[channel, :, :]
            )

        aia_stack = aia_stack.data.transpose(1, 2, 0)
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

    def save_jpgs(self):
        """
        Method that sets up the delayed actions to save all jpgs and executes them
        """

        # Create list
        delayed_list = []

        for i in range(self.aia_slice.shape[0]):
            delayed_list.append(dask.delayed(self.save_jpg)(i))

        with TqdmCallback(desc="Saving jpgs"):
            dask.compute(*delayed_list)


def get_percentiles(
    cumsum_dic: dict, bins: np.array, percentile_list: list = [80, 90]
) -> dict:
    """Function that gets percentile values based on a dictionary of histogram cumulative sums

    Parameters
    ----------
    cumsum_dic : dict
        Dictionary with cumulative sums
    bins : np.array
        Bins used for the calibration of the cumulative sums
    percentile_list : list, optional
        List of percentiles to calculate, by default [80, 90]

    Returns
    -------
    dict
        Dictionary with the calculated percentiles.  One for each AIA wavelength
    """
    percentile_dict = {}
    for wl, cumsum in cumsum_dic.items():
        # print(wl, cumsum)
        value_list = []
        for percentile in percentile_list:
            # print(cumsum<=percentile)
            # print(np.sum(cumsum<=percentile))
            index = np.sum(cumsum <= percentile)
            low_value = 0
            if index > 0:
                low_value = cumsum[index - 1]
            high_value = cumsum[index]
            # print(bins[index], bins[index+1], low_value, high_value)
            interpolated_value = bins[index] + (bins[index + 1] - bins[index]) * (
                percentile - low_value
            ) / (high_value - low_value)
            # print(interpolated_value)
            value_list.append(interpolated_value)

        percentile_dict[wl] = value_list

    return percentile_dict


def parse_args():
    # Commands
    p = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument(
        "--aia_path",
        dest="aia_path",
        type=str,
        default="/mnt/data.zarr",
        help="Path to zarr file",
    )
    p.add_argument(
        "--stack_outpath",
        dest="stack_outpath",
        type=str,
        default="/mnt/data_out",
        help="Path for jpg output",
    )
    p.add_argument(
        "--wavelength_order",
        dest="wavelength_order",
        type=str,
        nargs="+",
        default=None,
        help="Order in which to stack the files, needs to contain only available wavelengths",
    )
    p.add_argument("--debug", action="store_true", help="Only process a few files (10)")

    p.add_argument(
        "--hist_low_lim",
        dest="hist_low_lim",
        type=float,
        default=0,
        help="Low limit in histogram calucation, by default 0",
    )

    p.add_argument(
        "--hist_high_lim",
        dest="hist_high_lim",
        type=float,
        default=1000,
        help="High limit in histogram calculation, by default 1000",
    )

    p.add_argument(
        "--hist_delta",
        dest="hist_delta",
        type=float,
        default=0.1,
        help="Size of the histogram bin, by default 0.1",
    )

    p.add_argument(
        "--vmax_percentile",
        dest="vmax_percentile",
        type=float,
        default=99,
        help="Max percentile to be used to set vmax in the archsinstretch, by default 99",
    )

    p.add_argument(
        "--vmax_factor",
        dest="vmax_factor",
        type=float,
        default=2.5,
        help="Additional stretch that can help with very bright active regions, by default 2.5",
    )

    p.add_argument(
        "--stretch_percentile",
        dest="stretch_percentile",
        type=float,
        default=40,
        help="Percentile that will be pegged to a stretch position after stretch, by default 40",
    )

    p.add_argument(
        "--stretch_position",
        dest="stretch_position",
        type=float,
        default=0.4,
        help="Stretch position to wich the percentile above will be mapped, by default 0.4",
    )

    args = p.parse_args()
    return args


if __name__ == "__main__":
    # Parser
    args = parse_args()
    aia_path = args.aia_path
    stack_outpath = args.stack_outpath
    wavelength_order = args.wavelength_order
    debug = args.debug
    hist_low_lim = args.hist_low_lim
    hist_high_lim = args.hist_high_lim
    hist_delta = args.hist_delta
    vmax_percentile = args.vmax_percentile
    vmax_factor = args.vmax_factor
    stretch_percentile = args.stretch_percentile
    stretch_position = args.stretch_position

    # open zarr
    zarr_to_jpg = ZarrToJpg(
        aia_path=aia_path,
        stack_outpath=stack_outpath,
        wavelength_order=wavelength_order,
        debug=debug,
        hist_low_lim = hist_low_lim,
        hist_high_lim = hist_high_lim,
        hist_delta = hist_delta,
        vmax_percentile = vmax_percentile,
        vmax_factor = vmax_factor,
        stretch_percentile = stretch_percentile,
        stretch_position = stretch_position,
    )

    zarr_to_jpg.save_jpgs()

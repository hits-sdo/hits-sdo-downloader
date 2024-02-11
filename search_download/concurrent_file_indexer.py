import argparse
import glob
import logging
import os
import re

import dateutil.parser as dt
import pandas as pd
from tqdm import tqdm
from sunpy.map import Map

import dask
from dask.delayed import delayed
from tqdm.dask import TqdmCallback

def _filename_to_date(data_filename):
    """ Takes a single path to an AIA or HMI file and returns its associated date   
    Assumes that the files have the date within their name in the following format:
        YYYYMMDD_hhmmss

    Parameters
    ----------
    data_filename: str
        path to an HMI or AIA file
    Returns
    -------
    dt.datetime associated with the file    
    """
    try:
        date_string = re.search(r"\d{8}_\d{6}(?!.+\d{8}_\d{6}.+)", data_filename).group().replace('_', 'T')
    except:
        date_string = data_filename.split("_")[-1].split('.')[0]
    
    return dt.isoparse(date_string)


    
def filenames_to_dates(data_filenames, debug=False):
    """ load dates from filenames for both AIA and HMI. it    
    Assumes that the files have the date within their name in the following format:
        YYYYMMDD_hhmmss

    Parameters
    ----------
    data_filenames: List of Lists
        path names of the AIA files as a list of list, with each list in the list corresponding to
        an AIA wavelength.  In the case of HMI it should be a list of lists with a single list of hmi files.
    debug: 
        if True select only the first 10 dates.

    Returns
    -------
    List of lists with files converted to datetimes.
    """
    iso_dates = [[_filename_to_date(file) for file in wl_files] for wl_files in data_filenames]
    return iso_dates


def create_date_file_df(dates, files, sufix, dt_round='3min', debug=False):
    """ Parse a list of datetimes and files into dataframe

    Parameters
    ----------
    dates: list of dates
    files: list of filepaths
    sufix: string to use in the creation of the columns of the df.  Typically an
            AIA wavelength or the name 'hmi'
    dt_round: frequency alias to round dates
        see https://pandas.pydata.org/docs/reference/api/pandas.Series.dt.round.html
    debug: Whether to use only a small set of the files (10)


    Returns
    -------
    pandas df with datetime index and paths
    """
    df1 = pd.DataFrame(data={'dates':dates, f'files_{sufix}':files})
    df1['dates'] = df1['dates'].dt.round(dt_round)
    # Drop duplictaes in case datetimes round to the same value
    df1 = df1.drop_duplicates(subset='dates', keep='first')
    df1 = df1.set_index('dates', drop=True)

    if debug:
        df1 = df1.iloc[::debug,:]

    return df1


def match_file_times(all_iso_dates, all_filenames, all_sufixes, joint_df=None, debug=False):
    """ Parses aia_iso_dates and compile lists at the same time"

    Parameters
    ----------
    all_iso_dates: list of AIA channel datetimes
    all_filenames: filenames of AIA files
    all_sufixes: list of strings to use in the creation of the columns of the df.  Typically
            AIA wavelengths or the name 'hmi'
    joint_df: pandas dataframe to use as a starting point
    debug: Whether to use only a small set of the files (10)

    Returns
    -------
    pandas dataframe of matching datetimes
    """

    for n, (aia_iso_dates, aia_filenames, sufix) in enumerate(zip(all_iso_dates, all_filenames, all_sufixes)):
        df = create_date_file_df(aia_iso_dates, aia_filenames, sufix, debug=debug)
        if n == 0 and joint_df is None:
            joint_df = df
        else:
            joint_df = joint_df.join(df, how='inner')

    return joint_df


def get_fits_quality(filepath):
    s_map = Map(filepath)
    return s_map.meta["QUALITY"] == 0


if __name__ == "__main__":
    logging.basicConfig(format='%(levelname)-4s '
                            '[%(module)s:%(funcName)s:%(lineno)d]'
                            ' %(message)s')

    LOG = logging.getLogger()
    LOG.setLevel(logging.INFO)

    p = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument('--hmi_path', type=str, default=None,
                   help='path to directory of hmi files')
    p.add_argument('--aia_path', type=str, default=None,
                   help='path to directory of aia files')    
    p.add_argument('-wl','--wavelengths', type=str,
                        nargs='+', default=None,
                        help='Channels to combine')
    p.add_argument('--dt_round', type=str, default='3min',
                   help='frequency alias to round dates to find closest matches')
    p.add_argument('--check_fits', action='store_true',
                   help='whether to verify all fits files for the quality flag')
    p.add_argument('--debug', action='store_true',
                   help='Only process a few files (10)')

    args = p.parse_args()

    hmi_path = args.hmi_path
    aia_path = args.aia_path
    wavelengths = args.wavelengths
    dt_round = args.dt_round
    check_fits = args.check_fits
    debug = args.debug

    # Process AIA files, if hmi path provided
    if aia_path is not None:
        available_wavelengths = [d for d in os.listdir(aia_path) if os.path.isdir(aia_path+'/'+d)]
        intersection_wavelengths = list(set(available_wavelengths).intersection(wavelengths))
        intersection_wavelengths.sort(key=float)

        if len(intersection_wavelengths) < len(wavelengths):
            LOG.log(level=30, msg=f'Found only {available_wavelengths}, but the user request is {wavelengths}')

        nb_wavelengths = len(intersection_wavelengths)

        # LOADING AIA data
        # List of filenames, per wavelength

        aia_filenames = [[f.replace('\\', '/') for f in sorted(glob.glob(aia_path + '/%s/*aia*%s_*.fits' % (wl, wl)))] for wl in intersection_wavelengths]

        if debug:
            aia_filenames = [files[0:10] for files in aia_filenames]

    # Process HMI files, if hmi path provided
    if hmi_path is not None:
        hmi_filenames = [[f.replace('\\', '/') for f in sorted(glob.glob(hmi_path + '/*.fits'))]]
        if debug:
            hmi_filenames = [files[0:10] for files in hmi_filenames]

    if check_fits:
        # Assemble list of lists with delayed actions for all files per channel per instrument
        all_files = []
        if aia_path is not None:
            all_files.append(aia_filenames)
        if hmi_path is not None:
            all_files.append(hmi_filenames)

        delayed_quality = []
        for instrument in all_files:
            channels = []
            for channel in instrument:
                files = []
                for file in channel:
                    files.append(delayed(get_fits_quality)(file))
                channels.append(files)
            delayed_quality.append(channels)

        # Execute delayed actions to identify quality issues
        with TqdmCallback(desc="Checking quality flag for all files"):
            quality = dask.compute(*delayed_quality)

        # Remove files with bad quality
        hmi_index = 0
        if aia_path is not None:
            hmi_index = 1
            clean_aia_filenames = []
            for channel, mask in zip(aia_filenames, quality[0]):
                clean_channel = [channel[i] for i in range(len(channel)) if mask[i]]
                clean_aia_filenames.append(clean_channel)
            aia_filenames = clean_aia_filenames

        if hmi_path is not None:
            clean_hmi_filenames = []
            for channel, mask in zip(hmi_filenames, quality[hmi_index]):
                clean_channel = [channel[i] for i in range(len(channel)) if mask[i]]
                clean_hmi_filenames.append(clean_channel)
            hmi_filenames = clean_hmi_filenames        


    # load aia dates
    result_matches = None
    if aia_path is not None:
        aia_iso_dates = filenames_to_dates(aia_filenames, debug=debug)

        aia_sufixes = [f'aia{wl}' for wl in intersection_wavelengths]
        result_matches = match_file_times(aia_iso_dates, aia_filenames, aia_sufixes, debug=debug)

    # Process HMI files, if hmi path provided
    if hmi_path is not None:
        # load hmi dates
        hmi_iso_dates = filenames_to_dates(hmi_filenames, debug)
        result_matches = match_file_times(hmi_iso_dates, hmi_filenames, ['hmi'], joint_df=result_matches)


    # Save csv with aia filenames, aia iso dates, eve iso dates, eve indices, and time deltas
    if aia_path is not None:
        if hmi_path is not None:
            intersection_wavelengths.append('hmi')
            filename = f'aia_hmi_matches_{"_".join(intersection_wavelengths)}.csv'
        else:
            f'aia_matches_{"_".join(intersection_wavelengths)}.csv'
        filename = os.path.join(aia_path, filename).replace('\\','/')
        result_matches.to_csv(filename, index=True)
    elif hmi_path is not None:
        filename = 'hmi_index.csv'
        filename = os.path.join(hmi_path, filename).replace('\\','/')
        result_matches.to_csv(filename, index=True)
    
    

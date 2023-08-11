import argparse
import glob
import logging
import os
import re

import dateutil.parser as dt
import pandas as pd


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
    date_string = re.search(r"\d{8}_\d{6}(?!.+\d{8}_\d{6}.+)", data_filename).group().replace('_', 'T')
    
    return dt.isoparse(date_string)


    
def filenames_to_dates(data_filenames, debug):
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
    if debug:
        data_filenames = [wl_dates[0:10] for wl_dates in data_filenames]
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


def match_file_times(all_iso_dates, all_filenames, all_sufixes, joint_df=None):
    """ Parses aia_iso_dates and compile lists at the same time"

    Parameters
    ----------
    all_iso_dates: list of AIA channel datetimes
    all_filenames: filenames of AIA files
    all_sufixes: list of strings to use in the creation of the columns of the df.  Typically
            AIA wavelengths or the name 'hmi'
    joint_df: pandas dataframe to use as a starting point

    Returns
    -------
    pandas dataframe of matching datetimes
    """

    for n, (aia_iso_dates, aia_filenames, sufix) in enumerate(zip(all_iso_dates, all_filenames, all_sufixes)):
        df = create_date_file_df(aia_iso_dates, aia_filenames, sufix)
        if n == 0 and joint_df is None:
            joint_df = df
        else:
            joint_df = joint_df.join(df, how='inner')

    return joint_df


if __name__ == "__main__":
    logging.basicConfig(format='%(levelname)-4s '
                            '[%(module)s:%(funcName)s:%(lineno)d]'
                            ' %(message)s')

    LOG = logging.getLogger()
    LOG.setLevel(logging.INFO)

    p = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument('--hmi_path', type=str, default=None,
                   help='path to directory of hmi files')
    p.add_argument('--aia_path', type=str, default="/mnt/disks/aia-raw",
                   help='path to directory of aia files')    
    p.add_argument('-wl','--wavelengths', type=str,
                        nargs='+', default=None,
                        help='Channels to combine')
    p.add_argument('--dt_round', type=str, default='3min',
                   help='frequency alias to round dates to find closest matches')
    p.add_argument('--debug', action='store_true',
                   help='Only process a few files (10)')

    args = p.parse_args()

    hmi_path = args.hmi_path
    aia_path = args.aia_path
    wavelengths = args.wavelengths
    dt_round = args.dt_round
    debug = args.debug

    available_wavelengths = [d for d in os.listdir(aia_path) if os.path.isdir(aia_path+'/'+d)]
    intersection_wavelengths = list(set(available_wavelengths).intersection(wavelengths))
    intersection_wavelengths.sort(key=float)

    if len(intersection_wavelengths) < len(wavelengths):
        LOG.log(level=30, msg=f'Found only {available_wavelengths}, but the user request is {wavelengths}')

    nb_wavelengths = len(intersection_wavelengths)

    # LOADING AIA data
    # List of filenames, per wavelength

    aia_filenames = [[f.replace('\\', '/') for f in sorted(glob.glob(aia_path + '/%s/*aia_%s_*.fits' % (wl, wl)))] for wl in intersection_wavelengths]
    # load aia dates
    aia_iso_dates = filenames_to_dates(aia_filenames, debug)

    result_matches = match_file_times(aia_iso_dates, aia_filenames, intersection_wavelengths)

    # Process HMI files, if hmi path provided
    if hmi_path is not None:
        hmi_filenames = [[f.replace('\\', '/') for f in sorted(glob.glob(hmi_path + '/*.fits'))]]
        # load hmi dates
        hmi_iso_dates = filenames_to_dates(hmi_filenames, debug)
        result_matches = match_file_times(hmi_iso_dates, hmi_filenames, ['hmi'], joint_df=result_matches)


    # Save csv with aia filenames, aia iso dates, eve iso dates, eve indices, and time deltas
    if hmi_path is not None:
        intersection_wavelengths.append('hmi')
        filename = f'aia_hmi_matches_{"_".join(intersection_wavelengths)}.csv'
    else:
        f'aia_matches_{"_".join(intersection_wavelengths)}.csv'
    filename = os.path.join(aia_path, filename).replace('\\','/')
    result_matches.to_csv(filename, index=True)

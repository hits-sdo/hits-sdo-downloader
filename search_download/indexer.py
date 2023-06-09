import argparse
import glob
import logging
import os

import dateutil.parser as dt
import pandas as pd


def _load_aia_dates(aia_filenames, debug):
    """ load AIA dates from filenames.   Assumes HITS-SDO naming convention
        YYYYMMDD_hhmmss_*

    Parameters
    ----------
    aia_filenames: path names of the AIA files.
    nb_wavelengths: total number
    debug: if True select only the first 10 dates.

    Returns
    -------
    List of AIA datetimes.
    """
    aia_dates = [['T'.join(name.replace('\\','/').split("/")[-1].split('_')[0:2]) for name in wl_files] for wl_files in aia_filenames]

    if debug:
        aia_dates = [wl_dates[0:10] for wl_dates in aia_dates]
    aia_iso_dates = [[dt.isoparse(date) for date in wl_dates] for wl_dates in aia_dates]
    return aia_iso_dates


def create_date_file_df(dates, files, wl, dt_round='3min', debug=False):
    """ Parse a list of datetimes and files into dataframe

    Parameters
    ----------
    dates: list of dates
    files: list of filepaths
    wl:  wavelenght associated with dates and files
    dt_round: frequency alias to round
        see https://pandas.pydata.org/docs/reference/api/pandas.Series.dt.round.html


    Returns
    -------
    pandas df with datetime index and paths
    """
    df1 = pd.DataFrame(data={'dates':dates, f'files_{wl}':files})
    df1['dates'] = df1['dates'].dt.round(dt_round)
    # Drop duplictaes in case datetimes round to the same value
    df1 = df1.drop_duplicates(subset='dates', keep='first')
    df1 = df1.set_index('dates', drop=True)

    if debug:
        df1 = df1.iloc[::debug,:]

    return df1


def _match_aia_times(all_aia_iso_dates, all_aia_filenames, aia_wavelengths):
    """ Parses aia_iso_dates and compile lists at the same time"

    Parameters
    ----------
    aia_iso_dates: list of AIA channel datetimes
    aia_filenames: filenames of AIA files
    wavelengths: list of wavelengths

    Returns
    -------
    List of matching AIA channel datetimes
    """

    for n, (aia_iso_dates, aia_filenames, wl) in enumerate(zip(all_aia_iso_dates, all_aia_filenames, aia_wavelengths)):
        df = create_date_file_df(aia_iso_dates, aia_filenames, wl)
        if n == 0:
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
    p.add_argument('--aia_path', type=str, default="/mnt/disks/aia-raw", help='path to directory of aia files')
    p.add_argument('-wl','--wavelengths', type=str,
                        nargs='+', default=['211', '304','171'], help='Channels to combine')
    p.add_argument('--cutoff_aia', type=float, default='3min',
                   help='cutoff for time delta (difference between AIA images in different wavelengths) using pandas trequency aliases')
    p.add_argument('--debug', action='store_true', help='Only process a few files (10)')

    args = p.parse_args()

    aia_path = args.aia_path
    wavelengths = args.wavelengths
    cutoff_aia = args.cutoff_aia
    debug = args.debug

    ###########################################################################
    # MAIN -- Create pairs of AIA and EVE observations
    # keep in __main__ to use global variables for multithreading --> much faster

    available_wavelengths = [d for d in os.listdir(aia_path) if os.path.isdir(aia_path+'/'+d)]
    intersection_wavelengths = sorted(list(set(available_wavelengths).intersection(wavelengths)))

    if len(intersection_wavelengths) < len(wavelengths):
        LOG.log(level=30, msg=f'Found only {available_wavelengths}, but the user request is {wavelengths}')

    nb_wavelengths = len(intersection_wavelengths)

    # LOADING AIA data
    # List of filenames, per wavelength

    aia_filenames = [[f.replace('\\', '/') for f in sorted(glob.glob(aia_path + '/%s/*aia_%s_*.fits' % (wl, wl)))] for wl in intersection_wavelengths]
    # load aia dates
    aia_iso_dates = _load_aia_dates(aia_filenames, debug)

    result_matches = _match_aia_times(aia_iso_dates, aia_filenames, intersection_wavelengths)

    # Save csv with aia filenames, aia iso dates, eve iso dates, eve indices, and time deltas
    filename = os.path.join(aia_path, f'aia_matches_{"_".join(intersection_wavelengths)}.csv').replace('\\','/')
    result_matches.to_csv(filename, index=True)

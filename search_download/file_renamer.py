"""
File that contains the renamer function that renames standard JSOC filenames 
to a more compact string.

Developed by the 2023 NASA SEARCH Team Red:

Jonathan Vigil - jvigil1738@gmail.com
David Stone - wovenbone@gmail.com // https://github.com/11001011
Miguel Tellez - Tellezmiguel38@gmail.com // https://github.com/MiguelTel
Jasper Doan - jasperdoan@gmail.com
Daniel Geyfman - dgeyfman0@saddleback.edu
Andres Muñoz-Jaramillo - andres.munoz@swri.org // https://github.com/amunozj

"""


import re
import os
import glob
from functools import partial
import argparse

from tqdm.contrib.concurrent import process_map


def rename_filename(wavelength:int = None, file:str=None):
    '''
    Rename file name to this format: YYYYMMDD_HHMMSS_RESOLUTION_INSTRUMENT.[file_type] 
    aia strings look like aia.lev1_euv_12s.2010-12-21T120013Z.171.image_lev1.fits or
    aia.lev1_euv_12s.2010-12-21T000013Z.171.spikes.fits
    
    hmi strings look like hmi.m_720s.20101223_000000_TAI.1.magnetogram.fits    

    We're using RegEx:
    https://www.rexegg.com/regex-quickstart.html - RegEx cheat sheet    

    
    Parameters:
        file: str
            filemname to rename
        wavelength: int
            wavelength to append to the filename if None, it gets it from the filename
    
    Returns:
        None
    '''

    path = '/'.join(file.replace("\\", "/").split("/")[0:-1])
    file = file.replace("\\", "/").split("/")[-1]
    file_type = re.search(r"(jpg|fits)", file).group()
    instrument = re.search(r"[a-z]+", file).group()

    if file_type == 'fits':
        date = re.search(r"(\d+)(\S)(\d+)(\S)(\d+)", file).group()     # (\.) ([-|\.])
        hhmmss = re.search(r"[0-9]{6}", file).group()
        if instrument == 'aia':
            wavelength = re.search(r"(?<=\.)(\d{2,4})(?=\.)", file).group()
        else:
            wavelength = '1'

    else:
        date = re.search(r"[0-9]{8}", file).group()
        hhmmss = re.search(r"(?<=_)[0-9]{6}", file).group()
        if wavelength is None:
            wavelength = '1'

    spikes = ""
    if re.search("spikes", file):
        spikes = ".spikes"

    # Rename file name to this format: YYYYMMDD_HHMMSS_INSTRUMENT_WAVELENGTH_RESOLUTION_.[filetype]

    new_file_name = f"{date.replace('-','').replace('.','')}_{hhmmss.replace(':','')}_{instrument}_{wavelength}_4k{spikes}.{file_type}"
    # print(newFileName) # for testing.
    # rename file.
    os.rename(os.path.join(path, file).replace("\\", "/"), os.path.join(path, new_file_name).replace("\\", "/"))


def rename_filenames(files:list, wavelength:int = None, max_workers:int = None):
    '''
    File that uses parallel processing to rename all files.  It calls rename_file
    (see above).
    
    Parameters:
        files: list
            list of filemnames to rename
        wavelength: int
            wavelength to append to the filename if None, it gets it from the filename
        max_workers: int
            Number of workers to pass to the process map.
            See https://docs.python.org/3/library/concurrent.futures.html
    
    Returns:
        None
    '''

    partial_rename_filename = partial(rename_filename, wavelength)
    process_map(partial_rename_filename, files, max_workers=max_workers)


def parse_args(args=None):
    """
    Parses command line arguments to script. Sets up argument for which 
    dataset to label.

    Example:
    python file_renamer.py -f fits -p "D:\Mis Documentos\AAResearch\SEARCH\hits-sdo-downloader\command_test"

    Parameters:
        args (list):    defaults to parsing any command line arguments
    
    Returns:
        parser args:    Namespace from argparse
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-p','--path',
                        type=str,
                        help='Path to files'
                        )
    parser.add_argument('-f','--format',
                        type=str,
                        help='Specify the file type to download, either fits or jpg'
                        )

    parser.add_argument('--max_workers',
                    type=int,
                    default=None,
                    help='Specify the number of workers to use during process map'
                    )

    return parser.parse_args(args)

if __name__=="__main__":
    parser_output = parse_args()

    files = glob.glob(os.path.join(parser_output.path,'**', f'*.{parser_output.format}').replace('\\','/'))
    rename_filenames(files)


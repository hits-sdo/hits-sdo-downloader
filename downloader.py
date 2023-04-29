"""
File that contains the Downloader class to download fits and jpgs from Stanford Joint Science
Operations Center (JSOC) http://jsoc.stanford.edu/

Developed by the 2023 NASA SEARCH Team Red:

Jonathan Vigil - jvigil1738@gmail.com
David Stone - wovenbone@gmail.com // https://github.com/11001011
Miguel Tellez - Tellezmiguel38@gmail.com // https://github.com/MiguelTel
Jasper Doan - jasperdoan@gmail.com
Daniel Geyfman - dgeyfman0@saddleback.edu
Andres Muñoz-Jaramillo - andres.munoz@swri.org // https://github.com/amunozj

"""
import datetime
import os
import re
import argparse
import drms  # Module to interface with JSOC https://docs.sunpy.org/projects/drms/en/stable/_modules/drms/utils.html

class Downloader:
    """
    Initialize a downloader class with paramaters to interface with jsoc http://jsoc.stanford.edu/

    Parameters:
        email: (str)
            JSOC registered email to enable dowloading of fits and jpg images
        sdate: (str)
            Starting date in ISO format (YYYY-MM-DD hh:mm:ss) to define the period of 
            observations to download.   Has to be after May 25th, 2010
        edate: (str)
            End date in ISO format (YYYY-MM-DD hh:mm:ss) to define the period of observations 
            to download
        instrument: (str)
            Instrument/module in the SDO spacecraft to download from, currently only HMI and AIA
        wavelength: (list)
            Only valid for AIA. EUV wavelength(s) of images to download, it is ignored if 
            instrument is HMI
        cadence: (str)
            Frequency at which we want to download images within the download interval. 
            It has to be a number and a string character.
            "s" for seconds, "m" for minutes, "h" for hours, and "d" for days.
        format: (str)
            Specify the file type to download, either fits or jpg
        path: (str)
            Path to download the files to (default is current directory)
        download_limit: (int)
            Limit the number of files to download, if None, all files will be downloaded
        get_spike: (bool)
            Flag that specifies whether to download spikes files for AIA. Spikes are hot pixels
            that are normally removed from AIA images, but the user may want to retrieve them.

    """
    def __init__(self, 
                 email:str=None,
                 sdate:str=None,
                 edate:str=None,
                 wavelength:list=None,
                 instrument:str = None,
                 cadence:str = None,
                 file_format:str = None,
                 path:str = None,
                 download_limit:int = None,
                 get_spike:bool = None):
        
        self.email = email
        if isinstance(sdate, str):
            self.sdate = datetime.date.fromisoformat(sdate)
            self.edate = datetime.date.fromisoformat(edate)
        else:
            self.sdate = sdate
            self.edate = edate
        self.instrument = instrument.lower()    # Instrument/module in the SDO spacecraft (i.e. hmi, aia)
        self.validinstruments = ["aia", "hmi"]  #(hmi - magnetic fields), (aia - the sun in ultraviolet)
        self.wavelength = wavelength            # Only valid for AIA - Different colors of ultraviolet - used to look at different levels of the sun's atmosphere
        self.validwavelengths = [1700, 1600, 304, 171, 193, 211, 335, 94, 131]
        self.cadence = cadence # Cadence means the frequency at which we want to download images (e.g. one every three ours "3h")
        self.validcadence = ['s', 'm', 'h', 'd']   # s -> seconds, m -> minutes, h -> hours, d -> days) {cadence = 1d}  
        self.format = file_format
        self.validformats = ['fits', 'jpg']
        self.path = path
        # self.jsoc_string = None # Very specific way of putting together dates and instruments so that we can retrieve from the JSOC
        self.large_file_limit = False # False, there is no large file limit (limits number of files)
        self.download_limit = download_limit # Maximum number of files to download.
        self.client = drms.Client(email = self.email, verbose = True)
        self.get_spike = get_spike # Bool switch to download spikes files or not.   Spikes are hot pixels normally removed from AIA, but can be donwloaded if desired
        self.export = None

        self.jpg_defaults = {94: {'scaling':'LOG', 'min': 1, 'max':240, 'ct': 'aia_94.lut'},
                             131:{'scaling':'LOG', 'min': 3, 'max':500, 'ct': 'aia_131.lut'},
                             171:{'scaling':'LOG', 'min': 13, 'max':10000, 'ct': 'aia_171.lut'},
                             193:{'scaling':'LOG', 'min': 40, 'max':10000, 'ct': 'aia_193.lut'},
                             211:{'scaling':'LOG', 'min': 20, 'max':4000, 'ct': 'aia_211.lut'},
                             304:{'scaling':'LOG', 'min': 0.25, 'max':1000, 'ct': 'aia_304.lut'},
                             335:{'scaling':'LOG', 'min': 0.25, 'max':60, 'ct': 'aia_335.lut'},
                             1600:{'scaling':'LOG', 'min': 15, 'max':250, 'ct': 'aia_1600.lut'},
                             1700:{'scaling':'LOG', 'min': 215, 'max':4500, 'ct': 'aia_1700.lut'}
        }

        # If the download path doesn't exist, make one.
        if not os.path.exists(self.path):
            os.mkdir(self.path)


    def assemble_jsoc_string(self, wavelength:int=None):
        '''
        Given all the parameters, create the jsoc string to query the data

        Parameters:
            wavelength:  int
                AIA wavelength used to generate jsoc string

        Returns:
            None
        '''

        jsoc_string = f"[{self.sdate.isoformat()}-{self.edate.isoformat()}@{self.cadence}]" # used to assemble the query string that will be sent to the JSOC database

        # # The jsocString is used to assemble a string for query requests
        # # Assemble query string for AIA.
        if self.instrument == 'aia':
            if wavelength in [94, 131, 171, 193, 211, 304, 335]:
                jsoc_string = 'aia.lev1_euv_12s' + jsoc_string + f"[{wavelength}]"
            elif wavelength in [1600, 1700] :
                jsoc_string = 'aia.lev1_uv_24s' + jsoc_string + f"[{wavelength}]"
            elif wavelength == 4500:
                jsoc_string = 'aia.lev1_vis_1h' + jsoc_string + f"[{wavelength}]"
            # Adding image only to the JSOC string if user doesn't want spikes
            if not self.get_spike:
                jsoc_string = jsoc_string + f"{{image}}"

        # Assemble query string for HMI.
        if self.instrument == 'hmi':
            jsoc_string = 'hmi.M_720s' + jsoc_string

        return jsoc_string



    def create_query_request(self):
        '''
        Create a query request to get the number of files to download

        Parameters:
            None

        Returns:
            query: (panda.df)
                Dataframe with the number of files to download
                - Dates of the files
                - Number of files
        '''
        query_list = []

        for wavelength in self.wavelength:
            jsoc_string = self.assemble_jsoc_string(wavelength)
            query = self.client.query(jsoc_string, key = 't_rec')
            query_list.append(query)

        return query_list


    def download_data(self):
        '''
        Takes the jsoc string and downloads the data

        Parameters:
            None

        Returns:
            export_request: (panda.df)
                Dataframe with the number of files to download
        '''
        export = []
        # Renames file name to this format: YYYYMMDD_HHMMSS_RESOLUTION_INSTRUMENT.fits

        for wavelength in self.wavelength:
            jsoc_string = self.assemble_jsoc_string(wavelength)
            if self.format == 'jpg' and self.instrument == 'aia':
                export_request = self.client.export(jsoc_string,
                                                    protocol = self.format,
                                                    filenamefmt=None,
                                                    protocol_args = self.jpg_defaults[wavelength])
            else:
                export_request = self.client.export(jsoc_string,
                                                    protocol = self.format,
                                                    filenamefmt=None)
            export_output = export_request.download(self.path)
            export.append(export_output)
            self.rename_filename(export_output)
            if self.instrument == 'hmi':
                break
        # print(export[0]["record"])
        return export


    def rename_filename(self, export_request):
        '''
        Rename file name to this format: YYYYMMDD_HHMMSS_RESOLUTION_INSTRUMENT.[file_type] 

        Parameters:
            None
        
        Returns:
            None
        '''

        # QUESTIONS: What do all resolutions look like in string? Do we use sdate?
        # https://sdo.gsfc.nasa.gov/data/aiahmi/
        # an AIA string looks like this:  "aia.lev1_euv_12s[2010-12-21T00:00:00Z-2010-12-31T00:00:00Z@12h][171]" 
        # an HMI looks like this:         "hmi.M_720s[2010-12-21T00:00:00Z-2010-12-31T00:00:00Z@12h]"

        # aia.lev1_euv_12s.2010-12-21T120013Z.171.image_lev1.fits
        # or
        # aia.lev1_euv_12s.2010-12-21T000013Z.171.spikes.fits
        #
        # hmi.m_720s.20101223_000000_TAI.1.magnetogram.fits

        # We're using RegEx:
        # https://www.rexegg.com/regex-quickstart.html - RegEx cheat sheet

        files = export_request["download"]
        records = export_request["record"]

        for file, record in zip(files, records): # need to adjust RegEx still.
            file = file.replace("\\", "/").split("/")[-1]
            # File:   aia.lev1_euv_12s.2010-12-21T000004Z.94.image_lev1.fits 
            # Record: aia.lev1_euv_12s[2010-12-21T00:00:02Z][94]

            instrument = re.search(r"[a-z]+", record)
            date = re.search(r"(\d+)(\S)(\d+)(\S)(\d+)", record)     # (\.) ([-|\.])
            # resolution = re.search(r"4k", file) # NEED TO FIX THIS (not using RegEx - dummy statement)
            hhmmss = re.search(r"(\d+):(\d+):(\d+)", record)
            file_type = re.search(r"(jpg|fits)", file) # Need spikes files too.
            wavelength = re.search(r"(\]\[(\d+))", record)

            spikes = ""
            if re.search("spikes", file):
                spikes = ".spikes"
            
            # Rename file name to this format: YYYYMMDD_HHMMSS_RESOLUTION_INSTRUMENT.[filetype]

            new_file_name = date.group().replace('-','').replace('.','') + '_' + hhmmss.group().replace(':','') + '_' + instrument.group() + "_" + wavelength.group(2) + '_' + '4k' + spikes + '.' + file_type.group()
            # print(newFileName) # for testing.
            # rename file.
            os.rename(os.path.join(self.path, file), os.path.join(self.path, new_file_name))


def parse_args(args=None):
    """
    Parses command line arguments to script. Sets up argument for which 
    dataset to label.

    Example:
    python downloader.py --email email@email.edu -sd 2010-12-21 -ed 2010-12-22 -i aia -wl 171 131 -c 24h -f jpg -p "D:\Mis Documentos\AAResearch\SEARCH\hits-sdo-downloader\command_test" -dlim 3

    Parameters:
        args (list):    defaults to parsing any command line arguments
    
    Returns:
        parser args:    Namespace from argparse
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--email',
                        type=str,
                        help='JSOC registered email to enable dowloading of fits and jpg images'
                        )
    parser.add_argument('-sd','--sdate',
                        type=str,
                        help='Starting date in ISO format (YYYY-MM-DD hh:mm:ss) to define the period of observations to download. Has to be after May 25th, 2010'
                        )
    parser.add_argument('-ed','--edate',
                        type=str,
                        help='End date in ISO format (YYYY-MM-DD hh:mm:ss) to define the period of observations to download'
                        )
    parser.add_argument('-i','--instrument',
                        type=str,
                        help='Instrument to download, currently only HMI and AIA'
                        )
    parser.add_argument('-wl','--wavelength',
                        nargs='+',
                        type=int,
                        help='AIA wavelength of images to download, it is ignored if instrument is HMI'
                        )
    parser.add_argument('-c','--cadence',
                        type=str,
                        help='Frequency of the images within the download interval has to be a number and a string character. "s" for seconds, "m" for minutes, "h" for hours, and "d" for days.'
                        )
    parser.add_argument('-f','--format',
                        type=str,
                        help='Specify the file type to download, either fits or jpg'
                        )
    parser.add_argument('-p','--path',
                        type=str,
                        help='Path to download the files to (default is current directory)'
                        )
    parser.add_argument('-dlim','--download_limit',
                        type=int,
                        default = 1000,
                        help='Limit the number of files to download, defaults to 1000'
                        )

    return parser.parse_args(args)


if __name__=="__main__":
    parser = parse_args()
    downloader = Downloader(parser.email,
                            parser.sdate,
                            parser.edate,
                            parser.wavelength,
                            parser.instrument,
                            parser.cadence,
                            parser.format,
                            parser.path,
                            parser.download_limit)

    request = downloader.create_query_request() # create drms client query request.
    is_larger = False
    for i in request:
        if i.shape[0] > downloader.download_limit:
            print(f'Download request of {i.shape[0]} files is larger than download limit of {downloader.download_limit} files')
            is_larger = True
            break

    if not is_larger:
        downloader.download_data()

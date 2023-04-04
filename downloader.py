"""
Add docstring of how we use modules
"""
import datetime
import os   #system files
import drms #data query
import tarfile
import re
# use drums.utils? https://docs.sunpy.org/projects/drms/en/stable/_modules/drms/utils.html#
class Downloader:
    def __init__(self, email:str=None, sdate:str=None, edate:str=None, wavelength:list=None, instrument:str = None, cadence:str = None, format:str = None, path:str = None, downloadLimit:int = None, getSpike:bool = None):
        """
        Initialize a downloader class with paramaters to interface with jsoc http://jsoc.stanford.edu/

        Parameters:
            email: (str)
                JSOC registered email to enable dowloading of fits and jpg images
            sdate: (str)
                Starting date in ISO format (YYYY-MM-DD hh:mm:ss) to define the period of observations to download.
                Has to be after May 25th, 2010
            edate: (str)
                End date in ISO format (YYYY-MM-DD hh:mm:ss) to define the period of observations to download
            instrument: (str)
                Instrument/module in the SDO spacecraft to download from, currently only HMI and AIA
            wavelength: (list)
                Only valid for AIA. EUV wavelength(s) of images to download, it is ignored if instrument is HMI
            cadence: (str)
                Frequency at which we want to download images within the download interval. It has to be a number and a string character.
                "s" for seconds, "m" for minutes, "h" for hours, and "d" for days.
            format: (str)
                Specify the file type to download, either fits or jpg
            path: (str)
                Path to download the files to (default is current directory)
            downloadLimit: (int)
                Limit the number of files to download, if None, all files will be downloaded
            getSpike: (bool)
                Flag that specifies whether to download spikes files for AIA. Spikes are hot pixels
                that are normally removed from AIA images, but the user may want to retrieve them.

        """
        self.email = email
        self.sdate = datetime.date.fromisoformat(sdate)
        self.edate = datetime.date.fromisoformat(edate)
        self.instrument = instrument.lower()    # Instrument/module in the SDO spacecraft (i.e. hmi, aia)
        self.validinstruments = ["aia", "hmi"]  #(hmi - magnetic fields), (aia - the sun in ultraviolet)
        self.wavelength = wavelength            # Only valid for AIA - Different colors of ultraviolet - used to look at different levels of the sun's atmosphere
        self.validwavelengths = [1700, 4500, 1600, 304, 171, 193, 211, 335, 94, 131]
        self.cadence = cadence # Cadence means the frequency at which we want to download images (e.g. one every three ours "3h")
        self.validcadence = ['s', 'm', 'h', 'd']   # s -> seconds, m -> minutes, h -> hours, d -> days) {cadence = 1d}  
        self.format = format
        self.validformats = ['fits', 'jpg']
        self.path = path
        self.jsocString = None # Very specific way of putting together dates and instruments so that we can retrieve from the JSOC
        self.largeFileLimit = False # False, there is no large file limit (limits number of files)
        self.downloadLimit = downloadLimit # Maximum number of files to download.
        self.client = drms.Client(email = self.email, verbose = True)
        self.getSpike = getSpike # Bool switch to download spikes files or not.   Spikes are hot pixels normally removed from AIA, but can be donwloaded if desired

        # If the download path doesn't exist, make one.
        if not os.path.exists(self.path):
            os.mkdir(self.path)


    def assembleJsocString(self):
        '''
        Given all the parameters, create the jsoc string to query the data

        Parameters:
            None

        Returns:
            None
        '''
        self.jsocString = f"[{self.sdate.isoformat()}-{self.edate.isoformat()}@{self.cadence}]" # used to assemble the query string that will be sent to the JSOC database
        # The jsocString is used to assemble a string for query requests
        # Assemble query string for AIA.
        if(self.instrument == 'aia'):
            if(self.wavelength in [94, 131, 171, 193, 211, 304, 335]):
                self.jsocString = 'aia.lev1_euv_12s' + self.jsocString + f"[{self.wavelength}]"
            elif(self.wavelength in [1600, 1700]):
                self.jsocString = 'aia.lev1_uv_24s' + self.jsocString + f"[{self.wavelength}]"
            elif(self.wavelength == 4500):
                self.jsocString = 'aia.lev1_vis_1h' + self.jsocString + f"[{self.wavelength}]"
            # Adding image only to the JSOC string if user doesn't want spikes
            if (not self.getSpike):
                self.jsocString = self.jsocString + f"{{image}}"

        # Assemble query string for HMI.
        if(self.instrument == 'hmi'):
            self.jsocString = 'hmi.M_720s' + self.jsocString
            

    def createQueryRequest(self):
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
        query = self.client.query(self.jsocString, key = 't_rec')
        return query




    def downloadData(self):
        '''
        Takes the jsoc string and downloads the data

        Parameters:
            None

        Returns:
            export_request: (panda.df)
                Dataframe with the number of files to download
        '''
        # Renames file name to this format: YYYYMMDD_HHMMSS_RESOLUTION_INSTRUMENT.fits
        export_request = self.client.export(self.jsocString, protocol = self.format, filenamefmt=None)
        self.export = export_request.download(self.path)
        
        return self.export
        

    def renameFilename(self):
        '''
        Rename file name to this format: YYYYMMDD_HHMMSS_RESOLUTION_INSTRUMENT.[filetype] 

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

        files = os.listdir(self.path)

        for file in files:

            instrument = re.search(r"[a-z]+", file)
            date = re.search(r"\d+", file)
            resolution = re.search(r"4k", file) # NEED TO FIX THIS (not using RegEx - dummy statement)
            hhmmss = re.search(r"(_)(\d+)(_)", file)
            fileType = re.search(r"(jpg|fits)", file)
            # wavelength = 
            # Rename file name to this format: YYYYMMDD_HHMMSS_RESOLUTION_INSTRUMENT.[filetype]

            newFileName = date.group() + '_' + hhmmss.group(2) + '_' + instrument.group() + "_" + resolution.group() + '.' + fileType.group()
            # print(newFileName) # for testing.
            # rename file.
            os.rename(os.path.join(self.path, file), os.path.join(self.path, newFileName))

            # older method:
            # instruments = ['aia', 'hmi']
            # dateRegex = ""
            # resolutionRegex = ""
            # instrumentRegex = ""
            # cadenceRegex = ""
            # fileTypeRegex = ""
            # print(instrument.group())
            # print(date.group())
            # print(resolution.group())
            # print(cadence.group())
            # print(fileType.group())

            # date = file.split('.')[2]
            # resolution = file.split('.')[3]
            # resolution = 4096
        
            # if self.instrument == 'hmi':
            #     date = date.split('_')[0]
            #     newFileName = date + '_' + resolution + '_hmi.' + self.format
            # elif self.instrument == 'aia':
            #     year = date[0:4]
            #     month = date[5:7]
            #     day = date[8:10]
            #     hour = date[11:13]
            #     minute = date[13:15]
            #     second = date[15:17]
            #     newFileName = year + month + day + '_' + hour + minute + second + '_' + resolution + '_aia.' + self.format
            
            # os.rename(os.path.join(self.path, file), os.path.join(self.path, newFileName))
            # print (newFileName)   
            #      
            # newFileName = ""
            # print(newFileName)
            


    # def splitSpikes(self):
    #     name = "SpikesFolder"
    #     if not os.path.exists(name):
    #          os.mkdir(name)
        
        
    #     search_string = "spikes"
    #     for filename in os.listdir(directory)
    #     if search_string in filename:
        
    #     # -- finding substring within filenames in a directory --
    #     # search_string = "stuff"
    #     # for filename in os.listdir(directory):    # iterate through the files in the directory
    #     # if search_string in filename: # this will search for the substring "search_string" in the filename string
    #     # < do stuff >
        
    #     #can also look at find() method
    #     #filename.find('spikes') <- yes!
        
    #     for file_name in .os.listdir('.'):
    #         if file_name.endswith('.txt'):
                
                


        





 



 







'''
Jacob
    - downloadLimit has to work with the physical memory limits of the device
    - Great use of commenting before any code they may have to explain later
    - camelCase vs snake_case and mixing the two, consider a linter and autoformatter (PyLint & Black)?
    - Orange team is currently only testing jpeg, so we will need to refactor possibly
    - Is it possible that there is a scope of time with no photos taken? How would the user know an error hasn't occurred?
    - What kind of stacking? What kind of algorithm will you use to stack the images? What is the goal of stacking these images?
        - Is the goal to remove noise?

'''

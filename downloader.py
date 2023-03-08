import urllib
import datetime
import os
import drms
import tarfile

class Downloader:
    def __init__(self, email:str=None, sdate:str=None, edate:str=None, wavelength:int=None, instrument:str = None, cadence:str = None, format:str = None, path:str = None, downloadLimit:int = None):
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
                Instrument to download, currently only HMI and AIA
            wavelength: (int)
                AIA wavelength of images to download, it is ignored if instrument is HMI
            cadence: (str)
                Frequency of the images within the download interval has to be a number and a string character.
                "s" for seconds, "m" for minutes, "h" for hours, and "d" for days.
            format: (str)
                Specify the file type to download, either fits or jpg
            path: (str)
                Path to download the files to (default is current directory)
            downloadLimit: (int)
                Limit the number of files to download, if None, all files will be downloaded
        """
        self.email = email
        self.sdate = datetime.date.fromisoformat(sdate)
        self.edate = datetime.date.fromisoformat(edate)
        self.instrument = instrument.lower()
        self.validinstruments = ["aia", "hmi"]
        self.wavelength = wavelength
        self.validwavelengths = [1700, 4500, 1600, 304, 171, 193, 211, 335, 94, 131]
        self.cadence = cadence
        self.validcadence = ['s', 'm', 'h', 'd']       
        self.format = format
        self.validformats = ['fits', 'jpg']
        self.path = path
        self.tarPath = os.path.join(self.path,'untarFolder')
        self.jsocString = None
        self.largeFileLimit = False
        self.downloadLimit = downloadLimit

        self.client = drms.Client(email = self.email, verbose = True)

        if not os.path.exists(self.path):
            os.mkdir(self.path)

        if not os.path.exists(self.tarPath):
            os.mkdir(self.tarPath)


    def assembleJsocString(self):
        '''
        Given all the parameters, create the jsoc string to query the data

        Parameters:
            None

        Returns:
            None
        '''
        self.jsocString = f"[{self.sdate.isoformat()}-{self.edate.isoformat()}@{self.cadence}]"

        if(self.instrument == 'aia'):
            if(self.wavelength in [94, 131, 171, 193, 211, 304, 335]):
                self.jsocString = 'aia.lev1_euv_12s' + self.jsocString + f"[{self.wavelength}]"
            elif(self.wavelength in [1600, 1700]):
                self.jsocString = 'aia.lev1_uv_24s' + self.jsocString + f"[{self.wavelength}]"
            elif(self.wavelength == 4500):
                self.jsocString = 'aia.lev1_vis_1h' + self.jsocString + f"[{self.wavelength}]"

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
        export_request = self.client.export(self.jsocString, protocol = self.format, method='url-tar')
        self.export = export_request.download(self.tarPath, 0)

        for row in self.export.rows:
            print(row['download'])
        return self.export
    


    def untarDownload(self):
        '''
        Untar the downloaded tar file

        Parameters:
            None

        Returns:
            None
        '''
        for row in self.export.rows:
            tar = tarfile.open(row['download']) # edit to a general filename
            tar.extractall(self.path)
            tar.close()
            print(row['download'])
        

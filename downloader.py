import datetime
import os   #system files
import drms #data query
import tarfile
# use drums.utils? https://docs.sunpy.org/projects/drms/en/stable/_modules/drms/utils.html#
class Downloader:
    def __init__(self, email:str=None, sdate:str=None, edate:str=None, wavelength:int=None, instrument:str = None, cadence:str = None, format:str = None, path:str = None, downloadLimit:int = None, fileName = str):
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
        self.instrument = instrument.lower()    #wat is an instrument? VS waivlength?
        self.validinstruments = ["aia", "hmi"]  #(hmi - magnetic fields), (aia -the sun in ultraviolet)
        self.wavelength = wavelength            #what is the wavelength used for? - different colors of ultraviolet - used to look at different levels of the sun's atmosphere
        self.validwavelengths = [1700, 4500, 1600, 304, 171, 193, 211, 335, 94, 131]
        self.cadence = cadence #what is the cadence of the cadence? - frequency of measurements
        self.validcadence = ['s', 'm', 'h', 'd']   #what does smhd stand for?  --(seconds, minutes, hours, days) {cadence = 1d}  
        self.format = format
        self.validformats = ['fits', 'jpg']
        self.path = path
        # self.tarPath = os.path.join(self.path,'untarFolder')
        self.jsocString = None  #
        self.largeFileLimit = False #false, there is no large file limit (limits number of files)
        self.downloadLimit = downloadLimit # maximum number of files to download.
        self.client = drms.Client(email = self.email, verbose = True)

        # if the download path doen't exist, make one.
        if not os.path.exists(self.path):
            os.mkdir(self.path)

        # if not os.path.exists(self.tarPath):
        #    os.mkdir(self.tarPath)


    def assembleJsocString(self):
        '''
        Given all the parameters, create the jsoc string to query the data

        Parameters:
            None

        Returns:
            None
        '''
        self.jsocString = f"[{self.sdate.isoformat()}-{self.edate.isoformat()}@{self.cadence}]"
        
        #what is the JsocString used for?
        # assemble query string for AIA.
        if(self.instrument == 'aia'):
            if(self.wavelength in [94, 131, 171, 193, 211, 304, 335]):
                self.jsocString = 'aia.lev1_euv_12s' + self.jsocString + f"[{self.wavelength}]"
            elif(self.wavelength in [1600, 1700]):
                self.jsocString = 'aia.lev1_uv_24s' + self.jsocString + f"[{self.wavelength}]"
            elif(self.wavelength == 4500):
                self.jsocString = 'aia.lev1_vis_1h' + self.jsocString + f"[{self.wavelength}]"
        # assemble qury string for HMI.
        if(self.instrument == 'hmi'):
            self.jsocString = 'hmi.M_720s' + self.jsocString
        # self.jsocString =  "aia.lev1_euv_12s[2010-12-21T00:00:00Z-2010-12-31T00:00:00Z@12h][171]"
        print(self.jsocString)



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
        # File name right now: aia.lev1_euv_12s.2010-12-21T000013Z.171.image_lev1.fits
        # Need to rename file name to this format: YYYYMMDD_HHMMSS_RESOLUTION_INSTRUMENT.fits
        # 20101221_000013_171_AIA.fits
        export_request = self.client.export(self.jsocString, protocol = self.format, filenamefmt=None)
        self.export = export_request.download(self.path)
        
        # for row in self.export.rows:
        #     print(row['download'])
        return self.export
        

    def renameFilename(self):
        '''
        Rename file name to this format: YYYYMMDD_HHMMSS_RESOLUTION_INSTRUMENT.fits

        Parameters:
            None
        
        Returns:
            None
        '''
        # TO DO: a method for jpg and one for fits?

        files = os.listdir(self.path)
        for file in files:
            # Grab 2010-12-21T000013Z from the file name
            date = file.split('.')[2]
            # Grab 171 from the file name
            wavelength = file.split('.')[3]
            # Grab aia from the file name
            instrument = file.split('.')[0]

            # Split the date into year, month, day, hour, minute, second
            year = date[0:4]
            month = date[5:7]
            day = date[8:10]
            hour = date[11:13]
            minute = date[13:15]
            second = date[15:17]

            # Rename the file   
            newFileName = year + month + day + '_' + hour + minute + second + '_' + wavelength + '_' + instrument + '.fits'
            os.rename(os.path.join(self.path, file), os.path.join(self.path, newFileName))
            print(">>>>>>>>>>>>>>>>>>>>", hour, " ", minute, " ", second)

    
    
   
    def splitSpikes(self):
        name = "SpikesFolder"
        if not os.path.exists(name):
             os.mkdir(name)
        #Pattern.fullmatch(string[, 0[, 0]])
        
        search_string = "spikes"
        for filename in os.listdir(directory)
        if search_string in filename:
        
        # -- finding substring within filenames in a directory --
        # search_string = "stuff"
        # for filename in os.listdir(directory):    #iterate through the files in the directory
        # if search_string in filename: # this will search for the substring "search_string" in the filename string
        # < do stuff >
        
        #can also look at find() method
        #filename.find('spikes') <- yes!
        
        for file_name in .os.listdir('.'):
            if file_name.endswith('.txt'):
                
                


        





 



 









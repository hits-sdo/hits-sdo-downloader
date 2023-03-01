import urllib
import datetime
import os
import drms

class Downloader:

    def __init__(self, email:str=None, sdate:str=None, edate:str=None, wavelength:int=None, instrument:str = None, cadence:str = None, format:str = None, path:str = None, downloadLimit:int = None):
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
        self.jsocString = None
        self.largeFileLimit = False
        self.downloadLimit = downloadLimit

        self.client = drms.Client(email = self.email, verbose = True)

        if not os.path.exists(self.path):
            os.mkdir(self.path)

    def assembleJsocString(self):
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
        query = self.client.query(self.jsocString, key = 't_rec')
        return query

    def downloadData(self):
        export_request = self.client.export(self.jsocString, protocol = self.format, method='url-tar')
        return export_request.download(self.path, 0)

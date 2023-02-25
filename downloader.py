import urllib
import datetime
import os
import drms

class Downloader:

    def __init__(self, email:str=None, sdate:str=None, edate:str=None, wavelength:int=None, instrument:str = None, cadence:str = None, format:str = None, path:str = None):
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
        self.validformats = ['fits', 'jpeg']
        self.path = path
        self.jsocString = None

        self.client = drms.Client(email = self.email, verbose = True)

        if not os.path.exists(self.path):
            os.mkdir(self.path)

    def assembleJsocString(self):
        self.jsocString = f"[{self.sdate.isoformat()}-{self.edate.isoformat()}@{self.cadence}]"

        if(self.instrument == 'aia'):
            self.jsocString = 'aia.lev1_euv_12s' + self.jsocString + f"[{self.wavelength}]"
            
    def downloadData(self):
        query = self.client.query(self.jsocString, key = 't_rec')
        export_request = self.client.export(self.jsocString)
        export_request.download(self.path, 0)
        return query
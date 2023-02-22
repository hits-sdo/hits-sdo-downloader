import urllib
import datetime

class Downloader:
    # def __init__(self):
    #     ...

    def __init__(self, email:str=None, sdate:str=None, edate:str=None, wavelength:int=None, instrument:str = None, cadence:str = None):
        self.email = email
        self.sdate = datetime.date.fromisoformat(sdate)
        self.edate = datetime.date.fromisoformat(edate)
        self.instrument = instrument.lower()
        self.validinstruments = ["aia", "hmi"]
        self.wavelength = wavelength
        self.validwavelengths = [1700, 4500, 1600, 304, 171, 193, 211, 335, 94, 131]
        self.cadence = cadence
        self.validcadence = ['s', 'm', 'h', 'd']        



# TODO:
# - Method:
#     + download(self, ...)
#     + connect(self, ...)
#     + build_path(self, ...)
#     + query(self, ...)

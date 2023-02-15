import urllib
import datetime

class Downloader:
    # def __init__(self):
    #     ...

    def __init__(self, email:str=None, sdate:str=None, edate:str=None):
        self.email = email
        self.sdate = datetime.date.fromisoformat(sdate)
        self.edate = datetime.date.fromisoformat(edate)
        



# TODO:
# - Method:
#     + download(self, ...)
#     + connect(self, ...)
#     + build_path(self, ...)
#     + query(self, ...)

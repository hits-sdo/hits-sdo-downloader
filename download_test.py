import unittest
from downloader import Downloader
import datetime
import re
import os

class DownloaderTest(unittest.TestCase):

    def setUp(self): 
        email = 'amunozj@boulder.swri.edu' 
        sdate = '2010-12-21' # '2023-02-14' - the start date of the request.
        edate = '2010-12-22' # '2023-02-14' - the end date of the request.
        wavelength = [131, 304] # valid wl = 1700, 4500, 1600, 304, 171, 193, 211, 335, 94, 131
        instrument = "hmi"
        cadence = '24h'
        format = 'jpg'
        path = os.path.join(os.getcwd(), 'data2')
        downloadLimit = 25
        getSpike = False
        self.downloader = Downloader(email, sdate, edate, wavelength, instrument, cadence, format, path, downloadLimit, getSpike)
        self.downloader.assembleJsocString()

    def test_checkEmail(self):
        self.assertIsNotNone(self.downloader)
        self.assertIsInstance(self.downloader.email, str)
        self.assertIn('@', self.downloader.email)
        self.assertIn('.', self.downloader.email.split('@')[-1])

    def test_checkstartDate(self):
        self.assertIsNotNone(self.downloader)
        self.assertTrue(self.downloader.sdate >= datetime.date(2010, 5, 20))

    def test_checkEndDate(self):
        self.assertIsNotNone(self.downloader)
        self.assertTrue(self.downloader.edate > self.downloader.sdate and self.downloader.edate < datetime.date.today() )

    def test_checkaiaWavelength(self):
        if(self.downloader.instrument == "aia"):
            self.assertIsNotNone(self.downloader.wavelength)
            self.assertIsInstance(self.downloader.wavelength, list)
            self.assertTrue(set(self.downloader.wavelength).issubset(set(self.downloader.validwavelengths)))
            self.assertTrue(len(set(self.downloader.wavelength)) == len(self.downloader.wavelength))
    
    def test_checkInstrument(self):
        self.assertIsNotNone(self.downloader.instrument)
        self.assertTrue(self.downloader.instrument in self.downloader.validinstruments)

    def test_checkCadence(self):
        self.assertIsNotNone(self.downloader.cadence)
        self.assertTrue(self.downloader.cadence.endswith(tuple(self.downloader.validcadence)))
        m = re.search("^\d+[smhd]$", self.downloader.cadence) # == (time) // (s,m,d,h) ??
        self.assertIsNotNone(m)

    def test_checkFormats(self):
        self.assertIsNotNone(self.downloader.format)
        self.assertTrue(self.downloader.format in self.downloader.validformats)

    def test_path(self):
        self.assertIsNotNone(self.downloader.path)
        self.assertTrue(os.path.exists(self.downloader.path))

    def test_jsocString(self):
        # self.assertIsNotNone(self.downloader.jsocString)
        # A JSOC string is the command used to retrieve data from the Joint Operations Science Center (JSOC) in Stanford 
        # an AIA string looks like this:  "aia.lev1_euv_12s[2010-12-21T00:00:00Z-2010-12-31T00:00:00Z@12h][171]" 
        # an HMI looks like this:         "hmi.M_720s[2010-12-21T00:00:00Z-2010-12-31T00:00:00Z@12h]"

        query = self.downloader.downloadData()
        

    def test_queryRequest(self):
        request = self.downloader.createQueryRequest() # create drms client query request.
        for i in request:
            self.assertTrue(i.shape[0] < self.downloader.downloadLimit)


    def test_spikeOption(self):
        self.assertIsNotNone(self.downloader.getSpike)
       
 
if __name__ == "__main__":
    unittest.main()

import unittest
from downloader import Downloader
from urllib.parse import urlparse
import datetime
import re
import sys, os
import tarfile

class DownloaderTest(unittest.TestCase):

    def setUp(self): 
        email = 'amunozj@boulder.swri.edu' 
        sdate = '2010-12-21' # '2023-02-14' - the start date of the request.
        edate = '2010-12-22' # '2023-02-14' - the end date of the request.
        wavelength = [171, 131]
        instrument = "aia"
        cadence = '24h'
        format = 'fits'
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

            # valid = True
            # for item in self.downloader.wavelength:  
            #     if item not in self.downloader.validwavelengths:
            #         valid = False
            # self.assertTrue(self.downloader.wavelength in self.downloader.validwavelengths)
    
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
        # print(self.downloader.jsocString) 
        query = self.downloader.downloadData()
#        self.downloader.renameFilename()
        

    def test_queryRequest(self):
        request = self.downloader.createQueryRequest() # create drms client query request.
        self.assertTrue(request.shape[0] < self.downloader.downloadLimit)

    # def test_renameFileName(self):
    #      fileName = self.downloader.renameFilename
    #      self.assertTrue(fileName) 
        
    # def test_indexing(self):
    #     print(os.listdir(self.downloader.path))
    #     self.assertTrue(len(os.listdir(self.downloader.path)) > 0) # is not empty

    # def test_fileName(self):
    #     self.assertTrue()    

    def test_spikeOption(self):
        self.assertIsNotNone(self.downloader.getSpike)
       
 
if __name__ == "__main__":
    unittest.main()

# Team Yellow and Orange questions and comments:

# What is the main goal of team red
# - Provide a way to download data using the JSOC API

# I had a question regarding what the class path looked like regarding the file downloaded
# - I think the path is the directory where the file is downloaded to

# I know that we are working with a pickle'd image for team Yellow -- does this affect the code of 
# teams red/orange?
# - No, it shouldn't affect the code
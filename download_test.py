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
        edate = '2010-12-23' # '2023-02-14' - the end date of the request.
        wavelength = 171
        instrument = "aia"
        cadence = '12h'
        format = 'fits'
        path = os.path.join(os.getcwd(), 'data2')
        downloadLimit = 25
        self.downloader = Downloader(email, sdate, edate, wavelength, instrument, cadence, format, path, downloadLimit)
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
            self.assertIsInstance(self.downloader.wavelength, int)
            self.assertTrue(self.downloader.wavelength in self.downloader.validwavelengths)
    
    def test_checkInstrument(self):
        self.assertIsNotNone(self.downloader.instrument)
        self.assertTrue(self.downloader.instrument in self.downloader.validinstruments)

    def test_checkCadence(self):
        self.assertIsNotNone(self.downloader.cadence)
        # self.assertTrue(self.downloader.cadence[-1] in self.downloader.validcadence)
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
        self.assertIsNotNone(self.downloader.jsocString)
        print(self.downloader.jsocString) # what does the jsoc string look like?
        query = self.downloader.downloadData()
        # self.downloader.renameFilename()
        

    def test_queryRequest(self):
        request = self.downloader.createQueryRequest() # create drms client query request.
        self.assertTrue(request.shape[0] < self.downloader.downloadLimit)

    # def test_untar(self):
    #      tar = tarfile.open(os.path.join(self.downloader.path,'JSOC_20230301_080.tar')) # Left off here - test failing; no such file or directory + file being downloaded twice.
    #      tar.extractall(self.downloader.path)
    #      tar.close()

    # def test_indexing(self):
    #     print(os.listdir(self.downloader.path))
    #     self.assertTrue(len(os.listdir(self.downloader.path)) > 0) # is not empty

    # def test_fileName(self):
    #     self.assertTrue()    
        
 
if __name__ == "__main__":
    unittest.main()

# Team Yellow and Orange questions and comments: 

#What is the main goal of team red

#I had a question regarding what the class path looked like regarding the file downloaded


# i know that we are working with a pickle'd image for team Yellow -- does this affect the code of 
# teams red/orange?
#
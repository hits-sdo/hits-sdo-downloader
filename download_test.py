import unittest
from downloader import Downloader
from urllib.parse import urlparse
import datetime
import re
import sys, os

class DownloaderTest(unittest.TestCase):

    def setUp(self): 
        email = 'amunozj@boulder.swri.edu'
        sdate = '2010-12-21' # '2023-02-14'
        edate = '2010-12-22' # '2023-02-14'
        wavelength = 304
        instrument = "aia"
        cadence = '1d'
        format = 'fits'
        path ='D:/Mis Documentos/AAResearch/SEARCH/hits-sdo-downloader/data2'
        self.downloader = Downloader(email, sdate, edate, wavelength, instrument, cadence, format, path)
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
        m = re.search("^\d+[smhd]$", self.downloader.cadence)
        self.assertIsNotNone(m)

    def test_checkFormats(self):
        self.assertIsNotNone(self.downloader.format)
        self.assertTrue(self.downloader.format in self.downloader.validformats)

    def test_path(self):
        self.assertIsNotNone(self.downloader.path)
        self.assertTrue(os.path.exists(self.downloader.path))

    def test_jsocString(self):
        self.assertIsNotNone(self.downloader.jsocString)
        print(self.downloader.jsocString)
        query = self.downloader.downloadData()
        print(query)


        
        
        



        # Should we assertEqual the downloader to the self.downloader?
        # Okay so it seems the problem is that our "assertisNotNone" method doesn't exist - Daniel
        # We should make one if it doesnt then (?)
        # Yes I looked at the docs, the "is" needs to be "Is"

    # Ok since now we have a class that works, maybe start with the download methods? - Jasper

    # def test_checkDownload(self):
        
 
if __name__ == "__main__":
    unittest.main()
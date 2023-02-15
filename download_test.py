import unittest
from downloader import Downloader
from urllib.parse import urlparse
import datetime

class DownloaderTest(unittest.TestCase):

    def setUp(self): 
        email = '.team_red@hotmail.com'
        sdate = '2010-12-21' # '2023-02-14'
        edate = '2023-12-21' # '2023-02-14'
        self.downloader = Downloader(email, sdate, edate)

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



        # Should we assertEqual the downloader to the self.downloader?
        # Okay so it seems the problem is that our "assertisNotNone" method doesn't exist - Daniel
        # We should make one if it doesnt then (?)
        # Yes I looked at the docs, the "is" needs to be "Is"

    # Ok since now we have a class that works, maybe start with the download methods? - Jasper

    # def test_checkDownload(self):
        
 
if __name__ == "__main__":
    unittest.main()
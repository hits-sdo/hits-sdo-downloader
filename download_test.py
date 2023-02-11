import unittest
from downloader import Downloader
from urllib.parse import urlparse  

class DownloaderTest(unittest.TestCase):
    # def __init__(self, *args, **kwargs):
    #     super(DownloaderTest, self).__init__(*args, **kwargs)
    #     self.downloader = Downloader()

    
    # Try catch throw exception (?)
    # # check if the file exists? - jaedyn
    # assertEqual(downloader, self.downloader) ?

    # Ok what should we do now?


    # def test_checkDownloader(self):
    #     downloader = Downloader()
    #     # assertEqual(downloader, self.downloader)
    #     self.assertIsNotNone(downloader)


        
    def test_checkEmail(self):
        email = '.team_red@hotmail.com'
        self.assertIsInstance(email, str)

        downloader = Downloader(email=email)
        self.assertIsNotNone(downloader)
        self.assertIsInstance(downloader.email, str)

        self.assertIn('@', downloader.email)
        self.assertIn('.', downloader.email.split('@')[-1])


    def test_checkDate(self):
        date = 'date'
        self.assertIsInstance(date, str)


        # Should we assertEqual the downloader to the self.downloader?
        # Okay so it seems the problem is that our "assertisNotNone" method doesn't exist - Daniel
        # We should make one if it doesnt then (?)
        # Yes I looked at the docs, the "is" needs to be "Is"

    # Ok since now we have a class that works, maybe start with the download methods? - Jasper

    # def test_checkDownload(self):
        
 
if __name__ == "__main__":
    unittest.main()
"""
 Module provides regular expression matching
"""
import re
import unittest
import datetime
import os
from downloader import Downloader

class DownloaderTest(unittest.TestCase):
    '''
    Test the Downloader class.
    '''
    def setUp(self):
        '''
        Setup the test environment.
        '''
        email = 'amunozj@boulder.swri.edu'
        sdate = '2010-12-21' # '2023-02-14' - the start date of the request.
        edate = '2010-12-22' # '2023-02-14' - the end date of the request.
        wavelength = [193, 131]
        instrument = "aia"
        cadence = '24h'
        file_format = 'jpg'
        path = os.path.join(os.getcwd(), 'data2')
        download_limit = 25
        get_spike = True
        self.downloader = Downloader(email, sdate, edate, wavelength, instrument, cadence, file_format, path, download_limit, get_spike)
        self.downloader.assemble_jsoc_string()


    def test_check_email(self):
        '''
        Test that the email is a string and contains an @ and a .
        '''
        self.assertIsNotNone(self.downloader)
        self.assertIsInstance(self.downloader.email, str)
        self.assertIn('@', self.downloader.email)
        self.assertIn('.', self.downloader.email.split('@')[-1])


    def test_check_start_date(self):
        '''
        Test that the start date is a date and is not in the future.        
        '''
        self.assertIsNotNone(self.downloader)
        self.assertTrue(self.downloader.sdate >= datetime.date(2010, 5, 20))


    def test_check_end_date(self):
        '''
        Test that the end date is a date and is not in the future.
        '''
        self.assertIsNotNone(self.downloader)
        self.assertTrue(self.downloader.edate > self.downloader.sdate and self.downloader.edate < datetime.date.today() )


    def test_check_aia_wave_length(self):
        '''
        Test that the wavelength is a list and is a valid wavelength.
        '''
        if self.downloader.instrument == "aia":
            self.assertIsNotNone(self.downloader.wavelength)
            # self.assertIsInstance(self.downloader.wavelength, list)
            #self.assertTrue(set(self.downloader.wavelength).issubset(set(self.downloader.validwavelengths)))
           # self.assertTrue(len(set(self.downloader.wavelength)) == len(self.downloader.wavelength))
            # valid = True
            # for item in self.downloader.wavelength:  
            #     if item not in self.downloader.validwavelengths:
            #         valid = False
            # self.assertTrue(self.downloader.wavelength in self.downloader.validwavelengths)


    def test_check_instrument(self):
        '''
        Test that the instrument is a string and is a valid instrument.
        '''
        self.assertIsNotNone(self.downloader.instrument)
        self.assertTrue(self.downloader.instrument in self.downloader.validinstruments)


    def test_check_cadence(self):
        '''
        Test that the cadence is a string and is a valid cadence.
        '''
        self.assertIsNotNone(self.downloader.cadence)
        self.assertTrue(self.downloader.cadence.endswith(tuple(self.downloader.validcadence)))
        m = re.search("^\d+[smhd]$", self.downloader.cadence) # == (time) // (s,m,d,h) ??
        self.assertIsNotNone(m)


    def test_check_formats(self):
        '''
        Test that the format is a string and is a valid format.
        '''
        self.assertIsNotNone(self.downloader.format)
        self.assertTrue(self.downloader.format in self.downloader.validformats)


    def test_path(self):
        '''
        Test that the path is a string and is a valid path.
        '''
        self.assertIsNotNone(self.downloader.path)
        self.assertTrue(os.path.exists(self.downloader.path))


    def test_jsoc_string(self):
        '''
        Test that the jsoc_string is a string and is not empty.
        '''
        self.assertIsNotNone(self.downloader.jsoc_string)
        # A JSOC string is the command used to retrieve data from the Joint Operations Science Center (JSOC) in Stanford 
        # an AIA string looks like this:  "aia.lev1_euv_12s[2010-12-21T00:00:00Z-2010-12-31T00:00:00Z@12h][171]" 
        # an HMI looks like this:         "hmi.M_720s[2010-12-21T00:00:00Z-2010-12-31T00:00:00Z@12h]"
        print(self.downloader.jsoc_string) 
        query = self.downloader.download_data()
       # self.downloader.rename_filename()


    def test_query_request(self):
        '''
        Test that the query request is a string and is not empty.
        '''
        request = self.downloader.create_query_request() # create drms client query request.
        self.assertTrue(request.shape[0] < self.downloader.download_limit)
    


    # def test_rename_filename(self):
    #     '''
    #     Test that the file name is a string and is not empty.
    #     '''
    #     filename = self.downloader.rename_filename
    #     self.assertTrue(filename)
    # def test_indexing(self):
    #     print(os.listdir(self.downloader.path))
    #     self.assertTrue(len(os.listdir(self.downloader.path)) > 0) # is not empty
    # def test_filename(self):
    #     self.assertTrue()

    
    def test_spike_option(self):
        '''
        Test that the spike option is a boolean.
        '''
        self.assertIsNotNone(self.downloader.get_spike)

    def test_jpg_defaults(self):
        '''
        Test to ensure that jpgs for different wavelengths have defaults
        '''
        self.assertIsNotNone(self.downloader.jpg_defaults)
        print(self.downloader.jpg_defaults[94])


if __name__ == "__main__":
    unittest.main()

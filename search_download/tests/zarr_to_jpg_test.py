import unittest
import os
from search_download.zarr_to_jpg import ZarrToJpg
import glob

class ZarrToJpgTest(unittest.TestCase):
    """
    Test the Downloader class.
    """

    def setUp(self):
        aia_path = "/d0/euv/aia/preprocessed/aia_hmi_stacks_2010_2023_1d_full_ir.zarr"
        stack_outpath = "/d0/euv/aia/preprocessed"
        # wavelength_order = [211, 193, 171]
        # wavelength_order = [304, 211, 171]
        wavelength_order = [335, 193, 94]
        debug = True
        self.zarr_to_jpg = ZarrToJpg(
            aia_path=aia_path,
            stack_outpath=stack_outpath,
            wavelength_order=wavelength_order,
            debug=debug,
        )

    def test_check_class(self):
        """
            Check that the class exists
        """
        self.assertIsNotNone(self.zarr_to_jpg)

    def test_data_exists(self):
        """
            Check that the zarr array has data
        """
        self.assertIsNotNone(self.zarr_to_jpg.data)

    def test_array_dimensions(self):
        """
            Check that the zarr array has the right dimensions
        """
        self.assertEqual(len(self.zarr_to_jpg.data.aia_hmi.shape), 4)
        self.assertEqual(self.zarr_to_jpg.aia_slice.shape[1], 3)
        self.assertTrue(
            self.zarr_to_jpg.debug and self.zarr_to_jpg.aia_slice.shape[0] == 10
        )

    def test_statistics(self):
        """
            Check that the histogram, cumulative, and percentile dictionaries have been created
        """
        self.assertIsNotNone(self.zarr_to_jpg.histogram_dict)
        self.assertIsNotNone(self.zarr_to_jpg.cumsum_dict)
        self.assertIsNotNone(self.zarr_to_jpg.percentile_dict)

    def test_normalization(self):
        """
            Check that the arcsinh stretch normalization has been initialized
        """
        self.assertIsNotNone(self.zarr_to_jpg.sdo_asinh_norms)

    def test_output(self):
        """'
            Check that the program is generating jpgs
        """
        self.assertTrue(os.path.exists(self.zarr_to_jpg.stack_outpath))
        self.zarr_to_jpg.save_jpgs()
        self.assertTrue(
            any(
                File.endswith(".jpg")
                for File in os.listdir(self.zarr_to_jpg.stack_outpath)
            )
        )
        files = glob.glob(f"{self.zarr_to_jpg.stack_outpath}/*.jpg")
        self.assertEqual(len(files), 10)





if __name__ == "__main__":
    unittest.main()

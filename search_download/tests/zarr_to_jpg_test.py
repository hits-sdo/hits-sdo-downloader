import unittest
import os
from search_download.zarr_to_jpg import ZarrToJpg


class ZarrToJpgTest(unittest.TestCase):
    """
    Test the Downloader class.
    """

    def setUp(self):
        aia_path = "/d0/euv/aia/preprocessed/aia_hmi_stacks_2010_2023_1d_full.zarr"
        stack_outpath = "/d0/euv/aia/preprocessed"
        wavelength_order = [211, 193, 171]
        debug = True
        self.zarr_to_jpg = ZarrToJpg(
            aia_path=aia_path,
            stack_outpath=stack_outpath,
            wavelength_order=wavelength_order,
            debug=debug,
        )

    def test_check_class(self):
        """ """
        self.assertIsNotNone(self.zarr_to_jpg)

    def test_data_exists(self):
        self.assertIsNotNone(self.zarr_to_jpg.data)

    def test_array_dimensions(self):
        self.assertEqual(len(self.zarr_to_jpg.data.aia_hmi.shape), 4)
        self.assertEqual(self.zarr_to_jpg.aia_slice.shape[1], 3)
        self.assertTrue(
            self.zarr_to_jpg.debug and self.zarr_to_jpg.aia_slice.shape[0] == 10
        )

    def test_output(self):
        self.assertTrue(os.path.exists(self.zarr_to_jpg.stack_outpath))
        self.zarr_to_jpg.save_jpg(0)
        self.assertTrue(
            any(
                File.endswith(".jpg")
                for File in os.listdir(self.zarr_to_jpg.stack_outpath)
            )
        )


if __name__ == "__main__":
    unittest.main()

import numpy as np

from gbtgridder import grid_otf


# test the parse_channels function in gbtgridder.py
# this function is called by gbtgridder() in gbtgridder.py
#  and inherits args from grid_otf.py
class TestParse_Channels:
    def test_2d(self):
        # the convolve will always be in 3d but we want to make sure
        #  everything is working correctly first
        grid_otf.conv_weights = np.array([[2, 1], [0, 3]])
        grid_otf.spec = np.array([[1, 1], [3, 2]])
        # find the result of the convolving function
        # this will take the 0th index [1][3]
        res = grid_otf.convolve(0)
        np.testing.assert_allclose(res, np.array([5, 9]))

    def test_3d(self):
        grid_otf.conv_weights = np.array([[2, 1], [0, 3]])
        grid_otf.spec = np.array([[[1, 1], [3, 2]], [[2, 1], [0, 3]]])
        # find result of 0th index [1,1][2,1]
        res1 = grid_otf.convolve(0)
        # find result of 1st index [3,2][0,3]
        res2 = grid_otf.convolve(1)
        np.testing.assert_allclose(res1, np.array([[4, 3], [6, 3]]))
        np.testing.assert_allclose(res2, np.array([[6, 7], [0, 9]]))

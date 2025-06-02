import numpy as np
import pytest

from gbtgridder.boxcar import boxcar


# test the parse_channels function in gbtgridder.py
# this function is called by gbtgridder() in gbtgridder.py
#  and inherits args from gbtgridder_args.py
class TestBoxcar:
    def test_normal_boxcar(self):
        # want to make sure pytest is working
        dataArray = np.random.random((20, 40))
        freqAxis = np.random.random((40,))
        width = 4
        data, freq = boxcar(dataArray, freqAxis, width)
        assert data.shape == (20, 9)
        assert freq.shape == (9,)

    def test_rounding_boxcar(self):
        # want to make sure pytest is working
        dataArray = np.random.random((20, 43))
        freqAxis = np.random.random((40,))
        width = 4
        data, freq = boxcar(dataArray, freqAxis, width)
        assert data.shape == (20, 10)
        assert freq.shape == (10,)

    def test_rounding2_boxcar(self):
        # want to make sure pytest is working
        dataArray = np.random.random((20, 39))
        freqAxis = np.random.random((40,))
        width = 4
        data, freq = boxcar(dataArray, freqAxis, width)
        assert data.shape == (20, 9)
        assert freq.shape == (9,)

    def test_shape_boxcar(self):
        # want to make sure pytest is working
        dataArray = np.random.random((20, 40, 20))
        freqAxis = np.random.random((40,))
        width = 4
        with pytest.raises(ValueError):
            boxcar(dataArray, freqAxis, width)

    def test_large_width_boxcar(self):
        # want to make sure pytest is working
        dataArray = np.random.random((20, 40))
        freqAxis = np.random.random((40,))
        width = 50
        with pytest.raises(ValueError):
            boxcar(dataArray, freqAxis, width)

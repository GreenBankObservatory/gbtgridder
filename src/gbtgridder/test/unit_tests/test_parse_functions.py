import pytest

from gbtgridder.gbtgridder import parse_channels, parse_scans


# test the parse_channels function in gbtgridder.py
# this function is called by gbtgridder() in gbtgridder.py
#  and inherits args from gbtgridder_args.py
class TestParse_Channels:
    def test_practice(self):
        # want to make sure pytest is working
        assert True

    def test_std_chan(self):
        # want to test using a normal range
        # return results with normal range and test results
        i, j = parse_channels("45:50")
        assert i == 44
        assert j == 49

    def test_invalid_multRange_chan(self):
        # want to test using 2 ranges, this is illegal
        # illegal values will return (-1,1) in parse_channels()
        i, j = parse_channels("45:50, 70:73")
        assert i == -1
        assert j == 1

    def test_invalid_doubleColon_chan(self):
        # want to test using >1 colon, this is illegal
        # illegal values will return (-1,1) in parse_channels()
        i, j = parse_channels("45::50")
        assert i == -1
        assert j == 1

    def test_invalid_nonInt_chan(self):
        # want to test using not using integers, this raises an exception
        # make sure that exception is raised
        with pytest.raises(ValueError):
            parse_scans("test:testing")

    def test_invalid_nonInt_chan(self):
        # want to test using not using integers, this raises an exception
        # make sure that exception is raised
        with pytest.raises(ValueError):
            parse_scans("4.5:5.0")


# test the parse_scans function in gbtgridder.py
# this function is called by gbtgridder() in gbtgridder.py
#  and inherits args from gbtgridder_args.py
class TestParse_Scans:
    def test_std_scans(self):
        # want to test using a normal range
        # return results with normal range and test results
        assert parse_scans("45:47") == [45, 46, 47]

    def test_std_mult_scans(self):
        # want to test using several normal ranges
        # return results with normal ranges and test results
        assert parse_scans("45:47,48,50:51") == [45, 46, 47, 48, 50, 51]

    def test_invalid_neg_scans(self):
        # test using an invalid negative number
        # this should return an empty list
        assert parse_scans("-4:3") == []

    def test_invalid_noColonComma_scans(self):
        # test using an invalid charachter (comma)
        # this should raise an error
        with pytest.raises(ValueError):
            parse_scans("45-50")

    def test_invalid_decreasing_scans(self):
        # test using an invalid range where item1<item2
        # this should raise an error
        with pytest.raises(ValueError):
            parse_scans("50:45")

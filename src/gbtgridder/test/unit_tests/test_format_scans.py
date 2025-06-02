from gbtgridder.gbtgridder import format_scans

# test the format_scan() function in gbtgridder.py
# this function accepts imput from parse_scans() in gbtgridder.py


class TestFormat_Scans:
    def test_std_fmtScans(self):
        # want to test a normal range
        assert format_scans([45, 46, 47, 48, 49, 50]) == "45:50"

    def test_gap_fmtScans(self):
        # test with several 'types' of ranges
        # all should be accepted by the function
        assert format_scans([45, 46, 47, 49, 51, 52]) == "45:47,49,51:52"

    def test_empty_fmtScans(self):
        # test if the parse_scans() function sends format_scans()
        #    an empty list
        assert format_scans([]) == None

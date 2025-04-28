import os
import sys
from os import path

from gbtgridder import gbtgridder, gbtgridder_args


# test the gbtgridder function in gbtgridder.py
# first - get args from gbtgridder_args.py
class TestArgs:
    def test_with_cygrid(self):
        # set the output name
        name = "test_with_cygrid"
        # Find the path to the test
        test_file_dir = os.path.dirname(os.path.abspath(__file__))
        # still need some required args
        # and want to filter out the line image
        # pass in the args
        sys.argv = [sys.argv[0]]
        assert len(sys.argv) == 1
        sys.argv.append(f"{test_file_dir}/cygx_sdfits.fits")
        sys.argv.append("-o")
        sys.argv.append(name)
        sys.argv.append("--clobber")
        sys.argv.append("--autoConfirm")
        # get the args
        args = gbtgridder_args.parser_args(sys.argv, "1.0")
        # check the args
        gbtgridder_args.check_args(args)

        # grid !
        try:
            gbtgridder.gbtgridder(args)
        except ValueError:
            print("There was a ValueError in test_with_cygrid")

        assert path.exists(name + "_cube.fits")
        assert path.exists(name + "_weight.fits")

        # cleanup for the next test
        sys.argv = [sys.argv[0]]
        os.remove(name + "_cube.fits")
        os.remove(name + "_weight.fits")

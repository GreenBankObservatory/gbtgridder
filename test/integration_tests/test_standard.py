import os
import sys
from os import path

from gbtgridder import gbtgridder, gbtgridder_args


# test the gbtgridder function in gbtgridder.py
# first - get args from gbtgridder_args.py
class TestArgs:
    def setup_method(self):
        # Path to the test directory.
        self.test_file_dir = os.path.dirname(os.path.abspath(__file__))

    def test_with_std_args(self):
        # set the output name
        name = "test_with_std_args"
        # pass in the args
        sys.argv.append(f"{self.test_file_dir}/test.fits")
        sys.argv.append("-o")
        sys.argv.append(name)
        sys.argv.append("--pixelwidth")
        sys.argv.append("182.0")
        sys.argv.append("--mapcenter")
        sys.argv.append("351")
        sys.argv.append("7")
        sys.argv.append("-a")
        sys.argv.append("4")
        sys.argv.append("--size")
        sys.argv.append("40")
        sys.argv.append("40")
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
            print("There was a ValueError in test_with_std_args")

        assert path.exists(name + "_cube.fits")
        assert path.exists(name + "_weight.fits")

        # cleanup for the next test
        sys.argv = [sys.argv[0]]
        os.remove(name + "_cube.fits")
        os.remove(name + "_weight.fits")

    def test_with_no_args(self):
        # set the output name
        name = "test_with_no_args"
        # still need some required args
        # pass in the args
        sys.argv = [sys.argv[0]]
        assert len(sys.argv) == 1
        sys.argv.append(f"{self.test_file_dir}/test.fits")
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
            print("There was a ValueError in test_with_no_args")

        assert path.exists(name + "_cube.fits")
        assert path.exists(name + "_weight.fits")

        # cleanup for the next test
        sys.argv = [sys.argv[0]]
        os.remove(name + "_cube.fits")
        os.remove(name + "_weight.fits")

    def test_with_normal(self):
        # set the output name
        name = "test_with_normal"
        # still need some required args
        # pass in the args
        sys.argv = [sys.argv[0]]
        assert len(sys.argv) == 1
        sys.argv.append(f"{self.test_file_dir}/normal.fits")
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
            print("There was a ValueError in test_with_normal")

        assert path.exists(name + "_cube.fits")
        assert path.exists(name + "_weight.fits")

        # cleanup for the next test
        sys.argv = [sys.argv[0]]
        os.remove(name + "_cube.fits")
        os.remove(name + "_weight.fits")

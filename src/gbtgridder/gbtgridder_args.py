# -*- coding: utf-8 -*-
"""Created on Mon Jun  7 14:01:17 2021.

@author: kpurc
"""
import argparse
import os
import sys


def check_args(args):
    if args.clonecube is not None and not os.path.exists(args.clonecube):
        print(args.clonecube + " does not exist")
        sys.exit(-1)

    if args.mapcenter is not None and (
        abs(args.mapcenter[0]) > 360.0 or abs(args.mapcenter[1]) > 90.0
    ):
        print(
            "mapcenter values are in degrees. |LONG| should be <= 360.0 and |LAT| <= 90.0"
        )
        sys.exit(-1)

    if args.size is not None and (args.size[0] <= 0 or args.size[1] <= 0):
        print("X and Y size values must be > 0")
        sys.exit(-1)

    if args.pixelwidth is not None and args.pixelwidth <= 0:
        print("pixelwidth must be > 0")
        sys.exit(-1)

    if args.restfreq is not None and args.restfreq <= 0:
        print("restfreq must be > 0")
        sys.exit(-1)

    if args.mintsys is not None and args.mintsys < 0:
        print("mintsys must be > 0")
        sys.exit(1)

    if args.maxtsys is not None and args.maxtsys < 0:
        print("maxtsys must be > 0")
        sys.exit(1)

    if (
        args.maxtsys is not None
        and args.mintsys is not None
        and args.maxtsys <= args.mintsys
    ):
        print("maxtsys must be > mintsys")
        sys.exit(1)


def parser_args(args, gbtgridderVersion):
    parser = argparse.ArgumentParser(
        epilog="gbtgridder version: %s" % gbtgridderVersion
    )
    parser.add_argument(
        "-c",
        "--channels",
        type=str,
        help="Optional channel range to use.  " "'<start>:<end>' counting from 0.",
    )
    parser.add_argument(
        "-a",
        "--average",
        type=int,
        help="Optionally average channels, keeping only number of channels/naverage channels",
    )
    parser.add_argument(
        "-s",
        "--scans",
        type=str,
        help="Only use data from these scans.  comma separated list or <start>:<end> range syntax or combination of both",
    )
    parser.add_argument("-m", "--maxtsys", type=float, help="max Tsys value to use")
    parser.add_argument("-z", "--mintsys", type=float, help="min Tsys value to use")
    parser.add_argument(
        "SDFITSfiles", type=str, nargs="+", help="The calibrated SDFITS files to use."
    )
    parser.add_argument(
        "--clobber",
        default=False,
        action="store_true",
        help="Overwrites existing output files if set.",
    )
    parser.add_argument(
        "-k",
        "--kernel",
        type=str,
        default="gauss",
        choices=["gauss", "gaussbessel", "nearest"],
        help="gridding kernel, default is gauss",
    )
    parser.add_argument(
        "--diameter",
        type=float,
        default=100,
        help="Diameter of the telescope the observations were taken on.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="root output name, instead of source and rest frequency",
    )
    parser.add_argument(
        "--mapcenter",
        metavar=("LONG", "LAT"),
        type=float,
        nargs=2,
        help="Map center in longitude and latitude of coordinate type used in data (RA/DEC, Galactic, etc) (degrees)",
    )
    parser.add_argument(
        "--size", metavar=("X", "Y"), type=int, nargs=2, help="Image X,Y size (pixels)"
    )
    parser.add_argument(
        "--pixelwidth", type=float, help="Image pixel width on sky (arcsec)"
    )
    parser.add_argument(
        "--beam_fwhm",
        type=float,
        help="Specify the BEAM_FWHM (HPBW) value, default calculated per telscope diameter in degrees",
    )
    parser.add_argument("--restfreq", type=float, help="Rest frequency (MHz)")
    parser.add_argument(
        "-p",
        "--proj",
        type=str,
        default="SFL",
        choices=["SFL", "TAN"],
        help="Projection to use for the spatial axes, default is SFL",
    )
    parser.add_argument(
        "--clonecube",
        type=str,
        help="A FITS cube to use to set the image size and WCS parameters"
        " in the spatial dimensions.  The cube must have the same axes "
        " produced here, the spatial axes must be of the same type as "
        " found in the data to be gridded, and the projection used in the"
        " cube must be either TAN, SFL, or GLS [which is equivalent to SFL]."
        " Default is to construct the output cube using values appropriate for"
        " gridding all of the input data.  Use of --clonecube overrides any use"
        " of --size, --pixelwidth, --mapcenter and --proj arguments.",
    )
    parser.add_argument(
        "--autoConfirm",
        default=False,
        action="store_true",
        help="Set this to True if you'd like to auto-confirm the program stop and move straight into gridding",
    )
    parser.add_argument(
        "--noweight",
        default=False,
        action="store_true",
        help="Set this to turn off production of the output weight cube",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        type=int,
        default=4,
        help="set the verbosity level-- 0-1:none, "
        "2:errors only, 3:+warnings, "
        "4(default):+user info, 5:+debug",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version="gbtgridder version: %s" % gbtgridderVersion,
    )

    args = parser.parse_args()

    return args

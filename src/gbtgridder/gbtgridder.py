# Copyright (C) 2015 Associated Universities, Inc. Washington DC, USA.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#
# Correspondence concerning GBT software should be addressed as follows:
#       GBT Operations
#       National Radio Astronomy Observatory
#       P. O. Box 2
#       Green Bank, WV 24944-0002 USA

import os
import sys  # using sys.argv
import time
import warnings

import numpy as np
from astropy import wcs
from astropy.io import fits as pyfits

from . import gbtgridder_args
from .get_data import get_data
from .grid_otf import grid_otf
from .make_header import make_header
from .get_cube_info import get_cube_info
from . import version

gbtgridderVersion = version()
_C = 299792458.0  # speed of light (m/s)


def parse_channels(channelString, verbose=4):
    """Turn a valid channel range into start and end channels."""
    start = None
    end = None
    if channelString is not None:
        print("channelString (%s)" % channelString)
        # there must be a ":"
        items = channelString.split(":")
        if len(items) != 2:
            if verbose > 1:
                print(
                    "Unexpected channels argument, must contain exactly one ':' - %s"
                    % channelString
                )
            return (-1, 1)
        if len(items[0]) > 0:
            try:
                # subtract by 1 to go from FITS convention to python
                start = int(items[0]) - 1
                # fixes for start < 0 happen when used
            except (ValueError):
                if verbose > 1:
                    print(repr(":".join(items[0])), "not convertable to integer")
                raise
        if len(items[1]) > 0:
            try:
                # subtract by 1 to go from FITS to python convention
                end = int(items[1]) - 1
            except (ValueError):
                if verbose > 1:
                    print(repr(":".join(items[1])), "not convertable to integer")
                raise
    return (start, end)


def parse_scans(scanlist):
    """Given a range string, produce a list of integers.

    Inclusive and exclusive integers are both possible.

    The range string 1:4,6:8,10 becomes 1,2,3,4,6,7,8,10
    The range string 1:4,-2 becomes 1,3,4

    Keywords:
       rangelist -- a range string with inclusive ranges and
                    exclusive integers

    Returns:
       a (list) of integers

    >>> cl = CommandLine()
    >>> cl._parse_range('1:4,6:8,10')
    [1, 2, 3, 4, 6, 7, 8, 10]
    >>> cl._parse_range('1:4,-2')
    [1, 3, 4]
    """
    # copied from _parse_range in gbtpipeline

    oklist = set([])
    excludelist = set([])

    scanlist = scanlist.replace(" ", "")
    scanlist = scanlist.split(",")

    # item is single value or range
    for item in scanlist:
        item = item.split(":")

        # change to ints
        try:
            int_item = [int(ii) for ii in item]
        except (ValueError):
            print(repr(":".join(item)), "not convertable to integer")
            raise

        if 1 == len(int_item):
            # single inclusive or exclusive item
            if int_item[0] < 0:
                excludelist.add(abs(int_item[0]))
            else:
                oklist.add(int_item[0])

        elif 2 == len(int_item):
            # range
            if int_item[0] <= int_item[1]:
                if int_item[0] < 0:
                    print(
                        item[0], ",", item[1], "must start with a non-negative number"
                    )
                    return []

                if int_item[0] == int_item[1]:
                    thisrange = [int_item[0]]
                else:
                    thisrange = range(int_item[0], int_item[1] + 1)

                for ii in thisrange:
                    oklist.add(ii)
            else:
                raise ValueError(f"{item[0]},{item[1]} needs to be in increasing")
        else:
            print(item, "has more than 2 values")

    for exitem in excludelist:
        try:
            oklist.remove(exitem)
        except (KeyError):
            oklist = [str(item) for item in oklist]
            print("ERROR: excluded item", exitem, "does not exist in inclusive range")
            raise

    return sorted(list(oklist))


def format_scans(scanlist):
    """Turn a list of scans into a string using range syntax where
    appropriate."""
    result = None
    rangeCount = 0
    lastScan = -1
    for scan in sorted(scanlist):
        if result is None:
            result = "%s" % scan
        else:
            if (scan - lastScan) == 1:
                # it's a range
                rangeCount += 1
            else:
                if rangeCount > 0:
                    # a previous range has ended
                    result += ":%s" % lastScan
                    rangeCount = 0
                # either way, this one is printed - new item
                result += ",%s" % scan
        lastScan = scan
    if rangeCount > 0:
        # a final range needs to be terminated
        result += ":%s" % lastScan
    return result


def set_output_files(source, rest_freq, args, file_types, verbose=4):

    outputNameRoot = args.output
    clobber = args.clobber

    if outputNameRoot is None:
        outputNameRoot = "%s_%.0f_MHz" % (source, rest_freq / 1.0e6)
    # always tack on the underscore
    outputNameRoot += "_"
    if verbose > 4:
        print("outname root : ", outputNameRoot)
        print("     clobber : ", clobber)
        sys.stdout.flush()

    result = {}
    for file_type in file_types:
        typeName = outputNameRoot + file_type + ".fits"
        if os.path.exists(typeName):
            if not clobber:
                if verbose > 1:
                    print(typeName + " exists, will not overwrite")
                return {}
            else:
                os.remove(typeName)
                if verbose > 3:
                    print("existing " + typeName + " removed")
        result[file_type] = typeName
    return result


def gbtgridder(args):
    """"""

    start_time = time.time()
    print("Collecting arguments and data... ")

    if not args.SDFITSfiles:
        print("no SDFITSfile")
        return

    verbose = args.verbose
    chanStart, chanStop = parse_channels(args.channels, verbose=verbose)
    if (chanStart is not None and chanStart < 0) or (
        chanStop is not None and chanStop < 0
    ):
        print("channels didn't parse")
        return

    if chanStart is None:
        chanStart = 0

    average = args.average

    minTsys = args.mintsys
    maxTsys = args.maxtsys

    scanlist = args.scans
    if args.scans is not None:
        scanlist = parse_scans(scanlist)

    sdfitsFiles = args.SDFITSfiles
    for sdf in sdfitsFiles:
        if not os.path.exists(sdf):
            if verbose > 1:
                print(sdf + " does not exist")
            return

    # extract everything from the SDFITS files
    xsky = None
    ysky = None
    spec = None
    rest_freq = None
    faxis = None
    source = None
    dataUnits = None
    calibType = None
    veldef = None
    specsys = None
    coordType = (None, None)
    radesys = None
    equinox = None
    observer = None
    telescop = None
    frontend = None
    dateObs = None
    uniqueScans = None
    ntsysFlagCount = 0
    outputFiles = {}

    if verbose > 3:
        print("Loading data ... ")
        sys.stdout.flush()

    num_positions = 0
    for thisFile in sdfitsFiles:
        try:
            if verbose > 3:
                print("   ", thisFile)
                sys.stdout.flush()
            dataRecord = get_data(
                thisFile,
                chanStart,
                chanStop,
                average,
                scanlist,
                minTsys,
                maxTsys,
                verbose=verbose,
            )

            if dataRecord is None:
                # there was a problem that should not be recovered from
                # reported by get_data, no additional reporting necessary here
                sys.exit(1)

            if len(dataRecord) == 0:
                # empty file, skipping
                continue

            num_positions += dataRecord["xsky"].size
            if xsky is None:
                chanStart = dataRecord["chanStart"]
                chanStop = dataRecord["chanStop"]
                wt_value = dataRecord["wt"]
                faxis = dataRecord["freq"]
                source = dataRecord["source"]
                dataUnits = dataRecord["units"]
                calibType = dataRecord["calibtype"]
                veldef = dataRecord["veldef"]
                specsys = dataRecord["specsys"]
                coordType = (dataRecord["xctype"], dataRecord["yctype"])
                radesys = dataRecord["radesys"]
                equinox = dataRecord["equinox"]
                telescop = dataRecord["telescop"]
                frontend = dataRecord["frontend"]
                observer = dataRecord["observer"]
                dateObs = dataRecord["date-obs"]
                uniqueScans = np.unique(dataRecord["scans"])
                spec_size = dataRecord["spec_size"]
                rest_freq = dataRecord["restfreq"]
                old_velocity_axis = (faxis - rest_freq) / rest_freq
                old_velocity_axis *= _C / 1000.0  # km/s
                if spec_size != old_velocity_axis.size:
                    raise ValueError("Spec axis mismatch in %s", thisFile)

                # this also checks that the output files are OK to write
                # given the value of the clobber argument
                outputFiles = set_output_files(
                    source,
                    rest_freq,
                    args,
                    ["cube", "weight"],
                    verbose=verbose,
                )
                if len(outputFiles) == 0:
                    if verbose > 1:
                        print("Unable to write to output files")
                    return

            else:
                wt_value = np.append(wt_value, dataRecord["wt"])
                uniqueScans = np.unique(np.append(uniqueScans, dataRecord["scans"]))

            ntsysFlagCount += dataRecord["ntsysflag"]

        except (AssertionError):
            if verbose > 1:
                print("There was an unexpected problem processing %s" % thisFile)
            raise

    # Loop over SDFITS files and get data and positions
    spec = np.ones((num_positions, spec_size), dtype=np.float64) * np.nan
    xsky = np.ones(num_positions, dtype=np.float32) * np.nan
    ysky = np.ones(num_positions, dtype=np.float32) * np.nan
    texp = np.ones(num_positions, dtype=np.float32) * np.nan
    tsys = np.ones(num_positions, dtype=np.float32) * np.nan
    idx = 0
    # run through the file again so we have the right num_positions value
    for thisFile in sdfitsFiles:
        try:
            dataRecord = get_data(
                thisFile,
                chanStart,
                chanStop,
                average,
                scanlist,
                minTsys,
                maxTsys,
                verbose=verbose,
            )

            if dataRecord is None:
                # this should be covered in the above dataRecord loop
                sys.exit(1)

            if len(dataRecord) == 0:
                # empty file, skipping
                continue

            try:
                num = dataRecord["xsky"].size
                tsys[idx : idx + num] = dataRecord["tsys"]
                texp[idx : idx + num] = dataRecord["texp"]
                spec[idx : idx + num] = dataRecord["data"]  # K
                xsky[idx : idx + num] = dataRecord["xsky"]  # deg
                ysky[idx : idx + num] = dataRecord["ysky"]  # deg
                idx += num
            except:
                print("There was an error getting data from the SDFits file")
                return

        except (AssertionError):
            if verbose > 1:
                print("There was an unexpected problem processing %s" % thisFile)
            raise

    if verbose > 3:
        print("Data Extracted Successfully.")

    if xsky is None:
        if verbose > 1:
            print(
                "No data was found in the input SDFITS files given the data selection options used."
            )
            print("Can not continue.")
        return

    # Setting weight so we don't have to pass
    # the system temperature and exposure time to grid_otf.
    if args.equalweight:
        weights = None
        wt_value = None
    else:
        weights = np.nan_to_num(texp/tsys**2)

    if args.restfreq is not None:
        # Use user supplied rest frequency, conver to Hz
        rest_freq = args.restfreq * 1.0e6

    # Get beam size (deg)
    _D = args.diameter
    if args.beam_fwhm:
        beam_fwhm = args.beam_fwhm
    else:
        avg_faxis = (faxis[0] + faxis[len(faxis) - 1]) / 2
        beam_fwhm = np.rad2deg(1.2 * _C / (_D * avg_faxis))

    # account for a xsky value that crossed the 0-360 axis
    if xsky.max() > 180:
        xsky_calc = np.array([i - 360 if i > 180 else i for i in xsky])
    else:
        xsky_calc = xsky

    pix_scale = None
    nx = None
    ny = None
    refXpix = None
    refYpix = None
    refXsky = None
    refYsky = None

    if pix_scale is None:
        if args.pixelwidth is not None:
            # use user-supplied value, convert to degrees
            pix_scale = args.pixelwidth / 3600.0
            if pix_scale > beam_fwhm / 2:
                raise ValueError(
                    f"Pixel scale is larger than FWHM/2={beam_fwhm / 2 * 3600 : .2f}"
                )
        else:
            # find the cell size, first from the beam_fwhm
            pixPerBeam = 3.0
            if args.kernel == "nearest":
                # assume it's nyquist sampled, use 2 pixels per beam
                pixPerBeam = 2.0

            pix_scale = beam_fwhm / pixPerBeam

    if args.kernel == "nearest" and pix_scale > beam_fwhm / 5:
        warnings.warn(
            f"Pixel scale is larger than FWHM/5={beam_fwhm / 5 * 3600 : .2f} using nearest kernel"
            "resulting cube might contain spurious data. Try using a smaller pixel scale."
        )


    # this is needed ONLY when the cube center and size are not given 
    # on the command line in one way or another
    centerUnknown = ((refXsky is None or refYsky is None) and args.mapcenter is None)
    sizeUnknown = (args.size is None)
    nonZeroXY = None
    if centerUnknown or sizeUnknown:
        # this masks out antenna positions exactly equal to 0.0 - unlikely to happen
        # except when there is no valid antenna pointing for that scan.
        nonZeroXY = (xsky!=0.0) & (ysky!=0.0)

        # watch for the pathological case where there is no good antenna data
        # which can not be gridded at all
        if np.all(nonZeroXY == False):
            # always print this out, independent of verbosity level
            print("All antenna pointings are exactly equal to 0.0, can not grid this data")
            return

        if verbose > 3 and np.any(nonZeroXY == False):
            print(f"{(nonZeroXY == False).sum()} spectra will be excluded because the antenna pointing is exactly equal to 0.0 on both axes - unlikely to be a valid position")


    # Generate image dimensions
    if args.size is None:  # number of x axis pixels
        xsky_size = np.nanmax(xsky_calc[nonZeroXY]) - np.nanmin(xsky_calc[nonZeroXY])
        ysky_size = np.nanmax(ysky[nonZeroXY]) - np.nanmin(ysky[nonZeroXY])
        nx = int(np.ceil(xsky_size / pix_scale)) + 1  # ceil takes next greater integer
        ny = (
            int(np.ceil(ysky_size / pix_scale)) + 1
        )  # no padding, only buffer by one pixel
    else:
        nx = args.size[0]
        ny = args.size[1]

    if args.clonecube is not None:
        # use the cloned values
        cubeInfo = get_cube_info(args.clonecube, verbose=verbose)
        if cubeInfo is not None:
            if (
                (cubeInfo["xtype"] != coordType[0])
                or (cubeInfo["ytype"] != coordType[1])
                or (cubeInfo["proj"] != args.proj)
                or (radesys is not None and cubeInfo["radesys"] is not None and (cubeInfo["radesys"] != radesys))
                or (equinox is not None and cubeInfo["equinox"] is not None and (cubeInfo["equinox"] != equinox))
            ):
                if verbose > 2:
                    print(
                        "Sky coordinates of data are not the same type found in %s"
                        % args.clonecube
                    )
                    print("Will not clone the coordinate information from that cube")
                    if verbose > 4:
                        print("xtype : ", cubeInfo["xtype"], coordType[0])
                        print("ytype : ", cubeInfo["ytype"], coordType[1])
                        print("proj : ", cubeInfo["proj"], args.proj)
                        print("radesys : ", cubeInfo["radesys"], radesys)
                        print("equinox : ", cubeInfo["equinox"], equinox)
            else:
                pix_scale = cubeInfo["pix_scale"]
                nx = cubeInfo["xsize"]
                ny = cubeInfo["ysize"]
                refXsky = cubeInfo["xref"]
                refYsky = cubeInfo["yref"]
                refXpix = cubeInfo["xrefPix"]
                refYpix = cubeInfo["yrefPix"]

    if refXsky is None:
        if args.mapcenter is not None:
            # use user-supplied value
            refXsky = args.mapcenter[0]
        else:
            # set the reference sky position using the mean x and y positions
            # still need to worry about points clearly off the grid
            #   e.g. a reference position incorrectly included in the data to be gridded.
            #   not sure what an appropriate heuristic for that is

            # idlToSdfits rounds the center from the mean to the nearest second/arcsecond
            # for RA or HA, divide by 15
            if coordType[0] in ['RA','HA']:
                refXsky = round(np.mean(xsky[nonZeroXY])*3600.0/15)/(3600.0/15.0)
            else:
                refXsky = round(np.mean(xsky[nonZeroXY])*3600.0)/3600.0

    if refYsky is None:
        if args.mapcenter is not None:
            # use user-supplied value
            refYsky = args.mapcenter[1]
        else:
            # nonZeroXY MUST have already been set above to get here
            # do not check that it's set or set it here
            # assume that the Y coordinate is +- 90 and there's no problem
            # with 360/0 or +- 180 confusion as there may be with the X coordinate
            refYsky = round(np.mean(ysky[nonZeroXY])*3600.0)/3600.0


    # Avoid using 0,0 as map center.
    # `cygrid` does not handle this case well.
    if refXsky == 0:
        refXsky += 1e-8
    if refYsky == 0:
        refYsky += 1e-8


    # Get convolution Gaussian FWHM (deg)
    if args.kernel == "gauss":
        gauss_fwhm = 2.0 * np.sqrt(np.log(2.0) / 9) * beam_fwhm
    elif args.kernel == "gaussbessel":
        gauss_fwhm = 2.0 * np.sqrt(np.log(2.0) / 9) * beam_fwhm
    else:
        gauss_fwhm = 0.0  # don't need this value for pill box

    # used only for header purposes
    centerYsky = refYsky
    if refXpix is None or refYpix is None:
        # both should be set together or unset together
        if args.proj == "TAN":
            # this is how Adam does things in his IDL code
            # the reference pixel is in the center
            refXpix = nx / 2.0
            refYpix = ny / 2.0
        else:
            # must be SFL
            # this is how idlToSdfits+AIPS does things for GLS==SFL
            refXpix = nx / 2.0
            # for the Y axis is, this is where we want refYsky to be
            centerYpix = ny / 2.0 + 1.0
            # but by definition, refYsky must be 0.0, set refYpix
            # so that the current refYsky ends up at centerYpix
            refYpix = centerYpix - refYsky / pix_scale
            # then reset refYsky
            refYsky = 0.0

    print("\n Please note that this gridding will be done using a monochromatic beam ie. using a single frequency (color) for the convolution kernel. \n")
    if verbose > 4:
        print("Data summary ...")
        print("   scans : ", format_scans(uniqueScans))
        print("   channels : %d:%d" % (chanStart, chanStop))
        if args.mintsys is None and args.maxtsys is None:
            print("   no tsys selection")
        else:
            tsysRange = ""
            if args.mintsys is not None:
                tsysRange += "%f" % args.mintsys
            tsysRange += ":"
            if args.maxtsys is not None:
                tsysRange += "%f" % args.maxtsys
            print("   tsys range : ", tsysRange)
            print("   flagged outside of tsys range : ", ntsysFlagCount)
        # number of spectra actually gridded if wt is being used
        if wt_value is not None:
            print("   spectra to grid : ", (wt_value != 0.0).sum())
        else:
            print("   spectra to grid : ", len(xsky))
            print("   using equal weights")

        print("\n Map info ...")
        print("   beam_fwhm : ", beam_fwhm, "(", beam_fwhm * 60.0 * 60.0, " arcsec)")
        print("   pix_scale : ", pix_scale, "(", pix_scale * 60.0 * 60.0, " arcsec)")
        print("  gauss fwhm : ", gauss_fwhm, "(", gauss_fwhm * 60.0 * 60.0, " arcsec)")
        print("    ref Xsky : ", refXsky, "(if negative then add 360)")
        print("    ref Ysky : ", refYsky)
        print(" center Ysky : ", centerYsky)
        print("       xsize : ", nx)
        print("       ysize : ", ny)
        print("    ref Xpix : ", refXpix)
        print("    ref Ypix : ", refYpix)
        print("          f0 : ", faxis[0])
        print("    delta(f) : ", faxis[1] - faxis[0])
        print("  num. chan  : ", len(faxis))
        print("      source : ", source)
        print(" frest (MHz) : ", rest_freq / 1.0e6)

    # converting diameter to telescope string for print out
    if args.diameter == 100:
        telescope = "GBT"
    elif args.diameter == 20:
        telescope = "20m"
    elif args.diameter == 43:
        telescope = "140ft"
    else:
        telescope = str(args.diameter) + "m"

    ## checking if the user wants to continue
    # giving the relevent info
    print(
        "\n\n Your parameters were either user specified or assumed to be the following. Please review: \n"
    )
    print_list = [
        ["Kernel", args.kernel],
        ["Telescope", telescope],
        ["Projection", args.proj],
        ["Input Chan.", str(chanStart) + ":" + str(chanStop)],
        ["# Output Chan.", spec_size],
        ["# of spec.", num_positions],
        ["Image size", str(nx) + "x" + str(ny)],
        ["Beam_FWHM", beam_fwhm]
    ]
    print("{:<13} {:<2}".format("Name", "Value"))
    print("{:<13} {:<2}".format("--------", "---------"))
    for v in print_list:
        name, value = v
        print("{:<13} {:<2}".format(name, value))

    # getting their answer
    if not args.autoConfirm:
        answer = input(
            "\n If you need more info, type 'N' and run again with `--verbose 4` flag \n\n Would you like to continue with these parameters? \n 'Y' for yes, 'N' for no.  \n"
        )
        while (
            True
        ):  # only need to start a while loop, if 'yes' it will break out of while loop, if 'no' it will break out of the class
            if answer in ["Y", "y", "yes", "Yes"]:
                break
            elif answer in ["N", "n", "no", "No"]:
                print("Goodbye.")
                if verbose > 4:
                    end_time = time.time()
                    print(
                        "Runtime: {0:.1f} minutes".format(
                            (end_time - start_time) / 60.0
                        )
                    )
                return
            else:
                answer = input(
                    "Selection not recognized. Try again. Y for yes, N for no. \n"
                )

    # build the initial header object
    hdr = make_header(
        refXsky,
        refYsky,
        nx,
        ny,
        pix_scale,
        refXpix,
        refYpix,
        coordType,
        radesys,
        equinox,
        rest_freq,
        faxis,
        beam_fwhm,
        veldef,
        specsys,
        proj=args.proj,
        verbose=verbose,
    )

    wcsObj = wcs.WCS(hdr, relax=True)

    if verbose > 3:
        print("\n\n Gridding")
        sys.stdout.flush()

    try:  # pass all the info to the grid_otf function
        (cube, weight, final_fwhm) = grid_otf(
            spec,
            nx,
            ny,
            xsky,
            ysky,
            wcsObj,
            pix_scale,
            refXsky,
            centerYsky,
            beam_fwhm=beam_fwhm,
            weights=weights,
            kernel_type=args.kernel,
            gauss_fwhm=gauss_fwhm,
            verbose=verbose,
        )
    except MemoryError:
        if verbose > 1:
            print(
                "Not enough memory to create the image cubes necessary to grid this data"
            )
            print("   Requested image size : %d x %d x %d " % (nx, ny, len(faxis)))
            print(
                "   find a beefier machine, consider restricting the data to fewer channels or using channel averaging"
            )
            print("   or use AIPS (with idlToSdfits) to grid all of this data")
        return

    if cube is None or weight is None:
        if verbose > 1:
            print("Problem gridding data")
        return

    if verbose > 3:
        print("Writing cube")

    # start writing stuff to disk
    # add additional information to the header
    hdr["object"] = source
    hdr["telescop"] = telescop
    hdr["instrume"] = frontend
    hdr["observer"] = observer
    hdr["date-obs"] = (dateObs, "Observed time of first spectra gridded")
    hdr["date-map"] = (
        time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
        "Created by gbtgridder",
    )
    hdr["date"] = time.strftime("%Y-%m-%d", time.gmtime())
    hdr["obsra"] = refXsky
    hdr["obsdec"] = centerYsky
    hdr["beamFWHM"] = (beam_fwhm, "Main beamFWHM at centralFreq or user value")

    if args.kernel == "gauss":
        hdr.add_comment("Convolved with Gaussian convolution function.")
        hdr["BMAJ"] = (final_fwhm, "Beam FWHM of gridded cube at the central freq")
        hdr["BMIN"] = (final_fwhm, "Beam FWHM of gridded cube at the central freq")
    elif args.kernel == "gaussbessel":
        hdr.add_comment(
            "Convolved with optimized Gaussian-Bessel convolution function."
        )
        hdr["BMAJ"] = (final_fwhm, "*But* not Gaussian. Beam FWHM of gridded cube at the central freq")
        hdr["BMIN"] = (final_fwhm, "*But* not Gaussian. Beam FWHM of gridded cube at the central freq")
    else:
        hdr.add_comment("Gridded to nearest cell")
        hdr["BMAJ"] = (final_fwhm, "Beam FWHM of gridded cube at the central freq")
        hdr["BMIN"] = (final_fwhm, "Beam FWHM of gridded cube at the central freq")
    hdr["BPA"] = 0.0

    if dataUnits == "Jy":
        dataUnits = "Jy/Beam"
    hdr["BUNIT"] = (dataUnits, calibType)

    # This suppresses runtime NaN warnings if the cube is empty
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        hdr["DATAMAX"] = np.nanmax(cube)

    if np.isnan(hdr["DATAMAX"]):
        if verbose > 2:
            print(
                "Entire data cube is not-a-number, this may be because a few channels are consistently bad"
            )
            print("consider restricting the channel range")
        # remove it
        hdr.remove("DATAMAX")
    else:
        hdr["DATAMIN"] = np.nanmin(cube)

    # note the parameter values - this must be updated as new parameters are added
    hdr.add_history("gbtgridder version: %s" % gbtgridderVersion)
    if args.channels is not None:
        hdr.add_history("gbtgridder channels: " + args.channels)
    else:
        hdr.add_history("gbtgridder all channels used")
    hdr.add_history("gbtgridder clobber: " + str(args.clobber))
    if average is not None and average > 1:
        hdr.add_history("gbtgridder average: %s channels" % average)
    hdr.add_history("gbtgridder kernel: " + args.kernel)
    if args.output is not None:
        hdr.add_history("gbtgridder output: " + args.output)
    if args.scans is not None:
        hdr.add_history("gbtgridder scans: " + args.scans)
    if args.mintsys is None and args.maxtsys is None:
        hdr.add_history("gbtgridder no tsys selection")
    else:
        if args.mintsys is not None:
            hdr.add_history("gbtgridder mintsys: %f" % args.mintsys)
        if args.maxtsys is not None:
            hdr.add_history("gbtgridder maxtsys: %f" % args.maxtsys)
        hdr.add_history("gbtgridder N spectra outside tsys range: %d" % ntsysFlagCount)

    hdr.add_history("gbtgridder sdfits files ...")
    for thisFile in args.SDFITSfiles:
        # protect against long file names
        if len(thisFile) > 60:
            thisFile = "*" + thisFile[-59:]
        hdr.add_history("gbtgridder: " + thisFile)

    hdr.add_comment("IEEE not-a-number used for blanked pixels.")
    hdr.add_comment(
        "  FITS (Flexible Image Transport System) format is defined in 'Astronomy"
    )
    hdr.add_comment(
        "  and Astrophysics', volume 376, page 359; bibcode: 2001A&A...376..359H"
    )

    # adding STOKES axis
    # phdu = pyfits.PrimaryHDU(cube[..., None].T, header=hdr)
    phdu = pyfits.PrimaryHDU(cube[None, ...], header=hdr)
    phdu.writeto(outputFiles["cube"])

    if not args.noweight:
        if verbose > 3:
            print("Writing weight cube")
        wtHdr = hdr.copy()
        wtHdr["BUNIT"] = ("weight", "Weight cube")  # change from K -> weight
        wtHdr["DATAMAX"] = np.nanmax(weight)
        wtHdr["DATAMIN"] = np.nanmin(weight)

        # adding STOKES axis
        phdu = pyfits.PrimaryHDU(weight[None, ...], header=wtHdr)
        phdu.writeto(outputFiles["weight"])

    end_time = time.time()
    if verbose > 3:
        print("Runtime: {0:.1f} minutes".format((end_time - start_time) / 60.0))

    return


def main():
    if len(sys.argv) == 1:
        sys.argv.append("-h")

    args = gbtgridder_args.parser_args(sys.argv, gbtgridderVersion)

    # argument checking
    gbtgridder_args.check_args(args)

    gbtgridder(args)


if __name__ == "__main__":
    main()

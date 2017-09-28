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

from make_header import make_header
from grid_otf import grid_otf
from get_data import get_data
from get_cube_info import get_cube_info

from astropy import wcs
from astropy.io import fits as pyfits
import os
import sys
import argparse
import numpy
from scipy import constants
import math
import time
import warnings

gbtgridderVersion = "0.5"

def read_command_line(argv):
    """Read options from the command line."""
    # if no options are set, print help      
    if len(argv) == 1:                       
        argv.append("-h")                    

    parser = argparse.ArgumentParser(epilog="gbtgridder version: %s" % gbtgridderVersion)
    parser.add_argument("-c","--channels", type=str,
                        help="Optional channel range to use.  "
                             "'<start>:<end>' counting from 0.")
    parser.add_argument("-a","--average", type=int,
                        help="Optionally average channels, keeping only nchan/naverage channels")
    parser.add_argument("-s","--scans", type=str, 
                        help="Only use data from these scans.  comma separated list or <start>:<end> range syntax or combination of both")
    parser.add_argument("-m","--maxtsys", type=float,
                        help="max Tsys value to use")
    parser.add_argument("-z","--mintsys", type=float,
                        help="min Tsys value to use")
    parser.add_argument("SDFITSfiles", type=str, nargs="+",
                        help="The calibrated SDFITS files to use.") 
    parser.add_argument("--clobber", default=False, action="store_true",
                        help="Overwrites existing output files if set.")
    parser.add_argument("-k","--kernel", type=str, default="gauss", choices=["gauss","gaussbessel","nearest"],
                        help="gridding kernel, default is gauss")
    parser.add_argument("-o","--output", type=str,
                        help="root output name, instead of source and rest frequency")
    parser.add_argument('--mapcenter', metavar=('LONG','LAT'), type=float, nargs=2,
                        help="Map center in longitude and latitude of coordinate type used in data (RA/DEC, Galactic, etc) (degrees)")
    parser.add_argument('--size', metavar=('X','Y'), type=int, nargs=2,
                        help="Image X,Y size (pixels)")
    parser.add_argument('--pixelwidth', type=float, help="Image pixel width on sky (arcsec)")
    parser.add_argument('--restfreq', type=float, help="Rest frequency (MHz)")
    parser.add_argument("-p","--proj", type=str, default="SFL", choices=["SFL","TAN"],
                        help="Projection to use for the spatial axes, default is SFL")
    parser.add_argument("--clonecube",type=str,
                        help="A FITS cube to use to set the image size and WCS parameters"
                        " in the spatial dimensions.  The cube must have the same axes "
                        " produced here, the spatial axes must be of the same type as "
                        " found in the data to be gridded, and the projection used in the"
                        " cube must be either TAN, SFL, or GLS [which is equivalent to SFL]."
                        " Default is to construct the output cube using values appropriate for"
                        " gridding all of the input data.  Use of --clonecube overrides any use"
                        " of --size, --pixelwidth, --mapcenter and --proj arguments.")
    parser.add_argument("--eqweight",default=False, action="store_true",
                        help="Set this to use equal data weights for all spectra") 
    parser.add_argument("--noweight", default=False, action="store_true",
                        help="Set this to turn off production of the output weight cube")
    parser.add_argument("--noline", default=False, action="store_true",
                        help="Set this to turn off prodution of the output line cube")
    parser.add_argument("--nocont", default=False, action="store_true",
                        help="Set this to turn off prodution of the output 'cont' image")
    parser.add_argument("-v","--verbose", type=int, default=4,
                        help="set the verbosity level-- 0-1:none, "
                        "2:errors only, 3:+warnings, "
                        "4(default):+user info, 5:+debug")
    parser.add_argument("-V","--version", action="version", version="gbtgridder version: %s" % gbtgridderVersion)

    args = parser.parse_args()

    return args

def parse_channels(channelString,verbose=4):
    "Turn a valid channel range into start and end channels"
    start = None
    end = None
    if channelString is not None:
        print "channelString (%s)" % channelString
        # there must be a ":"
        items = channelString.split(":")
        if len(items) != 2:
            if verbose > 1:
                print "Unexpected channels argument, must contain exactly one ':' - %s" % channelString
            return (-1,1)
        if len(items[0]) > 0:
            try:
                # subtract by 1 to go from FITS convention to python
                start = int(items[0])-1
                # fixes for start < 0 happen when used
            except(ValueError):
                if verbose > 1:
                    print repr(':'.join(items[0])), 'not convertable to integer'
                raise
        if len(items[1]) > 0:
            try:
                # subtract by 1 to go from FITS to python convention
                end = int(items[1])-1
            except(ValueError):
                if verbose > 1:
                    print repr(':'.join(items[1])), 'not convertable to integer'
                raise
    return (start,end)

def parse_scans(scanlist):
    """Given a range string, produce a list of integers

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

    scanlist = scanlist.replace(' ', '')
    scanlist = scanlist.split(',')

    # item is single value or range
    for item in scanlist:
        item = item.split(':')

        # change to ints
        try:
            int_item = [int(ii) for ii in item]
        except(ValueError):
            print repr(':'.join(item)), 'not convertable to integer'
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
                    print item[0], ',', item[1], 'must start with a '
                    'non-negative number'
                    return []

                if int_item[0] == int_item[1]:
                    thisrange = [int_item[0]]
                else:
                    thisrange = range(int_item[0], int_item[1]+1)

                for ii in thisrange:
                    oklist.add(ii)
            else:
                print item[0], ',', item[1], 'needs to be in increasing '
                'order'
                raise
        else:
            print item, 'has more than 2 values'

    for exitem in excludelist:
        try:
            oklist.remove(exitem)
        except(KeyError):
            oklist = [str(item) for item in oklist]
            print 'ERROR: excluded item', exitem, 'does not exist in '
            'inclusive range'
            raise

    return sorted(list(oklist))

def format_scans(scanlist):
    "Turn a list of scans into a string using range syntax where appropriate"
    result = None
    rangeCount = 0
    lastScan = -1
    for scan in sorted(scanlist):
        if result is None:
            result = "%s" % scan
        else:
            if (scan-lastScan) == 1:
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

def set_output_files(source, frest, args, file_types, verbose=4):

    outputNameRoot = args.output
    clobber = args.clobber

    if outputNameRoot is None:
        outputNameRoot = "%s_%.0f_MHz" % (source,frest/1.e6)
    # always tack on the underscore
    outputNameRoot += "_"
    if verbose > 4:
        print "outname root : ", outputNameRoot
        print "     clobber : ", clobber
    
    result = {}
    for file_type in file_types:
        typeName = outputNameRoot + file_type + ".fits"
        if os.path.exists(typeName):
            if not clobber:
                if verbose > 1:
                    print typeName + " exists, will not overwrite"
                return {}
            else:
                os.remove(typeName)
                if verbose > 3:
                    print "existing " + typeName + " removed"
        result[file_type] = typeName
    return result

def gbtgridder(args):
    if not args.SDFITSfiles:
        return

    verbose = args.verbose
    chanStart, chanStop = parse_channels(args.channels,verbose=verbose)
    if (chanStart is not None and chanStart < 0) or (chanStop is not None and chanStop < 0):
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
                print sdf + ' does not exist'
            return

    # extract everything from the SDFITS files
    # this needs in the long run so that only one SDFITS file is opened at a time
    # and a reasonable amount of data are read and then gridded - repeat until done
    # right now, all of the data must be read first, then passed in one call
    # to the gridder.  In that case, there will be 2 passes through the SDFITS files
    # since the full extent of the data on the sky must be known before gridding can start.

    xsky = None
    ysky = None
    wt = None
    data = None
    nchan = None
    frest = None
    faxis = None
    source = None
    dataUnits = None
    calibType = None
    veldef = None
    specsys = None
    coordType = (None,None)
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
        print "Loading data ... "
    for thisFile in sdfitsFiles:
        try:
            if verbose > 3:
                print "   ",thisFile
            dataRecord = get_data(thisFile,nchan,chanStart,chanStop,average,scanlist,
                                  minTsys,maxTsys,verbose=verbose)
            if dataRecord is None:
                # there was a problem that should not be recovered from
                # reported by get_data, no additional reporting necessary here
                sys.exit(1)

            if len(dataRecord) == 0:
                # empty file, skipping
                continue

            if xsky is None:
                xsky = dataRecord["xsky"]
                ysky = dataRecord["ysky"]
                wt = dataRecord["wt"]
                data = dataRecord["data"]
                nchan = dataRecord["nchan"]
                chanStart = dataRecord["chanStart"]
                chanStop = dataRecord["chanStop"]
                frest = dataRecord["restfreq"]
                faxis = dataRecord["freq"]
                source = dataRecord["source"]
                dataUnits = dataRecord["units"]
                calibType = dataRecord["calibtype"]
                veldef = dataRecord["veldef"]
                specsys = dataRecord["specsys"]
                coordType = (dataRecord["xctype"],dataRecord["yctype"])
                radesys = dataRecord["radesys"]
                equinox = dataRecord["equinox"]
                telescop = dataRecord["telescop"]
                frontend = dataRecord["frontend"]
                observer = dataRecord["observer"]
                dateObs = dataRecord["date-obs"]
                uniqueScans = numpy.unique(dataRecord["scans"])

                # this also checks that the output files are OK to write
                # given the value of the clobber argument
                outputFiles = set_output_files(source, frest, args, ["cube","weight","line","cont"],
                                               verbose=verbose)
                if len(outputFiles) == 0:
                    if verbose > 1:
                        print "Unable to write to output files"
                    return
                
            else:
                xsky = numpy.append(xsky,dataRecord["xsky"])
                ysky = numpy.append(ysky,dataRecord["ysky"])
                wt = numpy.append(wt,dataRecord["wt"])
                data = numpy.append(data,dataRecord["data"],axis=0)
                uniqueScans = numpy.unique(numpy.append(uniqueScans,dataRecord["scans"]))

            ntsysFlagCount += dataRecord["ntsysflag"]

        except(AssertionError):
            if verbose > 1:
                print "There was an unexpected problem processing %s" % thisFile
            raise

    if xsky is None:
        if verbose > 1:
            print "No data was found in the input SDFITS files given the data selection options used."
            print "Can not continue."
        return

    if args.restfreq is not None:
        # Use user supplied rest frequency, conver to Hz
        frest = args.restfreq * 1.0e6

    # grid_otf.py already sets the weights to 1 if wt=None
    # Added a flag here called --eqweight 
    # print args.eqweight
    if args.eqweight is True: 
        #if verbose > 1:
        #    print "Setting all weights to 1."
        wt = None

    # characterize the center of the image

    # the beam_fwhm is needed in various places
    # currently we use the same equation used in idlToSdfits
    # there's about a 2% difference between the two

    # this equation comes from Adam's IDL code, where do the 747.6 and 763.8 values come from?
    # beam_fwhm = (747.6+763.8)/2.0/numpy.median(faxis/1.e9)/3600.
    # This is what idlToSdfits does (next 2 lines of code)
    # telescop diameter, in meters
    diam = 100.0
    beam_fwhm = 1.2 * constants.c * (180.0/constants.pi) / (diam * numpy.median(faxis))
    # the 747.6 and 763.8 values above are equivalent to diam of 99.3 and 97.2 m in this equation, respectively

    refXsky = None
    refYsky = None
    centerYsky = None
    pix_scale = None
    xsize = None
    ysize = None
    refXpix = None
    refYpix = None

    if args.clonecube is not None:
        # use the cloned values
        cubeInfo = get_cube_info(args.clonecube,verbose=verbose)
        if cubeInfo is not None:
            if (cubeInfo["xtype"] != coordType[0]) or \
                    (cubeInfo["ytype"] != coordType[1]) or \
                    (cubeInfo['proj'] != args.proj) or \
                    (radesys is not None and (cubeInfo['radesys'] != radesys)) or \
                    (equinox is not None and (cubeInfo['equinox'] != equinox)):
                if verbose > 2:
                    print "Sky coordinates of data are not the same type found in %s" % args.clonecube
                    print "Will not clone the coordinate information from that cube"
                    if verbose > 4:
                        print "xtype : ", cubeInfo["xtype"], coordType[0]
                        print "ytype : ", cubeInfo["ytype"], coordType[1]
                        print "proj : ", cubeInfo['proj'], args.proj
                        print "radesys : ", cubeInfo['radesys'], radesys
                        print "equinox : ", cubeInfo['equinox'], equinox
            else:
                refXsky = cubeInfo["xref"]
                refYsky = cubeInfo["yref"]
                pix_scale = cubeInfo["pix_scale"]
                xsize = cubeInfo["xsize"]
                ysize = cubeInfo["ysize"]
                refXpix = cubeInfo["xrefPix"]
                refYpix = cubeInfo["yrefPix"]


    # this is needed ONLY when the cube center and size are not given 
    # on the command line in one way or another
    centerUnknown = ((refXsky is None or refYsky is None) and args.mapcenter is None)
    sizeUnknown = ((xsize is None or ysize is None) and args.size is None)
    nonZeroXY = None
    if centerUnknown or sizeUnknown:
        # this masks out antenna positions exactly equal to 0.0 - unlikely to happen
        # except when there is no valid antenna pointing for that scan.
        nonZeroXY = (xsky!=0.0) & (ysky!=0.0)

        # watch for the pathological case where there is no good antenna data
        # which can not be gridded at all
        if numpy.all(nonZeroXY == False):
            # always print this out, independent of verbosity level
            print "All antenna pointings are exactly equal to 0.0, can not grid this data"
            return

        if verbose > 3 and numpy.any(nonZeroXY == False):
            print "%d spectra will be excluded because the antenna pointing is exactly equal to 0.0 on both axes - unlikely to be a valid position" % (nonZeroXY == False).sum()

    # need to watch for coordinates near 0/360  OR near +- 180
    # this technique will miss the difficult case of a mixture of +- 180 and 0:360 X coordinates
    # assumes that Y doesn't have this problem, likely is +- 90
    xskyMin = xsky[nonZeroXY].min()
    xskyMax = xsky[nonZeroXY].max()
    newXsky = None

    if (xskyMin > 0.0) :
        # all coordinates > 0, watch for 0/360 coordinates
        if (xskyMax - xskyMin) > 180.0:
            # probably a problem, subtract 360 for coordinates > 180.0 so that they run from -180 to +180 continuously through 0.0
            rangeBefore = xskyMax - xskyMin
            xskyMask = xsky>180.0
            newXsky = xsky.copy()
            newXsky[xskyMask] -= 360.0
    else:
        # some coordinates are < 0, watch for +- 180.0
        # same criteria
        if (xskyMax - xskyMin) > 180.0:
            # probably a problem, add 360 to all negative coordinates so they run from 0 through 360
            rangeBefore = xskyMax - xskyMin
            xskyMask = xsky<0.0
            newXsky = xsky.copy()
            newXsky[xskyMask] += 360.0

    if newXsky is not None:
        # see if that's an improvemenet
        newXskyMin = newXsky[nonZeroXY].min()
        newXskyMax = newXsky[nonZeroXY].max()
        if (newXskyMax-newXskyMin) < rangeBefore:
            # this is an improvement, use it
            xsky = newXsky.copy()
            xskyMin = newXskyMin
            xskyMax = newXskyMax

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
                refXsky = round(numpy.mean(xsky[nonZeroXY])*3600.0/15)/(3600.0/15.0)
            else:
                refXsky = round(numpy.mean(xsky[nonZeroXY])*3600.0)/3600.0

    if refYsky is None:
        if args.mapcenter is not None:
            # use user-supplied value
            refYsky = args.mapcenter[1]
        else:
            # nonZeroXY MUST have already been set above to get here
            # do not check that it's set or set it here
            # assume that the Y coordinate is +- 90 and there's no problem
            # with 360/0 or +- 180 confusion as there may be with the X coordinate
            refYsky = round(numpy.mean(ysky[nonZeroXY])*3600.0)/3600.0

    if pix_scale is None:
        if args.pixelwidth is not None:
            # use user-supplied value, convert to degrees
            pix_scale = args.pixelwidth / 3600.0
        else:
            # find the cell size, first from the beam_fwhm
            # Need to decide on number of cell's per beam.  Adam`'s code uses 4, idlToSdfits uses 6
            # idlToSdfits also rounds up to nearest arcsecond
            pixPerBeam = 6.0
            if args.kernel == "nearest":
                # assume it's nyquist sampled, use 2 pixels per beam
                pixPerBeam = 2.0

            pix_scale = math.ceil(3600.0*beam_fwhm/pixPerBeam)/3600.0

    if xsize is None or ysize is None:
        # set both together
        if args.size is not None:
            # use user-supplied value
            xsize = args.size[0]
            ysize = args.size[1]
        else:
            xRange = xskyMax-xskyMin
            yRange = ysky[nonZeroXY].max()-ysky[nonZeroXY].min()

            # image size, idlToSdfits method
            # padding around border
            # imPadding = math.ceil(45./(pix_scale*3600.0))
            # add in padding and truncate to an integer
            # xsize = int((xRange*1.1/pix_scale)+2*imPadding)
            # ysize = int((yRange*1.1/pix_scale)+2*imPadding)
            # image.py then does this ... 
            # xsize = int((2*round(xsize/1.95)) + 20)
            # ysize = int((2*round(ysize/1.95)) + 20)
            # But idlToSdfits only sees one SDFITS file at a time, so the extra padding makes sense there.
            # With all the data, I think just padding by 10% + 20 pixels is sufficient
            xsize = int(math.ceil(xRange*1.1/pix_scale))+20
            ysize = int(math.ceil(yRange*1.2/pix_scale))+20

    # used only for informational purposes
    centerYsky = refYsky
    if refXpix is None or refYpix is None:
        # both should be set together or unset together
        if args.proj == "TAN":
            # this is how Adam does things in his IDL code
            # the reference pixel is in the center
            refXpix = xsize/2.0
            refYpix = ysize/2.0
        else:
            # must be SFL
            # this is how idlToSdfits+AIPS does things for GLS==SFL
            refXpix = xsize/2.0
            # for the Y axis is, this is where we want refYsky to be
            centerYpix = ysize/2.0 + 1.0
            # but by definition, refYsky must be 0.0, set set refYpix
            # so that the current refYsky ends up at centerYpix
            refYpix = centerYpix - refYsky/pix_scale
            # then reset refYsky
            refYsky = 0.0
            
    # gaussian size to use in gridding.
    # this is what Adam used:  gauss_fwhm = beam_fwhm/3.0
    # this duplicates the aparm(2)=1.5*cellsize used by AIPS in the default pipeline settings
    # the following is about 0.41*beam_fwhm vs 0.33*beam_fwhm from Adam - so wider
    gauss_fwhm = (1.5*pix_scale)*2.354/math.sqrt(2.0)

    if verbose > 4:
        print "Data summary ..."
        print "   scans : ", format_scans(uniqueScans)
        print "   channels : %d:%d" % (chanStart, chanStop)
        if args.mintsys is None and args.maxtsys is None:
            print "   no tsys selection"
        else:
            tsysRange = ""
            if args.mintsys is not None:
                tsysRange += "%f" % args.mintsys
            tsysRange += ":"
            if args.maxtsys is not None:
                tsysRange += "%f" % args.maxtsys
            print "   tsys range : ", tsysRange
            print "   flagged outside of tsys range : ", ntsysFlagCount
        # number of spectra actually gridded if wt is being used
        if wt is not None:
            print "   spectra to grid : ", (wt != 0.0).sum()
        else:
            print "   spectra to grid : ", len(xsky)
            print "   using equal weights"

        print ""
        print "Map info ..."
        print "   beam_fwhm : ", beam_fwhm, "(", beam_fwhm*60.0*60.0, " arcsec)"
        print "   pix_scale : ", pix_scale, "(", pix_scale*60.0*60.0, " arcsec)"
        print "  gauss fwhm : ", gauss_fwhm, "(", gauss_fwhm*60.0*60.0, " arcsec)"
        print "    ref Xsky : ", refXsky
        print "    ref Ysky : ", refYsky
        print " center Ysky : ", centerYsky
        print "       xsize : ", xsize
        print "       ysize : ", ysize
        print "    ref Xpix : ", refXpix
        print "    ref Ypix : ", refYpix
        print "          f0 : ", faxis[0]
        print "    delta(f) : ", faxis[1]-faxis[0]
        print "      nchan  : ", len(faxis)
        print "      source : ", source
        print " frest (MHz) : ", frest/1.e6

    # build the initial header object
    # only enough to build the WCS object from it + BEAM size info
    # I had trouble with embedded HISTORY cards and the WCS constructor
    # so those are omitted for now
    hdr = make_header(refXsky, refYsky, xsize, ysize, pix_scale, refXpix, refYpix, coordType, radesys, equinox, frest, faxis, beam_fwhm, veldef, specsys, proj=args.proj, verbose=verbose)

    # relax is turned on here for compatibility with previous images produced by AIPS from the gbtpipeline
    # there may be a better solution
    # even so, it does not like the "-LSR" tag to the CTYPE3 value for the frequency axis
    wcsObj = wcs.WCS(hdr,relax=True)

    if verbose > 3:
        print "Gridding"

    try:
        (cube, weight, beam_fwhm) = grid_otf(data, xsky, ysky, wcsObj, len(faxis), xsize, ysize, pix_scale, weight=wt, beam_fwhm=beam_fwhm, kern=args.kernel, gauss_fwhm=gauss_fwhm, verbose=verbose)
    except MemoryError:
        if verbose > 1:
            print "Not enough memory to create the image cubes necessary to grid this data"
            print "   Requested image size : %d x %d x %d " % (xsize, ysize, len(faxis))
            print "   find a beefier machine, consider restricting the data to fewer channels or using channel averaging"
            print "   or use AIPS (with idlToSdfits) to grid all of this data"
        return

    if cube is None or weight is None:
        if verbose > 1:
            print "Problem gridding data"
        return

    if verbose > 3:
        print "Writing cube"

    # Add in the degenerate STOKES axis
    cube.shape = (1,)+cube.shape
    weight.shape = cube.shape    

    # start writing stuff to disk
    # add additional information to the header
    hdr['object'] = source
    hdr['telescop'] = telescop
    hdr['instrume'] = frontend
    hdr['observer'] = observer
    hdr['date-obs'] = (dateObs,'Observed time of first spectra gridded')
    hdr['date-map'] = (time.strftime("%Y-%m-%dT%H:%M:%S",time.gmtime()),"Created by gbtgridder")
    hdr['date'] = time.strftime("%Y-%m-%d",time.gmtime())
    hdr['obsra'] = refXsky
    hdr['obsdec'] = centerYsky

    if args.kernel == 'gauss':
        hdr.add_comment('Convolved with Gaussian convolution function.')
        hdr['BMAJ'] = beam_fwhm
        hdr['BMIN'] = beam_fwhm
    elif args.kernel == 'gaussbessel':
        hdr.add_comment('Convolved with optimized Gaussian-Bessel convolution function.')
        hdr['BMAJ'] = (beam_fwhm,'*But* not Gaussian.')
        hdr['BMIN'] = (beam_fwhm,'*But* not Gaussian.')
    else:
        hdr.add_comment('Gridded to nearest cell')
        hdr['BMAJ'] = beam_fwhm
        hdr['BMIN'] = beam_fwhm
    hdr['BPA'] = 0.0
    # need to change this to get the actual units from the data
    # could add additional notes to the comment field
    # if Jy, make this Jy/Beam
    if dataUnits == 'Jy':
        dataUnits = 'Jy/Beam'
    hdr['BUNIT'] = (dataUnits,calibType)

    # This suppresses runtime NaN warnings if the cube is empty
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        hdr['DATAMAX'] = numpy.nanmax(cube)

    nanCube = False
    if numpy.isnan(hdr['DATAMAX']):
        nanCube = True
        # this could possibly be done inside the above with block
        # if the warnings catch was more sophisticated
        if verbose > 2:
            print "Entire data cube is not-a-number, this may be because a few channels are consistently bad"
            print "consider restricting the channel range"
        # remove it
        hdr.remove('DATAMAX')
    else:
        hdr['DATAMIN'] = numpy.nanmin(cube)

    # note the parameter values - this must be updated as new parameters are added
    hdr.add_history("gbtgridder version: %s" % gbtgridderVersion)
    if args.channels is not None:
        hdr.add_history("gbtgridder channels: "+args.channels)
    else:
        hdr.add_history("gbtgridder all channels used")
    hdr.add_history("gbtgridder clobber: "+str(args.clobber))
    if average is not None and average > 1:
        hdr.add_history("gbtgridder average: %s channels" % average)
    hdr.add_history("gbtgridder kernel: "+args.kernel)
    if args.output is not None:
        hdr.add_history("gbtgridder output: "+args.output)
    if args.scans is not None:
        hdr.add_history("gbtgridder scans: "+args.scans)
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
        # protect against long file names - don't use more than one comment row to
        # document this.  80 chars total, 8 for "COMMENT ", 12 for "gbtgridder: "
        # leaving 60 for the file name
        if len(thisFile) > 60:
            thisFile = "*"+thisFile[-59:]
        hdr.add_history("gbtgridder: " + thisFile)

    hdr.add_comment("IEEE not-a-number used for blanked pixels.")
    hdr.add_comment("  FITS (Flexible Image Transport System) format is defined in 'Astronomy")
    hdr.add_comment("  and Astrophysics', volume 376, page 359; bibcode: 2001A&A...376..359H")

    phdu = pyfits.PrimaryHDU(cube, hdr)
    phdu.writeto(outputFiles["cube"])

    if not args.noweight:
        if verbose > 3:
            print "Writing weight cube"
        wtHdr = hdr.copy()
        wtHdr['BUNIT'] = ('weight','Weight cube')  # change from K -> weight
        wtHdr['DATAMAX'] = numpy.nanmax(weight)
        wtHdr['DATAMIN'] = numpy.nanmin(weight)

        phdu = pyfits.PrimaryHDU(weight, wtHdr)
        phdu.writeto(outputFiles["weight"])

    if not args.nocont:
        if verbose > 3:
            print "Writing 'cont' image"
        # "cont" map, sum along the spectral axis
        # SQUASH does a weighted average
        # As implemented here, this is equivalent if there are equal weights along the spectral axis
        # doing a weighted average using numpy.average and ignoring NaNs would be tricky here
        # some slices may be all NaNs (but an entire cube of NaNs was tested for earlier)
        # this suppresses that warning
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cont_map = numpy.nanmean(cube,axis=1)

        contHdr = hdr.copy()
        # AIPS just changes the channel count on the frequency axis, leaving everything else the same
        contHdr['NAXIS3'] = 1
        # restore the now-degenerate frequency axis to the shape
        cont_map.shape = (1,)+cont_map.shape
        contHdr.add_history('gbtgridder: average of cube along spectral axis')
        contHdr['DATAMAX'] = numpy.nanmax(cont_map)
        contHdr['DATAMIN'] = numpy.nanmin(cont_map)
        phdu = pyfits.PrimaryHDU(cont_map, contHdr)
        phdu.writeto(outputFiles["cont"])

    if not args.noline:
        if verbose > 3:
            print "Writing line image"
        # "line" map, subtract the along the spectral axis from every plane in the data_cube
        # replace the 0 channel with the avg
        # first, find the average over the baseline region
        n = len(faxis)
        baseRegion = [int(round(0.04*n)),int(round(0.12*n)),int(round(0.81*n)),int(round(0.89*n))]
        # construct an index from  these regions
        baseIndx = numpy.arange(baseRegion[1]-baseRegion[0]+1)+baseRegion[0]
        baseIndx = numpy.append(baseIndx,numpy.arange(baseRegion[3]-baseRegion[2]+1)+baseRegion[2])
        # this should probably be a weighted average
        avg_map = numpy.average(cube[:,baseIndx,:,:],axis=1)
        cube -= avg_map
        cube[:,0,:,:] = avg_map
        hdr['DATAMAX'] = numpy.nanmax(cube)
        hdr['DATAMIN'] = numpy.nanmin(cube)
        hdr.add_history('gbtgridder: subtracted an average over baseline region on freq axis')
        hdr.add_history('gbtgridder: average over channels: %d:%d and %d:%d' % tuple(baseRegion))
        hdr.add_history('gbtgridder: channel 0 replaced with averages')
        phdu = pyfits.PrimaryHDU(cube,hdr)
        phdu.writeto(outputFiles["line"])

    return

if __name__ == '__main__':

    args = read_command_line(sys.argv)

    # argument checking - perhaps this should be a separate function

    if args.clonecube is not None and not os.path.exists(args.clonecube):
        print args.clonecube + ' does not exist'
        sys.exit(-1)
        
    if args.mapcenter is not None and (abs(args.mapcenter[0]) > 360.0 or abs(args.mapcenter[1]) > 90.0):
        print "mapcenter values are in degrees. |LONG| should be <= 360.0 and |LAT| <= 90.0"
        sys.exit(-1)

    if args.size is not None and (args.size[0] <= 0 or args.size[1] <= 0):
        print "X and Y size values must be > 0"
        sys.exit(-1)

    if args.pixelwidth is not None and args.pixelwidth <= 0:
        print "pixelwidth must be > 0"
        sys.exit(-1)

    if args.restfreq is not None and args.restfreq <= 0:
        print "restfreq must be > 0"
        sys.exit(-1)

    if args.mintsys is not None and args.mintsys < 0:
        print "mintsys must be > 0"
        sys.exit(1)

    if args.maxtsys is not None and args.maxtsys < 0:
        print "maxtsys must be > 0"
        sys.exit(1)

    if args.maxtsys is not None and args.mintsys is not None and args.maxtsys <= args.mintsys:
        print "maxtsys must be > mintsys"
        sys.exit(1)

    try:
        gbtgridder(args)
    except ValueError, msg:
        if args.verbose > 1:
            print 'ERROR: ', msg
        sys.exit(-1)



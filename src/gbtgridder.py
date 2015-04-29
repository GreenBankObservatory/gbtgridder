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

import pyfits
from astropy import wcs
import os
import sys
import argparse
import numpy
from scipy import constants
import math
import time

def read_command_line(argv):
    """Read options from the command line."""
    # if no options are set, print help      
    if len(argv) == 1:                       
        argv.append('-h')                    

    parser = argparse.ArgumentParser()
    parser.add_argument('-c','--channels', type=str,
                        help=("Optional channel range to use.  "
                              "'<start>:<end>' counting from 0. "))
    parser.add_argument('SDFITSfiles', type=str, nargs='+',
                        help=("The calibrated SDFITS files to use.")) 
    parser.add_argument('--clobber', default=False, action='store_true',
                        help="Overwrites existing output files if set.")
    parser.add_argument('-k','--kernel', type=str, default='gauss',
                        help="gridding kernel, must be one of 'gauss', 'gaussbessel', or 'nearest', defaults to 'gauss'")
    parser.add_argument('-o','--output', type=str,
                        help="root output name, instead of source and rest frequency")

    args = parser.parse_args()

    return args

def parse_channels(channelString):
    "Turn a valid channel range into start and end channels"
    start = None
    end = None
    if channelString is not None:
        # there must be a ":"
        items = channelString.split(":")
        if len(items) != 2:
            print "Unexpected channels argument, must contain exactly one ':'"
            return (-1,1)
        if len(items[0]) > 0:
            try:
                # subtract by 1 to go from FITS convention to python
                start = int(items[0])-1
                # fixes for start < 0 happen when used
            except(ValueError):
                print repr(':'.join(items[0])), 'not convertable to integer'
                raise
        if len(items[1]) > 0:
            try:
                # subtract by 1 to go from FITS to python convention
                end = int(items[1])-1
            except(ValueError):
                print repr(':'.join(items[1])), 'not convertable to integer'
                raise
    return (start,end)

def set_output_files(source, frest, args, file_types):

    outputNameRoot = args.output
    clobber = args.clobber

    if outputNameRoot is None:
        outputNameRoot = "%s_%.0f_MHz" % (source,frest/1.e6)
    # always tack on the underscore
    outputNameRoot += "_"
    print "outname root : ", outputNameRoot
    print "     clobber : ", clobber
    
    result = {}
    for file_type in file_types:
        typeName = outputNameRoot + file_type + ".fits"
        if os.path.exists(typeName):
            if not clobber:
                print typeName + " exists, will not overwrite"
                return {}
            else:
                os.remove(typeName)
                print "existing " + typeName + " removed"
        result[file_type] = typeName
    return result

def gbtgridder(args):
    if not args.SDFITSfiles:
        return

    chanStart, chanStop = parse_channels(args.channels)
    if (chanStart is not None and chanStart < 0) or (chanStop is not None and chanStop < 0):
        return

    if chanStart is None:
        chanStart = 0

    sdfitsFiles = args.SDFITSfiles
    for sdf in sdfitsFiles:
        if not os.path.exists(sdf):
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
    rawdata = None
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
    instrume = None
    dateObs = None
    outputFiles = {}

    print "Loading data ... "
    for thisFile in sdfitsFiles:
        try:
            print "   ",thisFile
            dataRecord = get_data(thisFile,nchan,chanStart,chanStop)
            if len(dataRecord) == 0:
                # empty file, skipping
                continue

            if xsky is None:
                xsky = dataRecord["xsky"]
                ysky = dataRecord["ysky"]
                wt = dataRecord["wt"]
                rawdata = dataRecord["rawdata"]
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
                instrume = dataRecord["instrume"]
                observer = dataRecord["observer"]
                dateObs = dataRecord["date-obs"]

                # this also checks that the output files are OK to write
                # given the value of the clobber argument
                outputFiles = set_output_files(source, frest, args, ["cube","weight","line","cont"])
                if len(outputFiles) == 0:
                    print "Unable to write to output files"
                    return
                
            else:
                xsky = numpy.append(xsky,dataRecord["xsky"])
                ysky = numpy.append(ysky,dataRecord["ysky"])
                wt = numpy.append(wt,dataRecord["wt"])
                rawdata = numpy.append(rawdata,dataRecord["rawdata"],axis=0)

        except(AssertionError):
            print "%s had a problem, more than one table or not a valid GBT single dish FITS file?" % thisFile
            raise

    # characterize the center of the image
    # need to worry about points clearly off the grid, e.g. no Antenna pointings (0.0) or
    # a reference position incorrectly included in the data to be gridded.
    # idlToSdfits rounds the center from the mean to the nearest second/arcsecond
    # for RA or HA, divide by 15
    if coordType[0] in ['RA','HA']:
        centerXsky = round(numpy.mean(xsky)*3600.0/15)/(3600.0/15.0)
    else:
        centerXsky = round(numpy.mean(xsky)*3600.0)/3600.0
    centerYsky = round(numpy.mean(ysky)*3600.0)/3600.0

    # and the appropriate pixel size
    # need to worry about possible problems near 0/360 or +- 180?
    xRange = xsky.max()-xsky.min()
    yRange = ysky.max()-ysky.min()

    # find the cell size, first from the beam_fwhm
    # currently we use the same equation used in idlToSdfits
    # there's about a 2% difference between the two

    # this equation comes from Adam's IDL code, where do the 747.6 and 763.8 values come from?
    # beam_fwhm = (747.6+763.8)/2.0/numpy.median(faxis/1.e9)/3600.
    # This is what idlToSdfits does (next 2 lines of code)
    # telescop diameter, in meters
    diam = 100.0
    beam_fwhm = 1.2 * constants.c * (180.0/constants.pi) / (diam * numpy.median(faxis))
    # the 747.6 and 763.8 values above are equivalent to diam of 99.3 and 97.2 m in this equation, respectively

    # cell's per beam.  Adam's code uses 4, idlToSdfits uses 6
    # idlToSdfits also rounds up to nearest arcsecond
    pix_scale = math.ceil(3600.0*beam_fwhm/6.0)/3600.0

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

    # gaussian size to use in gridding.
    # this is what Adam used:  gauss_fwhm = beam_fwhm/3.0
    # this duplicates the aparm(2)=1.5*cellsize used by AIPS in the default pipeline settings
    # the following is about 0.41*beam_fwhm vs 0.33*beam_fwhm from Adam - so wider
    gauss_fwhm = (1.5*pix_scale)*2.354/math.sqrt(2.0)

    print "Map info ..."
    print "   beam_fwhm : ", beam_fwhm, "(", beam_fwhm*60.0*60.0, " arcsec)"
    print "   pix_scale : ", pix_scale, "(", pix_scale*60.0*60.0, " arcsec)"
    print "  gauss fwhm : ", gauss_fwhm, "(", gauss_fwhm*60.0*60.0, " arcsec)"
    print "    ctr Xsky : ", centerXsky
    print "    ctr Ysky : ", centerYsky
    print "       xsize : ", xsize
    print "       ysize : ", ysize
    print "          f0 : ", faxis[0]
    print "    delta(f) : ", faxis[1]-faxis[0]
    print "       nchan : ", nchan
    print "       nfreq : ", len(faxis)
    print "   N to grid : ", len(xsky)
    print "      source : ", source
    print " frest (MHz) : ", frest/1.e6

    # build the initial header object
    # only enough to build the WCS object from it + BEAM size info
    # I had trouble with embedded HISTORY cards and the WCS constructor
    # so those are omitted for now
    hdr = make_header(centerXsky, centerYsky, xsize, ysize, pix_scale, coordType, radesys, equinox, frest, faxis, beam_fwhm, veldef, specsys, proj='SFL')

    # relax is turned on here for compatibility with previous images produced by AIPS from the gbtpipeline
    # there may be a better solution
    # even so, it does not like the "-LSR" tag to the CTYPE3 value for the frequency axis
    wcsObj = wcs.WCS(hdr,relax=True)

    # eventually pix_scale here should come from the wcsObject
    (cube, weight, beam_fwhm) = grid_otf(rawdata, xsky, ysky, wcsObj, len(faxis), xsize, ysize, pix_scale, weight=wt, beam_fwhm=beam_fwhm, kern=args.kernel, gauss_fwhm=gauss_fwhm)

    if cube is None or weight is None:
        print "Problem gridding data"
        return

    # start writing stuff to disk
    # add additional information to the header
    hdr['telescop'] = telescop
    hdr['instrume'] = instrume
    hdr['observer'] = observer
    hdr['date-obs'] = (dateObs,'Observed time of first spectra gridded')
    hdr['date-map'] = (time.strftime("%Y-%m-%dT%H:%M:%S",time.gmtime()),"Created by gbtgridder")
    hdr['data'] = time.strftime("%Y-%m-%d",time.gmtime())

    if args.kernel == 'gauss':
        hdr.add_history('Convolved with Gaussian convolution function.')
        hdr['BMAJ'] = beam_fwhm
        hdr['BMIN'] = beam_fwhm
    elif kern == 'gaussbessel':
        hdr.add_history('Convolved with optimized Gaussian-Bessel convolution function.')
        hdr['BMAJ'] = (beam_fwhm,'*But* not Gaussian.')
        hdr['BMIN'] = (beam_fwhm,'*But* not Gaussian.')
    else:
        hdr.add_history('Gridded to nearest cell')
        hdr['BMAJ'] = beam_fwhm
        hdr['BMIN'] = beam_fwhm
    hdr['BPA'] = 0.0
    # need to change this to get the actual units from the data
    # could add additional notes to the comment field
    # if Jy, make this Jy/Beam
    if dataUnits == 'Jy':
        dataUnits = 'Jy/Beam'
    hdr['BUNIT'] = (dataUnits,calibType)
    hdr['DATAMAX'] = numpy.nanmax(cube)
    hdr['DATAMIN'] = numpy.nanmin(cube)
    # note the parameter values - this must be updated as new parameters are added
    if args.channels is not None:
        hdr.add_comment("gbtgridder: channels: "+args.channels)
    else:
        hdr.add_comment("gbtgridder: all channels used")
    hdr.add_comment("gbtgridder: clobber: "+str(args.clobber))
    hdr.add_comment("gbtgridder: kernel: "+args.kernel)
    if args.output is not None:
        hdr.add_comment("gbtgridder: output: "+args.output)
    hdr.add_comment("gbtgridder: sdfits files ...")
    for thisFile in args.SDFITSfiles:
        # protect against long file names - don't use more than one comment row to
        # document this.  80 chars total, 8 for "COMMENT ", 12 for "gbtgridder: "
        # leaving 60 for the file name
        if len(thisFile) > 60:
            thisFile = "*"+thisFile[-59:]
        hdr.add_comment("gbtgridder: " + thisFile)

    hdr.add_comment("IEEE not-a-number used for blanked pixels.")
    hdr.add_comment("  FITS (Flexible Image Transport System) format is defined in 'Astronomy")
    hdr.add_comment("  and Astrophysics', volume 376, page 359; bibcode: 2001A&A...376..359H")

    phdu = pyfits.PrimaryHDU(cube, hdr)
    phdu.writeto(outputFiles["cube"])

    wtHdr = hdr.copy()
    wtHdr['BUNIT'] = ('weight','Weight cube')  # change from K -> weight
    wtHdr['DATAMAX'] = numpy.nanmax(weight)
    wtHdr['DATAMIN'] = numpy.nanmin(weight)

    phdu = pyfits.PrimaryHDU(weight, wtHdr)
    phdu.writeto(outputFiles["weight"])

    # "cont" map, sum along the spectral axis
    # SQUASH does a weighted average
    # As implemented here, this is equivalent if there are equal weights along the spectral axis
    cont_map = numpy.average(cube,axis=0)
    contHdr = hdr.copy()
    # AIPS just changes the channel count on the frequency axis, leaving everything else the same
    contHdr['NAXIS3'] = 1
    cont_map.shape = (1,1,cont_map.shape[0],cont_map.shape[1])
    contHdr.add_history('Average of cube along spectral axis')
    contHdr['DATAMAX'] = numpy.nanmax(cont_map)
    contHdr['DATAMIN'] = numpy.nanmin(cont_map)
    phdu = pyfits.PrimaryHDU(cont_map, contHdr)
    phdu.writeto(outputFiles["cont"])

    # "line" map, subtract the along the spectral axis from every plane in the data_cube
    # replace the 0 channel with the avg
    # first, find the average over the baseline region
    n = len(faxis)
    baseRegion = [int(round(0.04*n)),int(round(0.12*n)),int(round(0.81*n)),int(round(0.89*n))]
    # construct an index from  these regions
    baseIndx = numpy.arange(baseRegion[1]-baseRegion[0]+1)+baseRegion[0]
    baseIndx = numpy.append(baseIndx,numpy.arange(baseRegion[3]-baseRegion[2]+1)+baseRegion[2])
    # this should probably be a weighted average
    avg_map = numpy.average(cube[baseIndx,:,:],axis=0)
    cube -= avg_map
    cube[0,:,:] = avg_map
    hdr['DATAMAX'] = numpy.nanmax(cube)
    hdr['DATAMIN'] = numpy.nanmin(cube)
    hdr.add_history('Subtracted the average along spectral axis over baseline region')
    hdr.add_history('Average over channels: %d:%d and %d:%d' % tuple(baseRegion))
    hdr.add_history('Channel 0 replaced with averages')
    phdu = pyfits.PrimaryHDU(cube,hdr)
    phdu.writeto(outputFiles["line"])

    return

if __name__ == '__main__':

    args = read_command_line(sys.argv)

    if args.kernel not in ["gauss","gaussbessel","nearest"]:
        print "kernel must be one of 'gauss', 'gaussbessel', or 'nearest'"
        sys.exit(-1)

    gbtgridder(args)
    sys.exit(-1)

    try:
        gbtgridder(args)
    except ValueError, msg:
        print 'ERROR: ', msg
        sys.exit(-1)



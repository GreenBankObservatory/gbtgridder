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

def get_data(sdfitsFile, nchan, chanStart, chanStop):
    """
    Given an sdfits file, return the desired raw data and associated
    sky positions, weight, and frequency axis information
    """
    result = {}
    thisFits = pyfits.open(sdfitsFile,memmap=True,mode='readonly')

    # this expects a single SDFITS table in each file
    assert(len(thisFits)==2 and thisFits[1].header['extname'] == 'SINGLE DISH')

    # if there are no rows, just move on
    if thisFits[1].header['NAXIS2'] == 0:
        print "Warning: %s has no rows in the SDFITS table.  Skipping." % sdfitsFile
        return result

    # get NCHAN for this file from the value of format for the DATA column
    # I wish pyfits had an easier way to get at this value
    colAtr = thisFits[1].columns.info("name,format",output=False)
    thisNchan = int(colAtr['format'][colAtr['name'].index('DATA')][:-1])

    if nchan is None:
        nchan = thisNchan

    # all tables must be consistent
    assert(nchan == thisNchan)

    result['xsky'] = thisFits[1].data.field('crval2')
    result['ysky'] = thisFits[1].data.field('crval3')
    # need to look at CTYPE2 and CTYPE3 for sky coordinate type
    # this code currently assumes RA/DEC J2000
    # what to do if the data aren't all in the same coord. system.?

    if chanStop is None or chanStop >= nchan:
        chanStop = nchan-1
    result["chanStart"] = chanStart
    result["chanStop"] = chanStop
    result["nchan"] = nchan

    # replace NaNs in the raw data with 0s
    result["rawdata"] = numpy.nan_to_num(thisFits[1].data.field('data')[:,chanStart:(chanStop+1)])

    # for now, scalar weights.  Eventually spectral weights - which will need to know
    # where the NaNs were in the above
    texp = thisFits[1].data.field('exposure')
    tsys = thisFits[1].data.field('tsys')
    # using nan_to_num here sets wt to 0 if there are tsys=0.0 values in the table
    result["wt"] = numpy.nan_to_num(texp/(tsys*tsys))

    # column values relevant to the frequency axis
    crv1 = thisFits[1].data.field('crval1')
    cd1 = thisFits[1].data.field('cdelt1')
    crp1 = thisFits[1].data.field('crpix1')
    vframe = thisFits[1].data.field('vframe')
    frest = thisFits[1].data.field('restfreq')
    beta = numpy.sqrt((constants.c+vframe)/(constants.c-vframe))

    # full frequency axis in doppler tracked frame from first row
    indx = numpy.arange(result["rawdata"].shape[1])+1.0+chanStart
    freq = (crv1[0]+cd1[0]*(indx-crp1[0]))*beta[0]
    result["freq"] = freq
    result["restfreq"] = frest[0]

    # source name of first spectra
    result['source'] = thisFits[1].data[0].field('object')
    
    thisFits.close()

    return result

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
    # this is OK if xsky is known to be RA, needs to avoid division by 15.0 if not
    centerXsky = round(numpy.mean(xsky)*3600.0/15)/(3600.0/15.0)
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
    imPadding = math.ceil(45./(pix_scale*3600.0))
    # add in padding and truncate to an integer
    xsize = int((xRange*1.1/pix_scale)+2*imPadding)
    ysize = int((yRange*1.1/pix_scale)+2*imPadding)
    # image.py then does this ... 
    xsize = int((2*round(xsize/1.95)) + 20)
    ysize = int((2*round(ysize/1.95)) + 20)

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
    hdr = make_header(centerXsky, centerYsky, xsize, ysize, pix_scale, frest, faxis, beam_fwhm, proj='SFL', veldef="RAD")

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
    hdr.add_history('Created by gbtgridder at '+ time.strftime("%a %b %d %H:%M%S %Z %Y",time.localtime()))
    if args.kernel == 'gauss':
        hdr.add_history('Convolved with Gaussian convolution function.')
        hdr['BMAJ'] = beam_fwhm
        hdr['BMIN'] = beam_fwhm
    elif kern == 'gaussbessel':
        hdr.add_history('Convolved with optimized Gaussian-Bessel convolution function.')
        hdr['BMAJ'] = (beam_fwhm,'*But* not Gaussian.')
        hdr['BMIN'] = (beam_fwhm,'*Bit* not Gaussian.')
    else:
        hdr.add_history('Gridded to nearest cell')
        hdr['BMAJ'] = beam_fwhm
        hdr['BMIN'] = beam_fwhm
    hdr['BPA'] = 0.0
    # need to change this to get the actual units from the data
    # could add additional notes to the comment field
    hdr['BUNIT'] = ('K','TA*')

    phdu = pyfits.PrimaryHDU(cube, hdr)
    phdu.writeto(outputFiles["cube"])

    wtHdr = hdr.copy()
    wtHdr['BUNIT'] = 'weight'  # change from K -> weight
    phdu = pyfits.PrimaryHDU(weight, wtHdr)
    phdu.writeto(outputFiles["weight"])

    # "cont" map, sum along the spectral axis
    # SQUASH does a weighted average
    # As implemented here, this is equivalent if there are equal weights along the spectral axis
    cont_map = numpy.average(cube,axis=0)
    contHdr = hdr.copy()
    # recast this as a 2D header
    contHdr['NAXIS'] = 2
    for kw in ['NAXIS3','CTYPE3','CUNIT3','CRVAL3','CRPIX3','CDELT3','SPECSYS','VELREF','RESTFRQ']:
        contHdr.remove(kw)
    contHdr.add_history('Average of cube along spectral axis')
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



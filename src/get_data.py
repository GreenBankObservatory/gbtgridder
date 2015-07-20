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

from boxcar import boxcar

import pyfits
import numpy
from scipy import constants

def get_data(sdfitsFile, nchan, chanStart, chanStop, average, scanlist, verbose=4):
    """
    Given an sdfits file, return the desired raw data and associated
    sky positions, weight, and frequency axis information
    """
    result = {}
    thisFits = pyfits.open(sdfitsFile,memmap=True,mode='readonly')

    # this expects a single SDFITS table in each file
    # it is a serious error and so None is the returned result
    if len(thisFits) < 2:
        if verbose > 2:
            print "%s has no extensions and is not a single dish FITS file, can not continue." % sdfitsFile
        return None

    if len(thisFits) > 2:
        if verbose > 2:
            print "%s has more than 1 extension, can not continue." % sdfitsFile
        return None

    if thisFits[1].header['extname'] != 'SINGLE DISH':
        if verbose > 2:
            print "%s is not a single dish FITS file, can not continue." % sdfitsFile
        return None

    # if there are no rows, just move on
    if thisFits[1].header['NAXIS2'] == 0:
        if verbose > 2:
            print "Warning: %s has no rows in the SDFITS table.  Skipping." % sdfitsFile
        thisFits.close()
        return result

    # get NCHAN for this file from the value of format for the DATA column
    # I wish pyfits had an easier way to get at this value
    colAtr = thisFits[1].columns.info("name,format",output=False)
    thisNchan = int(colAtr['format'][colAtr['name'].index('DATA')][:-1])

    if nchan is None:
        nchan = thisNchan

    # all tables must be consistent
    assert(nchan == thisNchan)

    # averaging must be > 0 and <= nchan (equal to nchan may be silly)
    if average is not None and (average < 1 or average > nchan):
        if verbose > 1:
            print "Error: averaging must be between 1 and the number of channels"
        thisFits.close()
        return result

    thisTabData = thisFits[1].data
    if scanlist is not None:
        allScans = thisTabData.field('scan')
        uniqueScans = numpy.unique(allScans)
        scanMask = numpy.full(allScans.shape,True,dtype=bool)
        for scan in uniqueScans:
            if scan not in scanlist:
                scanMask[allScans==scan] = False
        thisTabData = thisTabData[scanMask]
        if len(thisTabData) == 0:
            if verbose > 2:
                print "Warning: %s has no rows within the list of selected scan numbers.  Skipping." % sdfitsFile
            thisFits.close()
            return result                

    result['scans'] = thisTabData.field('scan')
    result['xsky'] = thisTabData.field('crval2')
    result['ysky'] = thisTabData.field('crval3')

    # assumes all the data are in the same coordinate system
    result['xctype'] = thisTabData[0].field('ctype2')
    result['yctype'] = thisTabData[0].field('ctype3')
    result['radesys'] = thisTabData[0].field('radesys')
    result['equinox'] = thisTabData[0].field('equinox')

    if chanStop is None or chanStop >= nchan:
        chanStop = nchan-1
    result["chanStart"] = chanStart
    result["chanStop"] = chanStop
    result["nchan"] = nchan

    # replace NaNs in the raw data with 0s
    result["rawdata"] = numpy.nan_to_num(thisTabData.field('data')[:,chanStart:(chanStop+1)])

    # for now, scalar weights.  Eventually spectral weights - which will need to know
    # where the NaNs were in the above
    texp = thisTabData.field('exposure')
    tsys = thisTabData.field('tsys')
    # using nan_to_num here sets wt to 0 if there are tsys=0.0 values in the table
    result["wt"] = numpy.nan_to_num(texp/(tsys*tsys))
    # to match current idlToSdfits behavior ..
    #     set wt to 0.0 where any of the values in the related spectrum were nan (now 0.0)
    #     eventually will have per-channel wts and this step will be different
    result["wt"][numpy.any(result["rawdata"]==0.0,axis=1)] = 0.0

    # column values relevant to the frequency axis
    # assumes axis is FREQ
    crv1 = thisTabData.field('crval1')
    cd1 = thisTabData.field('cdelt1')
    crp1 = thisTabData.field('crpix1')
    vframe = thisTabData.field('vframe')
    frest = thisTabData.field('restfreq')
    beta = numpy.sqrt((constants.c+vframe)/(constants.c-vframe))

    # full frequency axis in doppler tracked frame from first row
    indx = numpy.arange(result["rawdata"].shape[1])+1.0+chanStart
    freq = (crv1[0]+cd1[0]*(indx-crp1[0]))*beta[0]
    result["freq"] = freq
    result["restfreq"] = frest[0]

    # do any channel averaging here
    if average is not None:
        (result["rawdata"],result["freq"]) = boxcar(result["rawdata"],result["freq"],average)

    # decompose VELDEF into velocity definition (still call this veldef)
    # and specsys - appropriate for current WCS spectral coordinate convention.
    # this will throw an exception if there is no hyphen.  A proper
    # sdfits file will always have that hyphen
    veldef = thisTabData[0].field('veldef')
    veldef, dopframe = veldef.split('-')
    result['veldef'] = veldef
    # translate dopframe into specsys
    #  I'm not 100% sure that COB from the GBT is the same as CMDBIPOL from Greisen et al
    specSysDict = {'OBS':'TOPOCENT',
                   'GEO':'GEOCENTR',
                   'BAR':'BARYCENT',
                   'HEL':'HELIOCEN',
                   'GAL':'GALACTOC',
                   'LSD':'LSRD',
                   'LSR':'LSRK',
                   'LGR':'LOCALGRP',
                   'COB':'CMBDIPOL'}
    if dopframe in specSysDict:
        result['specsys'] = specSysDict[dopframe]
    else:
        if verbose > 2:
            print "WARN: unrecognized frequency reference frame %s ... using OBS" % dopframe
        result['specsys'] = specSysDict['OBS']

    # source name of first spectra
    result['source'] = thisTabData[0].field('object')

    # data units, assumes all rows have the same as the first one
    # also assumes DATA is column 7
    result['units'] = thisTabData[0].field('tunit7')
    # currently the pipeline sets this to the argument value of the
    # requested calibration units, e.g. Ta, Tmb, Jy.  This should
    # really be physical units with the calibration type indicated
    # separately.  Attempt to detangle that here ... anything that
    # isn't "Jy" is assumed to be "K" and the original unit
    # string is copied over to "calibtype".
    result['calibtype'] = result['units']
    if result['units'] != 'Jy':
        result['units'] = 'K'

    # additional information - this is what idlToSdfits supplies
    result['telescop'] = thisFits[1].header['telescop']
    result['instrume'] = thisFits[1].header['backend']
    result['observer'] = thisTabData[0].field('observer')
    # date-obs from first row
    result['date-obs'] = thisTabData[0].field('date-obs')
    
    thisFits.close()

    return result


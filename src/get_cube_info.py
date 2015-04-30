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

import pyfits
import os

def get_cube_info(cubeFile, verbose=4):
    """
    Return a dictionary containing the information on the first 2 axes
    of the indicated cube FITS file.

    Requirements:
      cubeFile must exist and it must contain a 4D image in the PHDU.
      CDELT1 and CDELT2 must have the same absolute value
      CDELT1 must be < 0 and CDELT2 must be > 0
      The projection found in CTYPE1 must match that in CTYPE2
      The projection must be one of SFL, GLS, or TAN

    The returned diction contains these fields:
       xsize, ysize: the number of pixels along each of the first 2 axes
       xref, yref: the world coordinates at the xrefPix, yrefPix values
          Note that for SFL, the "yref" always has a value of 0.0
            and the yrefPix is often far from the center of the image
       xrefPix, yrefPix: the center pixel
       pix_scale: the value of CDELT2
       proj: the 3-letter projection from CTYPE1
       xtype, ytype: the first 4 letters of CTYPE1 or CTYPE2 with trailing
          "-" removed
       radesys: RADESYS keyword value if found, else None
       equinox: EQUINOX keyword value if found, else None

    if any of the requirements are not met, the returned value is None
    
    verbose has the same meaning throughout gbtgridder
    """

    result = None

    if not os.path.exists(cubeFile):
        if verbose > 1:
            print "%s not found" % cubeFile
        return result

    try:
        cfits = pyfits.open(cubeFile,readonly=True,memmap=True)
        if cfits[0].header['naxis'] != 4:
            if verbose > 1:
                print "%s does not have 4 axes in the PHDU image" % cubeFile
            cfits.close()
            return result

        xsize = cfits[0].header['naxis1']
        ysize = cfits[0].header['naxis2']
        cdelt1 = cfits[0].header['cdelt1']
        cdelt2 = cfits[0].header['cdelt2']
        ctype1 = cfits[0].header['ctype1']
        ctype2 = cfits[0].header['ctype2']
        crpix1 = cfits[0].header['crpix1']
        crpix2 = cfits[0].header['crpix2']
        crval1 = cfits[0].header['crval1']
        crval2 = cfits[0].header['crval2']
        radesys = None
        equinox = None
        if 'radesys' in cfits[0].header:
            radesys = cfits[0].header['radesys']
        if 'equinox' in cfits[0].header:
            equinox = cfits[0].header['equinox']
        cfits.close()

        if cdelt1 > 0.0 or cdelt2 < 0.0:
            if verbose > 1:
                print "1st and/or 2nd axes of %s are inverted from expected direction" % cubeFile
            return result
        if abs(cdelt1) != cdelt2:
            if verbose > 1:
                print "Pixel size is not the same on axis 1 and 2 in %s" % cubeFile
            return result

        ctype1Proj = ctype1[4:]
        ctype2Proj = ctype2[4:]
        if ctype1Proj != ctype2Proj:
            if verbose > 1:
                print "projections are not the same for axis 1 and 2 in %s" % cubeFile
            return result

        # remove the leading '-'
        proj = ctype1Proj.split('-')[-1]
        if proj not in ["SFL","GLS","TAN"]:
            if verbose > 1:
                print "Unrecognized projection %s in %s" % (proj,cubeFile)

        if proj == "GLS":
            proj = "SFL"

        result = {}
        result["xref"] = crval1
        result["yref"] = crval2
        result["xrefPix"] = crpix1
        result["yrefPix"] = crpix2
        result["xsize"] = xsize
        result["ysize"] = ysize
        result["pix_scale"] = cdelt2
        result["proj"] = proj
        result["xtype"] = ctype1[:4].split('-')[0]
        result["ytype"] = ctype2[:4].split('-')[0]
        result["radesys"] = radesys
        result["equinox"] = equinox

        if result["radesys"] is None and result["equinox"] is not None and result["xtype"] == "RA":
            result["radesys"] = "FK5"

    except:
        if verbose > 1:
            print "problems opening and reading values from %s" % cubeFile
        raise

    return result

        

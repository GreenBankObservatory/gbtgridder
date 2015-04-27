
import pyfits
import time

def make_header(xctr, yctr, xsize, ysize, pix_scale, restfreq, faxis, beam_fwhm, proj="TAN",veldef="RAD"):

    hdr = pyfits.Header()

    # BASIC stuff, the WCS code needs this
    hdr['NAXIS'] = 3
    hdr['NAXIS1'] = xsize
    hdr['NAXIS2'] = ysize
    hdr['NAXIS3'] = len(faxis)

    # MAKE THE POSITION AXES
    if proj == 'TAN':
        hdr['CTYPE1'] = 'RA---TAN'
        hdr['CRVAL1'] = xctr
        hdr['CRPIX1'] = (xsize/2.0)
        hdr['CDELT1'] = -1.0*pix_scale

        hdr['CTYPE2'] = 'DEC--TAN'
        hdr['CRVAL2'] = yctr
        hdr['CRPIX2'] = (ysize/2.)
        hdr['CDELT2'] = pix_scale
    elif proj == 'SFL':
        hdr['CTYPE1'] = 'RA---SFL'
        hdr['CRVAL1'] = xctr
        hdr['CRPIX1'] = (xsize/2.)
        hdr['CDELT1'] = -1.0*pix_scale

        # GLS projection always has CRVAL2 at 0.0
        # set CRPIX2 so that at the center pixel (ysize/2)
        # the y value is yctr
        hdr['CTYPE2'] = 'DEC--SFL'
        hdr['CRVAL2'] = 0.0
        yctrPix = (ysize/2.0) + 1.0
        hdr['CRPIX2'] = yctrPix - (yctr/pix_scale)
        hdr['CDELT2'] = pix_scale
    else:
        raise Exception("%s is an invalid projection code, must be one of 'TAN' or 'SFL'" % proj)        

    # MAKE THE VELOCITY AXIS (ALONG THE THIRD DIMENSION)
    hdr['CTYPE3'] = 'FREQ-LSR'
    hdr['CUNIT3'] = 'Hz'
    hdr['CRVAL3'] = faxis[0]
    hdr['CRPIX3'] = 1.0
    hdr['CDELT3'] = faxis[1]-faxis[0]
    hdr['SPECSYS'] = 'LSRK'
    hdr['VELREF'] = 1
    # no check for other values of veldef arg
    if veldef == "RAD":
        hdr['VELREF'] = 257
        
    hdr['RESTFRQ'] = restfreq

    # ADD THE J2000 EQUINOX
    hdr['EQUINOX'] = 2000.

    # ADD THE BEAM
    hdr['BMAJ'] = beam_fwhm
    hdr['BMIN'] = beam_fwhm

    # ADD UNITS (TA* in K) - can we get these from the SDFITS?
    # pretend it's Jy/Beam to make casaviewer happy
    hdr['BUNIT'] =  ('Jy/beam', 'TA*, apply eff. to get Tmb')

    # ADD A STAMP
    #hdr.add_history('Header created by MAKE_HEADER.py')
    #hdr.add_history(time.strftime("%a %b %d %H:%M:%S %Z %Y",time.localtime()))

    return hdr

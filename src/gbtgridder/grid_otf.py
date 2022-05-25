# Copyright (C) 2015 Associated Universities, Inc. Washington DC, USA.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope. that it will be useful, but
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

#import multiprocessing as mp

import cygrid
import numpy as np

#import sparse
#from scipy.special import j1


# speed of light (m/s)
_C = 299792458.0
conv_weights = None
spec = None
glong = None
glong_axis = None
support_distance = None


def prepare_header(wcsObj, nx, ny, nchan):
    """"""

    # wcs.to_header() drops the number of elements in each axes.
    header = wcsObj.to_header()
    # Add them back at the start of the header.
    header.insert(0,"NAXIS1")
    header["NAXIS1"] = nx
    header.insert(1,"NAXIS2")
    header["NAXIS2"] = ny
    header.insert(2,"NAXIS3")
    header["NAXIS3"] = nchan

    return header


def grid_otf(
    spec_array,
    spec_size,
    nx,
    ny,
    glon,
    glon_calc,
    glat,
    wcsObj,
    pix_scale,
    refXsky,
    centerYsky,
    weights=None,
    beam_fwhm=None,
    kernel_type="gaussbessel",
    gauss_fwhm=None,
    verbose=4,
):
    """Grid individual spectra onto a specified regular grid following the
    recommendations of Mangum et al. (2007).  This is writtent to be of general
    use in gridding OTF data.

    Version 1.0 based on version 0.5 by Bob Garwood (NRAO) and sdgridder by Trey Wenger (DRAO)
    For Verison 1.0 support reach out to Kathlyn Purcell (kpurcell@nrao.edu)

    Inputs:
       spec_array - 2-d array containing the spectra to be gridded
       spec_size - size of the spectra from fits header, given through get_data.py
       glong - length vector of X positions on the sky for each spectra in data (deg)
       glat - length vector of Y positions on the sky for each spectra in data (deg)
       weight - (optional) an nspec length vector of weights for each spectra in data.
                if not supplied, equal weights are assumed
       beam_fwhm - the fwhm in decimal degrees of the telescope beam.  If not
                   supplied it must be found in the target_hdr.
       gauss_fwhm - the fwhm in decimal degrees of the gaussian used in the
                    convolution kernel.  Used only when kern="gauss".
                    Defaults to beam_fwhm/3 if not set.
       kernel_type - specify the gridding kernel to use from "gaussbessel", "gauss", or "nearest".
              defaults to "gaussbessel"

    Returns: (cube, weight, beam_fwhm) where cube is the cube array after gridding and
       weight is the related weight array and beam_fwhm is effective fwhm of the beam
       after the convolution.  Returns (None, None, None) on failure.

    Original IDL credits to CLASS's xy_map, E. Rosolowsky
    """

    result = (None, None, None)

    # argument checking
    if len(spec_array.shape) != 2 or len(glon.shape) != 1 or len(glat.shape) != 1:
        if verbose > 1:
            print("data, sky coordinates have unexpected shapes")
            print("data : ", spec_array.shape)
            print("gLongitude : ", glon.shape)
            print("gLatitude : ", glat.shape)
        return result

    nspec, nchan_data = spec_array.shape

    if nspec == 0 or nchan_data == 0:
        if verbose > 1:
            print("no data given")
        return result

    if nspec != len(glon) or nspec != len(glat):
        if verbose > 1:
            print(
                "Number of sky position values does not match number of spectra in data"
            )
        return result

    if kernel_type not in ["gaussbessel", "gauss", "nearest"]:
        if verbose > 1:
            print("kern must be one of gaussbessel or gauss")
        return result

    # Handle the weights.
    if weights.shape != spec_array.shape:
        if weights.shape[0] == spec_array.shape[0]:
            weight_array = weights[..., None] + np.empty(nchan_data, dtype=np.float32)
    else:
        weight_array = weights

    gauss_sigma = gauss_fwhm / (2.0 * np.sqrt(2.0 * np.log(2.0)))  # equivalent of 'b'
    # ie.       = 2.52*beam_fwhm/3.0
    final_fwhm = np.sqrt(
        beam_fwhm ** 2.0 + gauss_fwhm ** 2.0
    )  # verison0.5 equivialent of scale_fwhm*beam_fwhm

    # Get convolution Bessel function width (deg)
    # from Mangum, Emerson, Greisen (2007)  #version0.5 equivialent of 'a'
    bessel_width = 1.55 * beam_fwhm / 3.0

    # Support distance for convolution
    support_distance = beam_fwhm

    # account for the 'pill box' kernel
    if kernel_type == "nearest":
        support_distance = 1.0 * pix_scale  # one pixel

    header = prepare_header(wcsObj, nx, ny, nchan_data)

    # Set up kernel parameters.
    if kernel_type == "gauss":
        kernel_type = "gauss1d"
        kernel_params = (gauss_sigma)
    elif kernel_type == "gaussbessel":
        kernel_params = (bessel_width, gauss_sigma)
    kernel_support = support_distance
    hpx_maxres = gauss_sigma / 2.

    # Define a cygrid.gridder object and its kernel.
    mygridder = cygrid.WcsGrid(header)
    mygridder.set_kernel(kernel_type,
                         kernel_params,
                         kernel_support,
                         hpx_maxres
                         )

    # Do the gridding.
    mygridder.grid(glon, glat, spec_array, weights=weight_array)

    # Query results.
    data_cube = mygridder.get_datacube()
    weights_cube = mygridder.get_weights()

    return (data_cube, weights_cube, final_fwhm)

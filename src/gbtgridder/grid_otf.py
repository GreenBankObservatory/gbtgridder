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


import cygrid
import numpy as np

# speed of light (m/s)
_C = 299792458.0


def prepare_header(wcsObj, nx, ny, nchan):
    """"""

    # wcs.to_header() drops the number of elements in each axes.
    header = wcsObj.to_header()
    # Add them back at the start of the header.
    header.insert(0, "NAXIS1")
    header["NAXIS1"] = nx
    header.insert(1, "NAXIS2")
    header["NAXIS2"] = ny
    header.insert(2, "NAXIS3")
    header["NAXIS3"] = nchan

    return header


def grid_otf(
    spec,
    nx,
    ny,
    glon,
    glat,
    wcsObj,
    pix_scale,
    refXsky,
    centerYsky,
    beam_fwhm,
    weights,
    kernel_type,
    gauss_fwhm,
    verbose,
):
    """Grid individual spectra onto a specified regular grid using the package
    cygrid https://github.com/bwinkel/cygrid/tree/master/cygrid.

    Version 1.1 based on version 0.5 by Bob Garwood (NRAO) and cygrid by bwinkel
    For Verison 1.0 support reach out to Kathlyn Purcell (kpurcell@nrao.edu)

    Inputs:
       spec - 1-d array containing the spectra to be gridded
       nx - longitude size of resultant image in pixels
       ny - latitude size of resultant image in pixels
       glon - length vector of X positions on the sky for each spectra in data (deg)
       glat - length vector of Y positions on the sky for each spectra in data (deg)
       wscObj - wcs object created from the header data
       pix_scale - size of one pixel
       refXsky - reference for the X center of the resultant image
       centerYsky - reference for the Y center of the resultant image
       beam_fwhm - the fwhm in decimal degrees of the telescope beam.
       weights - (optional) an nspec length vector of weights for each spectra in data.
                if not supplied, equal weights are assumed
       gauss_fwhm - the fwhm in decimal degrees of the gaussian used in the
                    convolution kernel.  Used only when kern="gauss".
       kernel_type - specify the gridding kernel to use from "gaussbessel", "gauss", or "nearest".

    Returns: (cube, weight, final_fwhm) where cube is the cube array after gridding and
       weight is the related weight array and final_fwhm is effective fwhm of the beam
       after the convolution.  Returns (None, None, None) on failure.
    """

    result = (None, None, None)

    # argument checking
    if len(spec.shape) != 2 or len(glon.shape) != 1 or len(glat.shape) != 1:
        if verbose > 1:
            print("data, sky coordinates have unexpected shapes")
            print("data : ", spec.shape)
            print("gLongitude : ", glon.shape)
            print("gLatitude : ", glat.shape)
        return result

    nspec, nchan_data = spec.shape

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
    weights[weights == 0] += 1e-16
    if weights.shape != spec.shape:
        if weights.shape[0] == spec.shape[0]:
            weight_array = weights[..., None] + np.zeros_like(spec) 
    else:
        weight_array = weights

    # Remove NaN and inf values from the data before gridding.
    if np.isnan(np.sum(spec)):
        weight_array[np.isnan(spec)] = 0
        spec = np.nan_to_num(spec)

    # Final spatial resolution.
    final_fwhm = np.sqrt(beam_fwhm ** 2.0 + gauss_fwhm ** 2.0)

    header = prepare_header(wcsObj, nx, ny, nchan_data)

    # Set up kernel parameters.
    gauss_sigma = gauss_fwhm / (2.0 * np.sqrt(2.0 * np.log(2.0)))
    if kernel_type == "gauss":
        kernel_type = "gauss1d"
        kernel_params = gauss_sigma
        # Resolution of the healpix lookup table.
        # Value recommended by Winkel et al. (2016)
        # for Gaussian beams.
        hpx_maxres = gauss_sigma / 5.0
        # Support distance for convolution,
        # same as v0.5 of the `gbtgridder`.
        support_distance = 3.0 * gauss_fwhm
    elif kernel_type == "gaussbessel":
        kernel_type = "gaussbessel"
        # Convolution function width for a Gaussian tapered Bessel
        # from Mangum, Emerson, Greisen (2007).
        kernel_params = (beam_fwhm / 3.0, 2.52, 1.55)
        hpx_maxres = pix_scale / 2.0 
        # Support distance for convolution.
        support_distance = 1.0 * beam_fwhm
    elif kernel_type == "nearest":
        # kernel_type = "gauss1d"
        # kernel_params = (gauss_sigma)
        # hpx_maxres = gauss_sigma / 5
        kernel_type = "gaussbessel"
        kernel_params = (beam_fwhm / 3.0, 2.52, 1.55)
        hpx_maxres = beam_fwhm / 3.0 / 2.0
        support_distance = 0.5 * pix_scale

    kernel_support = support_distance

    # Define a `cygrid.gridder` object and its kernel.
    mygridder = cygrid.WcsGrid(header, dtype=np.float64)
    mygridder.set_kernel(kernel_type, kernel_params, kernel_support, hpx_maxres)

    # Do the gridding.
    if verbose > 1:
        print("Running cygrid on the data")
    mygridder.grid(glon, glat, spec, weights=weight_array)

    # Query results.
    #data_cube = mygridder.get_datacube()
    data_cube = mygridder.get_unweighted_datacube()
    weights_cube = mygridder.get_weights()

    # Avoid division by invalid values.
    data_cube = np.ma.masked_invalid(data_cube)
    weights_cube = np.ma.masked_invalid(weights_cube)
    data_cube /= weights_cube

    data_cube = data_cube.filled(np.nan)
    weights_cube = weights_cube.filled(np.nan)

    # Remove pixels whose weight is too small,
    # as these have a much larger scale.
    #data_cube[abs(weights_cube)<1e-5] = np.nan

    return (data_cube, weights_cube, final_fwhm)

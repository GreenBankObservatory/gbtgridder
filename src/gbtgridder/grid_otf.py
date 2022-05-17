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

import multiprocessing as mp
import sys

import numpy as np
import sparse
from scipy.special import j1

# speed of light (m/s)
_C = 299792458.0
conv_weights = None
spec = None
glong = None
glong_axis = None
support_distance = None


def convolve(idx):
    return conv_weights.dot(spec[:, idx])


def eval_positions(lat):
    value = np.float32(glong_axis[lat, :, None]) - np.float32(glong)
    remove = (np.abs(value) > support_distance) + np.isnan(value)
    value[remove] = np.inf  # this makes the distance of the removed value infinity
    value = sparse.COO(value, fill_value=np.inf)
    return value


def grid_otf(
    spec_array,
    spec_size,
    nx,
    ny,
    glong_array,
    glong_calc,
    glat,
    wcsObj,
    pix_scale,
    refXsky,
    centerYsky,
    weight=None,
    beam_fwhm=None,
    kern="gaussbessel",
    _D=100,
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
       kern - specify the gridding kernel to use from "gaussbessel", "gauss", or "nearest".
              defaults to "gaussbessel"
       _D (diameter) - specifies the diameter (in meters) of the telescope used for the scans
               defaults to a float value of 100 (m), the size of GBT

    Returns: (cube, weight, beam_fwhm) where cube is the cube array after gridding and
       weight is the related weight array and beam_fwhm is effective fwhm of the beam
       after the convolution.  Returns (None, None, None) on failure.

    Original IDL credits to CLASS's xy_map, E. Rosolowsky
    Updated matrix calculation credits to Trey Wenger, DRAO
    """
    result = (None, None, None)
    global conv_weights
    global spec
    global glong_axis
    global glong
    global support_distance

    spec = spec_array  # to use the global casting
    glong = glong_array

    # argument checking
    if len(spec.shape) != 2 or len(glong.shape) != 1 or len(glat.shape) != 1:
        if verbose > 1:
            print("data, sky coordinates have unexpected shapes")
            print("data : ", spec.shape)
            print("gLongitude : ", glong.shape)
            print("gLatitude : ", glat.shape)
        return result

    nspec, nchan_data = spec.shape
    if nspec == 0 or nchan_data == 0:
        if verbose > 1:
            print("no data given")
        return result

    if nspec != len(glong) or nspec != len(glat):
        if verbose > 1:
            print(
                "Number of sky position values does not match number of spectra in data"
            )
        return result

    if kern not in ["gaussbessel", "gauss", "nearest"]:
        if verbose > 1:
            print("kern must be one of gaussbessel or gauss")
        return result

    ## wcs will only evaluate data that is broadcastable so we have to make wcsObj where nx==ny temporarily
    # if nx > ny:
    #    wcs_shape = nx
    # else:
    #    wcs_shape = ny
    ## make our shapes to feed to wcs
    # glong_shape = np.arange(wcs_shape, dtype=np.float32)  # + glong_start#*pix_scale)
    # glat_shape = np.arange(wcs_shape, dtype=np.float32)  # + glat_start#*pix_scale)
    # zeros_tmp = np.zeros(len(glong_shape))  # dummy axis
    ## use wcs to give us a correctly calculated position cube - accounts for things like mapcenter, projection, etc
    # glong_axis, glat_axis, tmp_1, tmp_2 = wcsObj.wcs_pix2world(
    #    glong_shape, glat_shape, zeros_tmp, zeros_tmp, 0
    # )
    glat_shape, glon_shape = np.mgrid[0:ny:1, 0:nx:1]
    glong_axis, glat_axis = wcsObj.celestial.all_pix2world(
        glon_shape.flatten(), glat_shape.flatten(), 0
    )
    # glong_axis = glong_axis.reshape(nx,ny)
    # glat_axis = glat_axis.reshape(nx,ny)

    ## shorten the smaller axis once we return the correct values
    # if ny > nx:
    #    glong_axis = glong_axis[
    #        0 : -1 * (wcs_shape - nx)
    #    ]  # remove size from both sides of glong_wcs
    # if nx > ny:
    #    glat_axis = glat_axis[
    #        0 : -1 * (wcs_shape - ny)
    #    ]  # remove size from both sides of glat_wcs
    ## account for the 0_360 axis
    # if np.nanmin(glong_axis) < 0:
    #    glong_axis = np.array([i + 360 if i < 0 else i for i in glong_axis])

    gauss_sigma = gauss_fwhm / (2.0 * np.sqrt(2.0 * np.log(2.0)))  # equivalent of 'b'
    # ie.       = 2.52*beam_fwhm/3.0
    final_fwhm = np.sqrt(
        beam_fwhm ** 2.0 + gauss_fwhm ** 2.0
    )  # verison0.5 equivialent of scale_fwhm*beam_fwhm

    # Get convolution Bessel function width (deg)
    ## from Mangum, Emerson, Greisen (2007)  #version0.5 equivialent of 'a'
    bessel_width = 1.55 * beam_fwhm / 3.0

    # Support distance for convolution
    support_distance = beam_fwhm

    # account for the 'pill box' kernel
    if kern == "nearest":
        support_distance = 1.0 * pix_scale  # one pixel

    # Generate spare matrix for the distance^2 between each
    # grid point and each data point.
    if verbose > 2:
        print("Generating sparse distance matrix...")
        sys.stdout.flush()

    # c = np.vstack((a,b[[None]])
    glong_pool = [None, None, None]
    glong_axis = glong_axis.reshape(ny, nx)
    num_cpus = mp.cpu_count()
    with mp.Pool(num_cpus) as pool:
        chunksize = ny // num_cpus + 1
        glong_pool = pool.map(eval_positions, range(ny), chunksize=chunksize)
        pool.close()
        pool.join()
    glong_diff = sparse.stack(glong_pool)
    # testing is nan and returns true or false # removing anything that is greater than the support dist
    # glong_diff = glong_diff.reshape(ny,nx,nspec)
    # makes sparse matrix of the difference - the fill value (values with 0) is infinity so the dist is too great
    glat_axis = glat_axis.reshape(ny, nx)[:, 0]
    glat_diff = np.float32(glat_axis[..., None]) - np.float32(glat)
    remove = (np.abs(glat_diff) > support_distance) + np.isnan(glat_diff)
    glat_diff[remove] = np.inf
    # glat_diff = glat_diff.reshape(ny,nx,nspec)
    glat_diff = sparse.COO(glat_diff, fill_value=np.inf)
    # image_distance2 = (
    #    glong_diff[:, None, :] ** 2.0 + glat_diff[None, :, :] ** 2.0
    # )  # long dist  squared plus glat dist squared is the size of the image we want
    # import ipdb;ipdb.set_trace()
    image_distance2 = glong_diff ** 2.0 + glat_diff[:, None, :] ** 2.0

    # Evaluate the Gaussian convolution weights at each data point
    if verbose > 2:
        print("Calculating convolution weights...")
    if kern == "gauss":
        if verbose > 2:
            print("Using Gaussian kernel")
        conv_weights = np.exp(-image_distance2 / (np.float32(2.0 * gauss_sigma ** 2.0)))
    elif kern == "gaussbessel":
        if verbose:
            print("Using Gaussian x Bessel kernel")
        # add small positive number to catch zeros in sparse matrix
        image_distance = np.sqrt(image_distance2) + np.float32(1.0e-32)
        conv_weights = j1(np.abs(image_distance) * np.float32(np.pi / bessel_width))
        # replace j1(np.inf) = np.nan with 0.0
        conv_weights.fill_value = np.array(0.0)
        conv_weights = conv_weights / (
            np.abs(image_distance) * np.float32(np.pi / bessel_width)
        )
        conv_weights = conv_weights * np.exp(
            -image_distance2 / (np.float32(2.0 * gauss_sigma ** 2.0))
        )
    else:
        conv_weights = image_distance2  # all inside the pill box have equal weight
        conv_weights.fill_value = np.array(0.0)  # replace np.nan with 0.0

    # ensure convolution weights are masked > support_distance
    conv_weights = conv_weights * (image_distance2 < support_distance ** 2.0)

    # Generate data weights, combine with convolution weights # Generate the weights image
    if verbose > 2:
        print("Calculating data weights...")
        sys.stdout.flush()
    data_weights = weight
    isnan = np.isnan(data_weights)
    data_weights[isnan] = 0.0
    conv_weights = conv_weights * data_weights
    # add spectral axis
    # sum_conv_weights = np.nansum(conv_weights, axis=-1).todense()[..., None]
    sum_conv_weights = np.nansum(conv_weights, axis=-1).todense()[None, ...]

    counterMax = "%d" % spec_size
    counterFormat = "Channel %%%dd out of %s" % (len(counterMax), counterMax)
    result = np.empty((spec_size, ny, nx))
    if verbose > 2:
        print("Convolving...")
        sys.stdout.flush()
    for index in range(spec_size):
        counterStr = counterFormat % (index + 1)
        sys.stdout.write("\r%s" % counterStr)
        sys.stdout.flush()
        # result[:, :, index - 1] = convolve(index - 1)
        result[index - 1, :, :] = convolve(index - 1)

    print("\n")  # just to make the outputs look nicer
    image_cube = np.array(result, dtype=np.float32)
    # image_cube = np.moveaxis(image_cube,0,-1)

    # Use np.divide to catch division by zero
    image_cube = np.divide(
        image_cube,
        sum_conv_weights,
        # out=np.ones((ny, nx, spec_size)) * np.nan,
        out=np.ones(result.shape) * np.nan,
        where=sum_conv_weights != 0.0,
    )

    return (image_cube, sum_conv_weights, final_fwhm)

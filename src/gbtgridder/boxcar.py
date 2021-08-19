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

import math

import numpy


def boxcar(dataArray, freqAxis, width):
    """Smooth all of the spectra in dataArray using a boxcar of the requested
    width.

    This uses numpy.convolve.  The returned array is decimated by taking only every
    width channels.

    input:
       dataArray: an (nspec, nchan) array, smoothing is along the channel axis
       freqAxis: the frequency values at each channel on nchan, assumed to be linear in freq
       width: the width of the boxcar

    output:
       The smoothed array, now with dimension (nspec,nchan/width)

    The edge effects could be better handled.

    Expects to work with sdfits data where the data type is float32
    """

    if dataArray.ndim != 2:
        raise ValueError("boxcar expected dataArray to have 2 dimensions")

    if dataArray.shape[1] < width:
        raise ValueError("width must be < number of channels")

    box = numpy.ones(width, "float32") / width
    nspec, nchan = dataArray.shape
    nout = nchan / width
    # we always loose the channel on the end, no matter what
    if width * nout == nchan:
        nout -= 1

    nout = math.ceil(nout)

    result = numpy.zeros((nspec, nout), "float32")
    for i in range(nspec):
        y = numpy.convolve(box, dataArray[i, :], mode="valid")
        # decimate and save
        result[i, :] = y[0:-1:width]

    # and the new frequency axis
    newFreqAxis = (
        freqAxis[0 : (nout * width) : width]
        + freqAxis[(width - 1) : (nout * width) : width]
    ) / 2.0

    return (result, newFreqAxis)

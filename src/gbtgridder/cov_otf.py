# Copyright (C) 2021 Associated Universities, Inc. Washington DC, USA.
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

import numpy as np
from matplotlib import pyplot as plt


def cov_otf(glong, glat, verbose=4):
    """Coverage map generated using nearest kernel See grid_otf.py for more
    infformation on the calculations / software This is designed to produce a
    coverage map for one channel of data.

    For support reach out to Kathlyn Purcell (kpurcell@nrao.edu)

    Returns: coverage_cube : where coverage_cube is the cube array after creating map
    """

    if verbose > 3:
        print("Generating your Coverage Map")

    glong = np.array(
        [i - 360 if i > 360 else i for i in glong]
    )  # make all the values over 360 positive
    if glong.max() > 359:
        glong = -np.array(
            [i - 360 if i > 180 else i for i in glong]
        )  # make any wrapped values negative to simulate origin (0-360)

    glong *= 10
    glat *= -10  # make the integers bigger to store them as indicies

    glong_neg = 0.0  # set defaults if there are no negative values
    glat_neg = 0.0
    if (
        glat.min() < 0
    ):  # if there are negative values, they need to be positive to support being an array index
        glat_neg = glat.min()
        glat -= glat.min()
    if glong.min() < 0:
        glong_neg = glong.min()
        glong -= glong.min()

    x_size = (
        int(glong.max()) - int(glong.min()) + 1
    )  # gather the size of the coverage map we are interested in
    y_size = (
        int(glat.max()) - int(glat.min()) + 1
    )  # the plus one is to store *all* the values of glong/glat since the index starts at 0

    image_cube = np.zeros(
        (y_size, x_size)
    )  # want a blank matrix of 0's of size glong x glat
    for i in range(len(glong)):  # eval every spec to calc coverage
        image_cube[int(glat[i]), int(glong[i])] += 1
    image_cube[
        image_cube == 0
    ] = np.nan  # zeros can now be nan to conserve computation time

    # plot the coverage map
    plt.imshow(
        (image_cube),
        extent=[
            -(glong.min() + glong_neg) / 10,
            -(glong.max() + glong_neg) / 10,
            -(glat.max() + glat_neg) / 10,
            -(glat.min() + glat_neg) / 10,
        ],
    )  # -9,7])
    plt.title("Coverage Map")
    plt.colorbar()
    plt.show()

    return image_cube

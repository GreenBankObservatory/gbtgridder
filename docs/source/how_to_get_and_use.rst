How to Get and Use GBTGridder_matrix
=====================================

***Note: anything in `*...*` needs to be replaced with what is relevant to you and your project***
This tutorial assumes little is known about navigating a terminal

1.  To get the gridder

.. code-block:: bash

    # In a fresh shell
    alias python=/home/gbors/bin/python3.8
    # Then do the below
    git clone https://github.com/GreenBankObservatory/gbtgridder
    cd gbtgridder
    git checkout refactor-dev
    python -m venv .venv
    source .venv/bin/activate
    # Not required, but recommended
    pip install -U pip setuptools wheel build
    pip install -r requirements-dev.txt

2.  For more info on the gridder run the command `$ gbtgridder`

    - this will give you information on what arguments to use and how to use them

    * see appendix for the full printout

    - this command will also show the version of the gridder you are using

    * currently it is `version 1.0`


3.  To run the gridder

- ex. `$ gbtgridder_matrix --noline --noweight --nocont -o *output file name* --pixelwidth 105.0 --mapcenter 2.0 3.0 -a 70 -k gaussbessel --size 962 860 --channels "2300:2480" ./*fits file.fits* --verbose 5`

.. code-block:: bash

   channelString (2300:2480)
   Loading data ...
   	./14B_076_2_edit_shifted.fits

- Once it reads in the fits header data it will display several crucial parameters and prompt you if you'd like to continue.

.. code-block:: bash

   	 outname root :  14B_076_2_edit_shifted_
   	 clobber :  False
   Data summary ...
      scans :  717:726,728:732,734:751,753:784,809:816,818:824,1306:1324,1327:1331,1334:1335,1407:1445,1447:1452,1506:1538,1540:1559,1610:1613,1706:1728,1730:1736,1738:1743,1745:1748,1750:1762,1806:1814,1816:1822,1824:1831,1833:1840,1906:1961,2007:2062,2106:2162,2201:2219,2305:2321,2410:2435,2437:2452,2454:2461,2505:2530,2532:2536,2607:2642,2707:2780,2807:2891,2907:2927,2929:2967
      channels : 2299:2479
      no tsys selection
      spectra to grid :  107429

    Map info ...
      beam_fwhm :  0.1451149459394181 ( 522.4138053819051  arcsec)
      pix_scale :  0.029166666666666667 ( 105.0  arcsec)
     gauss fwhm :  0.08054407825984171 ( 289.95868173543016  arcsec)
   	   xsize :  962
   	   ysize :  860
   		  f0 :  1420388838.4948816
   	delta(f) :  -100141.86655688286
     num. chan  :  2
   	  source :  G03+4.0    STCOR
    frest (MHz) :  1420.4058


    Your parameters were either user specified or assumed to be the following. Please reveiw:

   Name          Value
   --------      ---------
   Kernel        gaussbessel
   Telescope     GBT
   Projected     SFL
   Input Chan.   2299:2479
   # avg'd chan. 2
   # of spec.    107429
   Image size    962x860

    If you need more info, type 'N' and run again with `--verbose 4` flag

    Would you like to continue with these parameters?
    'Y' for yes, 'N' for no.


- When it is done it will write your .fits files. The output for example above is only cube, so an example of the output when the gridding is complete is

.. code-block:: bash

    Would you like to continue with these parameters?
     'Y' for yes, 'N' for no.
    Y


     Gridding
    Generating sparse distance matrix...
    Calculating convolution weights...
    Using Gaussian x Bessel kernel
    Calculating data weights...
    Convolving...
    Channel 2 out of 2

    Writing cube
    Runtime: 0.9 minutes




4.  Reviewing the output files

In the above example, only cube output was specified so the output file is only `*file output name*_cube.fits`. We want to look at this data
        1.  Open casaviewer using `casaviewer`
        2.  Select your file
        3.  Select the appropriate file type - mine was 'raster'
        4.  You will now see you image - Congrats!
        5.  Below are more tips on using casaviewer


CasaViewer Tips and Tricks
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The menu bar above the image can be clicked by the three mouse buttons (right,left and scroll) to change the hotkeys and manipulate the image

- zoom magnifying glass is the zoom in
    - to use select a square and double click to zoom there
    - on the row above, use the magnifying glass with a four corners box to cancel the zoom
- dot in a box lets you select a point on the image
    - click the graph with a broken line in the list above
    - it opens a spectra window where you can compare the z axis (color axis) as a function of the channels in that cell
- use the blue buttons to the right to cycle through the channels
- the wrench is the data display tab
    - if you are seeing a solid color image then use the data display tab to change the 'data range' field to something like `[0,100]` or `[0,1]` to reduce the effect of the edge effects and see your data clearly



Appendix
~~~~~~~~~

Printout for `gbtgridder_matrix`
++++++++++++++++++++++++++++++++

.. code-block:: bash

    (gbtgridder-venv-3.8.5) [kpurcell@belinda /home/sandboxes/kpurcell/repos/gbtgridder/gbtgridder/src]$ gbtgridder_matrix
    usage: gbtgridder_matrix3_8.py [-h] [-c CHANNELS] [-a AVERAGE] [-s SCANS] [-m MAXTSYS] [-z MINTSYS] [--clobber] [-k {gauss,gaussbessel,nearest}] [--diameter DIAMETER] [-o OUTPUT] [--mapcenter LONG LAT]
                                   [--size X Y] [--pixelwidth PIXELWIDTH] [--restfreq RESTFREQ] [-p {SFL,TAN}] [--clonecube CLONECUBE] [--noweight] [--noline] [--nocont] [-v VERBOSE] [-V]
                                   SDFITSfiles [SDFITSfiles ...]

    positional arguments:
      SDFITSfiles           The calibrated SDFITS files to use.

    optional arguments:
      -h, --help            show this help message and exit
      -c CHANNELS, --channels CHANNELS
                            Optional channel range to use. '<start>:<end>' counting from 0.
      -a AVERAGE, --average AVERAGE
                            Optionally average channels, keeping only number of channels/naverage channels
      -s SCANS, --scans SCANS
                            Only use data from these scans. comma separated list or <start>:<end> range syntax or combination of both
      -m MAXTSYS, --maxtsys MAXTSYS
                            max Tsys value to use
      -z MINTSYS, --mintsys MINTSYS
                            min Tsys value to use
      --clobber             Overwrites existing output files if set.
      -k {gauss,gaussbessel,nearest}, --kernel {gauss,gaussbessel,nearest}
                            gridding kernel, default is gauss
      --diameter DIAMETER   Diameter of the telescope the observations were taken on.
      -o OUTPUT, --output OUTPUT
                            root output name, instead of source and rest frequency
      --mapcenter LONG LAT  Map center in longitude and latitude of coordinate type used in data (RA/DEC, Galactic, etc) (degrees)
      --size X Y            Image X,Y size (pixels)
      --pixelwidth PIXELWIDTH
                            Image pixel width on sky (arcsec)
      --restfreq RESTFREQ   Rest frequency (MHz)
      -p {SFL,TAN}, --proj {SFL,TAN}
                            Projection to use for the spatial axes, default is SFL
      --clonecube CLONECUBE
                            A FITS cube to use to set the image size and WCS parameters in the spatial dimensions. The cube must have the same axes produced here, the spatial axes must be of the same type as found
                            in the data to be gridded, and the projection used in the cube must be either TAN, SFL, or GLS [which is equivalent to SFL]. Default is to construct the output cube using values
                            appropriate for gridding all of the input data. Use of --clonecube overrides any use of --size, --pixelwidth, --mapcenter and --proj arguments.
      --noweight            Set this to turn off production of the output weight cube
      --noline              Set this to turn off prodution of the output line cube
      --nocont              Set this to turn off prodution of the output 'cont' image
      -v VERBOSE, --verbose VERBOSE
                            set the verbosity level-- 0-1:none, 2:errors only, 3:+warnings, 4(default):+user info, 5:+debug
      -V, --version         show program's version number and exit

    gbtgridder version: 1.0

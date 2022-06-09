How to Get and Use the GBTGridder-test
=====================================

***Note: anything in `<*...*>` needs to be replaced with what is relevant to you and your project***
This tutorial assumes little is known about navigating a terminal

1.  To get the gridder

.. code-block:: bash

    # Then do the below
    git clone https://github.com/GreenBankObservatory/gbtgridder.git
    cd gbtgridder
    # get onto the v1.0 branch
    git checkout cygrid_dev
    # make and source a new venv
    ~gbosdd/pythonversions/3.8/bin/python -m venv <path/vevnName>
    source <path/vevnName>/bin/activate
    pip install -U pip setuptools wheel build
    pip install -r requirements.txt
    pip install -e .

2.  For more info on the gridder run the command `$ gbtgridder-test --help`

    - this will give you information on what arguments to use and how to use them

    * see appendix for the full printout

    - this command will also show the version of the gridder you are using

    * currently it is `version 1.0`


3.  To run the gridder

- ex. `$ gbtgridder-test --noweight -o my_first_gbtgrid ./test/unit_tests/test.fits --verbose 6`

.. code-block:: bash

  Collecting arguments and data...
  Loading data ...
      ./test/unit_tests/test.fits
  outname root :  my_first_gbtgrid_
       clobber :  False
  Data Extracted Successfully.


- Once it reads in the fits header data it will display several crucial parameters and prompt you if you'd like to continue.

.. code-block:: bash

Collecting arguments and data...
Loading data ...
    ./test/unit_tests/test.fits
outname root :  my_first_gbtgrid_
     clobber :  True
existing my_first_gbtgrid_cube.fits removed
Data Extracted Successfully.
Data summary ...
   scans :  1937:1970
   channels : 0:449
   no tsys selection
   spectra to grid :  4692

 Map info ...
   beam_fwhm :  0.1451038186298307 ( 522.3737470673906  arcsec)
   pix_scale :  0.0483679395432769 ( 174.12458235579686  arcsec)
  gauss fwhm :  0.08053790219790387 ( 289.93644791245396  arcsec)
    ref Xsky :  350.99805555555554 (if negative then add 360)
    ref Ysky :  0.0
 center Ysky :  6.998333333333333
       xsize :  43
       ysize :  43
    ref Xpix :  21.5
    ref Ypix :  -122.18950712840723
          f0 :  1423726423.8457916
    delta(f) :  -14306.012469291687
  num. chan  :  450
      source :  G351.0+7.0 STCOR
 frest (MHz) :  1420.4058


 Your parameters were either user specified or assumed to be the following. Please review:

Name          Value
--------      ---------
Kernel        gauss
Telescope     GBT
Projection    SFL
Input Chan.   0:449
# Output Chan. 450
# of spec.    4692
Image size    43x43

 If you need more info, type 'N' and run again with `--verbose 4` flag

 Would you like to continue with these parameters?
 'Y' for yes, 'N' for no.


- When it is done it will write your .fits files. The output for example above is only cube, so an example of the output when the gridding is complete is

.. code-block:: bash

   Would you like to continue with these parameters?
   'Y' for yes, 'N' for no.
  Y


   Gridding
  Reshaping weights
  Running cygrid on the data
  Writing cube
  Runtime: 0.1 minutes


4.  Reviewing the output files

In the above example, only cube output was specified, so the output file is only `my_first_gbtgrid_cube.fits`. We want to look at this data
        1.  Open casaviewer using `$ casaviewer`
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

Printout for `gbtgridder-test`
++++++++++++++++++++++++++++++++

.. code-block:: bash

  $ gbtgridder-test --help
  usage: gbtgridder [-h] [-c CHANNELS] [-a AVERAGE] [-s SCANS] [-m MAXTSYS] [-z MINTSYS] [--clobber] [-k {gauss,gaussbessel,nearest}] [--diameter DIAMETER] [-o OUTPUT] [--mapcenter LONG LAT] [--size X Y] [--pixelwidth PIXELWIDTH]
                    [--beam_fwhm BEAM_FWHM] [--restfreq RESTFREQ] [-p {SFL,TAN}] [--clonecube CLONECUBE] [--autoConfirm] [--noweight] [-v VERBOSE] [-V]
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
    --beam_fwhm BEAM_FWHM
                          Specify the BEAM_FWHM (HPBW) value, default calculated per telscope diameter
    --restfreq RESTFREQ   Rest frequency (MHz)
    -p {SFL,TAN}, --proj {SFL,TAN}
                          Projection to use for the spatial axes, default is SFL
    --clonecube CLONECUBE
                          A FITS cube to use to set the image size and WCS parameters in the spatial dimensions. The cube must have the same axes produced here, the spatial axes must be of the same type as found in the data to be gridded,
                          and the projection used in the cube must be either TAN, SFL, or GLS [which is equivalent to SFL]. Default is to construct the output cube using values appropriate for gridding all of the input data. Use of
                          --clonecube overrides any use of --size, --pixelwidth, --mapcenter and --proj arguments.
    --autoConfirm         Set this to True if you'd like to auto-confirm the program stop and move straight into gridding
    --noweight            Set this to turn off production of the output weight cube
    -v VERBOSE, --verbose VERBOSE
                          set the verbosity level-- 0-1:none, 2:errors only, 3:+warnings, 4(default):+user info, 5:+debug
    -V, --version         show program's version number and exit

  gbtgridder version: 1.0

# gbtgridder

A stand-alone spectral gridder and imager for the Green Bank Telescope

## Installation

### General user
We recommend installing the `gbtgridder` in a separate virtual environment to avoid conflicts with other packages.
```bash
python -m pip install "gbtgridder @ git+https://github.com/GreenBankObservatory/gbtgridder@release_3.0"
```

### GB dev
Will currently only work within the GBO network, after configuring to use the private PyPI repo
```bash
pip install gbtgridder
```

## Usage

***Note: anything in `<*...*>` needs to be replaced with what is relevant to you and your project***

1. To grid a series of SDFITS files and save the outputs to my\_filename
```bash
gbtgridder -o <*my_filename*> <*input_sdfits_files*>
```
This will generate two files, my\_filename\_cube.fits and my\_filename\_weight.fits. 
The \_cube.fits file is the spectral line cube, and the \_weight.fits file is a cube with the weight used during the gridding.

2.  To see the available options, and the version of the `gbtgridder` being used (currently 3.0): 
```bash
gbtgridder --help
```
The full printout is available in the [appendix](#appendix).

### Example

Run the gridder without outputting a weight cube and with the highest level of verbosity. This will grid the data in `./test/integration_tests/test.fits`.

- `gbtgridder --noweight -o my_first_grid ./test/integration_tests/test.fits --verbose 5`

```bash
    Collecting arguments and data...
    Loading data ...
        ./test/unit_tests/test.fits
    outname root :  my_first_grid_
         clobber :  False
```

- Once it reads in the FITS header data it will display several crucial parameters and prompt you if you'd like to continue.

```bash
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

```

- When it is done it will write your FITS files. The output for this example is only a cube, so the output when the gridding is complete is

```bash
 Would you like to continue with these parameters?
 'Y' for yes, 'N' for no.
y


 Gridding
Reshaping weights
Running cygrid on the data
Writing cube
Runtime: 0.1 minutes
```

This will write a FITS cube called my\_first\_grid\_cube.fits.

### Viewing the output files

The outputs from the `gbtgridder` are FITS cubes that should be compatible with most FITS image viewers 
(e.g., <a href="https://casa.nrao.edu/UserMan/UserManch7.html" target="_blank">`casaviewer`</a>
or
<a href="https://sites.google.com/cfa.harvard.edu/saoimageds9" target="_blank">`SAOImageDS9`</a>)

In the above example, only cube output was specified, so the output file is only my\_first\_grid\_cube.fits. We want to look at this data
1.  Open casaviewer using `casaviewer`
2.  Select your file
3.  Select the appropriate file type
4.  You will now see you image - Congrats!
5.  Below are more tips on using casaviewer


* * *
* * *


## Testing
There are both unit and integration tests available through pytest. To run either go to the root of the repo and run
```bash
    RunAll[Unit,Integration]Tests
```
Please feel free to use the provided SDFITS files to compare to any other version of a gridder to determine the gbtgridder-test's accuracy

* * *
* * *


## CasaViewer Tips and Tricks

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


* * *
* * *

# <a name="#appendix"></a>Appendix


## Printout for `gbtgridder --help`


```bash
(gbtgridder_venv_py38) [kpurcell@belinda /home/sandboxes/kpurcell/gbtgridder]$ gbtgridder-test --help
usage: gbtgridder [-h] [-c CHANNELS] [-a AVERAGE] [-s SCANS] [-m MAXTSYS] [-z MINTSYS] [--clobber] [-k {gauss,gaussbessel,nearest}] [--diameter DIAMETER] [-o OUTPUT] [--mapcenter LONG LAT]
                  [--size X Y] [--pixelwidth PIXELWIDTH] [--beam_fwhm BEAM_FWHM] [--restfreq RESTFREQ] [-p {SFL,TAN}] [--clonecube CLONECUBE] [--autoConfirm] [--noweight] [-v VERBOSE] [-V]
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
                        A FITS cube to use to set the image size and WCS parameters in the spatial dimensions. The cube must have the same axes produced here, the spatial axes must be of
                        the same type as found in the data to be gridded, and the projection used in the cube must be either TAN, SFL, or GLS [which is equivalent to SFL]. Default is to
                        construct the output cube using values appropriate for gridding all of the input data. Use of --clonecube overrides any use of --size, --pixelwidth, --mapcenter and
                        --proj arguments.
  --autoConfirm         Set this to True if you'd like to auto-confirm the program stop and move straight into gridding
  --noweight            Set this to turn off production of the output weight cube
  -v VERBOSE, --verbose VERBOSE
                        set the verbosity level-- 0-1:none, 2:errors only, 3:+warnings, 4(default):+user info, 5:+debug
  -V, --version         show program's version number and exit

gbtgridder version: 3.0

```

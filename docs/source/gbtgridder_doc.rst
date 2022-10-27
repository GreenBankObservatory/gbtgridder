GBTGridder-test Docs
======================================

**For what:** GBTGridder Version 2.0, cygrid version

**Based On:** GBTGridder Version 0.5 https://github.com/GreenBankObservatory/gbtgridder branch: `release_1.0`

**Where:** https://github.com/GreenBankObservatory/gbtgridder branch: `master`

**Tested using:** https://safe.nrao.edu/wiki/bin/view/GB/Software/Testing_MatrixGridder

**Science Advisors:** Jay Lockman and Pedro Salas,
**Cygrid Author:** Benjamin Winkel,
**GBTGridder/Cygrid Version Author:** Kasey Purcell ([kpurcell@nrao.edu]), and Pedro Salas


Important Links/Information
~~~~~~~~~~~~~~~~~~~~~~~~~~~

CasaViewer
+++++++++++

[https://casa.nrao.edu/casadocs/casa-5.4.1/image-cube-visualization/viewer-basics]


SDGridder
++++++++++
[https://github.com/tvwenger/sdgridder]

Cygrid
+++++++++
[https://github.com/bwinkel/cygrid]

Testing
+++++++++++++
There are both unit and integration tests available through pytest. To run either go to the root of the repo and run `RunAll[Unit,Integration]Tests`
Please feel free to use the provided sdfits files to compare to any other version of a gridder to determine the gbtgridder's accuracy


Running Each
+++++++++++++

.. code-block:: bash

    # all arguments should be specific to the project, many more are also available
    # use `gbtgridder --help` to learn more
    gbtgridder[-original] --noweight [--nocont --noline] -o my_first_gbtgrid ./test/unit_tests/test.fits

What to expect from (original) gbtgridder
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. code-block:: bash

    $ gbtgridder-original --noweight --nocont --noline -o my_first_gbtgrid ./test/unit_tests/test.fits --verbose 6
    System seems to be running RHEL7
    Loading data ...
        ./test/unit_tests/test.fits
    WARNING: ErfaWarning: ERFA function "dtf2d" yielded 4692 of "dubious year (Note 6)" [astropy._erfa.core]
    outname root :  my_first_gbtgrid_
         clobber :  False
    Data summary ...
       scans :  1937:1970
       channels : 0:449
       no tsys selection
       spectra to grid :  4692

    Map info ...
       beam_fwhm :  0.14510381863 ( 522.373747067  arcsec)
       pix_scale :  0.0244444444444 ( 88.0  arcsec)
      gauss fwhm :  0.0610327433068 ( 219.717875905  arcsec)
        ref Xsky :  350.998055556
        ref Ysky :  0.0
     center Ysky :  6.99833333333
           xsize :  111
           ysize :  119
        ref Xpix :  55.5
        ref Ypix :  -225.795454545
              f0 :  1423726423.85
        delta(f) :  -14306.0124693
          nchan  :  450
          source :  G351.0+7.0 STCOR
     frest (MHz) :  1420.4058
    Gridding
    Row 111 out of 111
    Writing cube


What to expect from (new) gbtgridder-test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    $ gbtgridder --noweight -o my_first_gbtgrid ./test/unit_tests/test.fits --verbose 6 --autoConfirm

    Collecting arguments and data...
    Loading data ...
        ./test/unit_tests/test.fits
    outname root :  my_first_gbtgrid_
         clobber :  False
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


     Gridding
    Reshaping weights
    Running cygrid on the data
    Writing cube
    Runtime: 0.1 minutes

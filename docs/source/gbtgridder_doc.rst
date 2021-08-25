GBTGridder_Matrix Docs (In dev stage)
======================================

**For what:** GBTGridder Version 1.0, matrix version

**Based On:** GBTGridder Version 0.5 https://github.com/GreenBankObservatory/gbtgridder branch: `master`

**Where:** https://github.com/GreenBankObservatory/gbtgridder branch: `refactor-dev`

**Tested using:** `14B_076_2_edit_shifted.fits` and `14A_302+14B_461_edit_v2_shifted.fits` + `15B_139_edit_v2_shifted.fits`

**Authors:
Science Advisor:** Jay Lockman,
**Matrix Version Author:** Trey Wenger,
**GBTGridder/Matrix Version Author:** Kasey Purcell ([kpurcell@nrao.edu])


Important Links/Information
~~~~~~~~~~~~~~~~~~~~~~~~~~~

CasaViewer
+++++++++++

[https://casa.nrao.edu/casadocs/casa-5.4.1/image-cube-visualization/viewer-basics]


SDGridder
++++++++++
[https://github.com/tvwenger/sdgridder]



Running Each
+++++++++++++

.. code-block:: bash

    gbtgridder<_matrix> --noline --noweight --nocont -o 14B_076_2_edit_shifted --pixelwidth 105.0 --size 926 860 --mapcenter 2.0 3.0 -a 70 -k gaussbessel --channels '2300:2480' 14B_076_2_edit_shifted.fits

What to expect from original gridder
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. code-block:: bash

    (gridder-venv) [kpurcell@belinda /home/sandboxes/kpurcell/repos/gbtgridder/gbtgridder/src]$ gbtgridder --noline --noweight --nocont -o 14B_076_2_edit_shifted --pixelwidth 105.0 --size 926 860 --mapcenter 2.0 3.0 -a 70 -k gaussbessel --channels '2300:2480' 14B_076_2_edit_shifted.fits --verbose 5

    System seems to be running RHEL7
    channelString (2300:2480)
    Loading data ...
        14B_076_2_edit_shifted.fits
    outname root :  14B_076_2_edit_shifted_
         clobber :  False
    Data summary ...
       scans :  717:726,728:732,734:751,753:784,809:816,818:824,1306:1324,1327:1331,1334:1335,1407:1445,1447:1452,1506:1538,1540:1559,1610:1613,1706:1728,1730:1736,1738:1743,1745:1748,1750:1762,1806:1814,1816:1822,1824:1831,1833:1840,1906:1961,2007:2062,2106:2162,2201:2219,2305:2321,2410:2435,2437:2452,2454:2461,2505:2530,2532:2536,2607:2642,2707:2780,2807:2891,2907:2927,2929:2967
       channels : 2299:2479
       no tsys selection
       spectra to grid :  107429

    Map info ...
       beam_fwhm :  0.145121794593 ( 522.438460536  arcsec)
       pix_scale :  0.0291666666667 ( 105.0  arcsec)
      gauss fwhm :  0.0728231596274 ( 262.163374659  arcsec)
        ref Xsky :  2.0
        ref Ysky :  0.0
     center Ysky :  3.0
           xsize :  926
           ysize :  860
        ref Xpix :  463.0
        ref Ypix :  328.142857143
              f0 :  1420388838.49
        delta(f) :  -100141.866557
          nchan  :  2
          source :  G03+4.0    STCOR
     frest (MHz) :  1420.4058
    Gridding
    Row   4 out of 926


What to expect from the new matrix gbtgridder
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    $ gbtgridder_matrix --noline --noweight --nocont -o 14B_076_2_edit_shifted --pixelwidth 105.0 --mapcenter 2.0 3.0 -a 70 -k gaussbessel --size 926 860 --channels "2300:2480" ./14B_076_2_edit_shifted.fits --verbose 5

    channelString (2300:2480)
    Loading data ...
        ./14B_076_2_edit_shifted.fits
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


     Your parameters were either user specified or assumed to be the following. Please review:

    Name          Value
    --------      ---------
    Kernel        gaussbessel
    Telescope     GBT
    Projection       SFL
    Input Channels      2299:2479
    # avg'd chan. 2
    # of spec.    107429
    Image size    962x860

     If you need more info, type 'N' and run again with `--verbose 4` flag

     Would you like to continue with these parameters?
     'Y' for yes, 'N' for no.
    y


     Gridding
    Generating sparse distance matrix...
    Calculating convolution weights...
    Using Gaussian x Bessel kernel
    Calculating data weights...
    Convolving...
    Channel 2 out of 2

    Writing cube
    Runtime: 1.4 minutes

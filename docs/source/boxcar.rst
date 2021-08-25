What is `boxcar.py`
========================

This is a function that will take into account the average argument (if it is used), and convolve the data using a boxcar method to smooth the frequency axis. This method is called in `get_data.py`

Resources
----------
https://chem.libretexts.org/Bookshelves/Analytical_Chemistry/Supplemental_Modules_(Analytical_Chemistry)/Analytical_Sciences_Digital_Library/JASDL/Courseware/Introduction_to_Signals_and_Noise/04_Signal-to-Noise_Enhancement/03_Digital_Filtering/03_Boxcar_Averaging

What does boxcar do to the data and frequency axis?
-----------------------------------------------------------
The data is evaluated as a boxcar, this means for the data it is divided up into 'boxes' of size 'average' and those chucks of data are convolved with the box variable itself (which a array of values of size 'average' and of value 1/average). This results in a average of the values in the 'box of data'. These boxes add up to create an array of size `original_data/average_value`. I.e. if the channel range is of size 181 and the average argument is 70, then the output channel range of the boxcar will be 2.
This does a similar idea with the frequency axis, but executed differently. Here the first and last value of the 'box' will be accounted for and averaged over 2. This can repeat for as many times as necessary.


Software
---------

Input
+++++

dataArray - this is the data - it comes from the fits file and is the 'data' value

freqAxis - the frequency axis - this axis' length is equvalent to the number of channels

width - the average - this is given in the command line arguments

Output
++++++

result - this is the new data value array with the adapted length depending on `nout`

newFreqAxis - this is the potentially averaged, and smoothed frequency axis depeding on the `nout` value

Notable Others
+++++++++++++++

nchan - number of channels

nspec - number of spectra in each channel

nout - number of channels after averaging

box - the approperatly sized boxcar for smoothing based on the average parameter

y - the boxcar convolved array involving the boxcar and the data

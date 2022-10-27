What is `get_data.py`
======================


This function accesses the fits header for declaration in the [gbtgridder.py](http://gbtgridder.py) file. This function populates the dict `result`. The `gbtgridder.py` file initiates the `get_data` function as `dataRecord` and polls certain fields to access and use fits values for gridding. `get_data` also manipulates a few fits values to make them suitable fro gridding before adding them to the `results` dict. Some of these manipulations are described below.

Special Manipulations
----------------------

**result\["freq"\]**

    This is the frequency axis and is cast as `faxis` in the gbtgridder function. There is special manipulations to this value in order to account for doppler shift `numpy.sqrt((1.0+beta)/(1.0-beta))`

**result\["wt"\]**

    This is a value based on tsys (temperature of the system) and tint (integration time) `numpy.nan_to_num(texp/(relTsys*relTsys))`. Can be set to all equal weigths at 1 with the flag `--equalweights`

**result\['specsys'\]**

    This value is set through a dict of strings based on the `dopframe` value. Reference the `specSysDict` table (211:get_data.py) for more info on this conversion.

**boxcar, average, result['data']**

    This is due to the presence of the average (-a) argument. See 'What is the boxcar' for more info:

.. todo:: Add boxcar link

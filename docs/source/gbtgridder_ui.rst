GBTGridder UI (dev stage)
=========================

What is this?
--------------

It is a user interface for the gbtgridder program.

Why do you care?
-----------------

This ui can help users to understand the full capability of the gbtgridder and thus allow it to be used to its full capacity.
There is currently very little documentation and general knowledge of the gbtgridder, this ui helps to minimize that.
This will hopefully help with understanding what the gridder is and what it is used for.

Key features of the gbtgridder ui
----------------------------------

1.  All arguments are displayed

    - many users do not know the full argument capability of the gridder and fewer still know what each arguments can be used for.

    - The boxes for the arguments not only allow the user to see what are available, but they also serve to be a guide to only allow correct declaration of each argument, ex. kernels are limited to the three options in the combo-box.

2.  Help hover/message box for each of the arguments

    - on top of having each argument laid out, the help banners allow the user to see what each of the argument can do for their project - hover over any widget to see the help message

3.  Save/ Load functions

    - When the user develops their preferred arguments they can save the configuration and re-load it at a later date using the configuration UI

4.  GBTGridder 'grid' button

    - the user can run the gridder directly in the ui and see the command line output exactly as they would see running it outside the ui

    - if the user doesn't want to grid in the ui they can still benefit. There is a arguments string that is displayed in the main window of the ui that can be copy/pasted into the standard command line (while being cognizant of the paths and file names)

How to use the gridder ui (dev phase as of 08/24/2021)
---------------------------------------------------------------

1.  Run these commands

.. code-block:: bash

    source /home/sandboxes/kpurcell/repos/gbtgridder/gbtgridder_dev/src/kc-gridder-venv/bin/activate
    python3 /home/sandboxes/kpurcell/repos/gbtgridder/gbtgridder_dev/src/ui/gridder_idea.py


This will run the ui window. Keep in mind input and output files are relative to where you are running from. I recommend specifying the entire file path when using these values to avoid any confusion, but it is not necessary.

Feel free to poke around with that in mind and let me know if any errors occur or if you have any suggestions :)

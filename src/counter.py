# Print a progress status to the screen on a single line.
# infostring ignored for percent usage

import sys
import time

def counter(num, outof, infostring=None, wait_time=None, percent=None):
    if infostring is None:
        infostring = 'Number '

    if percent:
        outstr = "%s%3d%% completed" % (infostring,round(float(num)*100./outof))
    else:
        strOutOf = "%d" % outof
        frmt = "%s%%%dd out of %s" % (infostring,len(strOutOf),strOutOf)
        outstr = frmt % num

    sys.stdout.write("\r%s" % outstr)
    sys.stdout.flush()
    
    if wait_time is not None:
        time.sleep(wait_time)

#!/bin/env python

from ui import ui
from tftp import tftp
from images import images
from targets import targets
from plans import plans
from model import model
from controller import controller

def main(): # FIXME: we'll have command line arguments later
    mytftp = tftp(None, 69, False)
    myimages = images()
    mytargets = targets()
    myplans = plans()
    mymodel = model(mytftp, myimages, mytargets, myplans)
    mycontroller = controller(mymodel)
    myui = ui(mycontroller)

    myui.display_mainmenu()

if __name__ == '__main__':
    main()

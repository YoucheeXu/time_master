#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import sys
import os

from pyutilities.logit import pv, po
from time_manger_app import TimeMangerApp


def main():
    projpath = os.path.dirname(os.path.abspath(__file__))
    if getattr(sys, 'frozen', False):
        projpath = os.path.dirname(os.path.abspath(sys.executable))
    projpath = os.path.abspath(os.path.join(projpath, ".."))
    pv(projpath)
    xmlfile = os.path.join(projpath, 'resources', 'time_manager.xml')
    dbfile = os.path.join(projpath, "data", "my.db")
    app = TimeMangerApp(projpath, xmlfile,dbfile)
    app.run()
    app.close()


if __name__ == "__main__":
    main()

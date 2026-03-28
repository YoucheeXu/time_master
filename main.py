#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import sys
import os

from pyutilities.logit import pv, po, pe
from src.time_master import TimeMasterApp


def main():
    if getattr(sys, 'frozen', False):
        file_path = os.path.dirname(os.path.abspath(sys.executable))
    else:
        file_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(file_path, "public")
    proj_path = os.path.abspath(os.path.join(file_path, "."))
    xml_file = os.path.join(proj_path, 'resources', 'time_master.xml')
    app = TimeMasterApp(proj_path, xml_file)
    cfg_file = os.path.join(proj_path, "TimeMaster.json")
    app.open(cfg_file)
    app.run()
    app.close()


if __name__ == "__main__":
    main()

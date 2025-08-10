#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import sys
import os

from pyutilities.logit import pv, po
from time_master_app import TimeMasterApp


def main():
    file_path = os.path.dirname(os.path.abspath(__file__))
    if getattr(sys, 'frozen', False):
        file_path = os.path.dirname(os.path.abspath(sys.executable))
    proj_path = os.path.abspath(os.path.join(file_path, ".."))
    xml_file = os.path.join(proj_path, 'resources', 'time_master.xml')
    usr_path = os.path.join(proj_path, "data", "Youchee")
    app = TimeMasterApp(proj_path, xml_file)
    app.open_user(usr_path)
    app.run()
    app.close()


if __name__ == "__main__":
    main()

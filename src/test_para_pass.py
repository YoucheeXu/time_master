#!/usr/bin/python3
# -*- coding: UTF-8 -*-
from typing import cast

from pyutilities.logit import pv, po
from item_type import HourSqlTuple, HourDict, Hour, HourSqlRecord, HourRecordTuple


def get_hourdetail(iid: int, detail: HourDict):
    if iid == 3:
        detail["name"] = 'Listen'
        detail["rid"] = (3, 5)
        detail["clock"] = ""
        detail["schedule"] = '计划每日45m'
        detail["sums"] = 30
        detail["father"] = 2


def process_message(idmsg: str, **kwargs: object):
    if idmsg == "GetHourDetail":
        iid = cast(int, kwargs["id"])
        detail = cast(HourDict, kwargs["detail"])
        get_hourdetail(iid, detail)
        return True

def get_hourdetail2(iid: int):
    detail: HourDict = {"name": "", "rid": (0, 0), "clock": "", "schedule": "",
        "sums": 0, "father": -1}
    _ = process_message("GetHourDetail", id=iid, detail=detail)
    return detail


def main():
    detail = get_hourdetail2(3)
    pv(detail)


if __name__ == "__main__":
    main()

#!/usr/bin/python3
# -*- coding: UTF-8 -*-
"""
    set PYTHONPATH=..\time_master
    uv run .\\tools\\update_datebase.py .\\data\\Youchee\\hours0.db
"""
import os
import sys
from pathlib import Path
import sqlite3
import datetime
import re
from typing import TypedDict, cast

# from pyutilities.sqlite import SQLite
from pyutilities.logit import po, pv, pe

from src.hour_type import HourSqlTuple, HourSqlRecord
from src.time_database_type import IconTuple
from src.time_database_type import TimeUnit, DayType, default_reminder_data
from src.time_database_type import default_plan_data, default_record_data
from src.time_database_type import str2time
from src.time_database import TimeDatabase


class HourSqlDict(TypedDict):
    """ Database storage type of the hour item, table ITEMS

    Attributes:
        id (int): Id of hour item
        name (str): Name of hour item
        rid (str): Resource id of hour item
            format: i1_i2
                i1 (int): Group number of the resource
                i2 (int): Index number of the resource group
        clock (str): Reminder time of the hour item
            format: i1_i2_10:00
                i1: P: Per(Every), E: Even, O: Odd
                i2: CD: Calendar day, WD: Work day, HD: Holiday day
        schedule (str): Planned time spent within the cycle of the hour item
            format: i1_30m
                i1: PD: Per(Every) Day, PW: Per(Every) Week, PM: Per(Every) Month
                m: minute, h: hour
        sums (int): Total time for hour item in minutes
        father (int): Parent ID of the hour item
    """
    id: int
    name: str
    rid: str
    clock: str
    schedule: str
    sums: int   # minutes
    father: int

class RecordSqlDict(TypedDict):
    """ table RECORDS

    Attributes:
        iid (int): ID of linked hour item (foreign key to ITEMS.iid)
        strt (datetime.datetime): Start timestamp of the record
        end (datetime.datetime): End timestamp of the record
    """
    id: int
    # strt: sqlite3.Timestamp
    # start: datetime.datetime
    start: str
    # end: sqlite3.Timestamp
    # end: datetime.datetime
    end: str

# ------------------------------
# Parsing Functions
# ------------------------------
def parse_clock(clock_str: str):
    """Parse legacy clock string into time part, i1 (P/E/O), and i2 (CD/WD/HD).

    Args:
        clock_str: Legacy clock string (format: i1_i2_HH:MM)

    Returns:
        Tuple containing (clk_timestr, clock_i1, clock_i2).
        Empty string for invalid/empty input.

    Notes:
        - i1 values: P=Per(Every), E=Even, O=Odd
        - i2 values: CD=Calendar day, WD=Work day, HD=Holiday day
        - clk_timestr is the time part (e.g., "10:00" from "P_WD_10:00")
    """
    if not clock_str:
        return "", 1, ""

    parts = clock_str.split("_")
    if len(parts) != 3:
        return "", 1, ""

    everystr, clock_i2, clk_timestr = parts
    if everystr == "P":
        every = 1
    elif everystr in ["E", "O"]:
        every = 2
    else:
        every = 1
    # Validate time format (HH:MM)
    try:
        _ = datetime.datetime.strptime(clk_timestr, "%H:%M")
    except ValueError:
        return "", every, clock_i2

    return clk_timestr, every, clock_i2


def parse_schedule(schedule_str: str):
    """Parse legacy schedule string into every (int) and unit (ReminderDict format).

    Args:
        schedule_str: Legacy schedule string (format: i1_XXm/XXh)

    Returns:
        Tuple containing (every, unit, int) with default (1, "DY", 0) for invalid input.

    Notes:
        - i1 values: PD=Per Day, PW=Per Week, PM=Per Month
        - Schedule examples: "PD_30m" → every=1, unit="DY" (daily, 30min interval)
        - Unit mapping: m/h → HR, PD→DY, PW→WK, PM→MH
        - Every is always ≥1
    """
    # Default values if schedule is invalid/empty
    every = 1
    unit = TimeUnit.DAY
    duration = 0

    if not schedule_str:
        return every, unit, duration

    parts = schedule_str.split("_")
    if len(parts) != 2:
        return every, unit, duration

    i1_str, duration_str = parts

    # Map schedule type to ReminderDict unit
    schedule_unit_mapping = {
        "D": TimeUnit.DAY,  # Day → Day
        "W": TimeUnit.WEEK,  # Week → Week
        "M": TimeUnit.MONTH   # Month → Month
    }

    # Override unit based on schedule type (PD/PW/PM)
    if i1_str[1] in schedule_unit_mapping:
        unit = schedule_unit_mapping[i1_str[1]]

    # Extract numeric value and unit suffix (m/h)
    match = re.match(r"(\d+)([mh])", duration_str.lower())
    if not match:
        return every, unit, duration

    value = int(match.group(1))
    suffix = match.group(2)
    duration = value
    if suffix == "h":
        duration = value * 60

    return every, unit, duration


def generate_custom(every: int, clock_i2: str):
    """Generate customstr from legacy clock i1/i2 values.

    Args:
        every: i1 part from clock string (P/E/O)
        clock_i2: i2 part from clock string (CD/WD/HD)

    Returns:
        String representation of custom rule (ED/WD/HD per ReminderDict)

    Notes:
        - CD (Calendar Day) → ED (Every Day)
        - WD (Work Day) → WD (Work Day)
        - HD (Holiday Day) → HD (Holiday)
        - Defaults to ED if input is invalid
    """
    i2_mapping = {
        "CD": DayType.EVERYDAY,
        "WD": DayType.WORKDAY,
        "HD": DayType.HOLIDAY
    }

    if not clock_i2 or clock_i2 not in i2_mapping:
        return DayType.EVERYDAY

    return i2_mapping[clock_i2]


def to_unix_timestamp(datetime_obj: datetime.datetime | None):
    """Convert datetime object to Unix timestamp (float).

    Args:
        datetime_obj: datetime.datetime object from legacy RECORDS

    Returns:
        Unix timestamp (seconds since epoch) as float, 0.0 if input is None
    """
    if not datetime_obj:
        return 0.0
    return datetime_obj.timestamp()


# ------------------------------
# Main Migration Function
# ------------------------------
def migrate_legacy_to_new(legacy_db_path: str, new_db_path: str):
    """Main function to migrate legacy database to new schema.

    Args:
        legacy_db_path: Path to legacy SQLite database file
        new_db_path: Path to new SQLite database file (created if missing)

    Raises:
        sqlite3.Error: If database operation fails (e.g., missing tables)
        Exception: If data parsing or mapping fails
    """
    # Initialize database
    _legacy_conn = None
    _new_db = TimeDatabase()

    # try:
    # Connect to legacy database (read-only)
    _legacy_conn = sqlite3.connect(f"file:{legacy_db_path}?mode=ro", uri=True)
    # The row_factory attribute of a sqlite3.Connection object controls the type of object returned by cursor.fetchone()/fetchall() when querying the database.
    # by row_factory, you could Access fields by COLUMN NAME, like row["id"], and You can still use indexes if needed (backward compatible), like row[0]
    _legacy_conn.row_factory = sqlite3.Row
    legacy_cursor = _legacy_conn.cursor()

    # Step 1: open new tables
    _ = _new_db.open(new_db_path)

    # Step 2: Migrate legacy ITEMS → PLANS (using HourSqlTuple)
    _legacy_id_to_new_pid: dict[int, int] = {}  # Legacy ITEMS.iid → New PLANS.pid
    _legacy_id_to_new_pid[-1] = -1

    # Read all legacy ITEMS records
    _ = legacy_cursor.execute("SELECT id, name, rid, clock, schedule, sums, father FROM ITEMS")
    legacy_items: list[HourSqlTuple] = []
    for row in cast(list[HourSqlDict], legacy_cursor.fetchall()):
        # Map legacy row to HourSqlTuple
        legacy_item = HourSqlTuple(
            iid=row["id"],
            name=row["name"],
            rid=row["rid"],
            clock=row["clock"],
            schedule=row["schedule"],
            sums=row["sums"],
            father=row["father"]
        )
        legacy_items.append(legacy_item)

    # Insert into PLANS table
    for item in legacy_items:
        rid = item.rid.split("_")
        plandata = default_plan_data()
        plandata["name"] = item.name
        plandata["iid"] = IconTuple(int(rid[0]), int(rid[1]))
        plandata["fid"] = _legacy_id_to_new_pid[item.father]
        plandata["sums"] = item.sums
        new_pid = _new_db.add_plan(**plandata)
        # if item.sums > 0:
            # _ = _new_db.modify_plan(new_pid, "sums", item.sums)
        # Store legacy → new ID mapping
        _legacy_id_to_new_pid[item.iid] = new_pid
        # po(f"pid: {new_pid}, name: {item.name}")

    # pv(new_db.plan_dict)

    def clock_schedule2reminders():
        # Step 3: Migrate legacy ITEMS clock/schedule → REMINDERS
        for item in legacy_items:
            new_pid = _legacy_id_to_new_pid[item.iid]

            # Parse legacy fields
            clk_timestr, clock_i1, clock_i2 = parse_clock(item.clock)
            every, unit, duration = parse_schedule(item.schedule)
            custom = generate_custom(clock_i1, clock_i2)

            reminder = default_reminder_data()
            clk_time = str2time(clk_timestr)
            reminder["clk_time"] = clk_time
            reminder["bgn_time"] = clk_time
            reminder["duration"] = duration
            reminder["every"] = every
            reminder["unit"] = unit
            reminder["custom"] = custom
            _ = _new_db.add_reminder(new_pid, **reminder)
    clock_schedule2reminders()

    def records2records():
        # Step 4: Migrate legacy RECORDS → new RECORDS (using HourSqlRecord)
        # Read legacy RECORDS
        _ = legacy_cursor.execute("SELECT *, end FROM RECORDS")
        legacy_records: list[HourSqlRecord] = []
        for row in cast(list[RecordSqlDict], legacy_cursor.fetchall()):
            # Convert sqlite timestamp to datetime object
            strt = datetime.datetime.fromisoformat(row["start"])
            # strt = cast(datetime.datetime, new_db.timestamp2datetime(start))
            end = datetime.datetime.fromisoformat(row["end"])
            # end = cast(datetime.datetime, new_db.timestamp2datetime(row["end"]))

            # Map to HourSqlRecord
            legacy_record = HourSqlRecord(
                row["id"],
                strt,
                end
            )
            legacy_records.append(legacy_record)

        # Insert into new RECORDS table
        migrated_records = 0
        for record in legacy_records:
            # Skip orphaned records (no matching plan)
            # if record.iid not in legacy_id_to_new_pid:
                # continue

            new_pid = _legacy_id_to_new_pid[record.iid]
            # Get plan name for RECORDS.name (NOT NULL)
            plan_name = next(item.name for item in legacy_items if item.iid == record.iid)

            # Calculate duration in minutes (end - start)
            if record.strt and record.end:
                duration_min = int((record.end - record.strt).total_seconds() / 60)
            else:
                duration_min = 0

            # Convert start to Unix timestamp
            # bgn_timestamp = to_unix_timestamp(record.strt)

            migrated_records += 1
            _ = _new_db.add_record(name=plan_name,
                bgn_dtime=record.strt,
                pid=new_pid,
                duration=duration_min
            )
        return migrated_records
    migrated_records = records2records()

    # Commit all changes
    # new_db.commit()

    # Print migration summary
    print("✅ Migration completed successfully!")
    print(f"- Migrated {len(legacy_items)} items to PLANS table")
    print(f"- Created {len(legacy_items)} reminders in REMINDERS table")
    print(f"- Migrated {migrated_records} records to new RECORDS table")

    # except sqlite3.Error as e:
        # if new_db:
            # new_db.rollback()
        # raise sqlite3.Error(f"Database migration failed: {str(e)}") from e
    # except Exception as e:
        # if new_db:
            # new_db.rollback()
        # raise Exception(f"Data processing failed: {str(e)}") from e
    # finally:
    # Clean up connections
    if _legacy_conn:
        _legacy_conn.close()
    if _new_db:
        _ = _new_db.close()


# ------------------------------
# Run Migration
# ------------------------------
if __name__ == "__main__":
    # Configure database paths (update these to your actual paths)
    legacy_db_path = sys.argv[1]
    new_db_path = Path(sys.argv[1]).parent / "hours.db"
    # try:
    if new_db_path.is_file():
        os.remove(str(new_db_path))
    migrate_legacy_to_new(legacy_db_path, str(new_db_path))
    # except Exception as e:
        # print(f"❌ Migration failed: {str(e)}")

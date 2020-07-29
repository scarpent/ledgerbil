from datetime import date, datetime
from textwrap import dedent
from unittest import TestCase

import pytest
from dateutil.relativedelta import relativedelta

from .. import schedulething as ST
from .. import util
from ..ledgerbilexceptions import LdgSchedulerError
from ..schedulething import ScheduleThing


def reset_schedule_thing():
    ScheduleThing.do_file_config = True
    ScheduleThing.enter_days = 0
    ScheduleThing.entry_boundary_date = None


def setup_function():
    reset_schedule_thing()


def test_repr():
    lines = [
        "2013/06/29 lightning energy",
        "    ;; schedule ; monthly ; 12th ; ; auto",
        "    e: xyz",
        "    l: abc         $-10",
    ]
    ScheduleThing.do_file_config = False
    schedulething = ScheduleThing(lines)
    assert repr(schedulething) == f"ScheduleThing({lines})"
    assert isinstance(eval(repr(schedulething)), ScheduleThing)


class ScheduleThingTester(TestCase):
    def setUp(self):
        super().setUp()
        reset_schedule_thing()


class HandleFileConfig(ScheduleThingTester):
    @staticmethod
    def get_expected(enterdays):
        today_plus_enterdays = util.get_date_string(
            date.today() + relativedelta(days=enterdays)
        )
        return f"{enterdays} | {today_plus_enterdays}"

    @staticmethod
    def get_actual(schedule_thing):
        boundary = util.get_date_string(schedule_thing.entry_boundary_date)
        return f"{schedule_thing.enter_days} | {boundary}"

    def test_basic_file_config(self):
        schedule_line_file_config = [";; scheduler ; enter 7 days"]
        schedule_thing = ScheduleThing(schedule_line_file_config)
        assert self.get_actual(schedule_thing) == self.get_expected(7)

    def test_invalid_file_config(self):
        schedule_line_file_config = [";; shceduler ; enter 7 days"]
        with pytest.raises(LdgSchedulerError) as excinfo:
            ScheduleThing(schedule_line_file_config)
        expected = dedent(
            """\
            Invalid schedule file config:
            ;; shceduler ; enter 7 days
            Expected:
            ;; scheduler ; enter N days"""
        )
        assert str(excinfo.value) == expected

    def test_file_config(self):
        schedule_line_file_config = [";;scheduler;enter 7 days;;"]
        schedule_thing = ScheduleThing(schedule_line_file_config)
        assert self.get_actual(schedule_thing) == self.get_expected(7)

    def test_file_config_no_enter(self):
        schedule_line_file_config = [";;scheduler;;"]
        schedule_thing = ScheduleThing(schedule_line_file_config)
        assert self.get_actual(schedule_thing) == self.get_expected(0)

    def test_file_config_enter_less_than_one(self):
        schedule_line_file_config = [";;   scheduler   ; enter 0 day ; comment"]
        schedule_thing = ScheduleThing(schedule_line_file_config)
        assert self.get_actual(schedule_thing) == self.get_expected(0)


class GetSafeDate(TestCase):
    def setUp(self):
        super().setUp()
        schedule_lines_test = [
            "2013/06/29 lightning energy",
            "    ;; schedule ; monthly ; 12th ; ; auto",
        ]
        ScheduleThing.do_file_config = False
        self.schedule_thing = ScheduleThing(schedule_lines_test)

    def test_date_is_fine(self):
        expected = date(2013, 8, 31)
        actual = self.schedule_thing.get_safe_date(expected, 31)
        assert actual == expected

    def test_day_is_too_many(self):
        expected = date(2013, 8, 31)
        actual = self.schedule_thing.get_safe_date(date(2013, 8, 31), 99)
        assert actual == expected


class GetScheduledEntries(TestCase):
    def setUp(self):
        super().setUp()
        schedule_line_file_config = [";; scheduler ; enter 7 days"]
        ScheduleThing.do_file_config = True
        ScheduleThing(schedule_line_file_config)

    def test_one_entry_count(self):
        testdate = util.get_date_string(date.today())
        schedule_lines = [
            f"{testdate} lightning energy",
            "    ;; schedule ; monthly",
            "    blah blah blah",
        ]
        schedule_thing = ScheduleThing(schedule_lines)

        expected = 1
        actual = len(schedule_thing.get_scheduled_entries())

        assert actual == expected

    def test_one_entry_next_date(self):
        testdate = util.get_date_string(date.today())
        schedule_lines = [
            f"{testdate} lightning energy",
            "    ;; schedule ; monthly",
            "    blah blah blah",
        ]
        schedule_thing = ScheduleThing(schedule_lines)
        schedule_thing.get_scheduled_entries()

        expected = date.today() + relativedelta(months=1)
        actual = schedule_thing.thing_date

        assert actual == expected

    def test_one_entry_content(self):
        testdate = util.get_date_string(date.today())
        schedule_lines = [
            f"{testdate} lightning energy",
            "    ;; schedule ; monthly",
            "    blah blah blah",
        ]
        schedule_thing = ScheduleThing(schedule_lines)

        expected = [f"{testdate} lightning energy", "    blah blah blah"]

        actual = schedule_thing.get_scheduled_entries()[0].get_lines()

        assert actual == expected

    def test_two_entries_count(self):
        testdate = util.get_date_string(date.today() - relativedelta(months=1))
        schedule_lines = [
            f"{testdate} lightning energy",
            "    ;; schedule ; monthly",
            "    blah blah blah",
        ]
        schedule_thing = ScheduleThing(schedule_lines)

        expected = 2
        actual = len(schedule_thing.get_scheduled_entries())

        assert actual == expected

    def test_two_entries_next_date(self):
        testdate = util.get_date_string(date.today())
        schedule_lines = [
            f"{testdate} lightning energy",
            "    ;; schedule ; yearly",
            "    blah blah blah",
        ]
        schedule_thing = ScheduleThing(schedule_lines)
        schedule_thing.thing_date = date.today() - relativedelta(years=1)
        schedule_thing.get_scheduled_entries()

        expected = date.today() + relativedelta(years=1)
        actual = schedule_thing.thing_date

        assert actual == expected

    def test_no_entries_count(self):
        testdate = util.get_date_string(date.today() + relativedelta(months=2))
        schedule_lines = [
            f"{testdate} lightning energy",
            "    ;; schedule ; monthly",
            "    blah blah blah",
        ]
        schedule_thing = ScheduleThing(schedule_lines)

        expected = 0
        actual = len(schedule_thing.get_scheduled_entries())

        assert actual == expected

    def test_no_entries_next_date(self):
        testdate = util.get_date_string(date.today() + relativedelta(months=2))
        schedule_lines = [
            f"{testdate} lightning energy",
            "    ;; schedule ; monthly",
            "    blah blah blah",
        ]
        schedule_thing = ScheduleThing(schedule_lines)
        schedule_thing.get_scheduled_entries()

        expected = date.today() + relativedelta(months=2)
        actual = schedule_thing.thing_date

        assert actual == expected

    def test_bimonthly_next_date(self):
        testdate = util.get_date_string(date.today())
        schedule_lines = [
            f"{testdate} lightning energy",
            "    ;; schedule ; bimonthly",
            "    blah blah blah",
        ]
        schedule_thing = ScheduleThing(schedule_lines)
        schedule_thing.get_scheduled_entries()

        expected = date.today() + relativedelta(months=2)
        actual = schedule_thing.thing_date

        assert actual == expected

    def test_quarterly_next_date(self):
        testdate = util.get_date_string(date.today())
        schedule_lines = [
            f"{testdate} lightning energy",
            "    ;; schedule ; quarterly",
            "    blah blah blah",
        ]
        schedule_thing = ScheduleThing(schedule_lines)
        schedule_thing.get_scheduled_entries()

        expected = date.today() + relativedelta(months=3)
        actual = schedule_thing.thing_date

        assert actual == expected

    def test_biannual_next_date(self):
        testdate = util.get_date_string(date.today())
        schedule_lines = [
            f"{testdate} lightning energy",
            "    ;; schedule ; biannual",
            "    blah blah blah",
        ]
        schedule_thing = ScheduleThing(schedule_lines)
        schedule_thing.get_scheduled_entries()

        expected = date.today() + relativedelta(months=6)
        actual = schedule_thing.thing_date

        assert actual == expected

    def test_yearly_next_date(self):
        testdate = util.get_date_string(date.today())
        schedule_lines = [
            f"{testdate} lightning energy",
            "    ;; schedule ; yearly",
            "    blah blah blah",
        ]
        schedule_thing = ScheduleThing(schedule_lines)
        schedule_thing.get_scheduled_entries()

        expected = date.today() + relativedelta(months=12)
        actual = schedule_thing.thing_date

        assert actual == expected


class GetEntryThing(TestCase):
    def setUp(self):
        super().setUp()
        schedule_line_file_config = [";; scheduler ; enter 7 days"]
        ScheduleThing.do_file_config = True
        ScheduleThing(schedule_line_file_config)

    def test_basic_entry(self):
        schedule_lines = [
            "2013/06/13 lightning energy",
            "    ;; schedule ; monthly",
            "    blah blah blah",
        ]
        schedule_thing = ScheduleThing(schedule_lines)
        schedule_thing.thing_date = date(2013, 7, 1)

        expected = ["2013/07/01 lightning energy", "    blah blah blah"]

        actual = schedule_thing.get_entry_thing().get_lines()

        assert actual == expected


class HandleThingConfig(TestCase):
    def setUp(self):
        super().setUp()
        schedule_line_file_config = [";; scheduler ; enter 7 days"]
        ScheduleThing.do_file_config = True
        ScheduleThing(schedule_line_file_config)

    @staticmethod
    def get_expected(intervaluom, days, interval):
        return "%s | %s | %s" % (intervaluom, days, interval)

    @staticmethod
    def get_actual(schedule_thing):
        return "%s | %s | %s" % (
            schedule_thing.interval_uom,
            schedule_thing.days,
            schedule_thing.interval,
        )

    def test_basic_thing_config(self):
        # also tests sorting of days
        schedule_lines = [
            "2013/06/05 lightning energy",
            "    ;; schedule ; monthly ; eom30 2 15 ; 3 ; auto",
        ]
        schedule_thing = ScheduleThing(schedule_lines)
        expected = self.get_expected(ST.INTERVAL_MONTH, ["02", "15", "eom30"], 3)
        assert self.get_actual(schedule_thing) == expected

    def test_not_enough_parameters(self):
        schedule_lines = ["2013/06/05 lightning energy", "    ;; schedule"]
        with pytest.raises(LdgSchedulerError) as excinfo:
            ScheduleThing(schedule_lines)
        expected = dedent(
            """\
            Invalid schedule thing config:
                ;; schedule
            Not enough parameters"""
        )
        assert str(excinfo.value) == expected

    def test_schedule_label_not_right(self):
        schedule_lines = ["2013/06/05 lightning energy", "    ;; scheduble ; monthly"]
        with pytest.raises(LdgSchedulerError) as excinfo:
            ScheduleThing(schedule_lines)
        expected = dedent(
            """\
            Invalid schedule thing config:
                ;; scheduble ; monthly
            "schedule" label not found in expected place."""
        )
        assert str(excinfo.value) == expected

    def test_schedule_unrecognized_interval_uom(self):
        schedule_lines = ["2013/06/05 lightning energy", "    ;; schedule ; lunarly"]
        with pytest.raises(LdgSchedulerError) as excinfo:
            ScheduleThing(schedule_lines)
        expected = (
            "Invalid schedule thing config:\n"
            "    ;; schedule ; lunarly\n"
            'Interval UOM "lunarly" not recognized. Supported UOMs: '
            "daily, weekly, monthly, bimonthly, quarterly, biannual, yearly."
        )
        assert str(excinfo.value) == expected

    def test_interval_empty(self):
        schedule_lines = [
            "2013/06/05 lightning energy",
            "    ;; schedule ; monthly ; 15 eom30 ;   ; auto",
        ]
        schedule_thing = ScheduleThing(schedule_lines)
        expected = self.get_expected(ST.INTERVAL_MONTH, ["15", "eom30"], 1)
        assert self.get_actual(schedule_thing) == expected

    def test_interval_not_given(self):
        schedule_lines = [
            "2013/06/05 lightning energy",
            "    ;; schedule ; monthly ; 15 eom30",
        ]
        schedule_thing = ScheduleThing(schedule_lines)
        expected = self.get_expected(ST.INTERVAL_MONTH, ["15", "eom30"], 1)
        assert self.get_actual(schedule_thing) == expected

    def test_days_empty(self):
        schedule_lines = [
            "2013/06/27 lightning energy",
            "    ;; schedule ; monthly ;  ;  2 ",
        ]
        schedule_thing = ScheduleThing(schedule_lines)
        expected = self.get_expected(ST.INTERVAL_MONTH, ["27"], 2)
        assert self.get_actual(schedule_thing) == expected

    def test_no_days_and_no_interval(self):
        schedule_lines = ["2013/06/13 lightning energy", "    ;; schedule ; monthly"]
        schedule_thing = ScheduleThing(schedule_lines)
        expected = self.get_expected(ST.INTERVAL_MONTH, ["13"], 1)
        assert self.get_actual(schedule_thing) == expected

    def test_bimonthly(self):
        schedule_lines = ["2013/06/13 lightning energy", "    ;; schedule ; bimonthly"]
        schedule_thing = ScheduleThing(schedule_lines)
        expected = self.get_expected(ST.INTERVAL_MONTH, ["13"], 2)
        assert self.get_actual(schedule_thing) == expected

    def test_quarterly(self):
        schedule_lines = [
            "2013/06/13 lightning energy",
            "    ;; schedule ; quarterly ; 6th ; 3",
        ]
        schedule_thing = ScheduleThing(schedule_lines)
        expected = self.get_expected(ST.INTERVAL_MONTH, ["06"], 9)
        assert self.get_actual(schedule_thing) == expected

    def test_biannual(self):
        schedule_lines = [
            "2013/06/13 lightning energy",
            "    ;; schedule ; biannual ; 9th",
        ]
        schedule_thing = ScheduleThing(schedule_lines)
        expected = self.get_expected(ST.INTERVAL_MONTH, ["09"], 6)
        assert self.get_actual(schedule_thing) == expected

    def test_yearly(self):
        schedule_lines = [
            "2013/06/22 lightning energy",
            "    ;; schedule ; yearly ; ; 5",
        ]
        schedule_thing = ScheduleThing(schedule_lines)
        expected = self.get_expected(ST.INTERVAL_MONTH, ["22"], 60)
        assert self.get_actual(schedule_thing) == expected


class GetNextDate(TestCase):
    def setUp(self):
        super().setUp()
        schedule_line_file_config = [";; scheduler ; enter 7 days"]
        ScheduleThing.do_file_config = True
        ScheduleThing(schedule_line_file_config)

    def test_get_next_date_monthly_this_month_eom(self):
        schedule_lines = [
            "2013/06/05 lightning energy",
            "    ;; schedule ; monthly ; eom ; ; auto",
        ]
        schedule_thing = ScheduleThing(schedule_lines)
        actual_next = schedule_thing.get_next_date(schedule_thing.thing_date)
        assert actual_next == util.get_date("2013/06/30")

    def test_get_next_date_monthly_this_month_eom_on_the_day(self):
        schedule_lines = [
            "2013/06/30 lightning energy",
            "    ;; schedule ; monthly ; eom ; ; auto",
        ]
        schedule_thing = ScheduleThing(schedule_lines)
        actual_next = schedule_thing.get_next_date(schedule_thing.thing_date)
        assert actual_next == util.get_date("2013/07/31")

    def test_get_next_date_monthly_next_month_eom30(self):
        schedule_lines = [
            "2013/07/30 lightning energy",
            "    ;; schedule ; monthly ; eom30 ; ; auto",
        ]
        schedule_thing = ScheduleThing(schedule_lines)
        actual_next = schedule_thing.get_next_date(schedule_thing.thing_date)
        assert actual_next == util.get_date("2013/08/30")

    def test_get_next_date_monthly_this_month(self):
        schedule_lines = [
            "2013/06/05 lightning energy",
            "    ;; schedule ; monthly ; 12th ; ; auto",
        ]
        schedule_thing = ScheduleThing(schedule_lines)
        actual_next = schedule_thing.get_next_date(schedule_thing.thing_date)
        assert actual_next == util.get_date("2013/06/12")

    def test_get_next_date_monthly_next_month(self):
        schedule_lines = [
            "2013/06/17 lightning energy",
            "    ;; schedule ; monthly ; 12th ; ; auto",
        ]
        schedule_thing = ScheduleThing(schedule_lines)
        actual_next = schedule_thing.get_next_date(schedule_thing.thing_date)
        assert actual_next == util.get_date("2013/07/12")

    def test_get_next_date_monthly_next_month_again(self):
        schedule_lines = [
            "2013/06/12 lightning energy",
            "    ;; schedule ; monthly ; 12th ; ; auto",
        ]
        schedule_thing = ScheduleThing(schedule_lines)
        actual_next = schedule_thing.get_next_date(schedule_thing.thing_date)
        assert actual_next == util.get_date("2013/07/12")

    def test_get_next_date_monthly_next_month_first(self):
        schedule_lines = [
            "2013/06/28 lightning energy",
            "    ;; schedule ; monthly ; 1st",
        ]
        schedule_thing = ScheduleThing(schedule_lines)
        actual_next = schedule_thing.get_next_date(schedule_thing.thing_date)

        assert actual_next == util.get_date("2013/07/01")

    def test_get_next_date_monthly_multiple_days_this_month(self):
        schedule_lines = [
            "2013/06/05 lightning energy",
            "    ;; schedule ; monthly ; 7th, 12th ; ; auto",
        ]
        schedule_thing = ScheduleThing(schedule_lines)
        actual_next = schedule_thing.get_next_date(schedule_thing.thing_date)
        assert actual_next == util.get_date("2013/06/07")

    def test_get_next_date_monthly_multiple_days_this_month_again(self):
        schedule_lines = [
            "2013/06/08 lightning energy",
            "    ;; schedule ; monthly ; 7th, 12th",
        ]
        schedule_thing = ScheduleThing(schedule_lines)
        actual_next = schedule_thing.get_next_date(schedule_thing.thing_date)
        assert actual_next == util.get_date("2013/06/12")

    def test_get_next_date_monthly_multiple_days_next_month(self):
        schedule_lines = [
            "2013/06/27 lightning energy",
            "    ;; schedule ; monthly ; 7th, 27th ; ; auto",
        ]
        schedule_thing = ScheduleThing(schedule_lines)
        actual_next = schedule_thing.get_next_date(schedule_thing.thing_date)
        assert actual_next == util.get_date("2013/07/07")

    def test_get_next_date_monthly_interval3(self):
        schedule_lines = [
            "2013/06/15 lightning energy",
            "    ;; schedule ; monthly ; 15th ; 3 ; auto",
        ]
        schedule_thing = ScheduleThing(schedule_lines)
        actual_next = schedule_thing.get_next_date(schedule_thing.thing_date)
        assert actual_next == util.get_date("2013/09/15")

    def test_get_next_date_monthly_interval12eom_leap_one(self):
        schedule_lines = [
            "2011/02/28 lightning energy",
            "    ;; schedule ; monthly ; eom ; 12 ; auto",
        ]
        schedule_thing = ScheduleThing(schedule_lines)
        actual_next = schedule_thing.get_next_date(schedule_thing.thing_date)
        assert actual_next == util.get_date("2012/02/29")

    def test_get_next_date_monthly_interval12eom_leap_two(self):
        schedule_lines = [
            "2012/02/29 lightning energy",
            "    ;; schedule ; monthly ; eom ; 12 ; auto",
        ]
        schedule_thing = ScheduleThing(schedule_lines)
        actual_next = schedule_thing.get_next_date(schedule_thing.thing_date)
        assert actual_next == util.get_date("2013/02/28")

    def test_get_next_date_monthly_too_many29(self):
        schedule_lines = [
            "2013/01/31 lightning energy",
            "    ;; schedule ; monthly ; 29th ; 1 ; auto",
        ]
        schedule_thing = ScheduleThing(schedule_lines)
        actual_next = schedule_thing.get_next_date(schedule_thing.thing_date)
        assert actual_next == util.get_date("2013/02/28")

    def test_get_next_date_monthly_too_many30(self):
        schedule_lines = [
            "2013/01/30 lightning energy",
            "    ;; schedule ; monthly ; 30th ; 1 ; auto",
        ]
        schedule_thing = ScheduleThing(schedule_lines)
        actual_next = schedule_thing.get_next_date(schedule_thing.thing_date)
        assert actual_next == util.get_date("2013/02/28")

    def test_get_next_date_monthly_too_many70(self):
        schedule_lines = [
            "2013/07/15 lightning energy",
            "    ;; schedule ; monthly ; 70th ; 1 ; auto",
        ]
        schedule_thing = ScheduleThing(schedule_lines)
        actual_next = schedule_thing.get_next_date(schedule_thing.thing_date)
        assert actual_next == util.get_date("2013/07/31")


class GetWeekDay(TestCase):
    def setUp(self):
        schedule_lines_test = [
            "2013/06/29 lightning energy",
            "    ;; schedule ; monthly ; 12th ; ; auto",
        ]

        ScheduleThing.do_file_config = False
        self.schedule_thing = ScheduleThing(schedule_lines_test)

    def test_get_week_day(self):
        assert self.schedule_thing.get_week_day() == util.ERROR_RETURN_VALUE


class GetMonthDay(TestCase):
    def setUp(self):
        super().setUp()
        schedule_lines_test = [
            "2013/06/29 lightning energy",
            "    ;; schedule ; monthly ; 12th ; ; auto",
        ]

        ScheduleThing.do_file_config = False
        self.schedule_thing = ScheduleThing(schedule_lines_test)

    def test_get_month_day_normal(self):
        """normal day is returned as the same day number"""
        testdate = datetime(2013, 6, 16)
        assert self.schedule_thing.get_month_day("5", testdate) == 5

    def test_get_month_day_february_30(self):
        testdate = datetime(2016, 2, 16)
        assert self.schedule_thing.get_month_day("30", testdate) == 29

    def test_get_month_day_june_eom(self):
        """eom for a 30-day month is 30"""
        testdate = datetime(2013, 6, 16)
        actual = self.schedule_thing.get_month_day(ST.EOM, testdate)
        assert actual == 30

    def test_get_month_day_july_eom(self):
        """eom for a 31-day month is 31"""
        testdate = datetime(2013, 7, 1)
        actual = self.schedule_thing.get_month_day(ST.EOM, testdate)
        assert actual == 31

    def test_get_month_day_february_eom(self):
        """eom for a non-leap year february is 28"""
        testdate = datetime(2013, 2, 5)
        actual = self.schedule_thing.get_month_day(ST.EOM, testdate)
        assert actual == 28

    def test_get_month_day_leap_february_eom(self):
        """eom for a leap year february is 29"""
        testdate = datetime(2012, 2, 5)
        actual = self.schedule_thing.get_month_day(ST.EOM, testdate)
        assert actual == 29

    def test_get_month_day_june_eom30(self):
        """eom30 for a 30-day month is 30"""
        testdate = datetime(2013, 6, 16)
        actual = self.schedule_thing.get_month_day(ST.EOM30, testdate)
        assert actual == 30

    def test_get_month_day_july_eom30(self):
        """eom30 for a 31-day month is 30"""
        testdate = datetime(2013, 7, 1)
        actual = self.schedule_thing.get_month_day(ST.EOM30, testdate)
        assert actual == 30

    def test_get_month_day_february_eom30(self):
        """eom30 for a non-leap year february is 28"""
        testdate = datetime(2013, 2, 5)
        actual = self.schedule_thing.get_month_day(ST.EOM30, testdate)
        assert actual == 28

    def test_get_month_day_leap_february_eom30(self):
        """eom for a leap year february is 29"""
        testdate = datetime(2012, 2, 5)
        actual = self.schedule_thing.get_month_day(ST.EOM30, testdate)
        assert actual == 29

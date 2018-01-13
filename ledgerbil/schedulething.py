"""objects in schedule file: recurring transactions"""

import re
from calendar import monthrange
from copy import copy
from datetime import date

from dateutil.relativedelta import relativedelta

from .ledgerbilexceptions import LdgSchedulerError
from .ledgerthing import LedgerThing


class ScheduleThing(LedgerThing):

    # These three are also initialized in ScheduleFile init, mostly
    # to ensure tests run with expected initial state
    do_file_config = True
    enter_days = 0
    entry_boundary_date = None

    LINE_FILE_CONFIG = 0
    LINE_DATE = 0
    LINE_SCHEDULE = 1
    INTERVAL_WEEK = 'weekly'
    INTERVAL_MONTH = 'monthly'
    EOM = 'eom'
    EOM30 = 'eom30'
    SEPARATOR = ';'
    THING_CONFIG_LABEL = 'schedule'

    def __init__(self, lines):
        self.first_thing = False
        self.interval_uom = ''   # month or week
        self.days = []           # e.g. 5, 15, eom, eom30
        self.interval = 1        # e.g. 1 = every month, 2 = every other

        super().__init__(lines)

        if ScheduleThing.do_file_config:
            self._handle_file_config(
                lines[ScheduleThing.LINE_FILE_CONFIG]
            )
            self.first_thing = True
            ScheduleThing.do_file_config = False
            return

        self._handle_thing_config(lines[ScheduleThing.LINE_SCHEDULE])

    # file level config looks like this:
    # ;; scheduler ; enter N days
    # enter is optional
    @staticmethod
    def _handle_file_config(line):

        config_regex = r'''(?x)               # verbose mode
            ^                                 # line start
            \s*;;\s*scheduler\s*              # required
            (?:                               # non-capturing
                ;\s*enter\s+(\d+)\s+days?\s*  # days ahead to enter tran
            )?                                # optional
            (?:\s*;.*)?                       # optional end semi-colon
            $                                 # line end
            '''

        # capturing groups
        enter_days_idx = 1

        match = re.match(config_regex, line)
        if not match:
            raise LdgSchedulerError(
                'Invalid schedule file config:\n{}\nExpected:\n'
                ';; scheduler ; enter N days'.format(line)
            )

        if match.group(enter_days_idx):
            ScheduleThing.enter_days = int(match.group(enter_days_idx))

            if ScheduleThing.enter_days < 1:
                ScheduleThing.enter_days = 0

        ScheduleThing.entry_boundary_date = (
            date.today() + relativedelta(days=ScheduleThing.enter_days)
        )

    def _handle_thing_config(self, line):

        cfg_label_idx = 0
        interval_uom_idx = 1
        days_idx = 2
        interval_idx = 3

        # ';; schedule ; monthly ; 12th 21st eom; 3 ; auto'
        #        -->
        # ['', '', 'schedule', 'monthly', '12th 21st eom', '3', 'auto']
        configitems = [
            x.strip() for x in line.split(ScheduleThing.SEPARATOR)
        ]

        if len(configitems) < 4:
            raise LdgSchedulerError(
                'Invalid schedule thing config:\n{}\n'
                'Not enough parameters'.format(line)
            )

        del configitems[0:2]  # remove empty strings from opening ;;

        # now: ['schedule', 'monthly', '12th 21st eom', '3', 'auto']

        if configitems[cfg_label_idx].lower() != \
                ScheduleThing.THING_CONFIG_LABEL:
            raise LdgSchedulerError(
                'Invalid schedule thing config:\n{line}\n"{label}" '
                'label not found in expected place.'.format(
                    line=line,
                    label=ScheduleThing.THING_CONFIG_LABEL
                )
            )

        interval_uom_regex = (
            '(weekly|monthly|bimonthly|quarterly|biannual|yearly)'
        )

        match = re.match(
            interval_uom_regex,
            configitems[interval_uom_idx]
        )
        if not match:
            raise LdgSchedulerError(
                'Invalid schedule thing config:\n{line}\nInterval UOM '
                '"{uom}" not recognized. Supported UOMs: '
                'weekly, monthly, bimonthly, quarterly, biannual, '
                'yearly.'.format(
                    line=line,
                    uom=configitems[interval_uom_idx]
                )
            )

        intervaluom = match.group(1).lower()

        # schedule must have minimum two items; now let's make sure
        # optional fields are referenceable

        for x in range(len(configitems), 4):
            configitems.append('')

        if not configitems[days_idx].strip():
            configitems[days_idx] = str(self.thing_date.day)

        match = re.match(r'[^\d]*(\d+).*', configitems[interval_idx])
        interval = 1
        if match:
            interval = int(match.group(1))

        uom_translations = {
            'bimonthly': 2,
            'quarterly': 3,
            'biannual': 6,
            'yearly': 12,
        }

        if intervaluom in uom_translations:
            interval *= uom_translations[intervaluom]

        if intervaluom != ScheduleThing.INTERVAL_WEEK:
            intervaluom = ScheduleThing.INTERVAL_MONTH

        self.interval = interval
        self.interval_uom = intervaluom

        day_string = configitems[days_idx].lower()
        self.days = []
        days_regex = r'(\d+|eom(?:\d\d?)?)'
        for match in re.finditer(days_regex, day_string):
            if match.groups()[0].isdigit():
                theday = match.groups()[0].zfill(2)  # format for sorting
            else:
                theday = match.groups()[0]  # e.g. eom

            self.days.append(theday)

        self.days.sort()

    def get_scheduled_entries(self):

        entries = []

        if self.thing_date > ScheduleThing.entry_boundary_date:
            return entries

        entries.append(self._get_entry_thing())

        while True:
            self.thing_date = self._get_next_date(self.thing_date)

            if self.thing_date > ScheduleThing.entry_boundary_date:
                break

            entries.append(self._get_entry_thing())

        return entries

    def _get_entry_thing(self):
        """
        @rtype: LedgerThing
        """
        entry_lines = copy(self.lines)
        del entry_lines[ScheduleThing.LINE_SCHEDULE]
        entry_lines[ScheduleThing.LINE_DATE] = re.sub(
            self.DATE_REGEX,
            self.get_date_string(),
            entry_lines[ScheduleThing.LINE_DATE]
        )
        return LedgerThing(entry_lines)

    def _get_next_date(self, previousdate):

        if self.interval_uom == ScheduleThing.INTERVAL_MONTH:
            # first see if any scheduled days remaining in same month
            for scheduleday in self.days:
                scheduleday = self._get_month_day(
                    scheduleday,
                    previousdate
                )
                # compare with greater so we don't keep matching same
                if scheduleday > previousdate.day:
                    return self._get_safe_date(
                        previousdate,
                        scheduleday
                    )

            # advance to next month (by specified interval)

            nextdate = previousdate + relativedelta(
                months=self.interval
            )

            return self._get_safe_date(
                nextdate,
                self._get_month_day(self.days[0], nextdate)
            )

        if self.interval_uom == ScheduleThing.INTERVAL_WEEK:
            return previousdate + relativedelta(weeks=self.interval)

    # handle situations like 8/31 -> 9/31 (back up to 9/30)
    @staticmethod
    def _get_safe_date(thedate, theday):
        try:
            return date(thedate.year, thedate.month, theday)
        except ValueError:
            # day is out of range for month, so we'll get the last day
            # of month (may be unlikely now that we check lastDayOfMonth
            # in _getMonthDay)
            return date(
                thedate.year,
                thedate.month,
                monthrange(thedate.year, thedate.month)[1]
            )

    # knows how to handle "eom"
    def _get_month_day(self, scheduleday, currentdate):

        last_day_of_month = monthrange(
            currentdate.year,
            currentdate.month
        )[1]

        if str(scheduleday).isdigit():
            if int(scheduleday) > last_day_of_month:
                return last_day_of_month
            else:
                return int(scheduleday)

        if scheduleday == self.EOM:
            return last_day_of_month

        if scheduleday == '%s%s' % (self.EOM, '30'):
            if last_day_of_month >= 30:
                return 30
            else:
                return last_day_of_month  # february

    @staticmethod
    def _get_week_day():
        return -1

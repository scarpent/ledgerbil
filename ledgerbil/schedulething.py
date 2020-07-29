"""objects in schedule file: recurring transactions"""
import re
from calendar import monthrange
from datetime import date

from dateutil.relativedelta import relativedelta

from .ledgerbilexceptions import ERROR_RETURN_VALUE, LdgSchedulerError
from .ledgerthing import DATE_REGEX, LedgerThing

LINE_FILE_CONFIG = 0
LINE_DATE = 0
LINE_SCHEDULE = 1
INTERVAL_DAY = "daily"
INTERVAL_WEEK = "weekly"
INTERVAL_MONTH = "monthly"
EOM = "eom"
EOM30 = "eom30"
SEPARATOR = ";"
THING_CONFIG_LABEL = "schedule"


class ScheduleThing(LedgerThing):
    do_file_config = True
    enter_days = 0
    entry_boundary_date = None

    def __init__(self, lines):
        self.first_thing = False
        self.interval_uom = ""  # month or week
        self.days = []  # e.g. 5, 15, eom, eom30
        self.interval = 1  # e.g. 1 = every month, 2 = every other

        super().__init__(lines)

        if ScheduleThing.do_file_config:
            self.handle_file_config(lines[LINE_FILE_CONFIG])
            self.first_thing = True
            ScheduleThing.do_file_config = False
            return

        self.handle_thing_config(lines[LINE_SCHEDULE])

    def __repr__(self):
        return f"{self.__class__.__name__}({self.get_lines()})"

    # file level config looks like this:
    # ;; scheduler ; enter N days
    # enter is optional
    @staticmethod
    def handle_file_config(line):

        config_regex = r"""(?x)               # verbose mode
            ^                                 # line start
            \s*;;\s*scheduler\s*              # required
            (?:                               # non-capturing
              ;\s*enter\s+(\d+)\s+days?\s*    # days ahead to enter transaction
            )?                                # optional
            (?:\s*;.*)?                       # optional end semi-colon
            $                                 # line end
            """

        # capturing groups
        enter_days_idx = 1

        match = re.match(config_regex, line)
        if not match:
            raise LdgSchedulerError(
                f"Invalid schedule file config:\n{line}\nExpected:\n"
                ";; scheduler ; enter N days"
            )

        if match.group(enter_days_idx):
            ScheduleThing.enter_days = int(match.group(enter_days_idx))

            if ScheduleThing.enter_days < 1:
                ScheduleThing.enter_days = 0

        ScheduleThing.entry_boundary_date = date.today() + relativedelta(
            days=ScheduleThing.enter_days
        )

    def handle_thing_config(self, line):
        # ';; schedule ; monthly ; 12th 21st eom; 3 ; auto'
        #       -->
        # ['', '', 'schedule', 'monthly', '12th 21st eom', '3', 'auto']
        #
        # or perhaps more simply
        #
        # ';; schedule ; monthly'
        #       -->
        # ['', '', 'schedule', 'monthly']
        configitems = [x.strip() for x in line.split(SEPARATOR)]

        if len(configitems) < 4:
            raise LdgSchedulerError(
                f"Invalid schedule thing config:\n{line}\nNot enough parameters"
            )

        # remove empty strings from opening ;;, drop comment field,
        # and make sure optional fields can be referenced
        configitems = configitems[2:6] + ["", ""]

        config_label, config_intervaluom, config_days, config_interval = configitems[:4]

        if config_label.lower() != THING_CONFIG_LABEL:
            raise LdgSchedulerError(
                f"Invalid schedule thing config:\n{line}\n"
                f'"{THING_CONFIG_LABEL}" '
                "label not found in expected place."
            )

        interval_uom_regex = (
            "(daily|weekly|monthly|bimonthly|quarterly|biannual|yearly)"
        )

        match = re.match(interval_uom_regex, config_intervaluom)
        if not match:
            raise LdgSchedulerError(
                f"Invalid schedule thing config:\n{line}\nInterval UOM "
                f'"{config_intervaluom}" not recognized. Supported UOMs: daily, '
                "weekly, monthly, bimonthly, quarterly, biannual, yearly."
            )

        intervaluom = match.group(1).lower()

        if not config_days.strip():
            config_days = str(self.thing_date.day)

        match = re.match(r"[^\d]*(\d+).*", config_interval)
        interval = 1
        if match:
            interval = int(match.group(1))

        uom_translations = {"bimonthly": 2, "quarterly": 3, "biannual": 6, "yearly": 12}

        if intervaluom in uom_translations:
            interval *= uom_translations[intervaluom]

        if intervaluom not in [INTERVAL_DAY, INTERVAL_WEEK]:
            intervaluom = INTERVAL_MONTH

        self.interval = interval
        self.interval_uom = intervaluom

        day_string = config_days.lower()
        self.days = []
        days_regex = r"(\d+|eom(?:\d\d?)?)"
        for match in re.finditer(days_regex, day_string):
            if match.groups()[0].isdigit():
                theday = match.groups()[0].zfill(2)  # format for sorting
            else:
                theday = match.groups()[0]  # e.g. eom

            self.days.append(theday)

        self.days.sort()

    def get_scheduled_entries(self):
        entries = []
        while self.thing_date <= ScheduleThing.entry_boundary_date:
            entries.append(self.get_entry_thing())
            self.thing_date = self.get_next_date(self.thing_date)

        return entries

    def get_entry_thing(self):
        entry_lines = list(self.lines)
        del entry_lines[LINE_SCHEDULE]
        entry_lines[LINE_DATE] = re.sub(
            DATE_REGEX, self.get_date_string(), entry_lines[LINE_DATE]
        )
        return LedgerThing(entry_lines)

    def get_next_date(self, previousdate):

        if self.interval_uom == INTERVAL_DAY:
            return previousdate + relativedelta(days=self.interval)
        elif self.interval_uom == INTERVAL_WEEK:
            return previousdate + relativedelta(weeks=self.interval)
        else:  # INTERVAL_MONTH
            # first see if any scheduled days remaining in same month
            for scheduleday in self.days:
                scheduleday = self.get_month_day(scheduleday, previousdate)
                # compare with greater so we don't keep matching same
                if scheduleday > previousdate.day:
                    return self.get_safe_date(previousdate, scheduleday)

            # advance to next month (by specified interval)

            nextdate = previousdate + relativedelta(months=self.interval)

            return self.get_safe_date(
                nextdate, self.get_month_day(self.days[0], nextdate)
            )

    # handle situations like 8/31 -> 9/31 (back up to 9/30)
    @staticmethod
    def get_safe_date(thedate, theday):
        try:
            return date(thedate.year, thedate.month, theday)
        except ValueError:
            # day is out of range for month, so we'll get the last day of
            # month (may be unlikely now that we check last_day_of_month
            # in get_month_day)
            return date(
                thedate.year, thedate.month, monthrange(thedate.year, thedate.month)[1]
            )

    # knows how to handle "eom"
    def get_month_day(self, scheduleday, currentdate):

        last_day_of_month = monthrange(currentdate.year, currentdate.month)[1]

        if str(scheduleday).isdigit():
            if int(scheduleday) > last_day_of_month:
                return last_day_of_month
            else:
                return int(scheduleday)

        if scheduleday == EOM:
            return last_day_of_month

        # EOM30
        if last_day_of_month >= 30:
            return 30
        else:
            return last_day_of_month  # february

    @staticmethod
    def get_week_day():
        return ERROR_RETURN_VALUE

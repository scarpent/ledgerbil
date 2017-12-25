from textwrap import dedent

from ..schedulefile import ScheduleFile
from .filetester import FileTester
from .schedulething_tester import ScheduleThingTester


class ScheduleFileTests(ScheduleThingTester):

    scheduledata = dedent('''\
        ;; scheduler ; enter 45 days

        2016/10/31 absolute insurance
            ;; schedule ; monthly ; 15 ; 6 ; auto
            e: car: insurance
            l: credit card                          $-425

        2007/07/07 lightning energy
            ;; schedule ; monthly ; 12th 21st; ; auto
            e: bills: electricity
            a: checking up                          $-75

        2018/03/23 lorem ipsum
            ;; schedule ; monthly ; 15 ; 6 ; auto
            e: dolor
            a: cash                                 $-45
        ''')

    def test_next_scheduled_transaction(self):

        with FileTester.temp_input(self.scheduledata) as tempfilename:
            schedulefile = ScheduleFile(tempfilename)

        self.assertEqual(
            '2007/07/07',
            schedulefile.next_scheduled_date()
        )

    def test_next_scheduled_transaction_no_next(self):
        no_next = ''';; scheduler ; enter 45 days'''

        with FileTester.temp_input(no_next) as tempfilename:
            schedulefile = ScheduleFile(tempfilename)

        self.assertEqual('', schedulefile.next_scheduled_date())

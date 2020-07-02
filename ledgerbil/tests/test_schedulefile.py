from textwrap import dedent

from ..schedulefile import ScheduleFile
from . import filetester as FT

schedule_testdata = dedent(
    """\
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
    """
)


def test_next_scheduled_transaction():
    with FT.temp_file(schedule_testdata) as tempfilename:
        schedulefile = ScheduleFile(tempfilename)
    assert schedulefile.next_scheduled_date() == "2007/07/07"


def test_next_scheduled_transaction_no_next():
    scheduler_data = ";; scheduler ; enter 45 days"
    with FT.temp_file(scheduler_data) as tempfilename:
        schedulefile = ScheduleFile(tempfilename)
    assert schedulefile.next_scheduled_date() == ""


def test_add_thing_with_no_lines():
    scheduler_data = ";; scheduler ; enter 45 days"
    with FT.temp_file(scheduler_data) as tempfilename:
        schedulefile = ScheduleFile(tempfilename)

    assert len(schedulefile.things) == 1
    schedulefile.add_thing_from_lines([])
    assert len(schedulefile.things) == 1

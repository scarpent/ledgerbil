# inspect.stack()[1][3] gives name of calling function
import inspect
import os
import tempfile
from contextlib import contextmanager
from shutil import copyfile


class FileTester(object):

    path = os.path.dirname(__file__)
    testdir = os.path.join(path, 'files')

    testfile = os.path.join(testdir, 'test.ledger')
    sortedfile = os.path.join(testdir, 'test-already-sorted.ledger')
    alpha_unsortedfile = os.path.join(testdir, 'test-alpha-unsorted.ledger')
    alpha_sortedfile = os.path.join(testdir, 'test-alpha-sorted.ledger')
    readonlyfile = os.path.join(testdir, 'test-read-only.ledger')

    testschedulefileledger = os.path.join(testdir, 'test-schedule.ledger')
    test_enter_lessthan1 = os.path.join(
        testdir,
        'test-schedule-enter-days-lt1.ldg'
    )

    test_rec_multiple_match = os.path.join(
        testdir,
        'reconcile-multiple-match.ldg'
    )
    test_reconcile = os.path.join(testdir, 'reconcile.ledger')

    CACHE_FILE_TEST = os.path.join(testdir, '.ledgerbil_cache_test')

    @staticmethod
    def create_temp_file(testdata):
        temp_file = os.path.join(
            FileTester.testdir,
            f'temp_{inspect.stack()[1][3]}'
        )
        with open(temp_file, 'w') as f:
            f.write(testdata)
        return temp_file

    @staticmethod
    def copy_to_temp_file(filename):
        temp_file = os.path.join(
            FileTester.testdir,
            f'temp_{inspect.stack()[1][3]}'
        )
        copyfile(filename, temp_file)
        return temp_file

    @staticmethod
    def read_file(filename):
        with open(filename, 'r') as f:
            return f.read()

    @staticmethod
    def write_to_temp_file(filename, testdata):
        temp_file = f'{filename}_temp'
        with open(temp_file, 'w') as f:
            f.write(testdata)
        return temp_file

    @staticmethod
    @contextmanager
    def temp_input(data):
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp:
            temp.write(data)
        yield temp.name
        os.unlink(temp.name)

    @staticmethod
    def delete_test_cache_file():
        if os.path.exists(FileTester.CACHE_FILE_TEST):
            os.remove(FileTester.CACHE_FILE_TEST)

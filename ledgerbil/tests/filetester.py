import os
import tempfile
from contextlib import contextmanager

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


def read_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return f.read()


@contextmanager
def temp_file(data):
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp:
        temp.write(data)
    yield temp.name
    os.unlink(temp.name)


def delete_test_cache_file():
    if os.path.exists(CACHE_FILE_TEST):
        os.remove(CACHE_FILE_TEST)

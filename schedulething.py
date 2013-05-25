#!/usr/bin/python

"""objects in ledger file: transactions, etc"""

from __future__ import print_function

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'

import re

from ledgerthing import LedgerThing


class ScheduleThing(LedgerThing):

    firstLineRegex = r'''(?x)               # verbose mode
        ^                                   # line start
        \s+;;\s+scheduler\s+                # required
        (?:                                 # non-capturing
            ;\s+enter\s+(\d+)\s+days?\s+    # days ahead to enter trans
        )?                                  # optional
        (?:                                 # non-capturing
            ;\s+preview\s+(\d+)\s+days?\s+  # days to "preview" trans
        )?                                  # optional
        (?:\s;\s)?                          # optional ending semi-colon
        $                                   # line end
        '''


    def __init__(self, lines):
        super(ScheduleThing, self).__init__(lines)

        # if thingCounter == 1:
        #     match = re.match(self.firstLineRegex, lines[0])
        #     if match:
        #         if match.group(1):
        #             print('first match = %s' % match.group(1))
        #         if match.group(2):
        #             print('second match = %s' % match.group(2))
        # else:
        #     print('not a valid schedule file')

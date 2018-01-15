# ledgerbil

A small rodent-like program for working with ledger-cli journals.

Hi. I'm a personal finance enthusiast. Keeping my records organized and
analyzable is a soothing and reassuring activity for me. I used
Microsoft Money from 1995 to 2007, KMyMoney from 2008 to 2012, and
Ledger from 2013 to this very moment. Ledger is nifty:

http://www.ledger-cli.org/

It's strictly a reporting tool. From the web site: "Ledger never creates
or modifies your data. Your entries are kept in a text file that you
maintain, and you can rest assured, no automated tool will ever change
that data."

That is, no automated tool within the Ledger program itself. But you can
create or find tools to help with various data entry and reconciliation
chores.

At a minimum, all you really need is a text editor for data entry. I'm
using Sublime Text for my journal, and with the syntax highlighting
files included in this repo, I find it pleasant to work with and look
upon:

![ledger file with syntax highlighting](docs/images/ledger-syntax-highlighting.png "Syntax Highlighting")

Yet, being deluded, we desire to use the power of software to make our
lives easier, and seek out ways to lessen our drudgery.

Ledgerbil's features:
  * Automate the entry of recurring transactions via a scheduler.
  * Interactively reconcile accounts.
  * Sort a file by transaction date.

I don't use many of ledger's features and options, so your mileage may
vary for your own data. Please backup before trying, or make sure your
changes are committed to the source control system you certainly should
be using.

Ledgerbil will assume a properly formatted ledger file, although it
won't necessarily enforce rules or report problems with an input file.
It will be best to feed it files that run cleanly through ledger-cli.

Here is the current state of --help, which reflects the current state
of exciting features:

## --help

    usage: ledgerbil/main.py [-h] [-f FILE] [-S] [-r ACCT] [-s FILE] [-n]

    optional arguments:
      -h, --help                 show this help message and exit
      -f FILE, --file FILE       ledger file to be processed
      -S, --sort                 sort the file by transaction date
      -r ACCT, --reconcile ACCT  interactively reconcile the specified account
      -s FILE, --schedule FILE   file with scheduled transactions (to be added to
                                 -f ledger file)
      -n, --next-scheduled-date  show the date of the next scheduled transaction

    other commands (run with -h to see command help):
        ledgerbil/main.py investments (or inv)
        ledgerbil/main.py prices

### --sort

Ledgerbil understands a transaction as something that starts with a date
in the first position, like so:

    2013/05/11 abc store
        expenses: leisure: games
        liabilities: credit card                $-12.34


If there are comment lines or things it doesn't currently understand
(e.g. lines starting with `payee` or `account`), it will glom these
together with the nearest transaction that comes before, so that the
ordering of things will be maintained accordingly. If these items occur
before any dated transactions, they will be given a date in 1899 to
(most likely) keep them before your other transactions.

### --schedule

The schedule file handles recurring transactions and has two levels of configuration.

And the top of the file, for example::

    ;; scheduler ; enter 40 days

This determines how many days ahead transactions should be entered into the specified ledger file. Perhaps you'll run:

    python main.py --file journal.ledger --schedule schedule.ldg

This will read the ``schedule.ldg`` file and create new entries in ``journal.ledger`` up to 40 days into THE FUTURE. ``schedule.ldg`` will also be updated to reflect next dates.

(More to doc here...)

### --reconcile ACCT

Interactively reconcile the account matching ACCT string.

Help is available at the interactive prompt:

    > help

    Documented commands (type help <topic>):
    ========================================
    account  finish  list  quit    show       unmark
    aliases  help    mark  reload  statement

As mentioned above, this is targeted for my own usage, although may be
suitable for those with similar needs, perhaps requiring a bit of work.
(I didn't spend time on some scenarios that I would address if,
miraculously, someone else cared about them. And there are other
scenarios I won't address in any circumstance, given my aims here.)

The reconciler will error if more than one matching account is found.
Aliases aren't resolved so the same account will be seen as different if
it occurs in aliased and non-aliased form. (I keep my alias definitions
in a separate account file.)

If multiple entries for the account occur in one transaction, they'll be
treated as one amount and line item while reconciling. If they have
different statuses initially, there'll be an error. (When in sync,
they'll be updated to pending/cleared status together.)

The reconciler will total up all cleared (\*) transactions to get what
should be the "last statement balance," but only shows pending and
uncleared transactions.

For an example file:

    2016/10/21 dolor
        i: sit amet
      * a: cash         $100

    2016/10/26 lorem
        e: consectetur adipiscing elit
        a: cash         $-10

    2016/10/29 ipsum
        e: sed do eiusmod
        a: cash         $-20

##### list

(Note that there is pretty coloring in real life.)

    $ ./ledgerbil.py -f xyz.ldg -r cash

       1. 2016/10/26    $-10.00   lorem
       2. 2016/10/29    $-20.00   ipsum

    ending date: 2016/10/29 ending balance: (not set) cleared: $100.00

    >

##### statement

Will prompt you for the statement ending date and ending balance.

    > statement
    Ending Date (YYYY/MM/DD) [2016/10/29]:
    Ending Balance []: 70

       1. 2016/10/26    $-10.00   lorem
       2. 2016/10/29    $-20.00   ipsum

    ending date: 2016/10/29 ending balance: $70.00 cleared: $100.00
    to zero: $-30.00

Only transactions on or before that date will be shown, with the
exception of pending transactions. All pending transactions are included
regardless of date because they're needed to make the math work.

You can mark and unmark transactions without the ending balance but you
can't finish balancing and convert pending transactions to cleared.

Reconciler doesn't understand asset versus liability accounts so you'll
want to give a positive amount for assets and negative for liability,
assuming the normal state of these kinds of accounts.

Statement ending info is saved to ~/.ledgerbil and restored when the
reconciler is restarted.

##### mark / unmark

Set transactions as pending (!) or remove the pending mark. You can
enter multiple lines, "all", or give a single number by itself with no
command.

    > mark 1 2  (or)  1  (or)

    > mark all

    1. 2016/10/26    $-10.00 ! lorem
    2. 2016/10/29    $-20.00 ! ipsum

    ending date: 2016/10/29 ending balance: $70.00 cleared: $100.00
    to zero: $0.00

The ledger file is saved after every mark/unmark command.

Ledger allows a lot of flexibility in file formatting, and in general,
ledgerbil attempts to preserve all formatting, but in this case, for
simplicity's sake, ledgerbil maintains and enforces a four space indent
for transaction entries, with the ! or * going in the third "space" when
present. (It wouldn't be *that* hard to make it smarter about this, but
I didn't want to deal with some edge cases in the initial
implementation.) The reconciler only works with individual account
entries; never the whole transaction on the top line.

##### show

Show transaction details

    > show 2
    
    2016/10/26 lorem
        e: consectetur adipiscing elit
        a: cash         $-10

##### reload

Reload the ledger file from storage.

Ledgerbil loads the entire file into memory when it starts, and writes
after mark/unmark operations. This command lets you make an update
outside of the reconciler (e.g. in an editor) and refresh without having
to restart the program.

##### finish

If "to zero" is 0, this command will update all pending (!) entries for
the account to cleared (\*) and save the file.

    > finish

    ending date: 2016/10/29 ending balance: (not set) cleared: $70.00

### license

GPL v3 or greater



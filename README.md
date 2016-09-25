# ledgerbil

A small rodent-like program for working with ledger-cli journals.

Hi. I'm a personal finance enthusiast. Keeping my records organized
and analyzable has always been a soothing and reassuring activity for
me. I used Microsoft Money from 1995 to 2007, KMyMoney from 2008 to
2012, and Ledger from 2013 to this very moment. Ledger is nifty:

http://www.ledger-cli.org/

It's strictly a reporting tool. From the web site: "Ledger never creates
or modifies your data. Your entries are kept in a text file that you
maintain, and you can rest assured, no automated tool will ever change
that data."

That is, no automated tool within the Ledger program itself. But you can
create or find tools to help with various data entry and reconciliation
chores.

At a minimum, all you really need is a text editor. I'm using Sublime
Text to manage my journal, and with syntax highlighting and regular
expressions, it handles the job well.

But! We desire to use the power of software to make our lives easier.
(We're deluded that way.)

I first wanted to automate the entry of recurring transactions, and
this is ledgerbil's main function at the moment.

Ledgerbil can also sort a file by transaction date.

I'm rather narrow-mindedly focusing on supporting the subset of
ledger-cli that I'm actually using, and that is reflected in my
transactional journal file. (And in the included unit tests.)

Ledgerbil will assume a properly formatted ledger file, although it
won't necessarily enforce rules or report problems with an input file.
It will be best to feed it files that run cleanly through ledger-cli.

Here is the current state of --help, which reflects the current state
of exciting features:

## --help

    usage: ledgerbil.py [-h] -f FILE [-s] [-S FILE] [-p FILE]

    optional arguments:
      -h, --help            show this help message and exit
      -f FILE, --file FILE  ledger file to be processed
      -s, --sort            sort the file by transaction date
      -S FILE, --schedule-file FILE
                            file with scheduled transactions (to be added to -f
                            ledger file)

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

### --schedule-file

to do: documenting of this thing

### license

GPL v3 or greater



#!/usr/bin/python

from unittest import TestCase

import util


__author__ = 'Scott Carpenter'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'


class UtilTests(TestCase):

    def test_eval_expr(self):
        self.assertEqual(-100, util.eval_expr('-100'))
        self.assertEqual(4, util.eval_expr('2^6'))
        self.assertEqual(64, util.eval_expr('2**6'))
        self.assertEqual(
            -5,
            util.eval_expr('1 + 2*3**(4^5) / (6 + -7)')
        )
        self.assertEqual(
            12.873000000000001,
            util.eval_expr('12*1.07275')
        )
        self.assertEqual(-2, util.eval_expr('~1'))  # invert
        with self.assertRaises(TypeError):
            util.eval_expr('a')

'''
Created on 2011/09/15

@author: toshihiro
'''
import unittest

from pyrem_torq.treeseq import *

class TestTorqTreeseq(unittest.TestCase):
    def testRemoveStrattrs(self):
        seq = [ 'a', 1, 'b', 2, 'c' ]
        self.assertEquals(seq_remove_strattrs(seq), [ 'a', 'b', 'c' ])
    
        seq = [ 'a', [ 'B', 1, 'b' ], 2, 'c' ]
        self.assertEquals(seq_remove_strattrs(seq), [ 'a', [ 'B', 'b' ], 'c' ])
    
    def testEncloseStrattrs(self):
        seq = [ 'a', 1, 'b', 2, 'c' ]
        self.assertEquals(seq_enclose_strattrs(seq), [ 'a', ( 1, 'b' ), ( 2, 'c' ) ])
    
        seq = [ 'a', [ 'B', 1, 'b' ], 2, 'c' ]
        self.assertEquals(seq_enclose_strattrs(seq), [ 'a', [ 'B', ( 1, 'b' ) ], ( 2, 'c' ) ])
        
    def testEncloseStrattrsToIllegalData(self):
        seq = [ 'a', 1, 'b', 'c' ]
        with self.assertRaises(IndexError):
            seq_enclose_strattrs(seq)
    
        seq = [ 'a', [ 'B', 1, 'b' ], 'c' ]
        with self.assertRaises(IndexError):
            seq_enclose_strattrs(seq)
        
    def testDiscloseStrattrs(self):
        seq = [ 'a', ( 1, 'b' ), ( 2, 'c' ) ]
        self.assertEquals(seq_disclose_strattrs(seq), [ 'a', 1, 'b', 2, 'c' ])

        seq = [ 'a', [ 'B', ( 1, 'b' ) ], ( 2, 'c' ) ]
        self.assertEquals(seq_disclose_strattrs(seq), [ 'a', [ 'B', 1, 'b' ], 2, 'c' ])
        
    def testDiscloseStrattrsToIllegalData(self):
        seq = [ 'a', ( 1, 'b' ), 'c' ]
        with self.assertRaises(TypeError):
            seq_disclose_strattrs(seq)

        seq = [ 'a', [ 'B', ( 1, 'b' ) ], 'c' ]
        with self.assertRaises(TypeError):
            seq_disclose_strattrs(seq)

import numpy as np
import random
from unittest import TestCase
from HighCamera import HighCamera

def fake_bytearray(leng=13):
    arr = bytearray(leng)
    for i,v in enumerate(arr):
        arr[i]= random.randint(0,255)
    return arr
def try_to_print(a):
    try:
        print a
    except Exception as e:
        print("sorry, couldn't print:%s", e.message)

class TestHighCamera(TestCase):
    def test_process_row(self):
        hc = HighCamera(port="test")
        barr = fake_bytearray(80)
        hc.process_row(barr)
        shape = hc.last_frame.shape
        self.assertEquals(shape, (120, 160),
                          msg="generated frame is has not the expectd shape, but:"+str(shape))
        # all_zeros = np.count_nonzero(hc.last_frame) < 1
        # self.assertFalse(all_zeros, msg="generated frame contains only zeroes"+barr)

    def test_process_row_2b(self):
        hc = HighCamera(port="test")
        barr = fake_bytearray(13)
        row = hc.process_row_2b(barr)
        print ("array should conatain only 255 or 0", [x for x in row])
        """ the lenght has to be 81 because: 80 data + 1 byte that tell the row number"""
        self.assertEqual(len(row), 81, msg="length not correct")





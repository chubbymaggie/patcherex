#!/usr/bin/env python

import os
import nose
import struct
import subprocess

import patcherex
from patcherex.backends.basebackend import BaseBackend
from patcherex.patches import *


# TODO ideally these tests should be run in the vm

bin_location = str(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../binaries-private'))
qemu_location = str(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../tracer/bin/tracer-qemu-cgc"))

'''
This "old" version of QEMU works like a "normal" QEMU, failing to transmit partially invalid memory regions.
This is the commit I used (from cgc/tracer):

commit 46df5a786f0db52f0eb8c3524dc16732e58f204a
Merge: 9c1b3f3 d859fd7
Author: Nick Stephens <nick.d.stephens@gmail.com>
Date:   Fri Feb 5 14:26:30 2016 -0800
'''
old_qemu_location = str(os.path.join(os.path.dirname(os.path.realpath(__file__)), "old_tracer-qemu-cgc"))


def test_shadowstack():
    from patcherex.techniques.shadowstack import ShadowStack
    filepath = os.path.join(bin_location, "cgc_trials/CADET_00003")
    pipe = subprocess.PIPE

    p = subprocess.Popen([qemu_location, filepath], stdin=pipe, stdout=pipe, stderr=pipe)
    res = p.communicate("\x00"*1000+"\n")
    print res, p.returncode
    nose.tools.assert_equal((p.returncode == -11), True)

    with patcherex.utils.tempdir() as td:
        tmp_file = os.path.join(td, "patched")
        backend = BaseBackend(filepath)
        cp = ShadowStack(filepath, backend)
        patches = cp.get_patches()
        backend.apply_patches(patches)
        backend.save(tmp_file)

        p = subprocess.Popen([qemu_location, tmp_file], stdin=pipe, stdout=pipe, stderr=pipe)
        res = p.communicate("\x00"*100+"\n")
        print res, p.returncode
        nose.tools.assert_equal(p.returncode == 68, True)

def test_packer():
    from patcherex.techniques.packer import Packer
    filepath = os.path.join(bin_location, "cgc_trials/CADET_00003")
    pipe = subprocess.PIPE

    expected = "\nWelcome to Palindrome Finder\n\n\tPlease enter a possible palindrome: \t\tYes, that's a palindrome!\n\n\tPlease enter a possible palindrome: "
    with patcherex.utils.tempdir() as td:
        tmp_file = os.path.join(td, "patched")
        backend = BaseBackend(filepath)
        cp = Packer(filepath, backend)
        patches = cp.get_patches()
        backend.apply_patches(patches)
        backend.save(tmp_file)

        p = subprocess.Popen([qemu_location, tmp_file], stdin=pipe, stdout=pipe, stderr=pipe)
        res = p.communicate("A"*10+"\n")
        print res, p.returncode
        nose.tools.assert_equal((res[0] == expected and p.returncode == 0), True)

def test_simplecfi():
    from patcherex.techniques.simplecfi import SimpleCFI
    filepath = os.path.join(bin_location, "cgc_scored_event_2/cgc/0b32aa01_01")
    pipe = subprocess.PIPE

    p = subprocess.Popen([qemu_location, filepath], stdin=pipe, stdout=pipe, stderr=pipe)
    res = p.communicate("\x00"*1000+"\n")
    print res, p.returncode
    nose.tools.assert_equal((p.returncode == -11), True)

    #0x80480a0 is the binary entry point
    exploiting_input = "AAAA"+"\x00"*80+struct.pack("<I",0x80480a0)*20+"\n" 
    expected1 = "\nWelcome to Palindrome Finder\n\n\tPlease enter a possible palindrome: \nWelcome to Palindrome Finder\n\n\tPlease enter a possible palindrome: \t\tNope, that's not a palindrome\n\n\tPlease enter a possible palindrome: \nWelcome to Palindrome Finder\n\n\tPlease enter a possible palindrome: \nWelcome to Palindrome Finder\n\n\tPlease enter a possible palindrome: \nWelcome to Palindrome Finder\n\n\tPlease enter a possible palindrome: \nWelcome to Palindrome Finder\n\n\tPlease enter a possible palindrome: \nWelcome to Palindrome Finder\n\n\tPlease enter a possible palindrome: \nWelcome to Palindrome Finder\n\n\tPlease enter a possible palindrome: \nWelcome to Palindrome Finder\n\n\tPlease enter a possible palindrome: \nWelcome to Palindrome Finder\n\n\tPlease enter a possible palindrome: \nWelcome to Palindrome Finder\n\n\tPlease enter a possible palindrome: "

    p = subprocess.Popen([qemu_location, filepath], stdin=pipe, stdout=pipe, stderr=pipe)
    res = p.communicate(exploiting_input)
    expected_retcode = 1 #should be -11
    #TODO fix these two checks when our tracer will be fixed
    nose.tools.assert_equal((res[0][:200] == expected1[:200] and p.returncode == expected_retcode), True)

    expected2 = "\nWelcome to Palindrome Finder\n\n\tPlease enter a possible palindrome: \t\tYes, that's a palindrome!\n\n\tPlease enter a possible palindrome: "
    expected3 = "\nWelcome to Palindrome Finder\n\n\tPlease enter a possible palindrome: "
    with patcherex.utils.tempdir() as td:
        tmp_file = os.path.join(td, "patched")
        backend = BaseBackend(filepath)
        cp = SimpleCFI(filepath, backend)
        patches = cp.get_patches()
        backend.apply_patches(patches)
        backend.save(tmp_file)

        p = subprocess.Popen([qemu_location, tmp_file], stdin=pipe, stdout=pipe, stderr=pipe)
        res = p.communicate("A"*10+"\n")
        print res, p.returncode
        nose.tools.assert_equal((res[0] == expected2 and p.returncode == 0), True)

        p = subprocess.Popen([qemu_location, tmp_file], stdin=pipe, stdout=pipe, stderr=pipe)
        res = p.communicate(exploiting_input)
        print res, p.returncode
        nose.tools.assert_equal((res[0] == expected3 and p.returncode == 0x45), True)


def test_qemudetection():
    from patcherex.techniques.qemudetection import QemuDetection
    filepath = os.path.join(bin_location, "cgc_scored_event_2/cgc/0b32aa01_01")
    pipe = subprocess.PIPE

    p = subprocess.Popen([qemu_location, filepath], stdin=pipe, stdout=pipe, stderr=pipe)
    res = p.communicate("\x00"*1000+"\n")
    print res, p.returncode
    nose.tools.assert_equal((p.returncode == -11), True)

    expected = "\nWelcome to Palindrome Finder\n\n\tPlease enter a possible palindrome: \t\tYes, that's a palindrome!\n\n\tPlease enter a possible palindrome: "
    with patcherex.utils.tempdir() as td:
        tmp_file = os.path.join(td, "patched")
        backend = BaseBackend(filepath)
        cp = QemuDetection(filepath, backend)
        patches = cp.get_patches()
        backend.apply_patches(patches)
        backend.save(tmp_file)

        p = subprocess.Popen([old_qemu_location, tmp_file], stdin=pipe, stdout=pipe, stderr=pipe)
        res = p.communicate("A"*10+"\n")
        print res, p.returncode
        nose.tools.assert_equal(p.returncode == 0x40 or p.returncode == 0x41, True)

        p = subprocess.Popen([qemu_location, tmp_file], stdin=pipe, stdout=pipe, stderr=pipe)
        res = p.communicate("A"*10+"\n")
        print res, p.returncode
        nose.tools.assert_equal((res[0] == expected and p.returncode == 0), True)


def run_all():
    functions = globals()
    all_functions = dict(filter((lambda (k, v): k.startswith('test_')), functions.items()))
    for f in sorted(all_functions.keys()):
        if hasattr(all_functions[f], '__call__'):
            all_functions[f]()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        globals()['test_' + sys.argv[1]]()
    else:
        run_all()

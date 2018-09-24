"""
/*
 * Copyright (c) 2018, Henry Corrigan-Gibbs
 * 
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. 
 */


This script generates prio/params.h.
"""


# Has a subgroup of order 2^19
modulus = int('0x8000000000000000080001', 16)
# Generates the subgroup of order 2^19
gen19 = int('0x2597c14f48d5b65ed8dcca', 16)

# We want a generator of order 2^12, so compute
#   gen19^(2^7) = gen19^128   (mod p)
gen12 = gen19
for i in range(7):
    gen12 *= gen12
    gen12 %= modulus
    #print gen12

# Sanity check
rootsL = [1] * 2**12
rootsInvL = [1] * 2**12
for i in range(1, 2**12):
    rootsL[i] = (rootsL[i-1] * gen12) % modulus

assert ((rootsL[2**12 - 1] * gen12) % modulus) == 1

gen12inv = rootsL[2**12 - 1]
for i in range(1, 2**12):
    rootsInvL[i] = (rootsInvL[i-1] * gen12inv) % modulus
    
    assert rootsInvL[i] != 1 
assert ((rootsInvL[2**12 - 1] * gen12inv) % modulus) == 1

# We're going to save space by storing the roots once, and using that same
# data for both the roots and the inverse roots, so make sure we can do that.
assert rootsL[0] == rootsInvL[0]
nontrivialRoots = rootsL[1:]
nontrivialRootsInv = rootsInvL[1:]
nontrivialRootsInv.reverse()
assert nontrivialRoots == nontrivialRootsInv

# Instead of generating:
#
# static const char* const Roots[] = { "...", ... };
#
# we generate one long character array that is the equivalent of:
#
# struct roots {
#   const char r0[SIZE];
#   const char r1[SIZE];
#   ...
# };
#
# Because we're no longer storing pointers, just the raw character data,
# this storage format is smaller and can be shared between processes.
#
# We use individual characters, rather than strings, because some compilers
# reject long concatenated string constants.
def c_table(strings):
    def entry(s):
        chars = ', '.join("'%s'" % x for x in s)
        return '/* "{root}" */ {chars}, \'\\0\''.format(root=s, chars=chars)

    # Pad all strings to be the same width.
    width = max(len(s) for s in strings)
    strings = ["{root:0>{width}s}".format(root=s, width=width) for s in strings]
    # + 1 for the null terminator in each entry.
    return width + 1, ',\n    '.join(entry(s) for s in strings)

(width, table) = c_table(['%x' % x for x in rootsL])

output = """
/*
 * Copyright (c) 2018, Henry Corrigan-Gibbs
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 */

/****
 * NOTE: This file was auto-generated from scripts/gen_params.py.
 * Do not edit this file. Instead, edit the script.
 */

#ifndef __PARAMS_H__
#define __PARAMS_H__

// A prime modulus p.
static const char Modulus[] = "%(modulus)x";

// A generator g of a subgroup of Z*_p.
// static const char Generator[] = "%(generator)x";

// The generator g generates a subgroup of
// order 2^Generator2Order in Z*_p.
static const int Generator2Order = %(twoorder)d;

// Width of entries in Roots.
static const unsigned int RootWidth = %(width)d;

// clang-format off
static const char Roots[] = {
    %(roots)s
};
// clang-format on

#endif /* __PARAMS_H__ */
""" % {
    'modulus': modulus,
    'generator': gen12,
    'twoorder': 12,
    'width': width,
    'roots': table, 
}

print (output,)
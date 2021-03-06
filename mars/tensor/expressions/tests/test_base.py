#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 1999-2018 Alibaba Group Holding Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest

import numpy as np

from mars.tensor.expressions.datasource import ones, tensor, arange, array, asarray
from mars.tensor.expressions.base import transpose, broadcast_to, where, argwhere, array_split, \
    split, squeeze, digitize, result_type, repeat, copyto, isin
from mars.operands.base import CopyTo
from mars.tests.core import calc_shape


class Test(unittest.TestCase):
    def testArray(self):
        a = tensor([0, 1, 2], chunk_size=2)

        b = array(a)
        self.assertIsNot(a, b)

        c = asarray(a)
        self.assertIs(a, c)

    def testCopyto(self):
        a = ones((10, 20), chunk_size=3)
        b = ones(10, chunk_size=4)

        with self.assertRaises(ValueError):
            copyto(a, b)

        tp = type(a.op)
        b = ones(20, chunk_size=4)
        copyto(a, b)

        self.assertIsInstance(a.op, CopyTo)
        self.assertIs(a.inputs[0], b.data)
        self.assertIsInstance(a.inputs[1].op, tp)
        self.assertEqual(calc_shape(a), a.shape)

        a.tiles()

        self.assertIsInstance(a.chunks[0].op, CopyTo)
        self.assertEqual(len(a.chunks[0].inputs), 2)
        self.assertEqual(calc_shape(a.chunks[0]), a.chunks[0].shape)

        a = ones((10, 20), chunk_size=3, dtype='i4')
        b = ones(20, chunk_size=4, dtype='f8')

        with self.assertRaises(TypeError):
            copyto(a, b)

        b = ones(20, chunk_size=4, dtype='i4')
        copyto(a, b, where=b > 0)

        self.assertIsNotNone(a.op.where)
        self.assertEqual(calc_shape(a), a.shape)

        a.tiles()

        self.assertIsInstance(a.chunks[0].op, CopyTo)
        self.assertEqual(len(a.chunks[0].inputs), 3)
        self.assertEqual(calc_shape(a.chunks[0]), a.chunks[0].shape)

        with self.assertRaises(ValueError):
            copyto(a, a, where=np.ones(30, dtype='?'))

    def testAstype(self):
        arr = ones((10, 20, 30), chunk_size=3)

        arr2 = arr.astype(np.int32)
        arr2.tiles()

        self.assertEqual(arr2.shape, (10, 20, 30))
        self.assertEqual(calc_shape(arr2), arr2.shape)
        self.assertTrue(np.issubdtype(arr2.dtype, np.int32))
        self.assertEqual(arr2.op.casting, 'unsafe')
        self.assertEqual(calc_shape(arr2.chunks[0]), arr2.chunks[0].shape)

        with self.assertRaises(TypeError):
            arr.astype(np.int32, casting='safe')

    def testTranspose(self):
        arr = ones((10, 20, 30), chunk_size=[4, 3, 5])

        arr2 = transpose(arr)
        arr2.tiles()

        self.assertEqual(arr2.shape, (30, 20, 10))
        self.assertEqual(calc_shape(arr2), arr2.shape)
        self.assertEqual(len(arr2.chunks), 126)
        self.assertEqual(arr2.chunks[0].shape, (5, 3, 4))
        self.assertEqual(arr2.chunks[-1].shape, (5, 2, 2))
        self.assertEqual(calc_shape(arr2.chunks[0]), arr2.chunks[0].shape)
        self.assertEqual(calc_shape(arr2.chunks[-1]), arr2.chunks[-1].shape)

        with self.assertRaises(ValueError):
            transpose(arr, axes=(1, 0))

        arr3 = transpose(arr, (-2, 2, 0))
        arr3.tiles()

        self.assertEqual(arr3.shape, (20, 30, 10))
        self.assertEqual(calc_shape(arr3), arr3.shape)
        self.assertEqual(len(arr3.chunks), 126)
        self.assertEqual(arr3.chunks[0].shape, (3, 5, 4))
        self.assertEqual(arr3.chunks[-1].shape, (2, 5, 2))
        self.assertEqual(calc_shape(arr3.chunks[0]), arr3.chunks[0].shape)
        self.assertEqual(calc_shape(arr3.chunks[-1]), arr3.chunks[-1].shape)

        arr4 = arr.transpose(-2, 2, 0)
        arr4.tiles()

        self.assertEqual(arr4.shape, (20, 30, 10))
        self.assertEqual(calc_shape(arr4), arr4.shape)
        self.assertEqual(len(arr4.chunks), 126)
        self.assertEqual(arr4.chunks[0].shape, (3, 5, 4))
        self.assertEqual(arr4.chunks[-1].shape, (2, 5, 2))
        self.assertEqual(calc_shape(arr4.chunks[0]), arr4.chunks[0].shape)
        self.assertEqual(calc_shape(arr4.chunks[-1]), arr4.chunks[-1].shape)

        arr5 = arr.T
        arr5.tiles()

        self.assertEqual(arr5.shape, (30, 20, 10))
        self.assertEqual(calc_shape(arr5), arr5.shape)
        self.assertEqual(len(arr5.chunks), 126)
        self.assertEqual(arr5.chunks[0].shape, (5, 3, 4))
        self.assertEqual(arr5.chunks[-1].shape, (5, 2, 2))
        self.assertEqual(calc_shape(arr5.chunks[0]), arr5.chunks[0].shape)
        self.assertEqual(calc_shape(arr5.chunks[-1]), arr5.chunks[-1].shape)

    def testSwapaxes(self):
        arr = ones((10, 20, 30), chunk_size=[4, 3, 5])
        arr2 = arr.swapaxes(0, 1)
        arr2.tiles()

        self.assertEqual(arr2.shape, (20, 10, 30))
        self.assertEqual(calc_shape(arr2), arr2.shape)
        self.assertEqual(len(arr.chunks), len(arr2.chunks))
        self.assertEqual(calc_shape(arr2.chunks[-1]), arr2.chunks[-1].shape)

    def testBroadcastTo(self):
        arr = ones((10, 5), chunk_size=2)
        arr2 = broadcast_to(arr, (20, 10, 5))
        arr2.tiles()

        self.assertEqual(arr2.shape, (20, 10, 5))
        self.assertEqual(calc_shape(arr2), arr2.shape)
        self.assertEqual(len(arr2.chunks), len(arr.chunks))
        self.assertEqual(arr2.chunks[0].shape, (20, 2, 2))
        self.assertEqual(calc_shape(arr2.chunks[-1]), arr2.chunks[-1].shape)

        arr = ones((10, 5, 1), chunk_size=2)
        arr3 = broadcast_to(arr, (5, 10, 5, 6))
        arr3.tiles()

        self.assertEqual(arr3.shape, (5, 10, 5, 6))
        self.assertEqual(calc_shape(arr3), arr3.shape)
        self.assertEqual(len(arr3.chunks), len(arr.chunks))
        self.assertEqual(arr3.nsplits, ((5,), (2, 2, 2, 2, 2), (2, 2, 1), (6,)))
        self.assertEqual(arr3.chunks[0].shape, (5, 2, 2, 6))
        self.assertEqual(calc_shape(arr3.chunks[-1]), arr3.chunks[-1].shape)

        arr = ones((10, 1), chunk_size=2)
        arr4 = broadcast_to(arr, (20, 10, 5))
        arr4.tiles()

        self.assertEqual(arr4.shape, (20, 10, 5))
        self.assertEqual(calc_shape(arr4), arr4.shape)
        self.assertEqual(len(arr4.chunks), len(arr.chunks))
        self.assertEqual(arr4.chunks[0].shape, (20, 2, 5))
        self.assertEqual(calc_shape(arr4.chunks[-1]), arr4.chunks[-1].shape)

        with self.assertRaises(ValueError):
            broadcast_to(arr, (10,))

        with self.assertRaises(ValueError):
            broadcast_to(arr, (5, 1))

    def testWhere(self):
        cond = tensor([[True, False], [False, True]], chunk_size=1)
        x = tensor([1, 2], chunk_size=1)
        y = tensor([3, 4], chunk_size=1)

        arr = where(cond, x, y)
        arr.tiles()

        self.assertEqual(len(arr.chunks), 4)
        self.assertEqual(calc_shape(arr), arr.shape)
        self.assertTrue(np.array_equal(arr.chunks[0].inputs[0].op.data, [[True]]))
        self.assertTrue(np.array_equal(arr.chunks[0].inputs[1].op.data, [1]))
        self.assertTrue(np.array_equal(arr.chunks[0].inputs[2].op.data, [3]))
        self.assertTrue(np.array_equal(arr.chunks[1].inputs[0].op.data, [[False]]))
        self.assertTrue(np.array_equal(arr.chunks[1].inputs[1].op.data, [2]))
        self.assertTrue(np.array_equal(arr.chunks[1].inputs[2].op.data, [4]))
        self.assertTrue(np.array_equal(arr.chunks[2].inputs[0].op.data, [[False]]))
        self.assertTrue(np.array_equal(arr.chunks[2].inputs[1].op.data, [1]))
        self.assertTrue(np.array_equal(arr.chunks[2].inputs[2].op.data, [3]))
        self.assertTrue(np.array_equal(arr.chunks[3].inputs[0].op.data, [[True]]))
        self.assertTrue(np.array_equal(arr.chunks[3].inputs[1].op.data, [2]))
        self.assertTrue(np.array_equal(arr.chunks[3].inputs[2].op.data, [4]))
        self.assertEqual(calc_shape(arr.chunks[0]), arr.chunks[0].shape)

        with self.assertRaises(ValueError):
            where(cond, x)

        x = arange(9.).reshape(3, 3)
        y = where(x < 5, x, -1)

        self.assertEqual(y.dtype, np.float64)

    def testArgwhere(self):
        cond = tensor([[True, False], [False, True]], chunk_size=1)
        indices = argwhere(cond)

        self.assertTrue(np.isnan(indices.shape[0]))
        self.assertEqual(indices.shape[1], 2)
        self.assertEqual(calc_shape(indices), indices.shape)
        self.assertEqual(indices.op.calc_rough_shape(tuple(t.rough_shape for t in indices.inputs)), (4, 2))
        self.assertEqual(indices.rough_nbytes, 4 * 2 * indices.dtype.itemsize)

        indices.tiles()

        self.assertEqual(indices.nsplits[1], (1, 1))

        chunk = indices.chunks[0]
        self.assertTrue(np.isnan(calc_shape(chunk)[0]))
        self.assertEqual(calc_shape(chunk)[1], chunk.shape[1])
        self.assertEqual(chunk.rough_shape, (2, 1))

    def testArraySplit(self):
        a = arange(8, chunk_size=2)

        splits = array_split(a, 3)
        self.assertEqual(len(splits), 3)
        self.assertEqual([s.shape[0] for s in splits], [3, 3, 2])
        self.assertTrue(all(calc_shape(s) == ((3,), (3,), (2,)) for s in splits))

        splits[0].tiles()
        self.assertEqual(splits[0].nsplits, ((2, 1),))
        self.assertEqual(splits[1].nsplits, ((1, 2),))
        self.assertEqual(splits[2].nsplits, ((2,),))
        self.assertEqual(calc_shape(splits[0].chunks[0]), splits[0].chunks[0].shape)
        self.assertEqual(calc_shape(splits[1].chunks[0]), splits[1].chunks[0].shape)
        self.assertEqual(calc_shape(splits[2].chunks[0]), splits[2].chunks[0].shape)

        a = arange(7, chunk_size=2)

        splits = array_split(a, 3)
        self.assertEqual(len(splits), 3)
        self.assertEqual([s.shape[0] for s in splits], [3, 2, 2])
        self.assertTrue(all(calc_shape(s) == ((3,), (2,), (2,)) for s in splits))

        splits[0].tiles()
        self.assertEqual(splits[0].nsplits, ((2, 1),))
        self.assertEqual(splits[1].nsplits, ((1, 1),))
        self.assertEqual(splits[2].nsplits, ((1, 1),))
        self.assertEqual(calc_shape(splits[0].chunks[0]), splits[0].chunks[0].shape)
        self.assertEqual(calc_shape(splits[1].chunks[0]), splits[1].chunks[0].shape)
        self.assertEqual(calc_shape(splits[2].chunks[0]), splits[2].chunks[0].shape)

    def testSplit(self):
        a = arange(9, chunk_size=2)

        splits = split(a, 3)
        self.assertEqual(len(splits), 3)
        self.assertTrue(all(s.shape == (3,) for s in splits))
        self.assertTrue(all(calc_shape(s) == ((3,), (3,), (3,)) for s in splits))

        splits[0].tiles()
        self.assertEqual(splits[0].nsplits, ((2, 1),))
        self.assertEqual(splits[1].nsplits, ((1, 2),))
        self.assertEqual(splits[2].nsplits, ((2, 1),))
        self.assertEqual(calc_shape(splits[0].chunks[0]), splits[0].chunks[0].shape)
        self.assertEqual(calc_shape(splits[1].chunks[0]), splits[1].chunks[0].shape)
        self.assertEqual(calc_shape(splits[2].chunks[0]), splits[2].chunks[0].shape)

        a = arange(8, chunk_size=2)

        splits = split(a, [3, 5, 6, 10])
        self.assertEqual(len(splits), 5)
        self.assertEqual(splits[0].shape, (3,))
        self.assertEqual(splits[1].shape, (2,))
        self.assertEqual(splits[2].shape, (1,))
        self.assertEqual(splits[3].shape, (2,))
        self.assertEqual(splits[4].shape, (0,))
        self.assertTrue(all(calc_shape(s) == ((3,), (2,), (1,), (2,), (0,)) for s in splits))

        splits[0].tiles()
        self.assertEqual(splits[0].nsplits, ((2, 1),))
        self.assertEqual(splits[1].nsplits, ((1, 1),))
        self.assertEqual(splits[2].nsplits, ((1,),))
        self.assertEqual(splits[3].nsplits, ((2,),))
        self.assertEqual(splits[4].nsplits, ((0,),))
        self.assertEqual(calc_shape(splits[0].chunks[0]), splits[0].chunks[0].shape)
        self.assertEqual(calc_shape(splits[1].chunks[0]), splits[1].chunks[0].shape)
        self.assertEqual(calc_shape(splits[2].chunks[0]), splits[2].chunks[0].shape)
        self.assertEqual(calc_shape(splits[3].chunks[0]), splits[3].chunks[0].shape)
        self.assertEqual(calc_shape(splits[4].chunks[0]), splits[4].chunks[0].shape)

    def testSqueeze(self):
        data = np.array([[[0], [1], [2]]])
        x = tensor(data)

        t = squeeze(x)
        self.assertEqual(t.shape, (3,))
        self.assertIsNotNone(t.dtype)
        self.assertEqual(calc_shape(t), t.shape)

        t = squeeze(x, axis=0)
        self.assertEqual(t.shape, (3, 1))
        self.assertEqual(calc_shape(t), t.shape)

        with self.assertRaises(ValueError):
            squeeze(x, axis=1)

        t = squeeze(x, axis=2)
        self.assertEqual(t.shape, (1, 3))
        self.assertEqual(calc_shape(t), t.shape)

    def testDigitize(self):
        x = tensor(np.array([0.2, 6.4, 3.0, 1.6]), chunk_size=2)
        bins = np.array([0.0, 1.0, 2.5, 4.0, 10.0])
        inds = digitize(x, bins)

        self.assertEqual(inds.shape, (4,))
        self.assertIsNotNone(inds.dtype)
        self.assertEqual(calc_shape(inds), inds.shape)

        inds.tiles()

        self.assertEqual(len(inds.chunks), 2)
        self.assertEqual(calc_shape(inds.chunks[0]), inds.chunks[0].shape)

    def testResultType(self):
        x = tensor([2, 3], dtype='i4')
        y = 3
        z = np.array([3, 4], dtype='f4')

        r = result_type(x, y, z)
        e = np.result_type(x.dtype, y, z)
        self.assertEqual(r, e)

    def testRepeat(self):
        a = arange(10, chunk_size=2).reshape(2, 5)

        t = repeat(a, 3)
        self.assertEqual(t.shape, (30,))
        self.assertEqual(calc_shape(t), t.shape)

        t = repeat(a, 3, axis=0)
        self.assertEqual(t.shape, (6, 5))
        self.assertEqual(calc_shape(t), t.shape)

        t = repeat(a, 3, axis=1)
        self.assertEqual(t.shape, (2, 15))
        self.assertEqual(calc_shape(t), t.shape)

        t = repeat(a, [3], axis=1)
        self.assertEqual(t.shape, (2, 15))
        self.assertEqual(calc_shape(t), t.shape)

        t = repeat(a, [3, 4], axis=0)
        self.assertEqual(t.shape, (7, 5))
        self.assertEqual(calc_shape(t), t.shape)

        with self.assertRaises(ValueError):
            repeat(a, [3, 4], axis=1)

        a = tensor(np.random.randn(10), chunk_size=5)

        t = repeat(a, 3)
        t.tiles()
        self.assertEqual(sum(t.nsplits[0]), 30)
        self.assertEqual(calc_shape(t.chunks[0]), t.chunks[0].shape)

        a = tensor(np.random.randn(100), chunk_size=10)

        t = repeat(a, 3)
        t.tiles()
        self.assertEqual(sum(t.nsplits[0]), 300)
        self.assertEqual(calc_shape(t.chunks[0]), t.chunks[0].shape)

        a = tensor(np.random.randn(4))
        b = tensor((4,))

        t = repeat(a, b)
        self.assertEqual(calc_shape(t), t.shape)
        self.assertEqual(t.rough_shape, (4,))

        t.tiles()
        self.assertTrue(np.isnan(t.nsplits[0]))
        self.assertEqual(calc_shape(t.chunks[0]), t.chunks[0].shape)
        self.assertEqual(t.chunks[0].rough_shape, (4,))

    def testIsIn(self):
        element = 2 * arange(4, chunk_size=1).reshape(2, 2)
        test_elements = [1, 2, 4, 8]

        mask = isin(element, test_elements)
        self.assertEqual(mask.shape, (2, 2))
        self.assertEqual(mask.dtype, np.bool_)
        self.assertEqual(calc_shape(mask), mask.shape)

        mask.tiles()

        self.assertEqual(len(mask.chunks), len(element.chunks))
        self.assertEqual(len(mask.op.test_elements.chunks), 1)
        self.assertIs(mask.chunks[0].inputs[0], element.chunks[0].data)
        self.assertEqual(calc_shape(mask.chunks[0]), mask.chunks[0].shape)

        element = 2 * arange(4, chunk_size=1).reshape(2, 2)
        test_elements = tensor([1, 2, 4, 8], chunk_size=2)

        mask = isin(element, test_elements, invert=True)
        self.assertEqual(mask.shape, (2, 2))
        self.assertEqual(mask.dtype, np.bool_)
        self.assertEqual(calc_shape(mask), mask.shape)

        mask.tiles()

        self.assertEqual(len(mask.chunks), len(element.chunks))
        self.assertEqual(len(mask.op.test_elements.chunks), 1)
        self.assertIs(mask.chunks[0].inputs[0], element.chunks[0].data)
        self.assertTrue(mask.chunks[0].op.invert)
        self.assertEqual(calc_shape(mask.chunks[0]), mask.chunks[0].shape)

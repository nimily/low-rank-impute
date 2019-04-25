from typing import Tuple, List, Any

import numpy as np
import numpy.linalg as npl

from .measurement import Measurement, RowMeasurement, EntryMeasurement


class SampleSet:

    def __init__(self, shape):
        self.shape = shape

        self.xs: List[Measurement] = []
        self.ys: List[float] = []

    def add_all_obs(self, xs, ys):
        xs, ys = self._preprocess_all_obs(xs, ys)

        self.xs.extend(xs)
        self.ys.extend(ys)

    def _preprocess_all_obs(self, xs: List[Any], ys: List[float])\
            -> Tuple[List[Measurement], List[float]]:

        obs = [self._preprocess_obs(x, y) for x, y in zip(xs, ys)]

        xs = [x for x, _ in obs]
        ys = [y for _, y in obs]

        return xs, ys

    def _preprocess_obs(self, x: Any, y: float) -> Tuple[Measurement, float]:
        assert isinstance(x, Measurement)
        return x, y

    def add_obs(self, x: Any, y: float):
        self.add_all_obs([x], [y])

    def value(self, m):
        return np.array([x.sense(m) for x in self.xs])

    def adj_value(self, v):
        total = np.zeros(self.shape)

        for x, s in zip(self.xs, v):
            x.add_to(total, s)

        return total

    def rss_grad(self, b):
        return self.adj_value(self.value(b) - self.ys)

    def op_norm(self):
        xs = [x.as_matrix().flatten() for x in self.xs]
        xs = np.array(xs)

        return npl.norm(xs, 2)


class RowSampleSet(SampleSet):

    def __init__(self, shape):
        super().__init__(shape)

        self._op_norm = 0.0
        self._op_norm_fresh = True

        self._init_fast_op_norm()

    def _init_fast_op_norm(self):
        self.buckets = [[] for _ in range(self.shape[0])]
        self.dirty = [False for _ in range(self.shape[0])]
        self.row_op_norms = np.zeros(self.shape[0])

    def _preprocess_obs(self, x: Any, y: float):
        if isinstance(x, tuple):
            assert len(x) == 2

            i, v = x
            x = RowMeasurement(self.shape[0], i, v)
        else:
            assert isinstance(x, RowMeasurement)

        i = x.row_index
        self._op_norm_fresh = False
        self.dirty[i] = True
        self.buckets[i].append((x, y))

        return x, y

    def op_norm(self):
        if not self._op_norm_fresh:
            self._refresh_op_norm()

        return self._op_norm

    def _refresh_op_norm(self):
        for i, d in enumerate(self.dirty):
            if d:
                self._refresh_row_op_norm(i)

        self._op_norm = self.row_op_norms.max()
        self._op_norm_fresh = True

    def _refresh_row_op_norm(self, i):
        xis = [x.row_value for x, y in self.buckets[i]]
        xis = np.array(xis)

        self.row_op_norms[i] = npl.norm(xis, 2)

        self.dirty[i] = False


class EntrySampleSet(RowSampleSet):

    def _init_fast_op_norm(self):
        pass

    def _preprocess_obs(self, x: Any, y: float):
        if isinstance(x, tuple):
            assert len(x) == 3

            i, j, v = x
            x = EntryMeasurement(self.shape, i, j, v)
        else:
            assert isinstance(x, EntryMeasurement)

        self._op_norm = max(self._op_norm, x.entry_value)

        return x, y

    def _refresh_op_norm(self):
        pass

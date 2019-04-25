import numpy as np
import numpy.linalg as npl
import numpy.random as npr
import numpy.testing as npt

from impute.sample_set import EntrySampleSet
from impute.soft import SoftImpute
from impute.fpc import FpcImpute


def test_fpc_alpha_max():
    npr.seed(314159265)

    shape = 30, 30
    n_rows, n_cols = shape

    ss = EntrySampleSet(shape)

    for i in range(n_rows):
        for j in range(n_cols):
            if (i + j) % 2 == 1:
                x = (i, j, 1)
                y = 1 + npr.random()

                ss.add_obs(x, y)

    alpha = SoftImpute(shape).alpha_max(ss)

    imputer = FpcImpute(shape)

    zs = imputer.fit(ss, [alpha, alpha * 0.999])

    actual = zs[0].to_matrix()
    expect = np.zeros(shape)
    npt.assert_array_almost_equal(actual, expect)

    actual = npl.norm(zs[1].to_matrix())
    assert actual > 1e-5

Sparse Matrix
===============

What is a sparse matrix
------------------------

Matrix where most elements are zero

- opposite of dense matrix
- 'Sparse data is by nature more easily compressed and thus requires significantly less storage'
- [https://docs.scipy.org/doc/scipy/reference/sparse.html](https://docs.scipy.org/doc/scipy/reference/sparse.html)
- [https://pypi.org/project/sparse/]
- [https://sparse.pydata.org/en/stable/generated/sparse.COO.html]
- [https://docs.scipy.org/doc/scipy/reference/generated/scipy.special.j1.html]

GBTGridder uses a COO sparse matrix

Coordinate list (COO)
----------------------

- COO stores a list of (row, column, value) tuples
- Ideally, the entries are sorted first by row index and then by column index, to improve random access times

What is it used for
-------------------

To optimize with the sparse matrix so not every pixel is being calculated
This way if the pixel is farther than the supported distance from the source then it is not accounted for in the storage or calculations - therefore making the calculations faster and more efficient

- before the data was was either accounted for as a negligible weight (still needed to be stored and took computation time)

- the matrix makes it so that the pixels with a negligible amount of weight don't carry any weight and have no value

    - any pixels with a negligible value can be excluded from the sparse matrix and removed

From `scipy`: To save space we often avoid storing these arrays in traditional dense formats, and instead choose different data structures - such as sparse matrix

How is it used
---------------

From `sdgridder.py`:

.. code-block:: python

    Generate sparse matrix for the distance^2 between each
    grid point and each data point.
        glong_diff = glong_axis[..., None] - glong
        remove = (np.abs(glong_diff) > support_distance) + np.isnan(glong_diff)
            #testing is nan and returns true or false # removing anything that is greater than the support dist
        glong_diff[remove] = np.inf
            # this makes the distance of the removed value infinity
        glong_diff = sparse.COO(glong_diff, fill_value=np.inf)
            # makes sparse matrix of the difference
            #the fill value (values with 0) is infinity so the dist is too great to store this value

^^ repeated for glat

What is `sparse`
----------------

[https://pypi.org/project/sparse/]

in the sandbox - `pip install sparse`

in the file - `import sparse`

It is **necessary** to have version 0.12.0 or else the `.todense` function will NOT work

- this needs to be on python version >= 3.8.5

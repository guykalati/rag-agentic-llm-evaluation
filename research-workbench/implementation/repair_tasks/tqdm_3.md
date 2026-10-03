Repair the public tqdm candidate so the visible test
`tqdm/tests/tests_tqdm.py::test_bool` passes. Under the modified Python 3.8.1
development runtime, the unchanged buggy revision fails with
`TypeError: 'NoneType' object cannot be interpreted as an integer` when the
test converts a progress object around an empty generator to `bool`. Keep
existing tqdm behavior working. You may inspect the candidate source and
visible tests through the provided functions.

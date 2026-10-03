Repair the public PySnooper candidate so the visible test
`tests/test_pysnooper.py::test_file_output` passes. The unchanged buggy
revision fails with `NameError: name 'output_path' is not defined`. Keep
existing PySnooper behavior working. You may inspect the candidate source and
visible tests through the provided functions.

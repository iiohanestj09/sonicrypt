=================================================== test session starts ===================================================
platform win32 -- Python 3.14.7, pytest-9.1.1, pluggy-1.7.0 -- D:\VS CODE\3_Python\sonicrypt\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\VS CODE\3_Python\sonicrypt\tests
plugins: anyio-4.15.1
collected 7 items                                                                                                          

pipeline_test.py::test_roundtrip_in_memory PASSED                                                                    [ 14%]
pipeline_test.py::test_wrong_passphrase PASSED                                                                       [ 28%]
pipeline_test.py::test_wrong_magic PASSED                                                                            [ 42%]
pipeline_test.py::test_various_sizes PASSED                                                                          [ 57%]
pipeline_test.py::test_capacity_exceeded PASSED                                                                      [ 71%]
pipeline_test.py::test_embed_to_file PASSED                                                                          [ 85%]
pipeline_test.py::test_married_life_file PASSED                                                                      [100%]

==================================================== 7 passed in 1.08s ====================================================
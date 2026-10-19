=================================================== test session starts ===================================================
platform win32 -- Python 3.14.7, pytest-9.1.1, pluggy-1.7.0 -- D:\VS CODE\3_Python\sonicrypt\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\VS CODE\3_Python\sonicrypt\tests
plugins: anyio-4.15.1
collected 5 items                                                                                                          

validate_audio_test.py::test_valid_wav_passes PASSED                                                                 [ 20%]
validate_audio_test.py::test_missing_file PASSED                                                                     [ 40%]
validate_audio_test.py::test_8bit_wav_rejected PASSED                                                                [ 60%]
validate_audio_test.py::test_collect_files_from_folder PASSED                                                        [ 80%]
validate_audio_test.py::test_small_wav_insufficient_for_benchmark PASSED                                             [100%]

==================================================== 5 passed in 0.19s ====================================================
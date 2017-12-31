import unittest

if __name__ == '__main__':
    # These config settings will run all unit tests that are in
    # the "test" directory and have filepaths that match test*.py
    testsuite = unittest.TestLoader().discover('./test')
    unittest.TextTestRunner(verbosity=2).run(testsuite)

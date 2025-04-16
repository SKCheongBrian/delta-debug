from humandeltadebug import DD
import argparse
import os

'''
This example contains a test to show the use of dd to find a reference to a non-existant file.
The test case will fail if the file does not exist.
'''

class MissingFile(DD):
    def _test(self, c):
        python_code = DD.config_to_string(c)
        if python_code.strip() == "":
            return self.PASS

        try:
            # Simulate reading from a file
            if not os.path.exists(python_code.strip()):
                raise FileNotFoundError(f"File {python_code.strip()} not found.")
            return self.PASS
        except FileNotFoundError as e:
            return self.FAIL
        except Exception as e:
            return self.UNRESOLVED

    def coerce(self, c):
        return DD.config_to_string(c)

# Failing code (file not found)
failing_code = 'showcase4/test/path/to/existing/file1.txt'

# Passing code (correct file path)
passing_code = 'showcase4/test/path/to/existing/file.txt'

failing_config = DD.string_to_config(failing_code)
passing_config = DD.string_to_config(passing_code)

# Delta Debugging setup
dd = MissingFile()

# For testing verbose flag
parser = argparse.ArgumentParser()
parser.add_argument('--verbose', action='store_true')
args = parser.parse_args()

# Set verbosity for delta debugging
dd.verbose = 1 if args.verbose else 0

# Get minimal failing configuration
minimal_config = dd.dd(failing_config)
minimal_failing = DD.config_to_string(minimal_config[0])
print("**********************************************")
print("Minimal failing test case: " + minimal_failing)
print("**********************************************")

# Get maximal failing configuration
max_config = dd.ddmax(DD.string_to_config(minimal_failing), passing_config, 2)
maximal_failing = DD.config_to_string(max_config[1])
print("**********************************************")
print("Maximal failing test case: " + maximal_failing)
print("**********************************************")

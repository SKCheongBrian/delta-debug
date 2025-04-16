# @authors: skcheongbrian, sevenseasofbri
from humandeltadebug import DD
import argparse

'''
This example contains a test that demonstrates the use of dd to find the issue with a string configuration. A valid string configuration is one that contains a dollar sign ($) and the word "test".
The test case will fail if the string does not contain both of these elements.
'''

class TestString(DD):
        def _test(self, c):
            candidate = DD.config_to_string(c)
            if "$" in candidate and "test" in candidate:
                return self.PASS
            else:
                return self.FAIL
        
        def coerce(self, c):
            # Reassemble for output.
            return DD.config_to_string(c)
        
failing_string = "this input should fail"
passing_string = "while this should $ pass the test"

failing_config = DD.string_to_config(failing_string)
passing_config = DD.string_to_config(passing_string)

parser = argparse.ArgumentParser(description="Run delta debugging with verbosity control.")
parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
args = parser.parse_args()

test_string_dd = TestString()
test_string_dd.verbose = 1 if args.verbose else 0

minimal_config = test_string_dd.dd(failing_config)
minimal_failing = DD.config_to_string(minimal_config[0])
print("**********")
print("* Test 1 *")
print("**********************************************")
print("Failing test case to be minimised: " + failing_string)
print("**********************************************")
print("Minimal failing test case: " + minimal_failing)
print("**********************************************")
print("Passing test case to be maximised with respect to: " + passing_string)

max_config = test_string_dd.ddmax(DD.string_to_config(minimal_failing), passing_config, 2)
maximal_failing = DD.config_to_string(max_config[1])
print("**********************************************")
print("Maximal failing test case: " + maximal_failing)
print("**********************************************")
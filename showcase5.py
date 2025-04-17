from humandeltadebug import DD
import re
import argparse

'''
Example to show the use of dd to find a regex pattern that fails to compile.
The test case will fail if the regex pattern is invalid.
'''

class RegexQuantifierMissing(DD):
    def _test(self, c):
        pattern = DD.config_to_string(c)
        if pattern.strip() == "":
            return self.PASS
        try:
            re.compile(pattern)
            return self.PASS
        except re.error:
            return self.FAIL
        except Exception:
            return self.UNRESOLVED

    def coerce(self, c):
        return DD.config_to_string(c)

# Failing pattern (raises re.error)
failing = r"*abc"

# Passing pattern (valid regex)
passing = r"abc*abcdefghijklmnopqrs"

failing_config = DD.string_to_config(failing)
passing_config = DD.string_to_config(passing)

parser = argparse.ArgumentParser()
parser.add_argument('--verbose', action='store_true')
args = parser.parse_args()

dd = RegexQuantifierMissing()
dd.verbose = 1 if args.verbose else 0

minimal_config = dd.dd(failing_config)
minimal_failing = DD.config_to_string(minimal_config[0])
print("**********")
print("* Test 1 *")
print("**********************************************")
print("Failing test case to be minimised: \n " + failing)
print("**********************************************")
print("Minimal failing test case: \n" + repr(minimal_failing))
print("**********************************************")
print("Passing test case to be maximised with respect to: \n" + passing)

max_config = dd.ddmax(DD.string_to_config(minimal_failing), passing_config, 2)
maximal_failing = DD.config_to_string(max_config[1])
print("**********************************************")
print("Maximal failing test case: \n" + repr(maximal_failing))
print("**********************************************")

# @authors: skcheongbrian, sevenseasofbri
from humandeltadebug import DD
import json
import argparse

class Missing_curly_brace(DD):
        def _test(self, c):
            candidate = DD.config_to_string(c)
            # Treat an empty candidate as passing.
            if candidate.strip() == "":
                return self.PASS
            try:
                json.loads(candidate)
                return self.PASS
            except json.JSONDecodeError as e:
                if candidate[len(candidate) - 1] != '}':
                    return self.FAIL
                return self.UNRESOLVED
        
        def coerce(self, c):
            # Reassemble for output.
            return DD.config_to_string(c)
        
failing_json = '{"baz": 7, "zip": 1.0, "zop": [1, 2]'
passing_json = '{ "foo": 3.0 }'
print("**********")
print("* Test 1 *")
print("**********************************************")
print("Failing test case to be minimised: " + failing_json)

failing_config = DD.string_to_config(failing_json)
passing_config = DD.string_to_config(passing_json)

parser = argparse.ArgumentParser(description="Run delta debugging with verbosity control.")
parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
args = parser.parse_args()

missing_curly_brace_dd = Missing_curly_brace()
missing_curly_brace_dd.verbose = 1 if args.verbose else 0

minimal_config = missing_curly_brace_dd.dd(failing_config)
minimal_failing = DD.config_to_string(minimal_config[0])
print("**********************************************")
print("Minimal failing test case: " + minimal_failing)
print("**********************************************")
print("Passing test case to be maximised with respect to: " + passing_json)

max_config = missing_curly_brace_dd.ddmax(DD.string_to_config(minimal_failing), passing_config, 2)
maximal_failing = DD.config_to_string(max_config[1])
print("**********************************************")
print("Maximal failing test case: " + maximal_failing)
print("**********************************************")

failing_json2 = '{"foo": 3.0, "bar": 1.0 '
passing_json2 = '{ "boo": "bar" }'
print("")
print("**********")
print("* Test 2 *")
print("**********************************************")
print("Failing test case to be minimised: " + failing_json2)

failing_config2 = DD.string_to_config(failing_json2)
passing_config2 = DD.string_to_config(passing_json2)

minimal_config = missing_curly_brace_dd.dd(failing_config2)
minimal_failing = DD.config_to_string(minimal_config[0])
print("**********************************************")
print("Minimal failing test case: " + minimal_failing)
print("**********************************************")
print("Passing test case to be maximised with respect to: " + passing_json2)

max_config = missing_curly_brace_dd.ddmax(DD.string_to_config(minimal_failing), passing_config2, 2)
maximal_failing = DD.config_to_string(max_config[1])
print("**********************************************")
print("Maximal failing test case: " + maximal_failing)
print("**********************************************")
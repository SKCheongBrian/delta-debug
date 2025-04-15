from humandeltadebug import DD, string_to_config, config_to_string
import json

class Missing_curly_brace(DD):
        def _test(self, c):
            candidate = config_to_string(c)
            print("Testing candidate:", candidate)
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
            print(type(c))
            return config_to_string(c)
        
failing_json = '{"baz": 7, "zip": 1.0, "zop": [1, 2]'
passing_json = '{ "foo": 3.0 }'

failing_config = string_to_config(failing_json)
passing_config = string_to_config(passing_json)

missing_curly_brace_dd = Missing_curly_brace()

minimal_config = missing_curly_brace_dd.dd(failing_config)
minimal_failing = config_to_string(minimal_config[0])
print("**********************************************")
print("Minimal failing test case: " + minimal_failing)
print("**********************************************")

max_config = missing_curly_brace_dd._ddmax(string_to_config(minimal_failing), passing_config, 2)
maximal_failing = config_to_string(max_config[1])
print("**********************************************")
print("Maximal failing test case: " + maximal_failing)
print("**********************************************")

failing_json2 = '{"foo": 3.0, "bar": 1.0 '
passing_json2 = '{ "boo": "bar" }'

failing_config2 = string_to_config(failing_json2)
passing_config2 = string_to_config(passing_json2)

minimal_config = missing_curly_brace_dd.dd(failing_config2)
minimal_failing = config_to_string(minimal_config[0])
print("**********************************************")
print("Minimal failing test case: " + minimal_failing)
print("**********************************************")

max_config = missing_curly_brace_dd._ddmax(string_to_config(minimal_failing), passing_config2, 2)
maximal_failing = config_to_string(max_config[1])
print("**********************************************")
print("Maximal failing test case: " + maximal_failing)
print("**********************************************")
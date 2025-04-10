from dd2v6 import DD, OutcomeCache
import json

class Missing_curly_brace(DD):
        def _test(self, c):
            candidate = "".join(c)
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
            return "".join(c)
        
failing_json = '{"baz": 7, "zip": 1.0, "zop": [1, 2]'
passing_json = '{ "foo": 3.0 }'

failing_config = list(failing_json)
passing_config = list(passing_json)

missing_curly_brace_dd = Missing_curly_brace()

minimal_config = missing_curly_brace_dd.dd(failing_config)
minimal_failing = "".join(minimal_config[0])
print("**********************************************")
print("Minimal failing test case: " + minimal_failing)
print("**********************************************")

max_config = missing_curly_brace_dd._ddmax(list(minimal_failing), passing_config, 2)
maximal_failing = "".join(max_config[1])
print("**********************************************")
print("Maximal failing test case: " + maximal_failing)
print("**********************************************")
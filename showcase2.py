from dd2v6 import DD, OutcomeCache

class TestString(DD):
        def _test(self, c):
            candidate = "".join(c)
            if "$" in candidate and "test" in candidate:
                return self.PASS
            else:
                return self.FAIL
        
        def coerce(self, c):
            # Reassemble for output.
            print(type(c))
            return "".join(c)
        
failing_string = "this input should fail"
passing_string = "while this should $ pass the test"

failing_config = list(failing_string)
passing_config = list(passing_string)

test_string_dd = TestString()

minimal_config = test_string_dd.dd(failing_config)
minimal_failing = "".join(minimal_config[0])
print("**********************************************")
print("Minimal failing test case: " + minimal_failing)
print("**********************************************")

max_config = test_string_dd._ddmax(list(minimal_failing), passing_config, 2)
maximal_failing = "".join(max_config[1])
print("**********************************************")
print("Maximal failing test case: " + maximal_failing)
print("**********************************************")
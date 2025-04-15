from humandeltadebug import DD, string_to_config, config_to_string

class TestString(DD):
        def _test(self, c):
            candidate = config_to_string(c)
            if "$" in candidate and "test" in candidate:
                return self.PASS
            else:
                return self.FAIL
        
        def coerce(self, c):
            # Reassemble for output.
            print(type(c))
            return config_to_string(c)
        
failing_string = "this input should fail"
passing_string = "while this should $ pass the test"

failing_config = string_to_config(failing_string)
passing_config = string_to_config(passing_string)

test_string_dd = TestString()

minimal_config = test_string_dd.dd(failing_config)
minimal_failing = config_to_string(minimal_config[0])
print("**********************************************")
print("Minimal failing test case: " + minimal_failing)
print("**********************************************")

max_config = test_string_dd._ddmax(string_to_config(minimal_failing), passing_config, 2)
maximal_failing = config_to_string(max_config[1])
print("**********************************************")
print("Maximal failing test case: " + maximal_failing)
print("**********************************************")
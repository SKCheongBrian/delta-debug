# @authors: skcheongbrian, sevenseasofbri
from humandeltadebug import DD
import argparse

class WrongLogic(DD):
    def _test(self, c):
        candidate = DD.config_to_string(c)
        try:
            # Execute the candidate code in a sandboxed namespace
            ns = {}
            exec(candidate, ns)
            result = ns["add"](2, 3)
            if result == 5:
                return self.PASS
            else:
                return self.FAIL
        except Exception as e:
            if DD.verbose:
                print("Execution error:", e)
            return self.UNRESOLVED

    def coerce(self, c):
        return DD.config_to_string(c)

# Logic bug: the function subtracts instead of adds
failing_py = "def add(a, b):\n    return a - b"
passing_py = "def add(a, b):\n    return a + b"

failing_config = DD.string_to_config(failing_py)
passing_config = DD.string_to_config(passing_py)

parser = argparse.ArgumentParser(description="Run delta debugging with verbosity control.")
parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
args = parser.parse_args()

logic_bug_dd = WrongLogic()
logic_bug_dd.verbose = 1 if args.verbose else 0

# Minimizing the bug
minimal_config = logic_bug_dd.dd(failing_config)
minimal_failing = DD.config_to_string(minimal_config[0])
print("**********")
print("* Test 1 *")
print("**********************************************")
print("Failing test case to be minimised: \n " + failing_py)
print("**********************************************")
print("Minimal failing test case: \n" + minimal_failing)
print("**********************************************")
print("Passing test case to be maximised with respect to: \n" + passing_py)

# Maximizing it w.r.t the passing config
max_config = logic_bug_dd.ddmax(DD.string_to_config(minimal_failing), passing_config, 2)
maximal_failing = DD.config_to_string(max_config[1])
print("**********************************************")
print("Maximal failing test case: \n" + maximal_failing)
print("**********************************************")

from humandeltadebug import DD
import argparse

'''
Example to show the use of dd to find a bitmask feature check that fails to compile.
Checks if the first three bits of a binary string are all 1.
'''

class BitmaskFeatureCheck(DD):
    def _test(self, c):
        binary = DD.config_to_string(c).replace('\n', '').strip()

        if binary == "":
            return self.PASS

        if self.verbose:
            print(f"[TESTING BITMASK]: {binary}")

        # Check if first three bits are all 1 (required features A, B, C)
        if len(binary) < 3 or binary[:3] != "111":
            return self.FAIL
        return self.PASS

    def coerce(self, c):
        return DD.config_to_string(c)

# Inputs
failing_input = "11010000"     # Fails: missing feature C
passing_input = "11100001"     # Passes: has all required features

failing_config = DD.string_to_config(failing_input)
passing_config = DD.string_to_config(passing_input)

parser = argparse.ArgumentParser()
parser.add_argument('--verbose', action='store_true')
args = parser.parse_args()

dd = BitmaskFeatureCheck()
dd.verbose = 1 if args.verbose else 0

minimal_config = dd.dd(failing_config)
minimal_failing = DD.config_to_string(minimal_config[0])
print("**********")
print("* Test 1 *")
print("**********************************************")
print("Failing test case to be minimised: \n " + failing_input)
print("**********************************************")
print("Minimal failing test case: \n", minimal_failing)
print("**********************************************")
print("Passing test case to be maximised with respect to: \n" + passing_input)


max_config = dd.ddmax(DD.string_to_config(minimal_failing), passing_config, 2)
maximal_failing = DD.config_to_string(max_config[1])
print("**********************************************")
print("Maximal failing test case: \n" + maximal_failing)
print("**********************************************")

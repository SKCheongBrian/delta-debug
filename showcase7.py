from humandeltadebug import DD
import argparse

'''
Example: Whitespace-sensitive JSON parsing (From a real-wrold scenario!)
In a real-world scenario faced by one of the author's friends, a CGRA compiler script was found to be
parsing a JSON configuration in a format-dependent way - specifically it was expecting keys like "num_pes"
to appear with a precise number of spaces (e.g., 2 spaces after then colon). This led to the parser
failing on a valid JSON file not written in the original, hand-crafted formet. 

This example emulates that scenario. The WeirdJSONParser fails unless it finds the key "num_pes" with 
exactly 2 spaces following the colon. This behaviour in the parser is represented by the test function.

It can be seen that using ddmax finds a more readable test case to fail the parser. 
'''

class WeirdJSONParser(DD):
    def _test(self, c):
        string = DD.config_to_string(c)
        if self.verbose:
            print(f"[TESTING INPUT]:\n{string}\n---")

        # "Bad" parser expects '"num_pes":  ' with 2 spaces after the colon
        for line in string.splitlines():
            if '"num_pes":  ' in line:
                return self.PASS
        return self.FAIL

    def coerce(self, c):
        return DD.config_to_string(c)

# Sample Inputs
failing_input = '''
{
    "cgra": {
        "num_pes": 16,
        "clock_period": 10
    }
}
'''

passing_input = '''
{
    "cgra": {
        "num_pes":  64,
        "clock_period": 12
        "hops": 2
    }
}
'''

failing_config = DD.string_to_config(failing_input)
passing_config = DD.string_to_config(passing_input)

parser = argparse.ArgumentParser()
parser.add_argument('--verbose', action='store_true')
args = parser.parse_args()

dd = WeirdJSONParser()
dd.verbose = 1 if args.verbose else 0

min_config = dd.dd(failing_config)
minimal_failing = DD.config_to_string(min_config[0])
print("**********")
print("* Test 1 *")
print("**********************************************")
print("Failing test case to be minimised: \n " + failing_input)
print("**********************************************")
print("Minimal failing test case: \n", minimal_failing)
print("**********************************************")
print("Passing test case to be maximised with respect to: \n" + passing_input)

max_config = dd.ddmax(min_config[0], passing_config, 2)
maximal_failing = DD.config_to_string(max_config[1])
print("**********************************************")
print("Maximal failing test case: \n" + maximal_failing)
print("**********************************************")

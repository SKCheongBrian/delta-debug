# Modified from Prof. Andreas Zeller's original implementation in DD.py
# Stripped down unused portions and extended with ddmax
#
# ddmax is attempting to create a maximal failing test case with respect to a passing one
#
# The original implementations are available at:
# https://www.st.cs.uni-saarland.de/dd/DD.py
# https://github.com/grimm-co/delta-debugging/blob/master/delta_debugging/DD.py
 

import string

# This class hold test outcomes for configs. Avoid running same test twice.
# Ref: https://www.st.cs.uni-saarland.de/dd/DD.py
class OutcomeCache:
    # Implemented as a tree. Each node points to the outcome of the
    # remaining list.
    # From DD.py:
    # Example: ([1, 2, 3], PASS), ([1, 2], FAIL), ([1, 4, 5], FAIL):
    #
    #      (2, FAIL)--(3, PASS)
    #     /
    # (1, None)
    #     \
    #      (4, None)--(5, FAIL)

    def __init__(self):
        self.tail = {}
        self.result = None

    def add(self, c, result):
        # add (c, result) to cache
        cs = c[:]
        cs.sort()

        p = self

        for start in range(len(c)):
            if c[start] not in p.tail:
                p.tail[c[start]] = OutcomeCache()
            p = p.tail[c[start]]

        p.result = result
    
    def lookup(self, c):
        # lookup result for c in cache
        p = self
        for start in range(len(c)):
            if c[start] not in p.tail:
                return None
            p = p.tail[c[start]]

        return p.result

    def lookup_superset(self, c, start=0):
        # return result if there is some (c', result) in the cache with
        # c' being the superset of c or equal to c. else None.

        if start >= len(c):
            if self.result:
                return self.result
            elif self.tail != {}:
                # Select some superset
                superset = self.tail[list(self.tail.keys())[0]]
                return superset.lookup_superset(c, start + 1)
            else:
                return None

        if c[start] in self.tail:
            return self.tail[c[start]].lookup_superset(c, start + 1)

        # k0 larget element in tail s.t. k0 <= c[start]
        k0 = None
        for k in self.tail.keys():
            if (k0 is None or k > k0) and k <= c[start]:
                k0 = k

        if k0 is not None:
            return self.tail[k0].lookup_superset(c, start)
        
        return None
    
    def lookup_subset(self, c):
        # return result if there is some (c', result) in the cache with
        # c' being a subset of c or equal to c. else None.
        p = self
        for start in range(len(c)):
            if c[start] in p.tail:
                p = p.tail[c[start]]
        
        return p.result
    
    # test outcome cache 
def oc_test():
    oc = OutcomeCache()
    assert oc.lookup([1, 2, 3]) is None
    oc.add([1, 2, 3], 4)
    assert oc.lookup([1, 2, 3]) == 4
    assert oc.lookup([1, 2, 3, 4]) is None

    assert oc.lookup([5, 6, 7]) is None
    oc.add([5, 6, 7], 8)
    assert oc.lookup([5, 6, 7]) == 8
       
    assert oc.lookup([]) is None
    oc.add([], 0)
    assert oc.lookup([]) == 0
     
    assert oc.lookup([1, 2]) is None
    oc.add([1, 2], 3)
    assert oc.lookup([1, 2]) == 3
    assert oc.lookup([1, 2, 3]) == 4

    assert oc.lookup_superset([1]) == 3 or oc.lookup_superset([1]) == 4
    assert oc.lookup_superset([1, 2]) == 3 or oc.lookup_superset([1, 2]) == 4
    assert oc.lookup_superset([5]) == 8
    assert oc.lookup_superset([5, 6]) == 8
    assert oc.lookup_superset([6, 7]) == 8
    assert oc.lookup_superset([7]) == 8
    assert oc.lookup_superset([]) is not None

    assert oc.lookup_superset([9]) is None
    assert oc.lookup_superset([7, 9]) is None
    assert oc.lookup_superset([-5, 1]) is None
    assert oc.lookup_superset([1, 2, 3, 9]) is None
    assert oc.lookup_superset([4, 5, 6, 7]) is None

    assert oc.lookup_subset([]) == 0
    assert oc.lookup_subset([1, 2, 3]) == 4
    assert oc.lookup_subset([1, 2, 3, 4]) == 4
    assert oc.lookup_subset([1, 3]) is None
    assert oc.lookup_subset([1, 2]) == 3

    assert oc.lookup_subset([-5, 1]) is None
    assert oc.lookup_subset([-5, 1, 2]) == 3
    assert oc.lookup_subset([-5]) == 0

            
class DD:
    # Main DD implementation
    # dd() computes min failure-inducing diff
    # ddmax() computes the max failure inducing case with respect to a passing test case

    # Test outcomes, as defined in dd2 paper
    PASS = "PASS"
    FAIL  = "FAIL"
    UNRESOLVED = "UNRESOLVED"

    # Tag to indicate a set is a difference between a passing and failing run
    DIFFERENCE = "DIFFERENCE"

    # Resolving directions
    ADD = "ADD"
    REMOVE = "REMOVE"

    # Debugging flags
    debug_test = 0
    debug_dd = 0
    debug_split = 0
    debug_resolve = 0
    verbose = 0
    state_debugger = 0

    def __init__(self):
        self.__resolving = 0
        self.__last_reported_length = 0
        self.monotony = 0
        self.outcome_cache  = OutcomeCache()
        self.cache_outcomes = 1
        self.minimize = 1
        self.maximize = 1
        self.assume_axioms_hold = 1

        # Animation output (set to Animate object to enable)
        self.animate = None

        self.n_tests  = 0
        self.n_passes = 0
        self.n_fails  = 0
        self.n_unres  = 0
    
    # helpers
    # Ref: https://www.st.cs.uni-saarland.de/dd/DD.py
    def __listminus(self, c1, c2):
        """Return a list of all elements of C1 that are not in C2."""
        s2 = {}
        for delta in c2:
            s2[delta] = 1
        
        c = []
        for delta in c1:
            if delta not in s2:
                c.append(delta)

        return c

    def __listunion(self, c1, c2):
        """Return the union of C1 and C2."""
        if self.verbose:
            print("union")
            print(c1)
            print(c2)
        
        s1 = {}
        for delta in c1:
            s1[delta] = 1

        c = c1[:]
        for delta in c2:
            if delta not in s1:
                c.append(delta)

        if self.verbose:
            print(c)
            print("=====")
        return c

    def __listsubseteq(self, c1, c2):
        """Return 1 if C1 is a subset or equal to C2."""
        s2 = {}
        for delta in c2:
            s2[delta] = 1

        for delta in c1:
            if delta not in s2:
                return 0

        return 1
    
    # output
    def coerce(self, c):
        """Return the configuration C as a compact string"""
        # Default: use printable representation
        return c

    def pretty(self, c):
        """Like coerce(), but sort beforehand"""
        sorted_c = c[:]
        sorted_c.sort()
        return self.coerce(sorted_c)

    # testing
    def test(self, c):
        """Test the configuration C.  Return PASS, FAIL, or UNRESOLVED"""
        c.sort()

        if self.verbose:
            print(c)
            print("Testing candidate: " + DD.config_to_string(c))

        if self.debug_test:
            print()
            print("test(" + self.coerce(c) + ")...")

        outcome = self._test(c)

        #Statistics about actually executed tests
        self.n_tests +=1
        if   outcome == self.FAIL:
            self.n_fails  +=1
        elif outcome == self.PASS:
            self.n_passes +=1
        elif outcome == self.UNRESOLVED:
            self.n_unres  +=1

        if self.debug_test:
            print("test(" + self.coerce(c) + ") = " + outcome)

        if self.cache_outcomes:
            self.outcome_cache.add(c, outcome)

        return outcome

    def _test(self, c):
        """Stub to overload in subclasses"""
        return self.UNRESOLVED        # Placeholder
    
    def init_counting(self):
        self.n_tests  = 0
        self.n_passes = 0
        self.n_fails  = 0
        self.n_unres  = 0

    def get_counting(self):
        return {
            "TESTS":self.n_tests,
            "PASS" :self.n_passes,
            "FAIL" :self.n_fails,
            "UNRES":self.n_unres}
    
    # splitting
    def split(self, c, n):
        """Split C into [C_1, C_2, ..., C_n]."""
        if self.debug_split:
            print("split(" + self.coerce(c) + ", " + n + ")...")

        outcome = self._split(c, n)

        if self.debug_split:
            print("split(" + self.coerce(c) + ", " + n + ") = " + outcome)

        return outcome

    def _split(self, c, n):
        """Stub to overload in subclasses"""
        subsets = []
        start = 0
        for i in range(n):
            subset = c[start:int(start + (len(c) - start) / (n - i))]
            subsets.append(subset)
            start = start + len(subset)
        return subsets

    # resolving
    def resolve(self, csub, c, direction):
        """If direction == ADD, resolve inconsistency by adding deltas
          to CSUB.  Otherwise, resolve by removing deltas from CSUB."""

        if self.debug_resolve:
            print("resolve(" + csub + ", " + self.coerce(c) + ", " +
                  direction + ")...")

        outcome = self._resolve(csub, c, direction)

        if self.debug_resolve:
            print("resolve(" + csub + ", " + self.coerce(c) + ", " +
                  direction + ") = " + outcome)

        return outcome

    def _resolve(self, csub, c, direction):
        """Stub to overload in subclasses."""
        # By default, no way to resolve
        return None


    # test with fixes
    def test_and_resolve(self, csub, r, c, direction):
        """Repeat testing CSUB + R while unresolved."""

        initial_csub = csub[:]
        c2 = self.__listunion(r, c)
        csubr = self.__listunion(csub, r)
        t = self.test(csubr)

        # necessary to use more resolving mechanisms which can reverse each
        # other, can (but needn't) be used in subclasses
        self._resolve_type = 0 

        while t == self.UNRESOLVED:
            self.__resolving = 1
            csubr = self.resolve(csubr, c, direction)

            if csubr is None:
                # Nothing left to resolve
                break
            
            if len(csubr) >= len(c2):
                # Added everything: csub == c2. ("Upper" Baseline)
                # This has already been tested.
                csubr = None
                break
                
            if len(csubr) <= len(r):
                # Removed everything: csub == r. (Baseline)
                # This has already been tested.
                csubr = None
                break
            
            t = self.test(csubr)

        self.__resolving = 0
        if csubr is None:
            return self.UNRESOLVED, initial_csub

        # assert t == self.PASS or t == self.FAIL
        csub = self.__listminus(csubr, r)
        return t, csub
    
    # inquiries
    def resolving(self):
        """Return 1 while resolving."""
        return self.__resolving

    # logging
    def report_progress(self, c, title):
        if self.verbose and len(c) != self.__last_reported_length:
            print()
            print(title + ": " + str(len(c)) + " deltas left:", self.coerce(c))
            self.__last_reported_length = len(c)

    
    # general differential delta debugging (new TSE version)
    # Ref: https://www.st.cs.uni-saarland.de/dd/DD.py
    def dddiff(self, c):
        n = 2

        if self.debug_dd:
            print("dddiff(" + self.pretty(c) + ", " + n + ")...")

        outcome = self._dddiff([], c, n)

        if self.debug_dd:
            print("dddiff(" + self.pretty(c) + ", " + n + ") = " +
                   outcome)

        return outcome

    def _dddiff(self, c1, c2, n): 
        run = 1
        cbar_offset = 0

        c1_orig = c1[:]
        c2_orig = c2[:]

        # We replace the tail recursion from the paper by a loop
        while 1:
            if self.debug_dd:
                print("dd: c1 =", self.pretty(c1))
                print("dd: c2 =", self.pretty(c2))

            if self.assume_axioms_hold:
                t1 = self.PASS
                t2 = self.FAIL
            else:
                t1 = self.test(c1)
                t2 = self.test(c2)
            
            assert t1 == self.PASS
            assert t2 == self.FAIL
            assert self.__listsubseteq(c1, c2)

            c = self.__listminus(c2, c1)

            if self.debug_dd:
                print("dd: c2 - c1 =", self.pretty(c))

            if n > len(c):
                # No further minimizing
                if self.verbose:
                    print("dd: done")
                return (c, c1, c2)

            self.report_progress(c, "dd")

            cs = self.split(c, n)

            if self.verbose:
                print()
                print("dd (run #" + str(run) + "): trying",)
                for i in range(n):
                    if i > 0:
                        print("+",)
                    print(len(cs[i]),)
                print()

            progress = 0

            next_c1 = c1[:]
            next_c2 = c2[:]
            next_n = n

            # Check subsets
            for j in range(n):
                i = int((j + cbar_offset) % n)

                if self.debug_dd:
                    print("dd: trying", self.pretty(cs[i]))

                (t, csub) = self.test_and_resolve(cs[i], c1, c, self.REMOVE)
                # adding subset to c1
                csub = self.__listunion(c1, csub)

                # case 1: if union c1 with subset fails (c1 was initially passing)
                # c2 (failing test case) is now csub (union c1 subset)
                # minimal test would be within c1 and c2 again.
                if t == self.FAIL and t1 == self.PASS:
                    # Found
                    progress    = 1
                    next_c2     = csub
                    next_n      = 2
                    cbar_offset = 0

                    if self.debug_dd:
                        print("dd: reduce c2 to", len(next_c2), "deltas:",)
                        print(self.pretty(next_c2))
                    break

                if t == self.PASS and t2 == self.FAIL:
                    # Reduce to complement
                    progress    = 1
                    next_c1     = csub
                    next_n      = max(next_n - 1, 2)
                    cbar_offset = i

                    if self.debug_dd:
                        print("dd: increase c1 to", len(next_c1), "deltas:",)
                        print(self.pretty(next_c1))
                    break


                csub = self.__listminus(c, cs[i])
                (t, csub) = self.test_and_resolve(csub, c1, c, self.ADD)
                csub = self.__listunion(c1, csub)

                if t == self.PASS and t2 == self.FAIL:
                    # Found
                    progress    = 1
                    next_c1     = csub
                    next_n      = 2
                    cbar_offset = 0

                    if self.debug_dd:
                        print("dd: increase c1 to", len(next_c1), "deltas:",)
                        print(self.pretty(next_c1))
                    break

                if t == self.FAIL and t1 == self.PASS:
                    # Increase
                    progress    = 1
                    next_c2     = csub
                    next_n      = max(next_n - 1, 2)
                    cbar_offset = i

                    if self.debug_dd:
                        print("dd: reduce c2 to", len(next_c2), "deltas:",)
                        print(self.pretty(next_c2))
                    break

            if progress:
                if self.animate is not None:
                    self.animate.write_outcome(
                        self.__listminus(next_c1, c1_orig), self.PASS)
                    self.animate.write_outcome(
                        self.__listminus(c2_orig, next_c2), self.FAIL)
                    self.animate.write_outcome(
                        self.__listminus(next_c2, next_c1), self.DIFFERENCE)
                    self.animate.next_frame()

                self.report_progress(self.__listminus(next_c2, next_c1), "dd")
            else:
                if n >= len(c):
                    # No further minimizing
                    if self.verbose:
                        print("dd: done")
                    return (c, c1, c2)

                next_n = min(len(c), n * 2)
                if self.verbose:
                    print("dd: increase granularity to", next_n)
                cbar_offset = (cbar_offset * next_n) / n

            c1  = next_c1
            c2  = next_c2
            n   = next_n
            run = run + 1

    # @authors: skcheongbrian, sevenseasofbri
    def match_subset(self, c1, c2):
        """Mutate c1 to a subset of c2 if possible

        Args:
            c1 (config): config of c1
            c2 (config): config of c2
        """
        p1 = 0
        p2 = 0

        while p1 < len(c1):
            current_character = c1[p1][1]
            while p2 < len(c2) and c2[p2][1] is not current_character:
                p2 += 1
            if p2 == len(c2):
                return
            c1[p1] = (c2[p2][0], current_character)
            p2 += 1
            p1 += 1
    
    # @authors: skcheongbrian, sevenseasofbri
    def ddmax(self, c1, c2, n):  
        """Expand c1 to the maximal failing test case with respect to c2

        Args:
            c1 (config): The config to be expanded to
            c2 (config): The config to be expanded with respect to
            n (integer): The granularity size

        Returns:
            _type_: _description_
        """
        run = 1
        cbar_offset = 0
    
        c1_orig = c1[:]
        c2_orig = c2[:]
    
        # Replace tail recursion with a loop
        while True:
            if self.debug_dd:
                print("dd: c1 =", self.pretty(c1))
                print("dd: c2 =", self.pretty(c2))
    
            # Test c1 and c2
            t1 = self.test(c1)
            t2 = self.test(c2)
    
            assert t1 == self.FAIL, "c1 must be failing"
            assert t2 == self.PASS, "c2 must be passing"
            self.match_subset(c1,c2)
            assert self.__listsubseteq(c1, c2), "c1 must be a subset of c2"
    
            # Compute the difference between c2 and c1
            c = self.__listminus(c2, c1)
    
            if self.debug_dd:
                print("dd: c2 - c1 =", self.pretty(c))
    
            if n > len(c):
                # No further expanding
                if self.verbose:
                    print("dd: done")
                return (c, c1, c2)
    
            self.report_progress(c, "dd")
    
            # Split the difference into subsets
            cs = self.split(c, n)
    
            if self.verbose:
                print()
                print("dd (run #" + str(run) + "): trying",)
                for i in range(n):
                    if i > 0:
                        print("+",)
                    print(len(cs[i]),)
                print()
    
            progress = 0
    
            next_c1 = c1[:]
            next_n = n
    
            # Check subsets
            for j in range(n):
                i = int((j + cbar_offset) % n)
    
                if self.debug_dd:
                    print("dd: trying", self.pretty(cs[i]))
    
                # Try adding the subset to the back of c1
                csub = self.__listunion(c1, cs[i])
                t = self.test(csub)

                if self.verbose:
                    print("csub: ", csub)
    
                if t == self.FAIL:
                    # If adding to the back keeps c1 failing, keep the subset
                    progress = 1
                    next_c1 = csub
                    next_n = max(next_n - 1, 2)
                    cbar_offset = i
    
                    if self.debug_dd:
                        print("dd: expand c1 (back) to", len(next_c1), "deltas:",)
                        print(self.pretty(next_c1))
                    break
    
            if progress:
                if self.animate is not None:
                    self.animate.write_outcome(
                        self.__listminus(next_c1, c1_orig), self.FAIL)
                    self.animate.write_outcome(
                        self.__listminus(c2_orig, c2), self.PASS)
                    self.animate.write_outcome(
                        self.__listminus(c2, next_c1), self.DIFFERENCE)
                    self.animate.next_frame()
    
                self.report_progress(self.__listminus(c2, next_c1), "dd")
            else:
                if n >= len(c):
                    # No further expanding
                    if self.verbose:
                        print("dd: done")
                    return (c, c1, c2)
    
                next_n = min(len(c), n * 2)
                if self.verbose:
                    print("dd: increase granularity to", next_n)
                cbar_offset = (cbar_offset * next_n) / n
    
            c1 = next_c1
            n = next_n
            run += 1
            
    def dd(self, c):
        return self.dddiff(c)           # Backwards compatibility
    
    # @authors: skcheongbrian, sevenseasofbri
    def string_to_config(s):
        """Converts the string into a config

        Args:
            s (string): The string to be converted into a config

        Returns:
            config: The resultant config
        """
        res = []
        idx = 0
        for c in s:
            res.append((idx, c))
            idx += 1
        return res

    # @authors: skcheongbrian, sevenseasofbri
    def config_to_string(c):
        """Converts the config c to a string (usually for testing)

        Args:
            c (config): The config to be converted to string

        Returns:
            string: The resultant string
        """
        res = []
        for x, y in c:
            res.append(y)
        return "".join(res)


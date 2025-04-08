# From Prof Andreas Zeller's original implementation in DD.py
# https://github.com/grimm-co/delta-debugging/blob/master/delta_debugging/DD.py

import string

# This class hold test outcomes for configs. Avoid running same test twice.
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
        # cs.sort()

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
    # To use, overload test() method and call ddmin() method
    # ddmin() computes min failure-inducing config
    # dd() computes min failure-inducing diff

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
    verbose = 1
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

    def __listintersect(self, c1, c2):
        """Return the common elements of C1 and C2."""
        s2 = {}
        for delta in c2:
            s2[delta] = 1

        c = []
        for delta in c1:
            if delta in s2:
                c.append(delta)

        return c

    def __listunion(self, c1, c2):
        """Return the union of C1 and C2."""
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
        # c = sorted(c)

        # If we had this test before, return its result
        if self.cache_outcomes:
            cached_result = self.outcome_cache.lookup(c)
            if cached_result is not None:
                return cached_result

        if self.monotony:
            # Check whether we had a passing superset of this test before
            cached_result = self.outcome_cache.lookup_superset(c)
            if cached_result == self.PASS:
                return self.PASS
            
            cached_result = self.outcome_cache.lookup_subset(c)
            if cached_result == self.FAIL:
                return self.FAIL

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
        print("in test and resolve")
        c2 = self.__listunion(r, c)
        print(csub, r)
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

    def test_mix(self, csub, c, direction):
        if self.minimize:
            (t, csub) = self.test_and_resolve(csub, [], c, direction)
            if t == self.FAIL:
                return (t, csub)

        if self.maximize:
            csubbar = self.__listminus(self.CC, csub)
            cbar    = self.__listminus(self.CC, c)
            if direction == self.ADD:
                directionbar = self.REMOVE
            else:
                directionbar = self.ADD

            (tbar, csubbar) = self.test_and_resolve(csubbar, [], cbar,
                                                    directionbar)

            csub = self.__listminus(self.CC, csubbar)

            if tbar == self.PASS:
                t = self.FAIL
            elif tbar == self.FAIL:
                t = self.PASS
            else:
                t = self.UNRESOLVED

        return (t, csub)
    
    # dd
    def ddgen(self, c, minimize, maximize):
        """Return a 1-minimal failing subset of C"""

        self.minimize = minimize
        self.maximize = maximize

        n = 2
        self.CC = c

        if self.debug_dd:
            print("dd(%s, %d)..." % (self.pretty(c), n))

        outcome = self._dd(c, n)

        if self.debug_dd:
            print("dd(%s, %d) = %s" % (self.pretty(c), n, outcome))

        return outcome
    
    def _dd(self, c, n):
        """Stub to overload in subclasses"""

        assert self.test([]) == self.PASS

        run = 1
        cbar_offset = 0

        # We replace the tail recursion from the paper by a loop
        while 1:
            tc = self.test(c)
            assert tc == self.FAIL or tc == self.UNRESOLVED

            if n > len(c):
                # No further minimizing
                if self.verbose:
                    print("dd: done")
                return c

            self.report_progress(c, "dd")

            cs = self.split(c, n)

            if self.verbose:
                print()
                print("dd (run #%d): trying" % run)
                for i in range(n):
                    if i > 0:
                        print("+",)
                    print(len(cs[i]),)
                print()

            c_failed    = 0
            cbar_failed = 0

            next_c = c[:]
            next_n = n

            if not c_failed:
                # Check complements
                cbars = n * [self.UNRESOLVED]

                # print("cbar_offset =", cbar_offset)

                for j in range(n):
                    i = int((j + cbar_offset) % n)
                    cbars[i] = self.__listminus(c, cs[i])
                    t, cbars[i] = self.test_mix(cbars[i], c, self.ADD)
                    doubled = self.__listintersect(cbars[i], cs[i])
                    if doubled != []:
                        cs[i] = self.__listminus(cs[i], doubled)

                    if t == self.FAIL:
                        if self.debug_dd:
                            print("dd: reduced to", len(cbars[i]),)
                            print("deltas:",)
                            print(self.pretty(cbars[i]))

                        cbar_failed = 1
                        next_c = self.__listintersect(next_c, cbars[i])
                        next_n = next_n - 1
                        self.report_progress(next_c, "dd")

                        # In next run, start removing the following subset
                        cbar_offset = i
                        break

            if not c_failed and not cbar_failed:
                if n >= len(c):
                    # No further minimizing
                    print("dd: done")
                    return c

                next_n = min(len(c), n * 2)
                if self.verbose:
                    print("dd: increase granularity to", next_n)
                cbar_offset = (cbar_offset * next_n) / n

            c = next_c
            n = next_n
            run = run + 1

    def ddmin(self, c):
        return self.ddgen(c, 1, 0)

    def ddmax(self, c):
        return self.ddgen(c, 0, 1)

    def ddmix(self, c):
        return self.ddgen(c, 1, 1)

    # general delta debugging (new TSE version)
    def dddiff(self, c):
        n = 2

        if self.debug_dd:
            print("dddiff(" + self.pretty(c) + ", " + n + ")...")

        outcome = self._dddiff([], c, n)

        if self.debug_dd:
            print("dddiff(" + self.pretty(c) + ", " + n + ") = " +
                   outcome)

        return outcome

    def _dddiff(self, c1, c2, n): # @brian
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
                t1 = self._test(c1)
                t2 = self._test(c2)
            
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

    
    # def _ddmax(self, c1, c2, n): # @brian
    #     run = 1
    #     cbar_offset = 0

    #     c1_orig = c1[:]
    #     c2_orig = c2[:]

    #     # We replace the tail recursion from the paper by a loop
    #     while 1:
    #         if self.debug_dd:
    #             print("dd: c1 =", self.pretty(c1))
    #             print("dd: c2 =", self.pretty(c2))

    #         if self.assume_axioms_hold:
    #             t1 = self.FAIL
    #             t2 = self.PASS
    #         else:
    #             t1 = self._test(c1)
    #             t2 = self._test(c2)
            
    #         assert t1 == self.FAIL
    #         assert t2 == self.PASS
    #         assert self.__listsubseteq(c1, c2)

    #         c = self.__listminus(c2, c1)

    #         if self.debug_dd:
    #             print("dd: c2 - c1 =", self.pretty(c))

    #         if n > len(c):
    #             # No further minimizing
    #             if self.verbose:
    #                 print("dd: done")
    #             return (c, c1, c2)

    #         self.report_progress(c, "dd")

    #         cs = self.split(c, n)

    #         if self.verbose:
    #             print()
    #             print("dd (run #" + str(run) + "): trying",)
    #             for i in range(n):
    #                 if i > 0:
    #                     print("+",)
    #                 print(len(cs[i]),)
    #             print()

    #         progress = 0

    #         next_c1 = c1[:]
    #         next_n = n

    #         # Check subsets
    #         for j in range(n):
    #             i = int((j + cbar_offset) % n)

    #             if self.debug_dd:
    #                 print("dd: trying", self.pretty(cs[i]))

    #             csub = self.__listunion(c1, cs[i])
    #             t = self._test(csub)

    #             # case 1: if union c1 with subset fails (c1 was initially passing)
    #             # c2 (failing test case) is now csub (union c1 subset)
    #             # minimal test would be within c1 and c2 again.
    #             if t == self.FAIL:
    #                 # Found
    #                 progress    = 1
    #                 next_c1     = csub
    #                 next_n      = max(next_n - 1, 2)
    #                 cbar_offset = i

    #                 if self.debug_dd:
    #                     print("dd: reduce c2 to", len(c2), "deltas:",)
    #                     print(self.pretty(c2))
    #                 break

    #         if progress:
    #             if self.animate is not None:
    #                 self.animate.write_outcome(
    #                     self.__listminus(next_c1, c1_orig), self.PASS)
    #                 self.animate.write_outcome(
    #                     self.__listminus(c2_orig, c2), self.FAIL)
    #                 self.animate.write_outcome(
    #                     self.__listminus(c2, next_c1), self.DIFFERENCE)
    #                 self.animate.next_frame()

    #             self.report_progress(self.__listminus(c2, next_c1), "dd")
    #         else:
    #             if n >= len(c):
    #                 # No further minimizing
    #                 if self.verbose:
    #                     print("dd: done")
    #                 return (c, c1, c2)

    #             next_n = min(len(c), n * 2)
    #             if self.verbose:
    #                 print("dd: increase granularity to", next_n)
    #             cbar_offset = (cbar_offset * next_n) / n

    #         c1  = next_c1
    #         n   = next_n
    #         run = run + 1
    def _ddmax(self, c1, c2, n):  # Modified to handle adding to the front or back of c1
        """
        Expand c1 (failing) to find the maximum failing configuration such that
        adding or removing any element makes it passing or unresolved.
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
            t1 = self._test(c1)
            t2 = self._test(c2)
    
            assert t1 == self.FAIL, "c1 must be failing"
            assert t2 == self.PASS, "c2 must be passing"
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
                csub_back = self.__listunion(c1, cs[i])
                t_back = self._test(csub_back)
    
                # Try adding the subset to the front of c1
                csub_front = cs[i] + c1
                t_front = self._test(csub_front)
    
                if t_back == self.FAIL:
                    # If adding to the back keeps c1 failing, keep the subset
                    progress = 1
                    next_c1 = csub_back
                    next_n = max(next_n - 1, 2)
                    cbar_offset = i
    
                    if self.debug_dd:
                        print("dd: expand c1 (back) to", len(next_c1), "deltas:",)
                        print(self.pretty(next_c1))
                    break
    
                if t_front == self.FAIL:
                    # If adding to the front keeps c1 failing, keep the subset
                    progress = 1
                    next_c1 = csub_front
                    next_n = max(next_n - 1, 2)
                    cbar_offset = i
    
                    if self.debug_dd:
                        print("dd: expand c1 (front) to", len(next_c1), "deltas:",)
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
            
    # c1 is supposed to be passing
    # c2 is supposed to be failing
    # def _ddmax(self, c2, c1, n): # @brian
    #     run = 1
    #     cbar_offset = 0

    #     c1_orig = c1[:]
    #     c2_orig = c2[:]

    #     # We replace the tail recursion from the paper by a loop
    #     while 1:
    #         if self.debug_dd:
    #             print("dd: c1 =", self.pretty(c1))
    #             print("dd: c2 =", self.pretty(c2))

    #         if self.assume_axioms_hold:
    #             t1 = self.PASS
    #             t2 = self.FAIL
    #         else:
    #             t1 = self._test(c1)
    #             t2 = self._test(c2)
            
    #         assert t1 == self.PASS
    #         assert t2 == self.FAIL
    #         # reversed the subset check
    #         assert self.__listsubseteq(c2, c1)

    #         c = self.__listminus(c1, c2)

    #         if self.debug_dd:
    #             print("dd: c1 - c2 =", self.pretty(c))

    #         if n > len(c):
    #             # No further minimizing
    #             if self.verbose:
    #                 print("dd: done")
    #             return (c, c1, c2)

    #         self.report_progress(c, "dd")

    #         # the subsets
    #         cs = self.split(c, n)

    #         if self.verbose:
    #             print()
    #             print("dd (run #" + str(run) + "): trying",)
    #             for i in range(n):
    #                 if i > 0:
    #                     print("+",)
    #                 print(len(cs[i]),)
    #             print()

    #         progress = 0

    #         next_c1 = c1[:]
    #         next_c2 = c2[:]
    #         next_n = n

    #         # Check subsets
    #         for j in range(n):
    #             i = int((j + cbar_offset) % n)

    #             if self.debug_dd:
    #                 print("dd: trying", self.pretty(cs[i]))

    #             # For now not changing but potentially might have to.
    #             (t, csub) = self.test_and_resolve(cs[i], c2, c, self.REMOVE)
    #             # adding subset to c2
    #             csub = self.__listunion(c2, csub)

    #             # case 1: if union c1 with subset fails (c1 was initially passing)
    #             # c2 (failing test case) is now csub (union c1 subset)
    #             # minimal test would be within c1 and c2 again.
    #             if t == self.FAIL and t1 == self.PASS:
    #                 # Found
    #                 progress    = 1
    #                 next_c2     = csub
    #                 next_n      = 2
    #                 cbar_offset = 0

    #                 if self.debug_dd:
    #                     print("dd: reduce c2 to", len(next_c2), "deltas:",)
    #                     print(self.pretty(next_c2))
    #                 break

    #             if t == self.PASS and t2 == self.FAIL:
    #                 # Reduce to complement
    #                 progress    = 1
    #                 next_c1     = csub
    #                 next_n      = max(next_n - 1, 2)
    #                 cbar_offset = i

    #                 if self.debug_dd:
    #                     print("dd: increase c1 to", len(next_c1), "deltas:",)
    #                     print(self.pretty(next_c1))
    #                 break

    #             # considering complements now
    #             csub = self.__listminus(c, cs[i])
    #             (t, csub) = self.test_and_resolve(csub, c2, c, self.ADD)
    #             csub = self.__listunion(c2, csub)

    #             if t == self.PASS and t2 == self.FAIL:
    #                 # Found
    #                 progress    = 1
    #                 next_c1     = csub
    #                 next_n      = 2
    #                 cbar_offset = 0

    #                 if self.debug_dd:
    #                     print("dd: increase c1 to", len(next_c1), "deltas:",)
    #                     print(self.pretty(next_c1))
    #                 break

    #             if t == self.FAIL and t1 == self.PASS:
    #                 # Increase
    #                 progress    = 1
    #                 next_c2     = csub
    #                 next_n      = max(next_n - 1, 2)
    #                 cbar_offset = i

    #                 if self.debug_dd:
    #                     print("dd: reduce c2 to", len(next_c2), "deltas:",)
    #                     print(self.pretty(next_c2))
    #                 break

    #         if progress:
    #             if self.animate is not None:
    #                 self.animate.write_outcome(
    #                     self.__listminus(next_c1, c1_orig), self.PASS)
    #                 self.animate.write_outcome(
    #                     self.__listminus(c2_orig, next_c2), self.FAIL)
    #                 self.animate.write_outcome(
    #                     self.__listminus(next_c2, next_c1), self.DIFFERENCE)
    #                 self.animate.next_frame()

    #             self.report_progress(self.__listminus(next_c2, next_c1), "dd")
    #         else:
    #             if n >= len(c):
    #                 # No further minimizing
    #                 if self.verbose:
    #                     print("dd: done")
    #                 return (c, c1, c2)

    #             next_n = min(len(c), n * 2)
    #             if self.verbose:
    #                 print("dd: increase granularity to", next_n)
    #             cbar_offset = (cbar_offset * next_n) / n

    #         c1  = next_c1
    #         c2  = next_c2
    #         n   = next_n
    #         run = run + 1

    def dd(self, c):
        return self.dddiff(c)           # Backwards compatibility
    
    # all relevant deltas by applying ddmin

    # helper function: compute all different atoms of the term
    def condense_formula(self,formula):
        elems  = []
        result = []
        for and_term in formula:
            elems.extend(and_term)
        for e in elems:
            if not e in result:
                result.append(e)
        result.sort()
        return result

    # helper function: print a term in human readable form
    def pretty_formula(self,formula):
        ostr = ""
        for and_term in formula:
            print(ostr + "(",)
            astr = ""
            for el in and_term:
                print(astr + el,)
                astr = " and "
            print(")",)
            ostr = " or "

    #Helper function: compute all sets, where min_set is not subset
    def non_supersets(self, superset, min_set):
        result = []
        for e in min_set:
            result.append(self.__listminus(superset,[e]))
        return result

    #ard() computes a logical formula
    def ard(self, c):
        formula = []

        testsets = [c[:]]

        while testsets != []:
            if self.debug_dd:
                print("ard: Testsets")
                print(testsets)

            #First run
            testset = testsets.pop()
            min_set = self.ddmin(testset)


            #remove subsumed testsets
            new_testsets = []
            old_testsets = []
            for test in testsets:
                if self.__listsubseteq(min_set,test):
                    new_testsets.extend(self.non_supersets(test,min_set))
                else:
                    old_testsets.append(test)

            testsets = old_testsets

            #Create new testsets
            new_testsets.extend(self.non_supersets(testset,min_set))

            #Retest new testsets
            for test in new_testsets:
                outcome = self.test(test)
                if outcome == self.FAIL:
                    testsets.append(test)
                elif outcome == self.UNRESOLVED:
                    if self.debug_dd:
                        print("ard: UNRESOLVED don't know what to do yet")
                else:
                    pass 

            #Extend formula
            formula.append(min_set)

        if self.debug_dd:
            self.pretty_formula(formula)

            print("Needed "+ self.n_tests +":P:"+ self.n_passes+"/F:"+ self.n_fails +"/U:"+ self.n_unres )

        #Return a set of all relevant deltas, and a formula
        return (self.condense_formula(formula),[],c,formula)

import json

if __name__ == '__main__':
    # First, test the outcome cache
    oc_test()
    
    # Define our own DD subclass for our JSON parsing use case.
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
                error_message = str(e)
                error_pos = e.pos
                print("Error at position", error_pos, ":", error_message)
                if candidate[len(candidate) - 1] != '}':
                    print("------------------------------")
                    return self.FAIL
                return self.UNRESOLVED
        
        def coerce(self, c):
            # Reassemble for output.
            print(type(c))
            return "".join(c)
        
    class Missing_value(DD):
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
                error_message = str(e)
                error_pos = e.pos
                print("Error at position", error_pos, ":", error_message)
                if "Expecting value" in error_message:
                    print("------------------------------")
                    return self.FAIL
                return self.UNRESOLVED
        
        def coerce(self, c):
            # Reassemble for output.
            print(type(c))
            return "".join(c)
        
    class Fake(DD):
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
    
    print("Computing minimal failing JSON input...")
    # This input is invalid JSON: It is missing a closing bracket.
    failing_json = '{"baz": 7, "zip": 1.0, "zop": [1, 2]'
    # Convert the input JSON string into a list of characters (our configuration)
    failing_config = list(failing_json)
    
    missing_curly_brace_dd = Missing_curly_brace()
    missing_value_dd = Missing_value()
    # Check preconditions: an empty configuration (which parses to an empty string) should PASS,
    # while the full configuration (the broken JSON string) should FAIL.
    assert missing_curly_brace_dd._test([]) == missing_curly_brace_dd.PASS
    assert missing_curly_brace_dd._test(failing_config) == missing_curly_brace_dd.FAIL
    
    # Invoke ddmin to compute the 1-minimal failing configuration.
    minimal_config = missing_curly_brace_dd.dd(failing_config)
    print("minimal_config")
    for thing in minimal_config:
        print("".join(thing))
    print("==============")

    print("debug:" + str(minimal_config))
    # result = mydd.coerce(minimal_config)
    minimal_failing = "".join(minimal_config[0])
    
    print("The minimal failure-inducing JSON is:")
    print(minimal_failing)

    max_config = missing_curly_brace_dd._ddmax(list(minimal_failing), list('{ "foo": 1 }'), 2)
    for thing in max_config:
        print("".join(thing))

    print(missing_curly_brace_dd._test(list('{"t": , "bar": 3 }')))
    
    big_fail = 'asdfasdf$laksjdflasjdflkasjdflkasjdflkasjdflkj'
    initial_pass = 'sdf$abcdefgtesthijklmnop'

    fake_dd = Fake()

    minimal_config = fake_dd.dd(list(big_fail))
    print(minimal_config)

    max_config = fake_dd._ddmax(list(minimal_config[0]), list(initial_pass), 2)
    for thing in max_config:
        print("".join(thing))

    
    # Optionally, you can verify 1-minimality by testing removal of each character.
    # for i in range(len(minimal_config)):
    #     test_config = minimal_config[:i] + minimal_config[i+1:]
    #     outcome = mydd.test(test_config)
    #     print("Without char at index {}: '{}' => {}".format(i, "".join(test_config), outcome))
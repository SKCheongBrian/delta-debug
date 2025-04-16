def _dddiff(self, c1, c2, n):  # @brian
    run = 1
    cbar_offset = 0

    c1_orig = c1[:]
    c2_orig = c2[:]

    while True:
        if self.debug_dd:
            print("dd: c1 =", self.pretty(c1))
            print("dd: c2 =", self.pretty(c2))

        t1 = self.test(c1)
        t2 = self.test(c2)

        assert t1 == self.PASS
        assert t2 == self.FAIL
        assert self.__listsubseteq(c1, c2)

        c = self.__listminus(c2, c1)

        if self.debug_dd:
            print("dd: c2 - c1 =", self.pretty(c))

        if n > len(c):
            if self.verbose:
                print("dd: done")
            return (c, c1, c2)

        self.report_progress(c, "dd")

        # Sort splits by edit distance from c1
        cs = sorted(self.split(c, n), key=lambda chunk: editDistance(c1, chunk))

        if self.verbose:
            print("\ndd (run #", run, "): trying subsets sorted by edit distance")

        progress = 0
        next_c1 = c1[:]
        next_c2 = c2[:]
        next_n = n

        # Check subsets
        for j in range(n):
            i = (j + cbar_offset) % n

            if self.debug_dd:
                print("dd: trying", self.pretty(cs[i]))

            (t, csub) = self.test_and_resolve(cs[i], c1, c, self.REMOVE)
            csub = self.__listunion(c1, csub)

            if t == self.FAIL and t1 == self.PASS:
                progress = 1
                next_c2 = csub
                next_n = 2
                cbar_offset = 0

                if self.debug_dd:
                    print("dd: reduce c2 to", len(next_c2), "deltas:", self.pretty(next_c2))
                break

            if t == self.PASS and t2 == self.FAIL:
                progress = 1
                next_c1 = csub
                next_n = max(next_n - 1, 2)
                cbar_offset = i

                if self.debug_dd:
                    print("dd: increase c1 to", len(next_c1), "deltas:", self.pretty(next_c1))
                break

            # Complement test
            csub = self.__listminus(c, cs[i])
            (t, csub) = self.test_and_resolve(csub, c1, c, self.ADD)
            csub = self.__listunion(c1, csub)

            if t == self.PASS and t2 == self.FAIL:
                progress = 1
                next_c1 = csub
                next_n = 2
                cbar_offset = 0

                if self.debug_dd:
                    print("dd: increase c1 to", len(next_c1), "deltas:", self.pretty(next_c1))
                break

            if t == self.FAIL and t1 == self.PASS:
                progress = 1
                next_c2 = csub
                next_n = max(next_n - 1, 2)
                cbar_offset = i

                if self.debug_dd:
                    print("dd: reduce c2 to", len(next_c2), "deltas:", self.pretty(next_c2))
                break

        if progress:
            self.report_progress(self.__listminus(next_c2, next_c1), "dd")
        else:
            if n >= len(c):
                if self.verbose:
                    print("dd: done")
                return (c, c1, c2)

            next_n = min(len(c), n * 2)
            if self.verbose:
                print("dd: increase granularity to", next_n)
            cbar_offset = (cbar_offset * next_n) / n

        c1 = next_c1
        c2 = next_c2
        n = next_n
        run += 1

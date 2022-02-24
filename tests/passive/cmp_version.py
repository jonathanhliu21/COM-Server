#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A file containing implementation of the version class.
File not to be tested. 
"""


class Version:
    """
    A version object; determines if alpha, beta, or final release

    Also allows for comparing releases (less than, greater than, and equal only).
    """

    def __init__(self, v_str: str) -> None:
        """
        Parses release string given as `v_str` into the object.

        If `v_str` is not parsable, then raises `ValueError`.

        4 attributes:

        - X: major relase
        - Y: minor release
        - r: release_type (0 if 'a', 1 if 'b', 2 if '.'; makes easy to compare)
            - Will be evaluated to 2 if missing
            - Assumes 'a' is alpha, 'b' is beta, '.' is final release
        - N: release number
            - Will be evaluated to 0 if r is 2 and N is missing

        Acceptable:

        - "X.Y" -> n = 0, r = final release
        - "X.Y.N"
        - "X.YaN"
        - "X.YbN"

        Anything else will not be acceptable and will raise a `ValueError`.
        """

        self.x = -1
        self.y = -1
        self.r = -1
        self.n = -1

        v_arr = v_str.split(".")

        # v_arr should be size 2 or 3
        #   ["X", "Y"]
        #   ["X", "YaN"]
        #   ["X", "YbN"]
        #   ["X", "Y", "N"]

        # test which type of release
        if len(v_arr) == 3:
            # if len is 3, then it is a final release
            # x is arr[0], y is arr[1], r is 2, and n is arr[2]
            self.x = int(v_arr[0])
            self.y = int(v_arr[1])
            self.r = 2
            self.n = int(v_arr[2])

        elif len(v_arr) == 2:
            if v_arr[1].count("a") == 1:
                # test if ["X", "YaN"]; alpha release
                minor_rel = v_arr[1].split("a")

                self.x = int(v_arr[0])
                self.y = int(minor_rel[0])
                self.r = 0
                self.n = int(minor_rel[1])

            elif v_arr[1].count("b") == 1:
                # test if ["X", "YbN"]; beta release
                minor_rel = v_arr[1].split("b")

                self.x = int(v_arr[0])
                self.y = int(minor_rel[0])
                self.r = 1
                self.n = int(minor_rel[1])

            else:
                # could be ["X", "Y"]; assumes "X.Y.0"

                self.x = int(v_arr[0])
                self.y = int(v_arr[1])
                self.r = 2
                self.n = 0

        else:
            raise ValueError("Version not parsable")

        # check that all values are in range
        # all values have to be positive
        if self.x < 0 or self.y < 0 or self.r not in (0, 1, 2) or self.n < 0:
            raise ValueError("Version not parsable")

    def __repr__(self) -> str:
        """Returns string representation of self; should be same as incoming string"""

        if self.r == 0:
            dot = "a"
        elif self.r == 1:
            dot = "b"
        else:
            dot = "."

        return f"{self.x}.{self.y}{dot}{self.n}"

    def __lt__(self, other: "Version") -> bool:
        """Sees if one version is less than another

        If one value is less than the other, then returns True and breaks out without checking further.

        If one value is greater than the other, then returns False and breaks out without checking further.

        If one value is equal to the other, then continues checking.

        1. compare if major version1 < major version2
        2. compare if minor version1 < minor version2
        3. compare if release type 1 < release type 2
        4. compare if release num 1 < release num 2

        If here, then returns False.
        """

        # major version
        if self.x < other.x:
            return True
        elif self.x > other.x:
            return False

        # minor version
        if self.y < other.y:
            return True
        elif self.y > other.y:
            return False

        # release
        if self.r < other.r:
            return True
        elif self.r > other.r:
            return False

        # relase num
        if self.n < other.n:
            return True
        elif self.n > other.n:
            return False

        return False

    def __eq__(self, other: "Version") -> bool:
        """Returns if versions are equal"""

        return (
            self.x == other.x
            and self.y == other.y
            and self.r == other.r
            and self.n == other.n
        )

    def __gt__(self, other: "Version") -> bool:
        """Returns if one version is greater than another (i.e. not less than and not equal)"""

        return (not self.__lt__(other)) and (not self.__eq__(other))

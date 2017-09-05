"""Here is a class for getting names for jira random data generator
"""

import random


class Namebase:
    def __init__(self):
        self._minvalue = 1
        self._maxvalue = 99
        self._projects = (
                            'Apollo program',
                            'Solar program',
                            'Pioneer program',
                            'Helios program',
                            'Genesis program',
                            'Mariner program',
                            'Rosetta program',
                            'Phoenix program',
                            'Phobos program',
                            'Voyager program'
                        )
        self._users = (
                            'programmer',
                            'tester',
                            'constructor',
                            'user',
                            'collector',
                            'navigator',
                            'captain',
                            'pilot',
                            'designer',
                            'creator'
                        )
        self._components = (
                            'Super team',
                            'Mega team',
                            'Big team',
                            'Good team',
                            'Smart team',
                            'Clever team',
                            'Little team',
                            'Small team',
                            'Tiny team',
                            'Red team'
                        )
        self._issues = (
                            'Improve',
                            'Construct',
                            'Update',
                            'Test',
                            'Launch',
                            'Provide',
                            'Compound',
                            'Navigate',
                            'Fix',
                            'Deprecate'
                        )

    def getname_project(self):
        return "{} {}".format(random.choice(self._projects), random.randint(self._minvalue, self._maxvalue))

    def getname_user(self):
        return "{}_{}".format(random.choice(self._users), random.randint(self._minvalue, self._maxvalue))

    def getname_component(self):
        return "{} {}".format(random.choice(self._components), random.randint(self._minvalue, self._maxvalue))

    def getname_issue(self):
        return "{} {}".format(random.choice(self._issues), random.randint(self._minvalue, self._maxvalue))

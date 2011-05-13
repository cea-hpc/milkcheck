# Copyright CEA (2011)
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

'''
This modules defines the tests cases demonstrating the right behaviour for
the MilkCheck's engine
'''

from unittest import TestCase

# Classes
from MilkCheck.UI.Cli import CommandLineInterface
from MilkCheck.Engine.ServiceGroup import ServiceGroup
from MilkCheck.Engine.Service import Service
from MilkCheck.Engine.Action import Action

# Symbols
from MilkCheck.Engine.BaseEntity import NO_STATUS, DONE, TIMED_OUT
from MilkCheck.Engine.BaseEntity import WAITING_STATUS, ERROR
from MilkCheck.Engine.BaseEntity import DONE_WITH_WARNINGS, TOO_MANY_ERRORS
from MilkCheck.Engine.Dependency import CHECK, REQUIRE_WEAK

class CoreTest(TestCase):
    '''Define some strong tests cases for the Engine'''

    def test_core_behaviour_one(self):
        '''Test the ability of the core to solve a large graph N1'''
        # Define Group 1
        cli = CommandLineInterface()
        grp1 = ServiceGroup('GRP1')
        grp1_i1 = Service('I1')
        grp1_i2 = Service('I2')
        grp1_i3 = Service('I3')
        grp1_i1_act = Action('start', 'localhost', '/bin/true')
        grp1_i2_act = Action('start', 'localhost', '/bin/true')
        grp1_i2_suc = Action('status', 'localhost', '/bin/true')
        grp1_i3_act = Action('start', 'localhost', '/bin/true')
        grp1_i1.add_action(grp1_i1_act)
        grp1_i2.add_actions(grp1_i2_act, grp1_i2_suc)
        grp1_i3.add_action(grp1_i3_act)
        grp1.add_inter_dep(target=grp1_i1)
        grp1.add_inter_dep(base=grp1_i1, target=grp1_i2, sgth=CHECK)
        grp1.add_inter_dep(target=grp1_i3)
        
        # Define Group 2
        grp2 = ServiceGroup('GRP2')
        grp2_i1 = Service('I1')
        grp2_i2 = Service('I2')
        grp2_i1_act = Action('start', 'localhost', '/bin/false')
        grp2_i2_act = Action('start', 'localhost', '/bin/true')
        grp2_i1.add_action(grp2_i1_act)
        grp2_i2.add_action(grp2_i2_act)
        grp2.add_inter_dep(target=grp2_i1)
        grp2.add_inter_dep(base=grp2_i1, target=grp2_i2)
        
        # Define Group init
        s1 = Service('S1')
        s1_act = Action('start', 'localhost', '/bin/true')
        s1.add_action(s1_act)
        s2 = Service('S2')
        s2_act = Action('start', 'localhost', '/bin/true')
        s2.add_action(s2_act)
        s3 = Service('S3')
        s3_act = Action('start', 'localhost', '/bin/true')
        s3.add_action(s3_act)
        group_init = ServiceGroup('GROUP_INIT')
        group_init.add_inter_dep(target=s1)
        group_init.add_inter_dep(base=s1, target=s2, sgth=REQUIRE_WEAK)
        group_init.add_inter_dep(base=s1, target=grp1)
        group_init.add_inter_dep(base=s2, target=s3)
        group_init.add_inter_dep(base=grp1, target=s3, sgth=REQUIRE_WEAK)
        group_init.add_inter_dep(base=s3, target=grp2)
        
        # Solve the graph
        group_init.run('start')

        # Assertions
        self.assertEqual(grp2.status, ERROR)
        self.assertEqual(s3.status, ERROR)
        self.assertEqual(s2.status, ERROR)
        self.assertEqual(grp1.status, DONE_WITH_WARNINGS)
        self.assertEqual(s1.status, DONE_WITH_WARNINGS)
        self.assertEqual(group_init.status, DONE_WITH_WARNINGS)

    def test_core_behaviour_reverse(self):
        '''Test ability of the core to solve a large graph in reverse mode'''
        # Define Group 1
        grp1 = ServiceGroup('GRP1')
        grp1.algo_reversed = True
        grp1_i1 = Service('I1')
        grp1_i1.algo_reversed = True
        grp1_i2 = Service('I2')
        grp1_i2.algo_reversed = True
        grp1_i3 = Service('I3')
        grp1_i3.algo_reversed = True
        grp1_i1_act = Action('stop', 'localhost', '/bin/true')
        grp1_i2_act = Action('stop', 'localhost', '/bin/true')
        grp1_i3_act = Action('stop', 'localhost', '/bin/true')
        grp1_i1.add_action(grp1_i1_act)
        grp1_i2.add_actions(grp1_i2_act)
        grp1_i3.add_action(grp1_i3_act)
        grp1.add_inter_dep(target=grp1_i1)
        grp1.add_inter_dep(base=grp1_i1, target=grp1_i2)
        grp1.add_inter_dep(target=grp1_i3)

        # Define Group 2
        grp2 = ServiceGroup('GRP2')
        grp2.algo_reversed = True
        grp2_i1 = Service('I1')
        grp2_i1.algo_reversed = True
        grp2_i2 = Service('I2')
        grp2_i2.algo_reversed = True
        grp2_i1_act = Action('stop', 'localhost', '/bin/true')
        grp2_i2_act = Action('stop', 'localhost', '/bin/true')
        grp2_i1.add_action(grp2_i1_act)
        grp2_i2.add_action(grp2_i2_act)
        grp2.add_inter_dep(target=grp2_i1)
        grp2.add_inter_dep(base=grp2_i1, target=grp2_i2)

        # Define Group init
        s1 = Service('S1')
        s1.algo_reversed = True
        s1_act = Action('stop', 'localhost', '/bin/true')
        s1.add_action(s1_act)
        s2 = Service('S2')
        s2.algo_reversed = True
        s2_act = Action('stop', 'localhost', '/bin/true')
        s2.add_action(s2_act)
        s3 = Service('S3')
        s3.algo_reversed = True
        s3_act = Action('stop', 'localhost', '/bin/true')
        s3.add_action(s3_act)
        group_init = ServiceGroup('GROUP_INIT')
        group_init.algo_reversed = True
        group_init.add_inter_dep(target=s1)
        group_init.add_inter_dep(base=s1, target=s2, sgth=REQUIRE_WEAK)
        group_init.add_inter_dep(base=s1, target=grp1)
        group_init.add_inter_dep(base=s2, target=s3)
        group_init.add_inter_dep(base=grp1, target=s3)
        group_init.add_inter_dep(base=s3, target=grp2)

        # Solve the graph
        group_init.run('stop')

        # Assertions
        self.assertEqual(grp2.status, DONE)
        self.assertEqual(s3.status, DONE)
        self.assertEqual(s2.status, DONE)
        self.assertEqual(grp1.status, DONE)
        self.assertEqual(s1.status, DONE)
        self.assertEqual(group_init.status, DONE)
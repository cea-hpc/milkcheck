# Copyright CEA (2011)
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

'''
This modules defines the tests cases demonstrating the right behaviour for
the MilkCheck's engine
'''

from unittest import TestCase

# Classes
from MilkCheck.Engine.Action import Action
from MilkCheck.Engine.ServiceGroup import ServiceGroup
from MilkCheck.Engine.Service import Service

# Symbols
from MilkCheck.Engine.BaseEntity import DEP_ERROR, DONE
from MilkCheck.Engine.BaseEntity import CHECK, REQUIRE_WEAK

class CoreTest(TestCase):
    '''Define some strong tests cases for the Engine'''

    def test_core_behaviour_one(self):
        '''Test the ability of the core to solve a large graph N1'''
        # Define Group 1
        grp1 = ServiceGroup('GRP1')
        grp1_i1 = Service('I1')
        grp1_i2 = Service('I2')
        grp1_i3 = Service('I3')
        grp1_i1.add_action(Action('start', command='/bin/true'))
        grp1_i2.add_action(Action('start', command='/bin/true'))
        grp1_i2.add_action(Action('status', command='/bin/true'))
        grp1_i3.add_action(Action('start', command='/bin/true'))
        grp1.add_inter_dep(target=grp1_i1)
        grp1.add_inter_dep(base=grp1_i1, target=grp1_i2, sgth=CHECK)
        grp1.add_inter_dep(target=grp1_i3)
        
        # Define Group 2
        grp2 = ServiceGroup('GRP2')
        grp2_i1 = Service('I1')
        grp2_i2 = Service('I2')
        grp2_i1.add_action(Action('start', command='/bin/false'))
        grp2_i2.add_action(Action('start', command='/bin/true'))
        grp2.add_inter_dep(target=grp2_i1)
        grp2.add_inter_dep(base=grp2_i1, target=grp2_i2)
        
        # Define Group init
        svc1 = Service('S1')
        svc1.add_action(Action('start', command='/bin/true'))
        svc2 = Service('S2')
        svc2.add_action(Action('start', command='/bin/true'))
        svc3 = Service('S3')
        svc3.add_action(Action('start', command='/bin/true'))
        group_init = ServiceGroup('GROUP_INIT')
        group_init.add_inter_dep(target=svc1)
        group_init.add_inter_dep(base=svc1, target=svc2, sgth=REQUIRE_WEAK)
        group_init.add_inter_dep(base=svc1, target=grp1)
        group_init.add_inter_dep(base=svc2, target=svc3)
        group_init.add_inter_dep(base=grp1, target=svc3, sgth=REQUIRE_WEAK)
        group_init.add_inter_dep(base=svc3, target=grp2)
        
        # Solve the graph
        group_init.run('start')

        # Assertions
        self.assertEqual(grp2.status, DEP_ERROR)
        self.assertEqual(svc3.status, DEP_ERROR)
        self.assertEqual(svc2.status, DEP_ERROR)
        self.assertEqual(grp1.status, DONE)
        self.assertEqual(svc1.status, DONE)
        self.assertEqual(group_init.status, DONE)

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
        grp1_i1.add_action(Action('stop', command='/bin/true'))
        grp1_i2.add_action(Action('stop', command='/bin/true'))
        grp1_i3.add_action(Action('stop', command='/bin/true'))
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
        grp2_i1.add_action(Action('stop', command='/bin/true'))
        grp2_i2.add_action(Action('stop', command='/bin/true'))
        grp2.add_inter_dep(target=grp2_i1)
        grp2.add_inter_dep(base=grp2_i1, target=grp2_i2)

        # Define Group init
        svc1 = Service('S1')
        svc1.algo_reversed = True
        svc1.add_action(Action('stop', command='/bin/true'))
        svc2 = Service('S2')
        svc2.algo_reversed = True
        svc2.add_action(Action('stop', command='/bin/true'))
        svc3 = Service('S3')
        svc3.algo_reversed = True
        svc3.add_action(Action('stop', command='/bin/true'))
        group_init = ServiceGroup('GROUP_INIT')
        group_init.algo_reversed = True
        group_init.add_inter_dep(target=svc1)
        group_init.add_inter_dep(base=svc1, target=svc2, sgth=REQUIRE_WEAK)
        group_init.add_inter_dep(base=svc1, target=grp1)
        group_init.add_inter_dep(base=svc2, target=svc3)
        group_init.add_inter_dep(base=grp1, target=svc3)
        group_init.add_inter_dep(base=svc3, target=grp2)

        # Solve the graph
        group_init.run('stop')

        # Assertions
        self.assertEqual(grp2.status, DONE)
        self.assertEqual(svc3.status, DONE)
        self.assertEqual(svc2.status, DONE)
        self.assertEqual(grp1.status, DONE)
        self.assertEqual(svc1.status, DONE)
        self.assertEqual(group_init.status, DONE)

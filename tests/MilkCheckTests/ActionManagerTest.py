# Copyright CEA (2011)
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This modules defines the tests cases targeting the class ActionManager
"""

# Classes
from unittest import TestCase
from MilkCheck.Engine.Action import Action
from MilkCheck.Engine.Service import Service
from MilkCheck.ActionManager import ActionManager, action_manager_self

class ActionManagerTest(TestCase):
    """Test cases for action_manager_self"""

    def test_instanciation(self):
        """Test singleton handling of action_manager_self"""
        task_manager = action_manager_self()
        other_task_manager = action_manager_self()
        self.assertTrue(task_manager is other_task_manager)

    def test__add_task(self):
        """Test the behaviour of the _add_task method"""
        task_manager = ActionManager()
        task1 = Action('start')
        task1.fanout = 60
        task2 = Action('stop')
        task2.fanout = 12
        task3 = Action('status')
        task3.fanout = 50
        task_manager._add_task(task1)
        task_manager._add_task(task2)
        task_manager._add_task(task3)
        task_manager._add_task(task3)
        self.assertEqual(task_manager.fanout, 12)
        task4 = Action('check')
        task4.fanout = 3
        task_manager._add_task(task4)
        self.assertEqual(task_manager.fanout, 3)
        self.assertEqual(task_manager.tasks_count, 4)
        self.assertEqual(task_manager.tasks_done_count, 4)

    def test__add_task_weird_values(self):
        """Test the method add task with task without fanout"""
        task_manager = ActionManager()
        task1 = Action('start')
        task1.fanout = 60
        task2 = Action('stop')
        task3 = Action('status')
        task3.fanout = 50
        task_manager._add_task(task1)
        task_manager._add_task(task2)
        task_manager._add_task(task3)
        self.assertEqual(task_manager.fanout, 50)
        self.assertEqual(task_manager.tasks_count, 3)

    def test__remove_task(self):
        """Test the behaviour of the _remove_task method"""
        task_manager = ActionManager()
        task1 = Action('start')
        task1.fanout = 260
        task2 = Action('stop')
        task2.fanout = 85
        task3 = Action('status')
        task3.fanout = 85
        task4 = Action('check')
        task4.fanout = 148
        task_manager._add_task(task1)
        task_manager._add_task(task2)
        task_manager._add_task(task3)
        task_manager._add_task(task4)
        task_manager._remove_task(task2)
        self.assertEqual(task_manager.fanout, 85)
        task_manager._remove_task(task3)
        self.assertEqual(task_manager.fanout, 148)
        task_manager._remove_task(task4)
        self.assertEqual(task_manager.fanout, 260)
        task_manager._remove_task(task1)
        self.assertFalse(task_manager.fanout)
        self.assertEqual(task_manager.tasks_count, 0)
        self.assertEqual(task_manager.tasks_done_count, 4)

    def test__is_running_task(self):
        """Test the behaviour of the method _is_running_task"""
        task_manager = ActionManager()
        task1 = Action('start')
        task1.fanout = 260
        task2 = Action('stop')
        task2.fanout = 85
        task3 = Action('status')
        task3.fanout = 148
        task4 = Action('check')
        task_manager._add_task(task1)
        task_manager._add_task(task3)
        task_manager._add_task(task4)
        self.assertTrue(task_manager._is_running_task(task3))
        self.assertTrue(task_manager._is_running_task(task4))
        self.assertRaises(AssertionError, task_manager._is_running_task, None)
        self.assertFalse(task_manager._is_running_task(task2))

    def test_set_of_running_task(self):
        """
        Test return a sets of running tasks from the property running_tasks
        """
        task_manager = ActionManager()
        task1 = Action('start')
        task1.fanout = 260
        task2 = Action('stop')
        task2.fanout = 85
        task3 = Action('status')
        task3.fanout = 148
        task_manager._add_task(task1)
        task_manager._add_task(task2)
        task_manager._add_task(task3)
        self.assertTrue(task_manager.running_tasks)
        count_set = 0
        for aset in task_manager.running_tasks:
            count_set += 1
        self.assertEqual(count_set, 3)

    def test_perform_action(self):
        """test perform an action without any delay"""
        action = Action('start', 'localhost', '/bin/true')
        ser = Service('TEST')
        ser.add_action(action)
        ser.run('start')
        task_manager = action_manager_self()
        ActionManager._instance = None
        self.assertEqual(task_manager.tasks_done_count, 1)
        self.assertTrue(action.duration < 0.5)
        

    def test_perform_delayed_action(self):
        """test perform an action without any delay"""
        action = Action('start', 'localhost', 'sleep 3')
        ser = Service('TEST')
        ser.add_action(action)
        ser.run('start')
        task_manager = action_manager_self()
        ActionManager._instance = None
        self.assertEqual(task_manager.tasks_done_count, 1)
        self.assertTrue(2.8 < action.duration and action.duration < 3.5)
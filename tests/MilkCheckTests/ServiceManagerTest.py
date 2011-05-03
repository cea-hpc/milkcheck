# Copyright CEA (2011) 
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

"""
This modules defines the tests cases targeting the internal class
RunningTasksManager and the ServiceManager itself
"""

# Classes
from unittest import TestCase
from MilkCheck.Engine.Action import Action
from MilkCheck.ServiceManager import ServiceManager

class RunningTasksManagerTest(TestCase):
    """Test cases for the RunningTasksManager"""
    
    def test_add_task(self):
        """Test the behaviour of the add_task method"""
        task_manager = ServiceManager.RunningTasksManager()
        task1 = Action('start')
        task1.fanout = 60
        task2 = Action('stop')
        task2.fanout = 12
        task3 = Action('status')
        task3.fanout = 50
        task_manager.add_task(task1)
        task_manager.add_task(task2)
        task_manager.add_task(task3)
        task_manager.add_task(task3)
        self.assertEqual(task_manager.fanout, 12)
        task4 = Action('check')
        task4.fanout = 3
        task_manager.add_task(task4)
        self.assertEqual(task_manager.fanout, 3)
        self.assertEqual(task_manager.tasks_count, 4)
        self.assertEqual(task_manager.tasks_done_count, 4)

    def test_add_task_weird_values(self):
        """Test the method add task with task without fanout"""
        task_manager = ServiceManager.RunningTasksManager()
        task1 = Action('start')
        task1.fanout = 60
        task2 = Action('stop')
        task3 = Action('status')
        task3.fanout = 50
        task_manager.add_task(task1)
        task_manager.add_task(task2)
        task_manager.add_task(task3)
        self.assertEqual(task_manager.fanout, 50)
        self.assertEqual(task_manager.tasks_count, 3)
        
    def test_remove_task(self):
        """Test the behaviour of the remove_task method"""
        task_manager = ServiceManager.RunningTasksManager()
        task_manager = ServiceManager.RunningTasksManager()
        task1 = Action('start')
        task1.fanout = 260
        task2 = Action('stop')
        task2.fanout = 85
        task3 = Action('status')
        task3.fanout = 85 
        task4 = Action('check')
        task4.fanout = 148
        task_manager.add_task(task1)
        task_manager.add_task(task2)
        task_manager.add_task(task3)
        task_manager.add_task(task4)
        task_manager.remove_task(task2)
        self.assertEqual(task_manager.fanout, 85)
        task_manager.remove_task(task3)
        self.assertEqual(task_manager.fanout, 148)
        task_manager.remove_task(task4)
        self.assertEqual(task_manager.fanout, 260)
        task_manager.remove_task(task1)
        self.assertFalse(task_manager.fanout)
        self.assertEqual(task_manager.tasks_count, 0)
        self.assertEqual(task_manager.tasks_done_count, 4)
        
    def test_is_running_task(self):
        """Test the behaviour of the method is_running_task"""
        task_manager = ServiceManager.RunningTasksManager()
        task1 = Action('start')
        task1.fanout = 260
        task2 = Action('stop')
        task2.fanout = 85
        task3 = Action('status')
        task3.fanout = 148
        task4 = Action('check')
        task_manager.add_task(task1)
        task_manager.add_task(task3)
        task_manager.add_task(task4)
        self.assertTrue(task_manager.is_running_task(task3))
        self.assertTrue(task_manager.is_running_task(task4))
        self.assertRaises(AssertionError, task_manager.is_running_task, None)
        self.assertFalse(task_manager.is_running_task(task2))
        
    def test_set_of_running_task(self):
        """
        Test return a sets of running tasks from the property running_tasks
        """
        task_manager = ServiceManager.RunningTasksManager()
        task1 = Action('start')
        task1.fanout = 260
        task2 = Action('stop')
        task2.fanout = 85
        task3 = Action('status')
        task3.fanout = 148 
        task_manager.add_task(task1)
        task_manager.add_task(task2)
        task_manager.add_task(task3)
        self.assertTrue(task_manager.running_tasks)
        count_set = 0
        for aset in task_manager.running_tasks:
            count_set += 1
        self.assertEqual(count_set, 3)
        
    def test_manager_large_amount_tasks(self):
        """Test the behaviour of the manager with a large amount of tasks"""
        pass
        
        
class ServiceManagerTest(TestCase):
    """Tests cases for the class ServiceManager"""
    
    def test_instanciation(self):
        """Test the instanciation of the singleton class ServiceManager"""
        manager = ServiceManager()
        self.assertTrue(manager)
        same_manager = ServiceManager()
        self.assertTrue(manager is same_manager)
#!/usr/bin/env python3

import unittest
from unittest.mock import patch, MagicMock
from classes import ConfigurationManager, Log

class TestConfigurationManager(unittest.TestCase):

    def setUp(self):
        # Mock any external dependencies, such as the Log class
        self.mock_log = MagicMock()
        self.mock_log.get_instance.return_value = self.mock_log

        # Patch the external dependencies before each test
        patcher1 = patch('classes.Log', self.mock_log)
        patcher2 = patch('classes.Integration')
        patcher3 = patch('classes.PlaybookManager')
        patcher4 = patch('classes.os.listdir', return_value=[])

        self.addCleanup(patcher1.stop)
        self.addCleanup(patcher2.stop)
        self.addCleanup(patcher3.stop)
        self.addCleanup(patcher4.stop)

        patcher1.start()
        self.mock_integration = patcher2.start()
        self.mock_playbook_manager = patcher3.start()
        self.mock_os_listdir = patcher4.start()

        self.config_manager = ConfigurationManager()

    def test_get_enabled_integrations_no_files(self):
        # Test getting enabled integrations when no config files are present
        self.assertEqual(self.config_manager.enabled_integrations, [])

    @patch('classes.open')
    def test_add_integration_already_enabled(self, mock_open):
        # Test adding an integration that is already enabled
        self.mock_integration.return_value.enabled = True
        self.mock_integration.return_value.name = 'test_integration'

        self.config_manager._add_integration('test_integration')
        self.mock_log.info.assert_called_with('test_integration is already enabled. Returning...')

    @patch('classes.input', return_value='y')
    def test_remove_integration(self, mock_input):
        # Test removing an integration with user confirmation
        self.mock_integration.return_value.enabled = True
        self.mock_integration.return_value.name = 'test_integration'
        self.config_manager._enabled_integrations = {'test_integration': True}

        self.config_manager._remove_integration('test_integration')
        self.assertNotIn('test_integration', self.config_manager.enabled_integrations)

    # Add more tests for different scenarios and methods...

if __name__ == '__main__':
    unittest.main()

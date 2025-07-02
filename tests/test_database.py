# tests/test_database.py
"""
Database Tests for DENSO Project Manager Pro
Tests database connectivity, CRUD operations, and data integrity
"""

import unittest
import sys
import os
from datetime import datetime, timedelta
import tempfile
import json

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database_service import DatabaseService, get_database_service
from config_manager import ConfigManager


class TestDatabaseConnection(unittest.TestCase):
    """Test database connection and basic operations"""

    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.config_manager = ConfigManager()
        cls.db_service = get_database_service()

        # Test connection
        if not cls.db_service.connection_manager.test_connection():
            raise unittest.SkipTest("Database connection not available")

    def setUp(self):
        """Set up for each test"""
        self.test_data = {
            "user": {
                "username": f'test_user_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
                "password": "TestPassword123!",
                "email": f'test_{datetime.now().strftime("%Y%m%d_%H%M%S")}@test.com',
                "first_name": "Test",
                "last_name": "User",
                "role": "User",
                "department": "Testing",
            },
            "project": {
                "name": f'Test Project {datetime.now().strftime("%Y%m%d_%H%M%S")}',
                "description": "Test project description",
                "start_date": datetime.now().date(),
                "end_date": (datetime.now() + timedelta(days=30)).date(),
                "status": "Planning",
                "priority": "Medium",
                "budget": 10000.00,
                "client_name": "Test Client",
            },
        }

    def tearDown(self):
        """Clean up after each test"""
        # Clean up test data
        self._cleanup_test_data()

    def _cleanup_test_data(self):
        """Remove test data from database"""
        try:
            # Remove test users
            cleanup_query = "DELETE FROM Users WHERE Username LIKE 'test_user_%'"
            self.db_service.connection_manager.execute_non_query(cleanup_query)

            # Remove test projects
            cleanup_query = (
                "DELETE FROM Projects WHERE ProjectName LIKE 'Test Project %'"
            )
            self.db_service.connection_manager.execute_non_query(cleanup_query)

        except Exception as e:
            print(f"Cleanup warning: {str(e)}")

    def test_database_connection(self):
        """Test database connection"""
        result = self.db_service.connection_manager.test_connection()
        self.assertTrue(result, "Database connection should be successful")

    def test_connection_string_building(self):
        """Test connection string building"""
        connection_string = self.db_service.connection_manager.connection_string
        self.assertIsInstance(connection_string, str)
        self.assertIn("Driver=", connection_string)
        self.assertIn("Server=", connection_string)
        self.assertIn("Database=", connection_string)

    def test_execute_query(self):
        """Test basic query execution"""
        query = "SELECT COUNT(*) as user_count FROM Users"
        result = self.db_service.connection_manager.execute_query(query)

        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        self.assertIn("user_count", result[0])
        self.assertIsInstance(result[0]["user_count"], int)


class TestUserOperations(unittest.TestCase):
    """Test user-related database operations"""

    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.db_service = get_database_service()
        if not cls.db_service.connection_manager.test_connection():
            raise unittest.SkipTest("Database connection not available")

    def setUp(self):
        """Set up for each test"""
        self.test_user_data = {
            "username": f'test_user_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            "password": "TestPassword123!",
            "email": f'test_{datetime.now().strftime("%Y%m%d_%H%M%S")}@test.com',
            "first_name": "Test",
            "last_name": "User",
            "role": "User",
            "department": "Testing",
        }

    def tearDown(self):
        """Clean up test data"""
        try:
            cleanup_query = "DELETE FROM Users WHERE Username = ?"
            self.db_service.connection_manager.execute_non_query(
                cleanup_query, (self.test_user_data["username"],)
            )
        except:
            pass

    def test_create_user(self):
        """Test user creation"""
        result = self.db_service.create_user(self.test_user_data)
        self.assertTrue(result, "User creation should be successful")

        # Verify user exists
        query = "SELECT * FROM Users WHERE Username = ?"
        users = self.db_service.connection_manager.execute_query(
            query, (self.test_user_data["username"],)
        )

        self.assertEqual(len(users), 1)
        self.assertEqual(users[0]["Username"], self.test_user_data["username"])
        self.assertEqual(users[0]["Email"], self.test_user_data["email"])

    def test_authenticate_user(self):
        """Test user authentication"""
        # Create test user first
        self.db_service.create_user(self.test_user_data)

        # Test valid authentication
        user = self.db_service.authenticate_user(
            self.test_user_data["username"], self.test_user_data["password"]
        )

        self.assertIsNotNone(user)
        self.assertEqual(user["Username"], self.test_user_data["username"])

        # Test invalid authentication
        invalid_user = self.db_service.authenticate_user(
            self.test_user_data["username"], "wrong_password"
        )

        self.assertIsNone(invalid_user)

    def test_get_all_users(self):
        """Test getting all users"""
        # Create test user
        self.db_service.create_user(self.test_user_data)

        # Get all users
        users = self.db_service.get_all_users()

        self.assertIsInstance(users, list)
        self.assertGreater(len(users), 0)

        # Check if our test user is in the list
        test_user_found = any(
            user["Username"] == self.test_user_data["username"] for user in users
        )
        self.assertTrue(test_user_found)


class TestProjectOperations(unittest.TestCase):
    """Test project-related database operations"""

    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.db_service = get_database_service()
        if not cls.db_service.connection_manager.test_connection():
            raise unittest.SkipTest("Database connection not available")

        # Create a test user for project operations
        cls.test_user_data = {
            "username": f'project_test_user_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            "password": "TestPassword123!",
            "email": f'project_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}@test.com',
            "first_name": "Project",
            "last_name": "Tester",
            "role": "Manager",
            "department": "Testing",
        }

        cls.db_service.create_user(cls.test_user_data)

        # Get the created user
        users = cls.db_service.connection_manager.execute_query(
            "SELECT UserID FROM Users WHERE Username = ?",
            (cls.test_user_data["username"],),
        )
        cls.test_user_id = users[0]["UserID"]

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        try:
            # Clean up test projects first (due to foreign key constraint)
            cleanup_query = "DELETE FROM Projects WHERE CreatedBy = ?"
            cls.db_service.connection_manager.execute_non_query(
                cleanup_query, (cls.test_user_id,)
            )

            # Clean up test user
            cleanup_query = "DELETE FROM Users WHERE UserID = ?"
            cls.db_service.connection_manager.execute_non_query(
                cleanup_query, (cls.test_user_id,)
            )
        except:
            pass

    def setUp(self):
        """Set up for each test"""
        self.test_project_data = {
            "name": f'Test Project {datetime.now().strftime("%Y%m%d_%H%M%S")}',
            "description": "Test project description",
            "start_date": datetime.now().date(),
            "end_date": (datetime.now() + timedelta(days=30)).date(),
            "status": "Planning",
            "priority": "Medium",
            "budget": 10000.00,
            "client_name": "Test Client",
            "created_by": self.test_user_id,
        }
        self.created_project_id = None

    def tearDown(self):
        """Clean up test data"""
        if self.created_project_id:
            try:
                cleanup_query = "DELETE FROM Projects WHERE ProjectID = ?"
                self.db_service.connection_manager.execute_non_query(
                    cleanup_query, (self.created_project_id,)
                )
            except:
                pass

    def test_create_project(self):
        """Test project creation"""
        project_id = self.db_service.create_project(self.test_project_data)
        self.created_project_id = project_id

        self.assertIsNotNone(project_id)
        self.assertIsInstance(project_id, int)

        # Verify project exists

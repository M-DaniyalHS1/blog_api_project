import asyncio
import unittest
from unittest.mock import AsyncMock, patch
from sqlalchemy.exc import OperationalError
import test_articles  # Configures isolated test environment before importing main.
import main


class StartupTests(unittest.TestCase):
    def test_transient_dns_recovers(self):
        error = OperationalError(None, None, Exception("Temporary failure in name resolution"))
        with patch.object(main, "initialize_database", side_effect=[error, None]) as initialize, patch.object(main.asyncio, "sleep", new_callable=AsyncMock) as sleep:
            asyncio.run(main.connect_database())
            self.assertEqual(initialize.call_count, 2)
            sleep.assert_awaited_once_with(2)

    def test_retries_are_bounded(self):
        error = OperationalError(None, None, Exception("Temporary failure in name resolution"))
        with patch.object(main, "initialize_database", side_effect=error) as initialize, patch.object(main.asyncio, "sleep", new_callable=AsyncMock) as sleep:
            with self.assertRaises(OperationalError):
                asyncio.run(main.connect_database())
            self.assertEqual(initialize.call_count, 5)
            self.assertEqual(sleep.await_count, 4)

    def test_other_errors_fail_immediately(self):
        error = OperationalError(None, None, Exception("password authentication failed"))
        with patch.object(main, "initialize_database", side_effect=error) as initialize, patch.object(main.asyncio, "sleep", new_callable=AsyncMock) as sleep:
            with self.assertRaises(OperationalError):
                asyncio.run(main.connect_database())
            initialize.assert_called_once()
            sleep.assert_not_awaited()

import unittest

from contextlib import contextmanager

from selenium.common.exceptions import TimeoutException

from page import Page, ActionChainEx
from page_manager import PageManager


def PageTest(driver_class, page_class=Page):
    """
    PageTest is a dynamically generated class that extends unittest.TestCase and PageManager. Extend it to create
    custom test classes:

        class MyPageTest(PageTest(Firefox, MyPage)):
            def test_my_page():
                ...

    Args:
        driver_class (WebDriver): selenium driver to use (i.e. Firefox, Chrome, etc)
        page_class (Page): page to initialize the test to

    Returns:
        (PageTest) dynamic test class
    """
    class _PageTest(unittest.TestCase, PageManager):
        @classmethod
        def setUpClass(cls):
            """Create and attach the webdriver and page to the test class"""
            cls.driver = driver_class()
            cls.page = None
            cls.mouse = ActionChainEx(cls.driver)

        def setUp(self):
            self.get_page(page_class)
            self.mouse.reset_actions()

        @classmethod
        def tearDownClass(cls):
            """Close the webdriver"""
            cls.driver.quit()

        @staticmethod
        def assertCondition(condition, message=None):
            assert condition, message or condition.default_message

        def wait_for(self, condition, message=None, timeout=5, sleep_after=0):
            try:
                self.page.wait_for(condition, timeout=timeout, sleep_after=sleep_after)
            except TimeoutException as e:
                self.fail(message or f'Test failed after {e.msg}')

        @contextmanager
        def do_then_wait_until(self, condition, message=None, timeout=5, sleep_after=0):
            try:
                with self.page.do_then_wait_for(condition, timeout=timeout, sleep_after=sleep_after):
                    yield
            except TimeoutException as e:
                self.fail(message or f'Test failed after {e.msg}')

    return _PageTest

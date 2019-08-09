import re

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.wait import WebDriverWait


def make_default_condition_message(expected_condition):
    condition_class = re.search(r"<class '([\w.]+)'>", str(expected_condition.__class__)).group(1).split('.')[-1]
    message = f'condition {condition_class} was not met'
    if hasattr(expected_condition, 'locator'):
        return f'{message} for locator {str(expected_condition.locator)}'
    elif hasattr(expected_condition, 'pattern'):
        return f'{message} for pattern {str(expected_condition.pattern)}'
    else:
        return message


class Condition(object):
    def __init__(self, expected_condition, scope):
        self.expected_condition = expected_condition
        self.scope = scope

    @property
    def default_message(self):
        return make_default_condition_message(self.expected_condition)

    def wait_for(self, timeout=5):
        WebDriverWait(self.scope, timeout).until(
            self.expected_condition,
            message=f'{self.default_message} in {timeout} seconds'
        )

    def __bool__(self):
        try:
            return bool(self.expected_condition(self.scope))
        except NoSuchElementException:
            return False

    def __repr__(self):
        return str(self.__bool__())

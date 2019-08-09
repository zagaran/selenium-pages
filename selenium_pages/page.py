from contextlib import contextmanager
from time import sleep

from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec

from condition import Condition


def _parse_elem(element):
    if isinstance(element[0], Locator):
        return element[0], element[1]
    else:
        return element, {}


def _parse_locator(locator):
    if len(locator) == 3:
        if locator[2] == 'exclude':
            return (locator[0], locator[1]), True, None
        else:
            return (locator[0], locator[1]), False, locator[2]
    else:
        return (locator[0], locator[1]), False, None


class Locator(object):
    """
    Locator stores information about an element on a webpage and how selenium should find it. For information on
    locators see https://selenium-python.readthedocs.io/locating-elements.html
    """
    def __init__(self, by, value, n=1, exclude=False, test_func=None, elements=None):
        """
        Args:
            by (enum): search strategy (from selenium.webdriver.common.by.By)
            value (str) : search string
            n (int): number of elements to test for
            exclude (bool): exclude this element from locator tests
            test_func (func): custom test context to check for element in
            elements (dict): children elements
        """
        self.by = by
        self.value = value
        self.number = n
        self.exclude = exclude
        self.test_func = test_func
        self.elements = elements or {}


class Page(object):
    """
    Page is the base class that all pages inherit from. It instantiates the driver and implements methods
        common to all page instances.

    Its default url is 'about:blank' and should be replaced by the inheriting class

    It has a wait_for method that calls wait_for with its own driver
    """
    url = "^about:blank$"
    name = 'page'

    _elements = {
        'head': Locator(By.TAG_NAME, "head"),
        'body': Locator(By.TAG_NAME, "body")
    }

    def __init__(self, driver):
        self.driver = driver
        self.mouse = ActionChainEx(self.driver)
        for key in self.keys:
            locator = self._elements[key]
            setattr(self, key, WebElementEx(
                name=key,
                page=self,
                scope=self.driver,
                locator=locator
            ))

    def __getattribute__(self, item):
        try:
            return super().__getattribute__(item)
        except AttributeError:
            return self.driver.__getattribute__(item)

    def wait_for(self, condition_input, timeout=5, sleep_after=0):
        """
        Wait for a condition to be true on the driver in timeout seconds

        Args:
            condition_input (Condition / function):
                condition to evaluate, either an instance of the Condition class or a function that evaluates
                to truthy or falsey
            timeout (int): seconds to wait before raising a selenium TimeoutException
            sleep_after (int): seconds to sleep after the condition is met
        """
        if not isinstance(condition_input, Condition):
            condition = Condition(lambda d: condition_input(), self.driver)
        else:
            condition = condition_input
        wait_for(condition, timeout=timeout)
        sleep(sleep_after)

    @contextmanager
    def do_then_wait_for(self, condition_input, timeout=5, sleep_after=0):
        """
        Wait for a condition to be true on the driver in timeout seconds after context is run

        Args:
            condition_input (Condition / function):
                condition to evaluate, either an instance of the Condition class or a function that evaluates
                to truthy or falsey
            timeout (int): seconds to wait before raising a selenium TimeoutException
            sleep_after (int): seconds to sleep after the condition is met
        """
        if not isinstance(condition_input, Condition):
            condition = Condition(lambda d: condition_input(), self.driver)
        else:
            condition = condition_input
        with do_then_wait_for(condition, timeout=timeout):
            yield
        sleep(sleep_after)

    def test_elements(self):
        for key in self.keys:
            getattr(self, key).test()

    def navigate_to_page(self):
        """
        Navigate the driver to the url associated with the page.

        Overwrite this function for pages that require a click through to reach
        """
        url = self.url
        if url[0] == '^':
            url = url[1:]
        if url[-1] == '$':
            url = url[:-1]
        self.driver.get(url.replace(r"\.", '.'))

    def get(self):
        """Run navigate_to_page and wait for url to match"""
        with self.do_then_wait_for(self.url_matches(self.url)):
            self.navigate_to_page()

    def close(self):
        """Close the driver. This closes the current tab or window"""
        self.driver.close()

    def quit(self):
        """Quit the driver. This closes all tabs or windows"""
        self.driver.quit()

    @classmethod
    def extend_url(cls, extension):
        return cls.url.replace('$', extension + '$')

    @classmethod
    def extend_elements(cls, elements):
        return {
            **cls._elements,
            **elements
        }

    @property
    def keys(self):
        return list(self._elements.keys())

    @property
    def title(self):
        return self.driver.title

    @property
    def url_changes(self):
        return Condition(ec.url_changes(self.driver.current_url), self.driver)

    def url_contains(self, url):
        return Condition(ec.url_contains(url), self.driver)

    def url_matches(self, url_pattern):
        return Condition(ec.url_matches(url_pattern), self.driver)

    def url_is(self, url):
        return Condition(ec.url_to_be(url), self.driver)

    @property
    def alert_is_present(self):
        return Condition(ec.alert_is_present(), self.driver)

    @property
    def window_count(self):
        return len(self.driver.window_handles)

    def new_window_is_opened(self, current_handles=None):
        return Condition(ec.new_window_is_opened(current_handles or self.driver.window_handles), self.driver)


def wait_for(condition, timeout=5):
    """
    wait_for creates a conditional wait so that elements can be safely accessed.

        def my_test(self):
            # code that may run before condition is met
            wait_for(condition)
            # code that will run after condition is met

    Args:
        condition (Condition): a Condition object to evaluate
        timeout (int): seconds to wait before raising a selenium TimeoutException

    Raises:
        TimeoutException: If the condition is not met in time
    """
    condition.wait_for(timeout=timeout)


@contextmanager
def do_then_wait_for(condition, timeout=5):
    """
    do_then_wait_for uses wait_for as a context manager. It will run the contained code and then wait until the
        condition is met, or else raise a TimeoutException

        def my_test(self):
            with do_then_wait_for(condition):
                # code that may run before condition is met

            # code that will run after condition is met

    Args:
        condition (Condition): a Condition object to evaluate
        timeout (int): seconds to wait before raising a selenium TimeoutException

    Raises:
        TimeoutException: If the condition is not met in time
    """
    yield
    wait_for(condition, timeout=timeout)


class WebElementEx(object):
    """
    WebElementEx is an extension of the selenium WebElement that fixes the clears method for the react elements. This
        code should be removed along with all references to .element in tests and the corresponding code in
        safe_find above.

        The bug is documented here:  https://github.com/SeleniumHQ/selenium/issues/6837
    """
    def __init__(self, name, page, scope, locator, web_element=None):
        self._scope = scope
        self._elements = locator.elements
        self._locator = locator
        self.name = name
        self.page = page
        self._web_element = web_element
        for key in self.keys:
            locator = self._elements[key]
            setattr(self, key, WebElementEx(key, page, self, locator))

    def __getattribute__(self, item):
        try:
            return super().__getattribute__(item)
        except AttributeError:
            return self.element.get_attribute(item) \
                or self.element.get_attribute(item.replace('_', '-')) \
                or self.element.__getattribute__(item)

    def __getitem__(self, item):
        return self.all[item]

    @property
    def scope(self):
        if isinstance(self._scope, WebElementEx):
            return self._scope.element
        else:
            return self._scope

    @property
    def locator(self):
        return self._locator.by, self._locator.value

    @property
    def element(self):
        if self._web_element is not None:
            try:
                return self._web_element
            except NoSuchElementException:
                self._web_element = None
                return self.element
        else:
            try:
                result = self._scope.find_element(*self.locator)
                self._web_element = result
                return result

            except TimeoutException:
                raise NoSuchElementException(msg=f'Unable to locate {self.name} on {self.page} using locator {self.locator}')

    @property
    def all(self):
        try:
            wait_for(self.is_present, timeout=0)
            result = self._scope.find_elements(*self.locator)
            return [WebElementEx(self.name, self.page, self._scope, self._locator, web_element=web_element) for web_element in result]

        except TimeoutException:
            raise NoSuchElementException(msg=f'Unable to locate {self.name} in {self._scope.name} using locator {self.locator}')

    @property
    def classes(self):
        return self.element.get_attribute('class').split(' ')

    @property
    def count(self):
        return len(self._scope.find_elements(*self.locator))

    def hover(self, wait=0):
        self.page.mouse.move_to_element(self.element).perform()
        sleep(wait)
        self.page.mouse.reset_actions()

    @property
    def keys(self):
        return list(self._elements.keys())

    @property
    def selenium_id(self):
        return self.element.id

    @property
    def is_present(self):
        return Condition(ec.presence_of_element_located(self.locator), self._scope)

    @property
    def is_stale(self):
        return Condition(ec.staleness_of(self.element), self._scope)

    @property
    def is_visible(self):
        return Condition(ec.visibility_of(self.element), self._scope)

    @property
    def is_invisible(self):
        return Condition(ec.invisibility_of_element(self.element), self._scope)

    @property
    def is_clickable(self):
        return Condition(ec.element_to_be_clickable(self.locator), self._scope)

    @property
    def is_selected(self):
        return Condition(ec.element_to_be_selected(self.element), self._scope)

    @property
    def is_not_selected(self):
        return Condition(ec.element_selection_state_to_be(self.element, False), self._scope)

    def has_text(self, text):
        return Condition(ec.text_to_be_present_in_element(self.locator, text), self._scope)

    def has_class(self, class_name):
        return Condition(lambda x: class_name in self.classes)

    def clear(self):
        self.element.send_keys(Keys.CONTROL, 'a')
        self.element.send_keys(Keys.DELETE)

    def test(self):
        try:
            with self._setup_test_context():
                assert self._locator.exclude or (bool(self.element) and self.count == self._locator.number)
                for key in self.keys:
                    getattr(self, key).test()
        except NoSuchElementException as e:
            assert False, e.msg

    @contextmanager
    def _setup_test_context(self):
        if self._locator.test_func is not None:
            with getattr(self.page, self._locator.test_func)():
                yield
        else:
            yield


class ActionChainEx(object):
    """
    ActionChainEx is an extension of the selenium Action Chains that fixes the reset_actions method for the
        Firefox driver. When that bug is fixed, this section can be deleted along with the corresponding code in the
        BasePage init.

        The bug is documented at https://github.com/SeleniumHQ/selenium/issues/6837
    """
    def __init__(self, driver):
        self.action_chain = ActionChains(driver)

    def __getattribute__(self, item):
        try:
            return super().__getattribute__(item)
        except AttributeError:
            return self.action_chain.__getattribute__(item)

    def reset_actions(self):
        self.action_chain = ActionChains(self._driver)

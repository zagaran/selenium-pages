from contextlib import contextmanager
from selenium.webdriver.common.by import By

from selenium_pages import Page, Locator


class MdnHome(Page):
    url = r"^https://developer.mozilla.org/en-US/$"

    _elements = Page.extend_elements({
        'header': Locator(By.TAG_NAME, "header", elements={
            'technologies_dropdown': Locator(By.LINK_TEXT, 'Technologies'),
            'technologies_panel': Locator(By.ID, 'nav-tech-submenu'),
            'references_dropdown': Locator(By.LINK_TEXT, 'References & Guides'),
            'feedback_dropdown': Locator(By.LINK_TEXT, 'Feedback'),
            'open_search': Locator(By.CLASS_NAME, 'search-trigger'),
            'fake': Locator(By.ID, 'fake', exclude=True),
            'close_search': Locator(By.ID, 'close-header-search')}),
        'main_search_bar': Locator(By.ID, "home-q"),
        'div': Locator(By.TAG_NAME, 'div')
    })

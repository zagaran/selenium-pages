from page import Page


class PageManager(object):
    def __init__(self, driver_class, page_class=None):
        self.driver = driver_class()
        self.page = None
        self.get_page(page_class) if page_class else self.get_page((Page(self.driver)))
        self.mouse = self.page.mouse

    def __getattribute__(self, item):
        try:
            return super().__getattribute__(item)
        except AttributeError:
            return self.driver.__getattribute__(item)

    def set_page(self, page_class):
        self.page = page_class(self.driver)

    def get_page(self, page_class):
        self.set_page(page_class)
        self.page.get()

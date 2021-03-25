from unittest import TestCase
from nav.statemon.abstractchecker import AbstractChecker
from nav.web.servicecheckers import load_checker_classes, get_description


class ServiceCheckersTest(TestCase):
    def test_load_checkers(self):
        checkers = load_checker_classes()
        self.assertTrue(checkers, msg="no service checkers found")
        for checker in checkers:
            self.assertTrue(issubclass(checker, AbstractChecker))
            self.assertFalse(
                checker is AbstractChecker,
                msg="AbstractChecker returned as real checker",
            )

    def test_get_ssh_description(self):
        descr = get_description('ssh')
        self.assertTrue(descr)
        self.assertTrue('description' in descr)
        self.assertTrue('args' in descr)
        self.assertTrue('optargs' in descr)

import unittest
from mpw import make_breadcrumbs


class TestBreadCrumbs(unittest.TestCase):

    def test_make_breadcrumbs(self):
        self.assertListEqual(make_breadcrumbs(""), [
        ], msg="empty path")
        self.assertListEqual(make_breadcrumbs("/"), [
        ], msg="root path")
        self.assertListEqual(make_breadcrumbs("foo"), [
            {'label': 'foo', 'path': '/foo'},
        ])
        self.assertListEqual(make_breadcrumbs("foo/baz"), [
            {'label': 'foo', 'path': '/foo'},
            {'label': 'baz', 'path': '/foo/baz'},
        ])
        self.assertListEqual(make_breadcrumbs("/foo"), [
            {'label': 'foo', 'path': '/foo'},
        ])
        self.assertListEqual(make_breadcrumbs("/foo/baz"), [
            {'label': 'foo', 'path': '/foo'},
            {'label': 'baz', 'path': '/foo/baz'},
        ])

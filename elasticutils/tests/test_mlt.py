from nose.tools import eq_

from elasticutils import MLT
from elasticutils.tests import ElasticTestCase


class MoreLikeThisTest(ElasticTestCase):
    @classmethod
    def setup_class(cls):
        super(MoreLikeThisTest, cls).setup_class()
        if cls.skip_tests:
            return

        cls.create_index()
        cls.index_data([
                {'id': 1, 'foo': 'bar', 'tag': 'awesome'},
                {'id': 2, 'foo': 'bar', 'tag': 'boring'},
                {'id': 3, 'foo': 'bar', 'tag': 'awesome'},
                {'id': 4, 'foo': 'bar', 'tag': 'boring'},
                {'id': 5, 'foo': 'bar', 'tag': 'elite'},
                {'id': 6, 'foo': 'notbar', 'tag': 'gross'},
                {'id': 7, 'foo': 'notbar', 'tag': 'awesome'},
            ])
        cls.refresh()

    def test_mlt_on_foo(self):
        """Verify MLT with the foo field."""
        # We need to pass min_term_freq and min_doc_freq, because the terms
        # we are using are only once in each document.
        mlt = MLT(self.get_s(), 1, ['foo'], min_term_freq=1, min_doc_freq=1)
        eq_(len(mlt), 4)

    def test_mlt_on_tag(self):
        """Verify MLT with the tag field."""
        # We need to pass min_term_freq and min_doc_freq, because the terms
        # we are using are only once in each document.
        mlt = MLT(self.get_s(), 1, ['tag'], min_term_freq=1, min_doc_freq=1)
        eq_(len(mlt), 2)

    def test_mlt_on_two_fields(self):
        """Verify MLT on tag and foo fields."""
        mlt = MLT(self.get_s(), 1, ['tag', 'foo'],
                  min_term_freq=1, min_doc_freq=1)
        eq_(len(mlt), 5)

    def test_mlt_on_foo_with_filter(self):
        """Verify MLT with the foo field while filtering on tag."""
        # We need to pass min_term_freq and min_doc_freq, because the terms
        # we are using are only once in each document.
        mlt = MLT(self.get_s().filter(tag='boring'), 1, ['foo'],
                  min_term_freq=1, min_doc_freq=1)
        eq_(len(mlt), 2)

        mlt = MLT(self.get_s().filter(tag='elite'), 1, ['foo'],
                  min_term_freq=1, min_doc_freq=1)
        eq_(len(mlt), 1)

        mlt = MLT(self.get_s().filter(tag='awesome'), 1, ['foo'],
                  min_term_freq=1, min_doc_freq=1)
        eq_(len(mlt), 1)

        mlt = MLT(self.get_s().filter(tag='gross'), 1, ['foo'],
                  min_term_freq=1, min_doc_freq=1)
        eq_(len(mlt), 0)

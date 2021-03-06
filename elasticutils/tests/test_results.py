from nose.tools import eq_

from elasticutils import S, DefaultMappingType, NoModelError, MappingType
from elasticutils.tests import ElasticTestCase


model_cache = []


def reset_model_cache():
    del model_cache[0:]


class Meta(object):
    def __init__(self, db_table):
        self.db_table = db_table


class Manager(object):
    def filter(self, id__in=None):
        return [m for m in model_cache if m.id in id__in]


class FakeModel(object):
    _meta = Meta('fake')
    objects = Manager()

    def __init__(self, **kw):
        for key in kw:
            setattr(self, key, kw[key])
        model_cache.append(self)


class FakeMappingType(MappingType):
    def get_model(self):
        return FakeModel


class TestResultsWithData(ElasticTestCase):
    @classmethod
    def setup_class(cls):
        super(TestResultsWithData, cls).setup_class()
        if cls.skip_tests:
            return

        cls.create_index()
        cls.index_data([
                {'id': 1, 'foo': 'bar', 'tag': 'awesome', 'width': '2'},
                {'id': 2, 'foo': 'bart', 'tag': 'boring', 'width': '7'},
                {'id': 3, 'foo': 'car', 'tag': 'awesome', 'width': '5'},
                {'id': 4, 'foo': 'duck', 'tag': 'boat', 'width': '11'},
                {'id': 5, 'foo': 'train car', 'tag': 'awesome', 'width': '7'}
            ])

    @classmethod
    def teardown_class(cls):
        super(TestResultsWithData, cls).teardown_class()
        reset_model_cache()

    def test_default_results_are_default_mapping_type(self):
        """With untyped S, return dicts."""
        # Note: get_s with no args should return an untyped S
        searcher = list(self.get_s().query(foo='bar'))
        assert isinstance(searcher[0], DefaultMappingType)

    def test_typed_s_returns_type(self):
        """With typed S, return objects of type."""
        searcher = list(self.get_s(FakeMappingType).query(foo='bar'))
        assert isinstance(searcher[0], FakeMappingType)

    def test_values_dict_results(self):
        """With values_dict, return list of dicts."""
        searcher = list(self.get_s().query(foo='bar').values_dict())
        assert isinstance(searcher[0], dict)

    def test_values_list_no_fields(self):
        """Specifying no fields with values_list defaults to ['id']."""
        searcher = list(self.get_s().query(foo='bar').values_list())
        assert isinstance(searcher[0], tuple)
        # We sort the result and expected result here so that the
        # order is stable and comparable.
        eq_(sorted(searcher[0]), sorted((u'2', u'bar', u'awesome', 1)))

    def test_values_list_results(self):
        """With values_list fields, returns list of tuples."""
        searcher = list(self.get_s().query(foo='bar')
                                    .values_list('foo', 'width'))
        assert isinstance(searcher[0], tuple)

    def test_default_results_form_has_metadata(self):
        """Test default results form has metadata."""
        searcher = list(self.get_s().query(foo='bar'))
        assert hasattr(searcher[0], '_id')
        assert hasattr(searcher[0], '_score')
        assert hasattr(searcher[0], '_source')
        assert hasattr(searcher[0], '_type')
        assert hasattr(searcher[0], '_explanation')
        assert hasattr(searcher[0], '_highlight')

    def test_values_list_form_has_metadata(self):
        """Test default results form has metadata."""
        searcher = list(self.get_s().query(foo='bar').values_list('id'))
        assert hasattr(searcher[0], '_id')
        assert hasattr(searcher[0], '_score')
        assert hasattr(searcher[0], '_source')
        assert hasattr(searcher[0], '_type')
        assert hasattr(searcher[0], '_explanation')
        assert hasattr(searcher[0], '_highlight')

    def test_values_dict_form_has_metadata(self):
        """Test default results form has metadata."""
        searcher = list(self.get_s().query(foo='bar').values_dict())
        assert hasattr(searcher[0], '_id')
        assert hasattr(searcher[0], '_score')
        assert hasattr(searcher[0], '_source')
        assert hasattr(searcher[0], '_type')
        assert hasattr(searcher[0], '_explanation')
        assert hasattr(searcher[0], '_highlight')

    def test_values_dict_no_args(self):
        """Calling values_dict() with no args fetches all fields."""
        eq_(S().query(fld1=2)
               .values_dict()
               ._build_query(),
            {"query": {"term": {"fld1": 2}}})

    def test_values_list_no_args(self):
        """Calling values() with no args fetches only id."""
        eq_(S().query(fld1=2)
               .values_list()
               ._build_query(),
            {'query': {"term": {"fld1": 2}}})


class TestMappingType(ElasticTestCase):
    def tearDown(self):
        super(TestMappingType, self).tearDown()
        self.__class__.cleanup_index()

    def test_default_mapping_type(self):
        data = [
            {'id': 1, 'name': 'Alice'}
            ]

        self.__class__.create_index()
        self.__class__.index_data(data)
        s = self.get_s(DefaultMappingType)
        result = list(s)[0]

        assert isinstance(result, DefaultMappingType)
        eq_(result.id, 1)
        self.assertRaises(NoModelError, lambda: result.object)

    def test_mapping_type_attribute_override(self):
        data = [
            {'id': 1, '_object': 'foo'}
            ]

        self.__class__.create_index()
        self.__class__.index_data(data)
        s = self.get_s(DefaultMappingType)
        result = list(s)[0]

        # Instance attribute (which starts out as None) takes precedence.
        eq_(result._object, None)
        # _object ES result field is available through __getitem__
        eq_(result['_object'], 'foo')  # key/val from ES

        # Get the ES result field id
        eq_(result.id, 1)
        # Set id to something else
        result.id = 'foo'
        # Now it returns the instance attribute
        eq_(result.id, 'foo')
        # id still available through __getitem__
        eq_(result['id'], 1)

        # If it doesn't exist, throw AttributeError
        self.assertRaises(AttributeError, lambda: result.doesnt_exist)
        # If it doesn't exist, throw KeyError
        self.assertRaises(KeyError, lambda: result['doesnt_exist'])

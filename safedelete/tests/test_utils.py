from django.test import TestCase
from safedelete.utils import get_deleted_or_not_deleted_filters_dictionary
from safedelete import utils

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch  # for python 2 supporting


class TestFiltersDictionary(TestCase):

    @patch.object(utils, 'USE_BOOLEAN_FIELD', False)
    @patch.object(utils, 'FIELD_NAME', 'deleted')
    def test_get_deleted_with_datetime_field(self):
        filters = get_deleted_or_not_deleted_filters_dictionary(get_deleted=True)
        self.assertEqual(filters, {'deleted__isnull': False})

    @patch.object(utils, 'USE_BOOLEAN_FIELD', False)
    @patch.object(utils, 'FIELD_NAME', 'deleted')
    def test_get_not_deleted_with_datetime_field(self):
        filters = get_deleted_or_not_deleted_filters_dictionary(get_deleted=False)
        self.assertEqual(filters, {'deleted__isnull': True})

    @patch.object(utils, 'USE_BOOLEAN_FIELD', True)
    @patch.object(utils, 'BOOLEAN_FIELD_NAME', 'is_deleted')
    def test_get_deleted_with_boolean_field(self):
        filters = get_deleted_or_not_deleted_filters_dictionary(get_deleted=True)
        self.assertEqual(filters, {'is_deleted': True})

    @patch.object(utils, 'USE_BOOLEAN_FIELD', True)
    @patch.object(utils, 'BOOLEAN_FIELD_NAME', 'is_deleted')
    def test_get_not_deleted_with_boolean_field(self):
        filters = get_deleted_or_not_deleted_filters_dictionary(get_deleted=False)
        self.assertEqual(filters, {'is_deleted': False})

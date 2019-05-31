import pytest
from namedlist import namedlist
from mcod.lib.helpers import change_namedlist


class TestChangeNamedlist:
    def test_correct_change(self):
        test_list = namedlist('test_list', ['x', 'y'])
        test_list_instance = test_list(1, 2)
        assert test_list_instance.x == 1
        assert test_list_instance.y == 2

        test_list_instance2 = change_namedlist(test_list_instance, {'x': 3})
        assert test_list_instance2.x == 3
        assert test_list_instance2.y == 2

    def test_assert(self):
        test_list = namedlist('test_list', ['x', 'y'])
        test_list_instance = test_list(1, 2)
        with pytest.raises(KeyError) as e:
            change_namedlist(test_list_instance, {'z': 3})
        assert 'Field with name z is not in list test_list(x=1, y=2)' in str(e.value)

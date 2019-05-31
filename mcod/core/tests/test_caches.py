import pytest

from mcod.core.caches import flush_sessions, flush_cache


@pytest.mark.run(order=2)
def test_flush_sessions(sessions_cache):
    sessions_cache.set('aaaa', {'a': 'b'})
    val = sessions_cache.get('aaaa')
    assert 'a' in val
    assert val['a'] == 'b'

    flush_sessions()

    val = sessions_cache.get('aaaa')
    assert val is None


@pytest.mark.run(order=2)
def test_flush_cache(default_cache):
    default_cache.set('aaaa', {'a': 'b'})
    val = default_cache.get('aaaa')
    assert 'a' in val
    assert val['a'] == 'b'

    flush_cache()

    val = default_cache.get('aaaa')
    assert val is None

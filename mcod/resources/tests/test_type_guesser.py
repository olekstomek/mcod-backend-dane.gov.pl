from unittest import mock

import pytest

from mcod.resources.type_guess import TypeGuesser


@pytest.fixture
def guesser():
    return TypeGuesser()


@mock.patch("mcod.unleash.is_enabled", lambda x: True)
class TestTypeGuesser:

    def test_int(self, guesser):
        assert list(guesser.cast(10)) == [('integer', 'default', 9), ('number', 'default', 10), ('any', 'default', 13)]
        assert list(guesser.cast("10")) == [
            ('integer', 'default', 9),
            ('number', 'default', 10),
            ('string', 'default', 12),
            ('any', 'default', 13)
        ]

    def test_float(self, guesser):
        assert list(guesser.cast(10.1)) == [('number', 'default', 10), ('any', 'default', 13)]
        assert list(guesser.cast(10.123123123123123123123123123123123123123123123123123123123)) == [
            ('number', 'default', 10), ('any', 'default', 13)]

        assert list(guesser.cast('10.1')) == [('number', 'default', 10), ('string', 'default', 12),
                                              ('any', 'default', 13)]
        assert list(guesser.cast('15.04510682')) == [('number', 'default', 10), ('string', 'default', 12),
                                                     ('any', 'default', 13)]

        assert list(guesser.cast('15.0451068212332312312231111111111111112222222222233333333333333')) == [
            ('number', 'default', 10), ('string', 'default', 12),
            ('any', 'default', 13)]

    def test_time(self, guesser):
        assert list(guesser.cast("10:10")) == [('time', 'any', 6), ('string', 'default', 12), ('any', 'default', 13)]
        assert list(guesser.cast("23:59:59")) == [('time', 'any', 6), ('string', 'default', 12), ('any', 'default', 13)]
        assert list(guesser.cast("00:00:00")) == [('time', 'any', 6),
                                                  ('date', 'any', 7),
                                                  ('datetime', 'any', 8),
                                                  ('string', 'any', 12),
                                                  ('any', 'any', 13)]

        assert list(guesser.cast("00:00:01.10")) == [('time', 'any', 6),
                                                     ('datetime', 'any', 8),
                                                     ('string', 'default', 12),
                                                     ('any', 'default', 13)]

    def test_date(self, guesser):
        assert list(guesser.cast("11-02-2019")) == [('date', 'any', 7), ('string', 'default', 12),
                                                    ('any', 'default', 13)]
        assert list(guesser.cast("11/02/2019")) == [('date', 'any', 7), ('string', 'default', 12),
                                                    ('any', 'default', 13)]
        assert list(guesser.cast("11.02.2019")) == [('date', 'any', 7), ('string', 'default', 12),
                                                    ('any', 'default', 13)]

        assert list(guesser.cast("2019-11-02")) == [('date', 'any', 7), ('string', 'default', 12),
                                                    ('any', 'default', 13)]
        assert list(guesser.cast("2019/11/02")) == [('date', 'any', 7), ('string', 'default', 12),
                                                    ('any', 'default', 13)]
        assert list(guesser.cast("2019.11.02")) == [('date', 'any', 7), ('string', 'default', 12),
                                                    ('any', 'default', 13)]

    def test_datetime(self, guesser):
        # yyyy-MM-dd HH:mm
        assert list(guesser.cast("2019-11-02 11:12")) == [('datetime', 'any', 8), ('string', 'default', 12),
                                                          ('any', 'default', 13)]
        # yyyy-MM-dd HH:mm:ss
        assert list(guesser.cast("2019-11-02 11:12:12")) == [('datetime', 'any', 8), ('string', 'default', 12),
                                                             ('any', 'default', 13)]
        # yyyy-MM-dd HH:mm:ss.SSSSSS
        assert list(guesser.cast("2019-11-02 11:12:12.123")) == [('datetime', 'any', 8), ('string', 'default', 12),
                                                                 ('any', 'default', 13)]
        assert list(guesser.cast("2019-11-02 11:12:12.123456")) == [('datetime', 'any', 8), ('string', 'default', 12),
                                                                    ('any', 'default', 13)]
        # yyyy-MM-dd'T'HH:mm:ss.SSSSSS
        assert list(guesser.cast("2019-11-02T11:12:12.123")) == [('datetime', 'any', 8), ('string', 'default', 12),
                                                                 ('any', 'default', 13)]

        # yyyy/MMdd HH:mm
        assert list(guesser.cast("2019/11/02 11:12")) == [('datetime', 'any', 8), ('string', 'default', 12),
                                                          ('any', 'default', 13)]
        # yyyy/MM/dd HH:mm:ss
        assert list(guesser.cast("2019/11/02 11:12:12")) == [('datetime', 'any', 8), ('string', 'default', 12),
                                                             ('any', 'default', 13)]
        # yyyy/MM/dd HH:mm:ss.SSSSSS
        assert list(guesser.cast("2019/11/02 11:12:12.123")) == [('datetime', 'any', 8), ('string', 'default', 12),
                                                                 ('any', 'default', 13)]
        assert list(guesser.cast("2019/11/02 11:12:12.123456")) == [('datetime', 'any', 8), ('string', 'default', 12),
                                                                    ('any', 'default', 13)]
        # yyyy/MM/dd'T'HH:mm:ss.SSSSSS
        assert list(guesser.cast("2019/11/02T11:12:12.123")) == [('datetime', 'any', 8), ('string', 'default', 12),
                                                                 ('any', 'default', 13)]

        # yyyy.MM.dd HH:mm
        assert list(guesser.cast("2019.11.02 11:12")) == [('datetime', 'any', 8), ('string', 'default', 12),
                                                          ('any', 'default', 13)]
        # yyyy.MM.dd HH:mm:ss
        assert list(guesser.cast("2019.11.02 11:12:12")) == [('datetime', 'any', 8), ('string', 'default', 12),
                                                             ('any', 'default', 13)]
        # yyyy.MM.dd HH:mm:ss.SSSSSS
        assert list(guesser.cast("2019.11.02 11:12:12.123")) == [('datetime', 'any', 8), ('string', 'default', 12),
                                                                 ('any', 'default', 13)]
        assert list(guesser.cast("2019.11.02 11:12:12.123456")) == [('datetime', 'any', 8), ('string', 'default', 12),
                                                                    ('any', 'default', 13)]
        # yyyy.MM.dd'T'HH:mm:ss.SSSSSS
        assert list(guesser.cast("2019.11.02T11:12:12.123")) == [('datetime', 'any', 8), ('string', 'default', 12),
                                                                 ('any', 'default', 13)]

    def test_string(self, guesser):
        assert list(guesser.cast("2019.30.02 11:12")) == [('string', 'default', 12), ('any', 'default', 13)]
        assert list(guesser.cast("66:12")) == [('string', 'default', 12), ('any', 'default', 13)]
        assert list(guesser.cast("123a")) == [('string', 'default', 12), ('any', 'default', 13)]
        assert list(guesser.cast('12.123123123123:1')) == [('string', 'default', 12), ('any', 'default', 13)]
        assert list(guesser.cast("100 000 000")) == [('string', 'default', 12), ('any', 'default', 13)]
        assert list(guesser.cast("100 000 000.10")) == [('string', 'default', 12), ('any', 'default', 13)]

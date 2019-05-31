# import json
# from collections import namedtuple
#
# import falcon
# import pytest
# from marshmallow import Schema, ValidationError, validates, fields
#
# from mcod.lib.decorators import validate_request, login_required
#
#
# class RequestSchema(Schema):
#     value = fields.Str(required=True)
#
#     @validates('value')
#     def over_ten(self, value):
#         if len(value) > 10:
#             raise ValidationError('ERROR')
#
#     class Meta:
#         strict = True
#
#
# class HeaderSchema(Schema):
#     header = fields.Str(required=True, load_from='X-HEADER')
#
#     @validates('header')
#     def over_ten(self, value):
#         if len(value) > 10:
#             raise ValidationError('ERROR')
#
#     class Meta:
#         strict = True
#
#
# @pytest.fixture(scope='module')
# def uri():
#     return '/test_decorators'
#
#
# @pytest.fixture(scope='module')
# def fake_user():
#     return namedtuple('User', 'email state')
#
#
# @pytest.fixture(scope='module')
# def valid_header():
#     return 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjp7InNlc3Npb25fa2V5IjoiM' \
#            'SIsImVtYWlsIjoiYSJ9LCJpYXQiOjE1MTk4NjI0NjAsIm5iZiI6MTUxOTg2MjQ2MCwiZXhwIjoxOD' \
#            'M1MjIyNDYwfQ.OqnwP4mubuBBYVL0v6oJClhNbdy4mXY-mi6nHqtM5sY'
#
#
# class SampleResource(object):
#     @falcon.before(validate_request(HeaderSchema, 'headers', req_context=True, resp_context=True))
#     @falcon.before(validate_request(RequestSchema, 'query', req_context=True, resp_context=True))
#     def get_with_context(self, req, resp):
#         resp.status = falcon.HTTP_200
#         resp.body = json.dumps({'req': req.context, 'resp': resp.context})
#
#     @falcon.before(validate_request(HeaderSchema, 'headers'))
#     @falcon.before(validate_request(RequestSchema, 'query'))
#     def get_no_context(self, req, resp):
#         resp.status = falcon.HTTP_200
#         resp.body = json.dumps({'req': req.context, 'resp': resp.context})
#
#
# class LoginRequiredResource(object):
#     @falcon.before(login_required())
#     def on_get(self, req, resp):
#         resp.status = falcon.HTTP_200
#         resp.body = json.dumps(req.user._asdict())
#
#
# class TestRequestValidator(object):
#     @pytest.mark.run(order=2)
#     def test_missing_required_param(self, client, uri):
#         client.app.add_route(uri, SampleResource(), {'GET': 'get_with_context'})
#         headers = {'X-HEADER': 'awesome'}
#         # No param in query
#         result = client.simulate_get(uri, headers=headers)
#         assert result.json['code'] == 'entity_error'
#         assert result.status == falcon.HTTP_422
#
#         # Missing header
#         result = client.simulate_get(uri, params={'value': 'aaa'})
#         assert result.json['code'] == 'entity_error'
#         assert result.status == falcon.HTTP_422
#
#     @pytest.mark.run(order=2)
#     def test_validation_errors(self, client, uri):
#         client.app.add_route(uri, SampleResource(), {'GET': 'get_no_context'})
#         headers = {'X-HEADER': 'loooong value'}
#         result = client.simulate_get(uri, params={'value': 'valid'}, headers=headers)
#         assert result.status == falcon.HTTP_422
#         assert result.json['code'] == 'entity_error'
#
#         headers = {'X-HEADER': 'abcd'}
#         result = client.simulate_get(uri, params={'value': 'loooong value'}, headers=headers)
#         assert result.status == falcon.HTTP_422
#         assert result.json['code'] == 'entity_error'
#
#     @pytest.mark.run(order=2)
#     def test_param_in_context(self, client, uri):
#         client.app.add_route(uri, SampleResource(), {'GET': 'get_with_context'})
#         headers = {'X-HEADER': 'def'}
#         result = client.simulate_get(uri, params={'value': 'abc'}, headers=headers)
#         assert result.status == falcon.HTTP_200
#         assert result.json['req']['value'] == 'abc'
#         assert result.json['resp']['value'] == 'abc'
#         assert result.json['req']['header'] == 'def'
#         assert result.json['resp']['header'] == 'def'
#
#     @pytest.mark.run(order=2)
#     def test_param_not_in_context(self, client, uri):
#         client.app.add_route(uri, SampleResource(), {'GET': 'get_no_context'})
#         headers = {'X-HEADER': 'awesome'}
#         result = client.simulate_get(uri, params={'value': 'aaa'}, headers=headers)
#         assert result.status == falcon.HTTP_200
#         assert not result.json['req']
#         assert not result.json['resp']
#
#
# class TestLoginRequired(object):
#     @pytest.mark.run(order=2)
#     def test_wrong_header(self, client, uri):
#         client.app.add_route(uri, LoginRequiredResource())
#         result = client.simulate_get(uri)
#         assert result.status == falcon.HTTP_401
#         assert result.json['code'] == 'token_missing'
#         headers = {
#             'Authorization': 'Bearer wrongtoken'}
#         result = client.simulate_get(uri, headers=headers)
#         assert result.status == falcon.HTTP_401
#         assert result.json['code'] == 'token_error'
#
#     @pytest.mark.run(order=2)
#     def test_auth_error(self, client, uri, fake_user, valid_header, mocker):
#         headers = {
#             'Authorization': valid_header
#         }
#
#         mocker.patch("mcod.lib.decorators.decode_jwt_token", return_value={"user": {'aaa': 'bbb'}})
#         result = client.simulate_get(uri, headers=headers)
#         assert result.status == falcon.HTTP_401
#         assert result.json['code'] == 'token_error'
#
#         mocker.patch("mcod.lib.decorators.decode_jwt_token",
#                      return_value={"user": {'session_key': '1234567890', 'aaa': 'bbb'}})
#         result = client.simulate_get(uri, headers=headers)
#         assert result.status == falcon.HTTP_401
#         assert result.json['code'] == 'token_error'
#
#         mocker.patch("mcod.lib.decorators.decode_jwt_token", return_value={"user": {'s': 1, 'email': 'a'}})
#         result = client.simulate_get(uri, headers=headers)
#         assert result.status == falcon.HTTP_401
#         assert result.json['code'] == 'token_error'
#
#         mocker.patch("mcod.lib.decorators.get_user", return_value=fake_user(
#             email='b',
#             state='active'
#         ))
#         mocker.patch("mcod.lib.decorators.decode_jwt_token",
#                      return_value={"user": {'session_key': '1234567890', 'email': 'a'}})
#         result = client.simulate_get(uri, headers=headers)
#         assert result.status == falcon.HTTP_401
#         assert result.json['code'] == 'authentication_error'
#
#     @pytest.mark.run(order=2)
#     def test_statuses(self, client, uri, fake_user, valid_header, mocker):
#         headers = {
#             'Authorization': valid_header
#         }
#
#         mocker.patch("mcod.lib.decorators.get_user", return_value=fake_user(
#             email='a',
#             state='dummystate'
#         ))
#         result = client.simulate_get(uri, headers=headers)
#         assert result.status == falcon.HTTP_401
#
#         mocker.patch("mcod.lib.decorators.get_user", return_value=fake_user(
#             email='a',
#             state='deleted'))
#         result = client.simulate_get(uri, headers=headers)
#         assert result.status == falcon.HTTP_401
#
#         mocker.patch("mcod.lib.decorators.get_user", return_value=fake_user(
#             email='a',
#             state='draft'))
#         result = client.simulate_get(uri, headers=headers)
#         assert result.status == falcon.HTTP_401
#
#         mocker.patch("mcod.lib.decorators.get_user", return_value=fake_user(
#             email='a',
#             state='draft'))
#         result = client.simulate_get(uri, headers=headers)
#         assert result.status == falcon.HTTP_401
#
#         mocker.patch("mcod.lib.decorators.get_user", return_value=fake_user(
#             email='a',
#             state='pending'))
#         result = client.simulate_get(uri, headers=headers)
#         assert result.status == falcon.HTTP_403
#
#     @pytest.mark.run(order=2)
#     def test_valid_auth(self, client, uri, fake_user, valid_header, mocker):
#         headers = {
#             'Authorization': valid_header
#         }
#         mocker.patch("mcod.lib.decorators.get_user", return_value=fake_user(
#             email='a',
#             state='active'
#
#         ))
#         result = client.simulate_get(uri, headers=headers)
#         assert result.status == falcon.HTTP_200
#         assert 'email' in result.json
#         assert result.json['email'] == 'a'

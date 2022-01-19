from pytest_bdd import scenarios
# import falcon
# import pytest
# from marshmallow import Schema, ValidationError, validates, fields
#
# from mcod.lib.resources.resources import BaseResourceOld
#
#
# class SampleSchema(Schema):
#     value = fields.Int(required=True)
#
#     @validates('value')
#     def over_ten(self, value):
#         if value > 2:
#             raise ValidationError('ERROR')
#
#     class Meta:
#         strict = True
#
#
# class SampleResource(BaseResourceOld):
#     def on_get_valid(self, req, resp):
#         data = {'value': 1}
#         resp.status = falcon.HTTP_200
#         resp.body = self.get_response(SampleSchema, data)
#
#     def on_get_invalid_1(self, req, resp):
#         data = {'value': 3}
#         resp.status = falcon.HTTP_200
#         resp.body = self.get_response(SampleSchema, data)
#
#     def on_get_invalid_2(self, req, resp):
#         data = {'v': 1}
#         resp.status = falcon.HTTP_200
#         resp.body = self.get_response(SampleSchema, data)
#
#     def model_validation_1(self, req, resp):
#         user = self.get_user_object()
#         user.email = 'aaaaa'
#         self.clean_model(user)
#         resp.status = falcon.HTTP_200
#         resp.body = {'result': 'ok'}
#
#     def model_validation_2(self, req, resp):
#         user = self.get_user_object()
#         user.email = 123
#         self.clean_model(user)
#         resp.status = falcon.HTTP_200
#         resp.body = {'result': 'ok'}
#
#     def get_user_object(self):
#         return object()
#
#
# @pytest.fixture(scope='module')
# def uri():
#     return '/test_resources'
#
#
# class TestResources(object):
#     @pytest.mark.run(order=0)
#     def test_valid(self, client, uri):
#         client.app.add_route(uri, SampleResource(), {'GET': 'on_get_valid'})
#         result = client.simulate_get(uri)
#         assert result.status == falcon.HTTP_200
#
#     @pytest.mark.run(order=0)
#     def test_invalid(self, client, uri):
#         client.app.add_route(uri, SampleResource(), {'GET': 'on_get_invalid_1'})
#         result = client.simulate_get(uri)
#         assert result.status_code == 520
#         assert result.status == '520 Unknown Error'
#         assert result.json['code'] == 'serialization_error'
#         assert result.json['title'] == '520 Response Error'
#
#         client.app.add_route(uri, SampleResource(), {'GET': 'on_get_invalid_2'})
#         result = client.simulate_get(uri)
#         assert result.status_code == 520
#         assert result.status == '520 Unknown Error'
#         assert result.json['code'] == 'serialization_error'
#         assert result.json['title'] == '520 Response Error'
#
#     @pytest.mark.run(order=0)
#
#     def test_model_validation(self, client, mocker, active_user):
#         client.app.add_route('/test_model_validation_1', SampleResource(), {'GET': 'model_validation_1'})
#         client.app.add_route('/test_model_validation_2', SampleResource(), {'GET': 'model_validation_2'})
#         mocker.patch('mcod.lib.tests.test_resources.SampleResource.get_user_object', return_value=active_user)
#         result = client.simulate_get('/test_model_validation_1')
#
#         assert result.status_code == 422
#         assert result.json['code'] == 'entity_error'
#         assert 'email' in result.json['errors']
#
#         # result = client.simulate_get('/test_model_validation_2')
#         # assert result.status_code == 400
#         # assert result.json['code'] == 'error'


scenarios(
    'features/api_spec.feature')

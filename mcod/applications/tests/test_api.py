from pytest_bdd import scenarios

scenarios(
    'features/application_details_api.feature',
    'features/applications_list_api.feature',
    'features/featured_applications.feature',
)

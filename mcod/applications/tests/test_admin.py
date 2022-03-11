from pytest_bdd import scenarios

from mcod.unleash import is_enabled


if not is_enabled('S46_hide_applications_admin.be'):
    scenarios(
        'features/application_details_admin.feature',
        'features/applications_list_admin.feature',
    )

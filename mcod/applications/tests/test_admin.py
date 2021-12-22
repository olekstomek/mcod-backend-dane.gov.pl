from pytest_bdd import scenarios

from mcod.unleash import is_enabled


if not is_enabled('S39_showcases.be'):  # applications are replaced by showcases in admin panel.
    scenarios(
        'features/application_details_admin.feature',
        'features/applications_list_admin.feature',
    )

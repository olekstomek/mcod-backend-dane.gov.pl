from pytest_bdd import scenarios

from mcod.unleash import is_enabled


scenarios(
    'features/account.feature',
    'features/change_password.feature',
    'features/login.feature',
    'features/logout.feature',
    'features/registration.feature',
    'features/resend_activation_email.feature',
    'features/reset_password.feature',
    'features/reset_password_confirm.feature',
    'features/dashboard.feature',
)

if is_enabled('hod.be'):
    scenarios('features/dashboard_schedules.feature')


scenarios('features/meetings_api.feature')

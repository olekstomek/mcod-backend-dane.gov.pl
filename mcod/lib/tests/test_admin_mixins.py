from pytest_bdd import scenarios
from mcod.unleash import is_enabled

if is_enabled('S25_restore_from_trash_action.be'):
    scenarios('features/admin_mixins.feature')

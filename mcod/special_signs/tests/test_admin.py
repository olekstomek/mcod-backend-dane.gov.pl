from pytest_bdd import scenarios

from mcod.unleash import is_enabled

if is_enabled('S16_special_signs.be'):
    scenarios('features/specialsigns_admin_list.feature')

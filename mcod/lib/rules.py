import rules


@rules.predicate
def assigned_to_organization(current_user):
    if not current_user or current_user.is_anonymous:
        return False
    return bool(current_user.organizations.all())


@rules.predicate
def users_is_editor(current_user):
    return current_user.is_staff

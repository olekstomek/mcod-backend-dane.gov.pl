import copy


def change_namedlist(namedlist, fields_to_change):
    """
    Make deep copy and change given fields with given values

    :param namedlist: namedlist.namedlist
    :param kwargs: dict
    :return: namedlist
    """
    new = copy.deepcopy(namedlist)
    for k, v in fields_to_change.items():
        try:
            new.__setattr__(k, v)
        except AttributeError:
            raise KeyError("Field with name {} is not in list {}".format(k, new))
    return new


def get_paremeters_from_post(POST, startswith="rule_type_", resultname="col"):
    parameters = {}
    for rule in POST:
        if rule.startswith(startswith):
            _id = int(rule.replace(startswith, "")) + 1
            col_id = f"{resultname}{_id}"
            parameters[col_id] = POST[rule]
    return parameters

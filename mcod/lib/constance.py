def replace_constanse_defaults(constance_config, d):
    for key, value in d.items():
        constance_config[key] = (value,) + constance_config[key][1:]

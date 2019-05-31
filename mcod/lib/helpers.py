from email.mime.image import MIMEImage

import copy
from django.contrib.staticfiles import finders
from functools import lru_cache


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


def parametrize_to_dict(parametrize_list, fields_list='title notes author url date image status state'):
    if type(fields_list) == str:
        fields_list = fields_list.split()
    if type(parametrize_list) == str:
        parametrize_list == parametrize_list.split()

    if len(parametrize_list) != len(fields_list):
        raise ValueError("There are different numbers of elements in input lists")
    else:
        return dict(zip(fields_list, parametrize_list))


@lru_cache()
def image_data(image_path):
    cid_name = image_path.split("/")[-1].split(".")[0]
    with open(finders.find(image_path), 'rb') as f:
        image_data = f.read()
    image = MIMEImage(image_data)
    image.add_header('Content-ID', '<' + cid_name + '>')
    return image

import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage


class BaseFileSystemStorage(FileSystemStorage):
    def __init__(self, location=None, base_url=None, **kwargs):
        location = location or settings.MEDIA_ROOT
        base_url = base_url or settings.MEDIA_URL

        if not os.path.exists(location):
            os.makedirs(location)

        super(BaseFileSystemStorage, self).__init__(
            location, base_url, **kwargs)

    def name_from_url(self, url):
        if url:
            name = url.replace(self.base_url, '')
            if self.exists(name):
                return name
        return None


class ResourcesStorage(BaseFileSystemStorage):
    def __init__(self, location=None, base_url=None, **kwargs):
        location = location or settings.RESOURCES_MEDIA_ROOT
        base_url = base_url or '%s' % settings.RESOURCES_URL
        super().__init__(location=location, base_url=base_url, **kwargs)


class WaitingResourcesStorage(BaseFileSystemStorage):
    def __init__(self, location=None, base_url=None, **kwargs):
        location = location or os.path.join(settings.RESOURCES_MEDIA_ROOT, 'waiting')
        base_url = base_url or '%s/%s' % (settings.RESOURCES_URL, 'waiting')
        super().__init__(location=location, base_url=base_url, **kwargs)


class ApplicationImagesStorage(BaseFileSystemStorage):
    def __init__(self, location=None, base_url=None, **kwargs):
        location = location or os.path.join(settings.IMAGES_MEDIA_ROOT, 'applications')
        base_url = base_url or '%s/%s' % (settings.IMAGES_URL, 'applications')
        super().__init__(location=location, base_url=base_url, **kwargs)


class OrganizationImagesStorage(BaseFileSystemStorage):
    def __init__(self, location=None, base_url=None, **kwargs):
        location = location or os.path.join(settings.IMAGES_MEDIA_ROOT, 'organizations')
        base_url = base_url or '%s/%s' % (settings.IMAGES_URL, 'organizations')
        super().__init__(location=location, base_url=base_url, **kwargs)


class CommonStorage(BaseFileSystemStorage):
    def __init__(self, location=None, base_url=None, **kwargs):
        location = location or os.path.join(settings.IMAGES_MEDIA_ROOT, 'common')
        base_url = base_url or '%s/%s' % (settings.IMAGES_URL, 'common')
        super().__init__(location=location, base_url=base_url, **kwargs)


AVAILABLE_STORAGES = {
    'applications': ApplicationImagesStorage,
    'organizations': OrganizationImagesStorage,
    'resources': ResourcesStorage,
    'waiting_resources': WaitingResourcesStorage,
    'common': CommonStorage
}


def get_storage(storage_name, location=None, base_url=None):
    storage_name = storage_name or 'images'
    try:
        cls_storage = AVAILABLE_STORAGES[storage_name]
    except KeyError:
        cls_storage = BaseFileSystemStorage
    return cls_storage(location=location, base_url=base_url)

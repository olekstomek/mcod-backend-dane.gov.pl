import logging

from celery import shared_task
from django.apps import apps
from django.db.models import Count, Sum

from mcod.counters.lib import Counter

logger = logging.getLogger('kibana-statistics')


@shared_task
def save_counters():
    counter = Counter()
    counter.save_counters()
    return {}


@shared_task
def kibana_statistics():
    resource_model = apps.get_model('resources.Resource')
    resources = resource_model.objects.all()
    organization_model = apps.get_model('organizations.Organization')
    organizations_with_dataset = organization_model.objects.annotate(num_datasets=Count('datasets')).filter(num_datasets__gt=0)
    institution_type_private = organization_model.INSTITUTION_TYPE_PRIVATE

    public_organizations_with_dataset = organizations_with_dataset.exclude(institution_type=institution_type_private)
    resources_of_public_organizations = resources.exclude(dataset__organization__institution_type=institution_type_private)
    public_downloads_count = resources_of_public_organizations.aggregate(Sum('downloads_count'))['downloads_count__sum']
    public_views_count = resources_of_public_organizations.aggregate(Sum('views_count'))['views_count__sum']
    size_of_documents_of_public_organizations = sum(
        resource.file.size
        for resource in resources_of_public_organizations.iterator()
        if resource.file and resource.file.storage.exists(resource.file.path)
    )

    private_organizations_with_dataset = organizations_with_dataset.filter(institution_type=institution_type_private)
    resources_of_private_organizations = resources.filter(dataset__organization__institution_type=institution_type_private)
    private_downloads_count = resources_of_private_organizations.aggregate(Sum('downloads_count'))['downloads_count__sum']
    private_views_count = resources_of_private_organizations.aggregate(Sum('views_count'))['views_count__sum']
    size_of_documents_of_private_organizations = sum(
        resource.file.size
        for resource in resources_of_private_organizations.iterator()
        if resource.file and resource.file.storage.exists(resource.file.path)
    )

    logger.info("public_organizations_with_dataset %d", public_organizations_with_dataset.count())
    logger.info("resources_of_public_organizations %d", resources_of_public_organizations.count())
    logger.info("downloads_of_documents_of_public_organizations %d", public_downloads_count)
    logger.info("views_of_documents_of_public_organizations %d", public_views_count)
    logger.info("size_of_documents_of_public_organizations %d", size_of_documents_of_public_organizations)

    logger.info("private_organizations_with_dataset %d", private_organizations_with_dataset.count())
    logger.info("resources_of_private_organizations %d", resources_of_private_organizations.count())
    logger.info("downloads_of_documents_of_private_organizations %d", private_downloads_count)
    logger.info("views_of_documents_of_private_organizations %d", private_views_count)
    logger.info("size_of_documents_of_private_organizations %d", size_of_documents_of_private_organizations)
    return {}

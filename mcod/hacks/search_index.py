from __future__ import unicode_literals, absolute_import

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django_elasticsearch_dsl.registries import registry
from six.moves import input


class Command(BaseCommand):
    help = 'Manage elasticsearch index.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--models',
            metavar='app[.model]',
            type=str,
            nargs='*',
            help="Specify the model or app to be updated in elasticsearch"
        )
        parser.add_argument(
            '--create',
            action='store_const',
            dest='action',
            const='create',
            help="Create the indices in elasticsearch"
        )
        parser.add_argument(
            '--populate',
            action='store_const',
            dest='action',
            const='populate',
            help="Populate elasticsearch indices with models data"
        )
        parser.add_argument(
            '--delete',
            action='store_const',
            dest='action',
            const='delete',
            help="Delete the indices in elasticsearch"
        )
        parser.add_argument(
            '--rebuild',
            action='store_const',
            dest='action',
            const='rebuild',
            help="Delete the indices and then recreate and populate them"
        )
        parser.add_argument(
            '-f',
            action='store_true',
            dest='force',
            help="Force operations without asking"
        )
        parser.add_argument(
            '--parallel',
            action='store_true',
            dest='parallel',
            help='Run populate/rebuild update multi threaded'
        )
        parser.add_argument(
            '--no-parallel',
            action='store_false',
            dest='parallel',
            help='Run populate/rebuild update single threaded'
        )
        parser.set_defaults(parallel=getattr(settings, 'ELASTICSEARCH_DSL_PARALLEL', False))
        parser.add_argument(
            '--no-count',
            action='store_false',
            default=True,
            dest='count',
            help='Do not include a total count in the summary log line'
        )
        parser.add_argument(
            '--create-connections',
            action='store_const',
            dest='connection',
            const='create',
            help="Create ES connection to each thread",
        )
        parser.add_argument(
            '--get-connections',
            action='store_const',
            dest='connection',
            const='get',
            help="Use ES connections from get_connection method",
        )
        parser.add_argument(
            '--chunk-size',
            dest='chunk_size',
            type=int,
            default=2000,
            help='Chunk size (default: 2000)',
        )

    def _get_models(self, args):
        """
        Get Models from registry that match the --models args
        """
        if args:
            models = []
            for arg in args:
                arg = arg.lower()
                match_found = False

                for model in registry.get_models():
                    if model._meta.app_label == arg:
                        models.append(model)
                        match_found = True
                    elif '{}.{}'.format(
                        model._meta.app_label.lower(),
                        model._meta.model_name.lower()
                    ) == arg:
                        models.append(model)
                        match_found = True

                if not match_found:
                    raise CommandError("No model or app named {}".format(arg))
        else:
            models = registry.get_models()

        return set(models)

    def _get_docs(self, models):
        _last_doc = None
        _logentries_doc = None
        _docs = []

        for doc in registry.get_documents(models):
            # Move history index
            if doc.Index.name == 'histories':
                _last_doc = doc
            elif doc.Index.name == 'logentries':
                _logentries_doc = doc
            else:
                _docs.append(doc)

        if _last_doc:
            _docs.append(_last_doc)
        if _logentries_doc:
            _docs.append(_logentries_doc)
        return _docs

    def _create(self, models, options):
        for index in registry.get_indices(models):
            self.stdout.write("Creating index '{}'".format(index._name))
            index.create()

    def _populate(self, models, options):
        parallel = options.get('parallel', False)
        chunk_size = options.get('chunk_size', 2000)
        for doc in self._get_docs(models):
            self.stdout.write("Indexing {} '{}' objects in '{}' index {}".format(
                doc().get_queryset_count() if options['count'] else 'all',
                doc.__name__,
                doc.Index.name,
                "(parallel)" if parallel else "")
            )
            qs = doc().get_indexing_queryset(chunk_size=chunk_size)
            doc().update(qs, parallel=parallel, chunk_size=chunk_size)

    def _delete(self, models, options):
        index_names = [str(index._name) for index in registry.get_indices(models)]

        if not options['force']:
            response = input(
                "Are you sure you want to delete "
                "the '{}' indexes? [n/Y]: ".format(", ".join(index_names)))
            if response.lower() != 'y':
                self.stdout.write('Aborted')
                return False

        for index in registry.get_indices(models):
            self.stdout.write("Deleting index '{}'".format(index._name))
            index.delete(ignore=404)
        return True

    def _rebuild(self, models, options):
        if not self._delete(models, options):
            return

        self._create(models, options)
        self._populate(models, options)

    def handle(self, *args, **options):
        if not options['action']:
            raise CommandError(
                "No action specified. Must be one of"
                " '--create','--populate', '--delete' or '--rebuild' ."
            )

        action = options['action']
        models = self._get_models(options['models'])

        if action == 'create':
            self._create(models, options)
        elif action == 'populate':
            self._populate(models, options)
        elif action == 'delete':
            self._delete(models, options)
        elif action == 'rebuild':
            self._rebuild(models, options)
        else:
            raise CommandError(
                "Invalid action. Must be one of"
                " '--create','--populate', '--delete' or '--rebuild' ."
            )
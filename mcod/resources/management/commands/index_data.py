from django.core.management.base import CommandError
from django_tqdm import BaseCommand
from elasticsearch_dsl.connections import get_connection

from mcod.celeryapp import app
from mcod.resources.models import Resource
from mcod.resources.tasks import process_resource_data_indexing_task


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--pks', type=str, default='')
        parser.add_argument(
            '--no-orphans',
            action='store_true',
            default=False,
            help='Delete orphans (stale indices with tabular data).',
            dest='no_orphans',
        )
        parser.add_argument(
            '--delete',
            action='store_true',
            default=False,
            help='Delete indices with tabular data.',
            dest='delete',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            default=False,
            help='Force reindexing even if indexed_data queue is not empty.',
            dest='force',
        )
        parser.add_argument(
            '--info',
            action='store_true',
            default=False,
            help='Just returns basic info about indexing_data queue state.',
            dest='info',
        )
        parser.add_argument(
            '--purge',
            action='store_true',
            default=False,
            help='Purge existing messages in indexing_data queue.',
            dest='purge',
        )
        parser.add_argument(
            '--rate-limit',
            type=str,
            help='Rate_limit (int, str) - the rate limit as tasks/sec or a rate limit string (`100/m`, etc.)',
            dest='rate_limit',
        )
        parser.add_argument(
            '-y, --yes',
            action='store_true',
            default=None,
            help='Continue without asking confirmation.',
            dest='yes',
        )

    def _delete_data(self, objs, **options):
        answer = options['yes']
        indices = ','.join([f'resource-{x.id}' for x in objs])
        if indices:
            self.stdout.write('Indices to delete: {}'.format(indices))
            if answer is None:
                response = input('Are you sure you want to continue? [y/N]: ').lower().strip()
                answer = response == 'y'
            if answer:
                connection = get_connection()
                connection.indices.delete(indices, ignore_unavailable=True)
                self.stdout.write('Done.')
            else:
                self.stdout.write('Aborted.')
        else:
            self.stdout.write('No indices found!')

    def _delete_orphans(self, queryset, **options):
        connection = get_connection()
        valid_indices = [x.data.idx_name for x in queryset]
        resource_data_indices = connection.indices.get('resource-*')
        indices = [x for x in resource_data_indices if x not in valid_indices]
        indices = ','.join(indices) if indices else ''
        self.stdout.write('Trying to delete orphans (stale indices with tabular data):')
        self.stdout.write(indices or '(no stale indices found)')
        if indices:
            answer = options['yes']
            if answer is None:
                response = input('Are you sure you want to continue? [y/N]: ').lower().strip()
                answer = response == 'y'
            if answer:
                connection.indices.delete(indices, ignore_unavailable=True)
            else:
                self.stdout.write('Delete of stale indices aborted.')

    def _index_data(self, objs, **options):
        self.stdout.write('Indexing of data for {} resources is delegated to Celery tasks.'.format(objs.count()))
        answer = options['yes']
        if answer is None:
            response = input('Are you sure you want to continue? [y/N]: ').lower().strip()
            answer = response == 'y'
        if answer:
            rate_limit = None
            if options['rate_limit']:
                try:
                    rate_limit = int(options['rate_limit'])
                except Exception:
                    rate_limit = options['rate_limit']
            self.app.control.rate_limit('mcod.resources.tasks.process_resource_data_indexing_task', rate_limit)

            for obj in objs:
                process_resource_data_indexing_task.s(obj.id).apply_async(queue='indexing_data')
            self.stdout.write('Done.')
        else:
            self.stdout.write('Aborted.')

    def _get_queue_info(self, queue='indexing_data'):
        data = {}
        with self.app.connection_or_acquire() as conn:
            data['message_count'] = conn.default_channel.queue_declare(queue=queue, passive=True).message_count
        return data

    def _purge_queue(self, queue='indexing_data'):
        with self.app.connection_for_write() as conn:
            conn.connect()
            count = self.app.amqp.queues[queue].bind(conn).purge()
            self.stdout.write(self.style.SUCCESS(f'Purge {queue} with {count} message(s)'))

    def handle(self, *args, **options):
        self.app = app
        qs_all = Resource.objects.with_tabular_data()

        queue_info = self._get_queue_info()

        if options['info']:
            self.stdout.write('Queue Info: {}'.format(queue_info))
            return

        if options['purge']:
            self._purge_queue()
            return

        if options['no_orphans']:
            self._delete_orphans(qs_all, **options)
            return

        count = queue_info.get('message_count')
        msg = 'Current number of msgs in \'indexing_data\' queue: {}'.format(count)
        if count > 0 and not options['force']:
            raise CommandError(
                'Operation terminated! {}. Pass --force parameter to continue anyway.'.format(msg))

        pks_str = options.get('pks')
        pks = (pk for pk in pks_str.split(',') if pk) if pks_str else None
        objs = qs_all.filter(id__in=pks).order_by('id') if pks else qs_all
        if options['delete']:
            self._delete_data(objs, **options)
        else:
            self._index_data(objs, **options)

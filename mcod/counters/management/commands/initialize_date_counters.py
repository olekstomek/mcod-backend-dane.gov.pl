import csv
import logging
import re
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from dateutil import rrule, relativedelta
from django_tqdm import BaseCommand
from django.conf import settings

from mcod.counters.models import ResourceDownloadCounter, ResourceViewCounter
from mcod.resources.models import Resource
from mcod.reports.models import SummaryDailyReport

logger = logging.getLogger('mcod')


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '--log_paths',
            nargs='+',
            help='Path to api logs containing request data.'
        )

    def handle(self, *args, **options):
        res_data = {}
        for log_path in options['log_paths']:
            self.read_from_log_history(log_path, res_data)
        self.read_from_report_files(res_data)
        res_q = Resource.orig.values('pk', 'published_at')
        res_published_dates = {r['pk']: r['published_at'].date() for r in res_q}

        rvc_count_views = 0
        rdc_count_downloads = 0
        for res_id, res_details in res_data.items():
            if Resource.orig.filter(pk=res_id).exists():
                logger.debug('Started computing counters for resource with id: ', res_id)
                rvc_list = []
                rdc_list = []
                start_date = res_published_dates.get(res_id, datetime(2018, 9, 1).date())
                dates_list = list(res_details.keys())
                dates_list.sort()
                end_date = dates_list[-1]
                sorted_entries = []
                for timestamp in rrule.rrule(freq=rrule.DAILY, dtstart=start_date, until=end_date):
                    dt = timestamp.date()
                    if dt == start_date and dt not in res_details:
                        init_val = 0
                    else:
                        init_val = None
                    if dt == start_date and dt in res_details and res_details[dt]['summary_views'] is None:
                        res_details['summary_views'] = res_details['views']
                        res_details['summary_downloads'] = res_details['downloads']
                    sorted_entries.append(
                        dict(date=dt,
                             **res_details.get(dt, {'summary_views': init_val, 'summary_downloads': init_val,
                                                    'views': init_val, 'downloads': init_val})))
                data_gaps = self.find_summary_data_gaps(sorted_entries)
                self.fill_summary_data_gaps(sorted_entries, data_gaps)
                for i in range(len(sorted_entries) - 1, -1, -1):
                    views_count = sorted_entries[i]['summary_views'] - sorted_entries[i - 1]['summary_views'] if i > 0 else\
                        sorted_entries[i]['summary_views']
                    downloads_count = sorted_entries[i]['summary_downloads'] - sorted_entries[i - 1]['summary_downloads'] \
                        if i > 0 else sorted_entries[i]['summary_downloads']
                    if views_count > 0:
                        rvc_list.append(ResourceViewCounter(
                            timestamp=sorted_entries[i]['date'], resource_id=res_id, count=views_count))
                        rvc_count_views += views_count
                    if downloads_count > 0:
                        rdc_list.append(ResourceDownloadCounter(
                            timestamp=sorted_entries[i]['date'], resource_id=res_id, count=downloads_count))
                        rdc_count_downloads += downloads_count
                logger.debug('Creating counters in db for resource with id: ', res_id)
                ResourceViewCounter.objects.bulk_create(rvc_list)
                ResourceDownloadCounter.objects.bulk_create(rdc_list)
        logger.debug('Total created views count:', rvc_count_views)
        logger.debug('Total created downloads count:', rdc_count_downloads)

    def read_from_report_files(self, res_data):
        directory_path = settings.ROOT_DIR
        files = list(SummaryDailyReport.objects.all().values_list('file', flat=True).order_by('file'))
        for file_path in files:
            logger.debug('Reading data from daily report:', file_path)
            file_name = file_path.split('/')[-1]
            name_parts = file_name.split('_')
            file_date = datetime(int(name_parts[3]), int(name_parts[4]), int(name_parts[5])).date()
            counters_date = file_date - relativedelta.relativedelta(days=1)
            full_path = f'{directory_path}{file_path}' if file_path.startswith('/') else f'{directory_path}/{file_path}'
            with open(full_path) as csvfile:
                report_reader = csv.reader(csvfile, delimiter=',')
                headers = next(report_reader, None)
                if 'formaty_po_konwersji' in headers:
                    views_index = 10
                    downloads_index = 11
                else:
                    views_index = 9
                    downloads_index = 10
                for row in report_reader:
                    try:
                        res_id = row[0]
                        views_count = int(row[views_index])
                        downloads_count = int(row[downloads_index])
                        try:
                            res_details = res_data[res_id].get(counters_date, {'views': None, 'downloads': None})
                            res_details['summary_views'] = views_count
                            res_details['summary_downloads'] = downloads_count
                            res_data[res_id][counters_date] = res_details
                        except KeyError:
                            res_data[res_id] = {counters_date: {
                                'summary_views': views_count, 'summary_downloads': downloads_count,
                                'views': None, 'downloads': None}}
                    except (IndexError, ValueError):
                        pass

    def read_from_log_history(self, log_path, res_data):
        logger.debug('Reading data from log file:', log_path)
        overall_views_count = 0
        overall_downloads_count = 0
        views_regex = r'(\[(?P<date>\d\d\/\w+\/\d\d\d\d)(\:\d\d){3}\s\+\d{4}\]\s\"GET(?!.*\b(?:media)\b)[^\"]+' \
                      r'/resources/(?P<res_id>\d+)(,[-a-zA-Z0-9_]+)?/?\sHTTP)'
        downloads_regex = r'\[(?P<date>\d\d\/\w+\/\d\d\d\d)(\:\d\d){3}\s\+\d{4}\]\s\"GET[^\"]+' \
                          r'/resources/(?P<res_id>\d+)(,[-a-zA-Z0-9_]+)?/(file|csv|jsonld)/?\sHTTP'
        max_size = 1024 * 1024 * 512
        found_lines = 0
        found_views_lines = 0
        with open(log_path, 'r') as log_file:
            def read_chunks():
                return log_file.read(max_size)
            for chunk in iter(read_chunks, ''):
                views_matches = re.findall(views_regex, chunk)
                downloads_matches = re.findall(downloads_regex, chunk)
                found_lines += len(downloads_matches)
                found_views_lines += len(views_matches)
                for match in downloads_matches:
                    match_date = datetime.strptime(match[0], '%d/%b/%Y').date()
                    try:
                        res_details = res_data[match[2]].setdefault(match_date, {
                            'downloads': 0, 'views': 0, 'summary_views': None, 'summary_downloads': None})
                        res_details['downloads'] += 1
                        res_data[match[2]][match_date] = res_details
                        overall_downloads_count += 1
                    except KeyError:
                        res_data[match[2]] = {match_date: {
                            'downloads': 1, 'views': 0, 'summary_views': None, 'summary_downloads': None}}
                for match in views_matches:
                    match_date = datetime.strptime(match[1], '%d/%b/%Y').date()
                    try:
                        res_details = res_data[match[3]].setdefault(
                            match_date, {'downloads': 0, 'views': 0, 'summary_views': None, 'summary_downloads': None})
                        res_details['views'] += 1
                        res_data[match[3]][match_date] = res_details
                        overall_views_count += 1
                    except KeyError:
                        res_data[match[3]] =\
                            {match_date: {'downloads': 0, 'views': 1, 'summary_views': None, 'summary_downloads': None}}
        return overall_views_count, overall_downloads_count, found_lines, found_views_lines

    def find_summary_data_gaps(self, sorted_entries):
        data_gaps = []
        gap_start = 0
        found_gap = False
        for entry_index, entry_details in enumerate(sorted_entries):
            if entry_details['summary_views'] is None and not found_gap:
                found_gap = True
            elif entry_details['summary_views'] is not None and not found_gap:
                gap_start = entry_index
            elif entry_details['summary_views'] is not None and found_gap:
                found_gap = False
                data_gaps.append((gap_start, entry_index))
                gap_start = entry_index
            if found_gap and entry_index == len(sorted_entries) - 1:
                data_gaps.append((gap_start, entry_index))
        return data_gaps

    def fill_summary_data_gaps(self, sorted_entries, data_gaps):
        for gap in data_gaps:
            gap_start = gap[0] + 1
            sliced_entries = sorted_entries[gap_start: gap[1] + 1]
            gap_start_views_count = sorted_entries[gap[0]]['summary_views']
            gap_end_views_count = sliced_entries[-1]['summary_views']
            gap_start_downloads_count = sorted_entries[gap[0]]['summary_downloads']
            gap_end_downloads_count = sliced_entries[-1]['summary_downloads']
            if gap_end_views_count is not None and gap_start_views_count is not None:
                self.compute_gap_valid_count_values(
                    gap_start_views_count, gap_end_views_count, 'views', sliced_entries, sorted_entries, gap_start)
                self.compute_gap_valid_count_values(
                    gap_start_downloads_count, gap_end_downloads_count, 'downloads',
                    sliced_entries, sorted_entries, gap_start)
                for i in range(gap[1] - 1, gap_start - 1, -1):
                    sorted_entries[i]['summary_views'] =\
                        sorted_entries[i + 1]['summary_views'] - sorted_entries[i + 1]['views']
                    sorted_entries[i]['summary_downloads'] =\
                        sorted_entries[i + 1]['summary_downloads'] - sorted_entries[i + 1][
                        'downloads']
            elif gap_end_views_count is None and gap_start_views_count is not None:
                for i in range(gap_start, gap[1] + 1):
                    current_views = sorted_entries[i]['views'] if sorted_entries[i]['views'] is not None else 0
                    current_downloads =\
                        sorted_entries[i]['downloads'] if sorted_entries[i]['downloads'] is not None else 0
                    sorted_entries[i]['summary_views'] =\
                        sorted_entries[i - 1]['summary_views'] + current_views
                    sorted_entries[i]['summary_downloads'] =\
                        sorted_entries[i - 1]['summary_downloads'] + current_downloads

    def compute_gap_valid_count_values(self, gap_start_count, gap_end_count,
                                       values_type, sliced_entries, sorted_entries, gap):
        count_of_entries = len(sliced_entries)
        slice_values = [0 if entry[values_type] is None else entry[values_type] for entry in sliced_entries]
        slice_values_sum = sum(slice_values)
        if slice_values_sum == 0:
            slice_profile = [1 / len(sliced_entries) for _ in range(count_of_entries)]
        else:
            slice_profile = [slice_value / slice_values_sum for slice_value in slice_values]
        slice_summary_diff = gap_end_count - gap_start_count
        if slice_summary_diff != slice_values_sum:
            result_values = self.compute_profiled_values(slice_summary_diff, slice_profile)
        else:
            result_values = slice_values
        for index, new_value in enumerate(result_values):
            sorted_entries[gap + index][values_type] = new_value

    def compute_profiled_values(self, slice_data_diff, slice_data_profile):
        profiled_result_values =\
            [Decimal(str(profile_val * slice_data_diff)).quantize(Decimal('1.'), rounding=ROUND_HALF_UP)
             for profile_val in slice_data_profile]
        profiled_sum = sum(profiled_result_values)
        profiled_diff = slice_data_diff - profiled_sum
        if profiled_diff > 0:
            profiled_result_values[-1] += profiled_diff
        elif profiled_diff < 0:
            abs_diff = abs(profiled_diff)
            new_profiled_values = []
            for profiled_val in profiled_result_values:
                lower_val = min(profiled_val, abs_diff)
                changed_profiled_val = profiled_val - lower_val
                abs_diff -= lower_val
                new_profiled_values.append(changed_profiled_val)
            profiled_result_values = new_profiled_values
        return profiled_result_values

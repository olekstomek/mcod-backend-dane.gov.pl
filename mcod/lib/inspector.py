# -*- coding: utf-8 -*-
import datetime

from goodtables.inspector import Inspector


class NonThreadedInspector(Inspector):
    def inspect(self, source, preset=None, **options):
        start = datetime.datetime.now()

        # Prepare preset
        preset = self._Inspector__get_source_preset(source, preset)
        if preset == 'nested':
            options['presets'] = self._Inspector__presets
            for s in source:
                if s.get('preset') is None:
                    s['preset'] = self._Inspector__get_source_preset(s['source'])

        # Prepare tables
        preset_func = self._Inspector__get_preset(preset)['func']
        warnings, tables = preset_func(source, **options)
        if len(tables) > self._Inspector__table_limit:
            warnings.append(
                'Dataset inspection has reached %s table(s) limit' %
                (self._Inspector__table_limit))
            tables = tables[:self._Inspector__table_limit]

        # Collect table reports
        table_reports = []
        for table in tables:
            table_warnings, table_report = self._Inspector__inspect_table(table)
            warnings.extend(table_warnings)
            table_reports.append(table_report)

        # Stop timer
        stop = datetime.datetime.now()

        # Compose report
        report = {
            'time': round((stop - start).total_seconds(), 3),
            'valid': all(item['valid'] for item in table_reports),
            'error-count': sum(len(item['errors']) for item in table_reports),
            'table-count': len(tables),
            'tables': table_reports,
            'warnings': warnings,
            'preset': preset,
        }

        return report

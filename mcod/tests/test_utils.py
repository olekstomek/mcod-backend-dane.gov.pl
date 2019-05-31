from django.conf import settings
from mcod.lib.utils import analyze_resource_file

import os

dbf_path = os.path.join(settings.DATA_DIR, 'dbf_examples')


class TestAnalyzeResourceFile:

    def test_dbf_file(self):
        test_files = ['cp1251.dbf',
                      "cp1251.dbf",
                      "dbase_03.dbf",
                      "dbase_30.dbf",
                      "dbase_31.dbf",
                      "dbase_83.dbf",
                      "dbase_83_missing_memo.dbf",
                      "dbase_8b.dbf",
                      "dbase_f5.dbf",
                      ]
        for fname in test_files:
            path = os.path.join(dbf_path, fname)
            assert analyze_resource_file(path)[0] == 'dbf'

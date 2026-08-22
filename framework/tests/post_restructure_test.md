============================= test session starts ==============================
platform linux -- Python 3.11.13, pytest-9.1.1, pluggy-1.6.0
django: version: 5.2.17, settings: betat_community.settings (from ini)
rootdir: /workspace/framework
configfile: pyproject.toml
plugins: django-4.14.0
collected 22 items

tests/test_core.py ......                                                [ 27%]
tests/test_store.py FFF....FFFF.FFFF                                     [100%]

=================================== FAILURES ===================================
_______________________ test_append_writes_valid_record ________________________

self = <django.db.backends.utils.CursorWrapper object at 0x7fa5fbdc7850>
sql = 'UPDATE "store_provenancerecord" SET "betat_version" = %s, "timestamp" = %s, "hi_tag" = %s, "provenancier" = %s, "cont...ecord_signature" = %s, "correction_of_id" = NULL, "disputes_id" = NULL WHERE "store_provenancerecord"."record_id" = %s'
params = ('0.1', '2026-06-12T14:32:00Z', True, '{"identity": "did:key:z6Mkftest", "identity_type": "cryptographic_key", "authen...me": "Example Community", "domain": "testing", "content_type": "text", "store_uri": "https://example.org/store"}', ...)
ignored_wrapper_args = (False, {'connection': <DatabaseWrapper vendor='sqlite' alias='default'>, 'cursor': <django.db.backends.utils.CursorWrapper object at 0x7fa5fbdc7850>})

    def _execute(self, sql, params, *ignored_wrapper_args):
        # Raise a warning during app initialization (stored_app_configs is only
        # ever set during testing).
        if not apps.ready and not apps.stored_app_configs:
            warnings.warn(self.APPS_NOT_READY_WARNING_MSG, category=RuntimeWarning)
        self.db.validate_no_broken_transaction()
        with self.db.wrap_database_errors:
            if params is None:
                # params default might be backend specific.
                return self.cursor.execute(sql)
            else:
>               return self.cursor.execute(sql, params)
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:105: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <django.db.backends.sqlite3.base.SQLiteCursorWrapper object at 0x7fa5fbbd2a80>
query = 'UPDATE "store_provenancerecord" SET "betat_version" = ?, "timestamp" = ?, "hi_tag" = ?, "provenancier" = ?, "content"..."record_signature" = ?, "correction_of_id" = NULL, "disputes_id" = NULL WHERE "store_provenancerecord"."record_id" = ?'
params = ('0.1', '2026-06-12T14:32:00Z', True, '{"identity": "did:key:z6Mkftest", "identity_type": "cryptographic_key", "authen...me": "Example Community", "domain": "testing", "content_type": "text", "store_uri": "https://example.org/store"}', ...)

    def execute(self, query, params=None):
        if params is None:
            return super().execute(query)
        # Extract names if params is a mapping, i.e. "pyformat" style is used.
        param_names = list(params) if isinstance(params, Mapping) else None
        query = self.convert_query(query, param_names=param_names)
>       return super().execute(query, params)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       sqlite3.OperationalError: no such table: store_provenancerecord

../.venv/lib64/python3.11/site-packages/django/db/backends/sqlite3/base.py:360: OperationalError

The above exception was the direct cause of the following exception:

    def test_append_writes_valid_record():
>       record = store.append(_valid_record_data())
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/test_store.py:53: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
betat_community/store/store.py:98: in append
    record.save()
../.venv/lib64/python3.11/site-packages/django/db/models/base.py:902: in save
    self.save_base(
../.venv/lib64/python3.11/site-packages/django/db/models/base.py:1008: in save_base
    updated = self._save_table(
../.venv/lib64/python3.11/site-packages/django/db/models/base.py:1138: in _save_table
    updated = self._do_update(
../.venv/lib64/python3.11/site-packages/django/db/models/base.py:1203: in _do_update
    return filtered._update(values) > 0
           ^^^^^^^^^^^^^^^^^^^^^^^^
../.venv/lib64/python3.11/site-packages/django/db/models/query.py:1288: in _update
    return query.get_compiler(self.db).execute_sql(ROW_COUNT)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../.venv/lib64/python3.11/site-packages/django/db/models/sql/compiler.py:2060: in execute_sql
    row_count = super().execute_sql(result_type)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../.venv/lib64/python3.11/site-packages/django/db/models/sql/compiler.py:1623: in execute_sql
    cursor.execute(sql, params)
../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:79: in execute
    return self._execute_with_wrappers(
../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:92: in _execute_with_wrappers
    return executor(sql, params, many, context)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:100: in _execute
    with self.db.wrap_database_errors:
../.venv/lib64/python3.11/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:105: in _execute
    return self.cursor.execute(sql, params)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <django.db.backends.sqlite3.base.SQLiteCursorWrapper object at 0x7fa5fbbd2a80>
query = 'UPDATE "store_provenancerecord" SET "betat_version" = ?, "timestamp" = ?, "hi_tag" = ?, "provenancier" = ?, "content"..."record_signature" = ?, "correction_of_id" = NULL, "disputes_id" = NULL WHERE "store_provenancerecord"."record_id" = ?'
params = ('0.1', '2026-06-12T14:32:00Z', True, '{"identity": "did:key:z6Mkftest", "identity_type": "cryptographic_key", "authen...me": "Example Community", "domain": "testing", "content_type": "text", "store_uri": "https://example.org/store"}', ...)

    def execute(self, query, params=None):
        if params is None:
            return super().execute(query)
        # Extract names if params is a mapping, i.e. "pyformat" style is used.
        param_names = list(params) if isinstance(params, Mapping) else None
        query = self.convert_query(query, param_names=param_names)
>       return super().execute(query, params)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       django.db.utils.OperationalError: no such table: store_provenancerecord

../.venv/lib64/python3.11/site-packages/django/db/backends/sqlite3/base.py:360: OperationalError
___________ test_record_id_computed_server_side_ignores_caller_value ___________

self = <django.db.backends.utils.CursorWrapper object at 0x7fa5faf6e450>
sql = 'UPDATE "store_provenancerecord" SET "betat_version" = %s, "timestamp" = %s, "hi_tag" = %s, "provenancier" = %s, "cont...ecord_signature" = %s, "correction_of_id" = NULL, "disputes_id" = NULL WHERE "store_provenancerecord"."record_id" = %s'
params = ('0.1', '2026-06-12T14:32:00Z', True, '{"identity": "did:key:z6Mkftest", "identity_type": "cryptographic_key", "authen...me": "Example Community", "domain": "testing", "content_type": "text", "store_uri": "https://example.org/store"}', ...)
ignored_wrapper_args = (False, {'connection': <DatabaseWrapper vendor='sqlite' alias='default'>, 'cursor': <django.db.backends.utils.CursorWrapper object at 0x7fa5faf6e450>})

    def _execute(self, sql, params, *ignored_wrapper_args):
        # Raise a warning during app initialization (stored_app_configs is only
        # ever set during testing).
        if not apps.ready and not apps.stored_app_configs:
            warnings.warn(self.APPS_NOT_READY_WARNING_MSG, category=RuntimeWarning)
        self.db.validate_no_broken_transaction()
        with self.db.wrap_database_errors:
            if params is None:
                # params default might be backend specific.
                return self.cursor.execute(sql)
            else:
>               return self.cursor.execute(sql, params)
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:105: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <django.db.backends.sqlite3.base.SQLiteCursorWrapper object at 0x7fa5fb9ec4d0>
query = 'UPDATE "store_provenancerecord" SET "betat_version" = ?, "timestamp" = ?, "hi_tag" = ?, "provenancier" = ?, "content"..."record_signature" = ?, "correction_of_id" = NULL, "disputes_id" = NULL WHERE "store_provenancerecord"."record_id" = ?'
params = ('0.1', '2026-06-12T14:32:00Z', True, '{"identity": "did:key:z6Mkftest", "identity_type": "cryptographic_key", "authen...me": "Example Community", "domain": "testing", "content_type": "text", "store_uri": "https://example.org/store"}', ...)

    def execute(self, query, params=None):
        if params is None:
            return super().execute(query)
        # Extract names if params is a mapping, i.e. "pyformat" style is used.
        param_names = list(params) if isinstance(params, Mapping) else None
        query = self.convert_query(query, param_names=param_names)
>       return super().execute(query, params)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       sqlite3.OperationalError: no such table: store_provenancerecord

../.venv/lib64/python3.11/site-packages/django/db/backends/sqlite3/base.py:360: OperationalError

The above exception was the direct cause of the following exception:

    def test_record_id_computed_server_side_ignores_caller_value():
        data = _valid_record_data()
        data['record_id'] = 'attacker-supplied-value'
>       record = store.append(data)
                 ^^^^^^^^^^^^^^^^^^

tests/test_store.py:61: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
betat_community/store/store.py:98: in append
    record.save()
../.venv/lib64/python3.11/site-packages/django/db/models/base.py:902: in save
    self.save_base(
../.venv/lib64/python3.11/site-packages/django/db/models/base.py:1008: in save_base
    updated = self._save_table(
../.venv/lib64/python3.11/site-packages/django/db/models/base.py:1138: in _save_table
    updated = self._do_update(
../.venv/lib64/python3.11/site-packages/django/db/models/base.py:1203: in _do_update
    return filtered._update(values) > 0
           ^^^^^^^^^^^^^^^^^^^^^^^^
../.venv/lib64/python3.11/site-packages/django/db/models/query.py:1288: in _update
    return query.get_compiler(self.db).execute_sql(ROW_COUNT)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../.venv/lib64/python3.11/site-packages/django/db/models/sql/compiler.py:2060: in execute_sql
    row_count = super().execute_sql(result_type)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../.venv/lib64/python3.11/site-packages/django/db/models/sql/compiler.py:1623: in execute_sql
    cursor.execute(sql, params)
../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:79: in execute
    return self._execute_with_wrappers(
../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:92: in _execute_with_wrappers
    return executor(sql, params, many, context)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:100: in _execute
    with self.db.wrap_database_errors:
../.venv/lib64/python3.11/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:105: in _execute
    return self.cursor.execute(sql, params)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <django.db.backends.sqlite3.base.SQLiteCursorWrapper object at 0x7fa5fb9ec4d0>
query = 'UPDATE "store_provenancerecord" SET "betat_version" = ?, "timestamp" = ?, "hi_tag" = ?, "provenancier" = ?, "content"..."record_signature" = ?, "correction_of_id" = NULL, "disputes_id" = NULL WHERE "store_provenancerecord"."record_id" = ?'
params = ('0.1', '2026-06-12T14:32:00Z', True, '{"identity": "did:key:z6Mkftest", "identity_type": "cryptographic_key", "authen...me": "Example Community", "domain": "testing", "content_type": "text", "store_uri": "https://example.org/store"}', ...)

    def execute(self, query, params=None):
        if params is None:
            return super().execute(query)
        # Extract names if params is a mapping, i.e. "pyformat" style is used.
        param_names = list(params) if isinstance(params, Mapping) else None
        query = self.convert_query(query, param_names=param_names)
>       return super().execute(query, params)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       django.db.utils.OperationalError: no such table: store_provenancerecord

../.venv/lib64/python3.11/site-packages/django/db/backends/sqlite3/base.py:360: OperationalError
________________________ test_round_trip_byte_identical ________________________

self = <django.db.backends.utils.CursorWrapper object at 0x7fa5fb284e50>
sql = 'UPDATE "store_provenancerecord" SET "betat_version" = %s, "timestamp" = %s, "hi_tag" = %s, "provenancier" = %s, "cont...ecord_signature" = %s, "correction_of_id" = NULL, "disputes_id" = NULL WHERE "store_provenancerecord"."record_id" = %s'
params = ('0.1', '2026-06-12T14:32:00Z', True, '{"identity": "did:key:z6Mkftest", "identity_type": "cryptographic_key", "authen...me": "Example Community", "domain": "testing", "content_type": "text", "store_uri": "https://example.org/store"}', ...)
ignored_wrapper_args = (False, {'connection': <DatabaseWrapper vendor='sqlite' alias='default'>, 'cursor': <django.db.backends.utils.CursorWrapper object at 0x7fa5fb284e50>})

    def _execute(self, sql, params, *ignored_wrapper_args):
        # Raise a warning during app initialization (stored_app_configs is only
        # ever set during testing).
        if not apps.ready and not apps.stored_app_configs:
            warnings.warn(self.APPS_NOT_READY_WARNING_MSG, category=RuntimeWarning)
        self.db.validate_no_broken_transaction()
        with self.db.wrap_database_errors:
            if params is None:
                # params default might be backend specific.
                return self.cursor.execute(sql)
            else:
>               return self.cursor.execute(sql, params)
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:105: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <django.db.backends.sqlite3.base.SQLiteCursorWrapper object at 0x7fa5fb9cbda0>
query = 'UPDATE "store_provenancerecord" SET "betat_version" = ?, "timestamp" = ?, "hi_tag" = ?, "provenancier" = ?, "content"..."record_signature" = ?, "correction_of_id" = NULL, "disputes_id" = NULL WHERE "store_provenancerecord"."record_id" = ?'
params = ('0.1', '2026-06-12T14:32:00Z', True, '{"identity": "did:key:z6Mkftest", "identity_type": "cryptographic_key", "authen...me": "Example Community", "domain": "testing", "content_type": "text", "store_uri": "https://example.org/store"}', ...)

    def execute(self, query, params=None):
        if params is None:
            return super().execute(query)
        # Extract names if params is a mapping, i.e. "pyformat" style is used.
        param_names = list(params) if isinstance(params, Mapping) else None
        query = self.convert_query(query, param_names=param_names)
>       return super().execute(query, params)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       sqlite3.OperationalError: no such table: store_provenancerecord

../.venv/lib64/python3.11/site-packages/django/db/backends/sqlite3/base.py:360: OperationalError

The above exception was the direct cause of the following exception:

    def test_round_trip_byte_identical():
        data = _valid_record_data()
>       record = store.append(data)
                 ^^^^^^^^^^^^^^^^^^

tests/test_store.py:69: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
betat_community/store/store.py:98: in append
    record.save()
../.venv/lib64/python3.11/site-packages/django/db/models/base.py:902: in save
    self.save_base(
../.venv/lib64/python3.11/site-packages/django/db/models/base.py:1008: in save_base
    updated = self._save_table(
../.venv/lib64/python3.11/site-packages/django/db/models/base.py:1138: in _save_table
    updated = self._do_update(
../.venv/lib64/python3.11/site-packages/django/db/models/base.py:1203: in _do_update
    return filtered._update(values) > 0
           ^^^^^^^^^^^^^^^^^^^^^^^^
../.venv/lib64/python3.11/site-packages/django/db/models/query.py:1288: in _update
    return query.get_compiler(self.db).execute_sql(ROW_COUNT)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../.venv/lib64/python3.11/site-packages/django/db/models/sql/compiler.py:2060: in execute_sql
    row_count = super().execute_sql(result_type)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../.venv/lib64/python3.11/site-packages/django/db/models/sql/compiler.py:1623: in execute_sql
    cursor.execute(sql, params)
../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:79: in execute
    return self._execute_with_wrappers(
../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:92: in _execute_with_wrappers
    return executor(sql, params, many, context)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:100: in _execute
    with self.db.wrap_database_errors:
../.venv/lib64/python3.11/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:105: in _execute
    return self.cursor.execute(sql, params)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <django.db.backends.sqlite3.base.SQLiteCursorWrapper object at 0x7fa5fb9cbda0>
query = 'UPDATE "store_provenancerecord" SET "betat_version" = ?, "timestamp" = ?, "hi_tag" = ?, "provenancier" = ?, "content"..."record_signature" = ?, "correction_of_id" = NULL, "disputes_id" = NULL WHERE "store_provenancerecord"."record_id" = ?'
params = ('0.1', '2026-06-12T14:32:00Z', True, '{"identity": "did:key:z6Mkftest", "identity_type": "cryptographic_key", "authen...me": "Example Community", "domain": "testing", "content_type": "text", "store_uri": "https://example.org/store"}', ...)

    def execute(self, query, params=None):
        if params is None:
            return super().execute(query)
        # Extract names if params is a mapping, i.e. "pyformat" style is used.
        param_names = list(params) if isinstance(params, Mapping) else None
        query = self.convert_query(query, param_names=param_names)
>       return super().execute(query, params)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       django.db.utils.OperationalError: no such table: store_provenancerecord

../.venv/lib64/python3.11/site-packages/django/db/backends/sqlite3/base.py:360: OperationalError
_____________________ test_correction_references_original ______________________

self = <django.db.backends.utils.CursorWrapper object at 0x7fa5fb250290>
sql = 'UPDATE "store_provenancerecord" SET "betat_version" = %s, "timestamp" = %s, "hi_tag" = %s, "provenancier" = %s, "cont...ecord_signature" = %s, "correction_of_id" = NULL, "disputes_id" = NULL WHERE "store_provenancerecord"."record_id" = %s'
params = ('0.1', '2026-06-12T14:32:00Z', True, '{"identity": "did:key:z6Mkftest", "identity_type": "cryptographic_key", "authen...me": "Example Community", "domain": "testing", "content_type": "text", "store_uri": "https://example.org/store"}', ...)
ignored_wrapper_args = (False, {'connection': <DatabaseWrapper vendor='sqlite' alias='default'>, 'cursor': <django.db.backends.utils.CursorWrapper object at 0x7fa5fb250290>})

    def _execute(self, sql, params, *ignored_wrapper_args):
        # Raise a warning during app initialization (stored_app_configs is only
        # ever set during testing).
        if not apps.ready and not apps.stored_app_configs:
            warnings.warn(self.APPS_NOT_READY_WARNING_MSG, category=RuntimeWarning)
        self.db.validate_no_broken_transaction()
        with self.db.wrap_database_errors:
            if params is None:
                # params default might be backend specific.
                return self.cursor.execute(sql)
            else:
>               return self.cursor.execute(sql, params)
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:105: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <django.db.backends.sqlite3.base.SQLiteCursorWrapper object at 0x7fa5fb9c8e60>
query = 'UPDATE "store_provenancerecord" SET "betat_version" = ?, "timestamp" = ?, "hi_tag" = ?, "provenancier" = ?, "content"..."record_signature" = ?, "correction_of_id" = NULL, "disputes_id" = NULL WHERE "store_provenancerecord"."record_id" = ?'
params = ('0.1', '2026-06-12T14:32:00Z', True, '{"identity": "did:key:z6Mkftest", "identity_type": "cryptographic_key", "authen...me": "Example Community", "domain": "testing", "content_type": "text", "store_uri": "https://example.org/store"}', ...)

    def execute(self, query, params=None):
        if params is None:
            return super().execute(query)
        # Extract names if params is a mapping, i.e. "pyformat" style is used.
        param_names = list(params) if isinstance(params, Mapping) else None
        query = self.convert_query(query, param_names=param_names)
>       return super().execute(query, params)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       sqlite3.OperationalError: no such table: store_provenancerecord

../.venv/lib64/python3.11/site-packages/django/db/backends/sqlite3/base.py:360: OperationalError

The above exception was the direct cause of the following exception:

    def test_correction_references_original():
>       original = store.append(_valid_record_data())
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/test_store.py:103: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
betat_community/store/store.py:98: in append
    record.save()
../.venv/lib64/python3.11/site-packages/django/db/models/base.py:902: in save
    self.save_base(
../.venv/lib64/python3.11/site-packages/django/db/models/base.py:1008: in save_base
    updated = self._save_table(
../.venv/lib64/python3.11/site-packages/django/db/models/base.py:1138: in _save_table
    updated = self._do_update(
../.venv/lib64/python3.11/site-packages/django/db/models/base.py:1203: in _do_update
    return filtered._update(values) > 0
           ^^^^^^^^^^^^^^^^^^^^^^^^
../.venv/lib64/python3.11/site-packages/django/db/models/query.py:1288: in _update
    return query.get_compiler(self.db).execute_sql(ROW_COUNT)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../.venv/lib64/python3.11/site-packages/django/db/models/sql/compiler.py:2060: in execute_sql
    row_count = super().execute_sql(result_type)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../.venv/lib64/python3.11/site-packages/django/db/models/sql/compiler.py:1623: in execute_sql
    cursor.execute(sql, params)
../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:79: in execute
    return self._execute_with_wrappers(
../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:92: in _execute_with_wrappers
    return executor(sql, params, many, context)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:100: in _execute
    with self.db.wrap_database_errors:
../.venv/lib64/python3.11/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:105: in _execute
    return self.cursor.execute(sql, params)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <django.db.backends.sqlite3.base.SQLiteCursorWrapper object at 0x7fa5fb9c8e60>
query = 'UPDATE "store_provenancerecord" SET "betat_version" = ?, "timestamp" = ?, "hi_tag" = ?, "provenancier" = ?, "content"..."record_signature" = ?, "correction_of_id" = NULL, "disputes_id" = NULL WHERE "store_provenancerecord"."record_id" = ?'
params = ('0.1', '2026-06-12T14:32:00Z', True, '{"identity": "did:key:z6Mkftest", "identity_type": "cryptographic_key", "authen...me": "Example Community", "domain": "testing", "content_type": "text", "store_uri": "https://example.org/store"}', ...)

    def execute(self, query, params=None):
        if params is None:
            return super().execute(query)
        # Extract names if params is a mapping, i.e. "pyformat" style is used.
        param_names = list(params) if isinstance(params, Mapping) else None
        query = self.convert_query(query, param_names=param_names)
>       return super().execute(query, params)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       django.db.utils.OperationalError: no such table: store_provenancerecord

../.venv/lib64/python3.11/site-packages/django/db/backends/sqlite3/base.py:360: OperationalError
_______________ test_list_records_newest_first_and_since_filter ________________

self = <django.db.backends.utils.CursorWrapper object at 0x7fa5fb914e50>
sql = 'UPDATE "store_provenancerecord" SET "betat_version" = %s, "timestamp" = %s, "hi_tag" = %s, "provenancier" = %s, "cont...ecord_signature" = %s, "correction_of_id" = NULL, "disputes_id" = NULL WHERE "store_provenancerecord"."record_id" = %s'
params = ('0.1', '2026-01-01T00:00:00Z', True, '{"identity": "did:key:z6Mkftest", "identity_type": "cryptographic_key", "authen...me": "Example Community", "domain": "testing", "content_type": "text", "store_uri": "https://example.org/store"}', ...)
ignored_wrapper_args = (False, {'connection': <DatabaseWrapper vendor='sqlite' alias='default'>, 'cursor': <django.db.backends.utils.CursorWrapper object at 0x7fa5fb914e50>})

    def _execute(self, sql, params, *ignored_wrapper_args):
        # Raise a warning during app initialization (stored_app_configs is only
        # ever set during testing).
        if not apps.ready and not apps.stored_app_configs:
            warnings.warn(self.APPS_NOT_READY_WARNING_MSG, category=RuntimeWarning)
        self.db.validate_no_broken_transaction()
        with self.db.wrap_database_errors:
            if params is None:
                # params default might be backend specific.
                return self.cursor.execute(sql)
            else:
>               return self.cursor.execute(sql, params)
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:105: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <django.db.backends.sqlite3.base.SQLiteCursorWrapper object at 0x7fa5fb9cbe30>
query = 'UPDATE "store_provenancerecord" SET "betat_version" = ?, "timestamp" = ?, "hi_tag" = ?, "provenancier" = ?, "content"..."record_signature" = ?, "correction_of_id" = NULL, "disputes_id" = NULL WHERE "store_provenancerecord"."record_id" = ?'
params = ('0.1', '2026-01-01T00:00:00Z', True, '{"identity": "did:key:z6Mkftest", "identity_type": "cryptographic_key", "authen...me": "Example Community", "domain": "testing", "content_type": "text", "store_uri": "https://example.org/store"}', ...)

    def execute(self, query, params=None):
        if params is None:
            return super().execute(query)
        # Extract names if params is a mapping, i.e. "pyformat" style is used.
        param_names = list(params) if isinstance(params, Mapping) else None
        query = self.convert_query(query, param_names=param_names)
>       return super().execute(query, params)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       sqlite3.OperationalError: no such table: store_provenancerecord

../.venv/lib64/python3.11/site-packages/django/db/backends/sqlite3/base.py:360: OperationalError

The above exception was the direct cause of the following exception:

    def test_list_records_newest_first_and_since_filter():
>       r1 = store.append(_valid_record_data(timestamp='2026-01-01T00:00:00Z'))
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/test_store.py:114: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
betat_community/store/store.py:98: in append
    record.save()
../.venv/lib64/python3.11/site-packages/django/db/models/base.py:902: in save
    self.save_base(
../.venv/lib64/python3.11/site-packages/django/db/models/base.py:1008: in save_base
    updated = self._save_table(
../.venv/lib64/python3.11/site-packages/django/db/models/base.py:1138: in _save_table
    updated = self._do_update(
../.venv/lib64/python3.11/site-packages/django/db/models/base.py:1203: in _do_update
    return filtered._update(values) > 0
           ^^^^^^^^^^^^^^^^^^^^^^^^
../.venv/lib64/python3.11/site-packages/django/db/models/query.py:1288: in _update
    return query.get_compiler(self.db).execute_sql(ROW_COUNT)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../.venv/lib64/python3.11/site-packages/django/db/models/sql/compiler.py:2060: in execute_sql
    row_count = super().execute_sql(result_type)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../.venv/lib64/python3.11/site-packages/django/db/models/sql/compiler.py:1623: in execute_sql
    cursor.execute(sql, params)
../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:79: in execute
    return self._execute_with_wrappers(
../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:92: in _execute_with_wrappers
    return executor(sql, params, many, context)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:100: in _execute
    with self.db.wrap_database_errors:
../.venv/lib64/python3.11/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:105: in _execute
    return self.cursor.execute(sql, params)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <django.db.backends.sqlite3.base.SQLiteCursorWrapper object at 0x7fa5fb9cbe30>
query = 'UPDATE "store_provenancerecord" SET "betat_version" = ?, "timestamp" = ?, "hi_tag" = ?, "provenancier" = ?, "content"..."record_signature" = ?, "correction_of_id" = NULL, "disputes_id" = NULL WHERE "store_provenancerecord"."record_id" = ?'
params = ('0.1', '2026-01-01T00:00:00Z', True, '{"identity": "did:key:z6Mkftest", "identity_type": "cryptographic_key", "authen...me": "Example Community", "domain": "testing", "content_type": "text", "store_uri": "https://example.org/store"}', ...)

    def execute(self, query, params=None):
        if params is None:
            return super().execute(query)
        # Extract names if params is a mapping, i.e. "pyformat" style is used.
        param_names = list(params) if isinstance(params, Mapping) else None
        query = self.convert_query(query, param_names=param_names)
>       return super().execute(query, params)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       django.db.utils.OperationalError: no such table: store_provenancerecord

../.venv/lib64/python3.11/site-packages/django/db/backends/sqlite3/base.py:360: OperationalError
_________________ test_verify_integrity_passes_on_clean_record _________________

self = <django.db.backends.utils.CursorWrapper object at 0x7fa5fb239450>
sql = 'UPDATE "store_provenancerecord" SET "betat_version" = %s, "timestamp" = %s, "hi_tag" = %s, "provenancier" = %s, "cont...ecord_signature" = %s, "correction_of_id" = NULL, "disputes_id" = NULL WHERE "store_provenancerecord"."record_id" = %s'
params = ('0.1', '2026-06-12T14:32:00Z', True, '{"identity": "did:key:z6Mkftest", "identity_type": "cryptographic_key", "authen...me": "Example Community", "domain": "testing", "content_type": "text", "store_uri": "https://example.org/store"}', ...)
ignored_wrapper_args = (False, {'connection': <DatabaseWrapper vendor='sqlite' alias='default'>, 'cursor': <django.db.backends.utils.CursorWrapper object at 0x7fa5fb239450>})

    def _execute(self, sql, params, *ignored_wrapper_args):
        # Raise a warning during app initialization (stored_app_configs is only
        # ever set during testing).
        if not apps.ready and not apps.stored_app_configs:
            warnings.warn(self.APPS_NOT_READY_WARNING_MSG, category=RuntimeWarning)
        self.db.validate_no_broken_transaction()
        with self.db.wrap_database_errors:
            if params is None:
                # params default might be backend specific.
                return self.cursor.execute(sql)
            else:
>               return self.cursor.execute(sql, params)
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:105: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <django.db.backends.sqlite3.base.SQLiteCursorWrapper object at 0x7fa5fb9ec5f0>
query = 'UPDATE "store_provenancerecord" SET "betat_version" = ?, "timestamp" = ?, "hi_tag" = ?, "provenancier" = ?, "content"..."record_signature" = ?, "correction_of_id" = NULL, "disputes_id" = NULL WHERE "store_provenancerecord"."record_id" = ?'
params = ('0.1', '2026-06-12T14:32:00Z', True, '{"identity": "did:key:z6Mkftest", "identity_type": "cryptographic_key", "authen...me": "Example Community", "domain": "testing", "content_type": "text", "store_uri": "https://example.org/store"}', ...)

    def execute(self, query, params=None):
        if params is None:
            return super().execute(query)
        # Extract names if params is a mapping, i.e. "pyformat" style is used.
        param_names = list(params) if isinstance(params, Mapping) else None
        query = self.convert_query(query, param_names=param_names)
>       return super().execute(query, params)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       sqlite3.OperationalError: no such table: store_provenancerecord

../.venv/lib64/python3.11/site-packages/django/db/backends/sqlite3/base.py:360: OperationalError

The above exception was the direct cause of the following exception:

    def test_verify_integrity_passes_on_clean_record():
>       record = store.append(_valid_record_data())
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/test_store.py:127: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
betat_community/store/store.py:98: in append
    record.save()
../.venv/lib64/python3.11/site-packages/django/db/models/base.py:902: in save
    self.save_base(
../.venv/lib64/python3.11/site-packages/django/db/models/base.py:1008: in save_base
    updated = self._save_table(
../.venv/lib64/python3.11/site-packages/django/db/models/base.py:1138: in _save_table
    updated = self._do_update(
../.venv/lib64/python3.11/site-packages/django/db/models/base.py:1203: in _do_update
    return filtered._update(values) > 0
           ^^^^^^^^^^^^^^^^^^^^^^^^
../.venv/lib64/python3.11/site-packages/django/db/models/query.py:1288: in _update
    return query.get_compiler(self.db).execute_sql(ROW_COUNT)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../.venv/lib64/python3.11/site-packages/django/db/models/sql/compiler.py:2060: in execute_sql
    row_count = super().execute_sql(result_type)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../.venv/lib64/python3.11/site-packages/django/db/models/sql/compiler.py:1623: in execute_sql
    cursor.execute(sql, params)
../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:79: in execute
    return self._execute_with_wrappers(
../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:92: in _execute_with_wrappers
    return executor(sql, params, many, context)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:100: in _execute
    with self.db.wrap_database_errors:
../.venv/lib64/python3.11/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:105: in _execute
    return self.cursor.execute(sql, params)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <django.db.backends.sqlite3.base.SQLiteCursorWrapper object at 0x7fa5fb9ec5f0>
query = 'UPDATE "store_provenancerecord" SET "betat_version" = ?, "timestamp" = ?, "hi_tag" = ?, "provenancier" = ?, "content"..."record_signature" = ?, "correction_of_id" = NULL, "disputes_id" = NULL WHERE "store_provenancerecord"."record_id" = ?'
params = ('0.1', '2026-06-12T14:32:00Z', True, '{"identity": "did:key:z6Mkftest", "identity_type": "cryptographic_key", "authen...me": "Example Community", "domain": "testing", "content_type": "text", "store_uri": "https://example.org/store"}', ...)

    def execute(self, query, params=None):
        if params is None:
            return super().execute(query)
        # Extract names if params is a mapping, i.e. "pyformat" style is used.
        param_names = list(params) if isinstance(params, Mapping) else None
        query = self.convert_query(query, param_names=param_names)
>       return super().execute(query, params)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       django.db.utils.OperationalError: no such table: store_provenancerecord

../.venv/lib64/python3.11/site-packages/django/db/backends/sqlite3/base.py:360: OperationalError
________________ test_verify_integrity_fails_on_tampered_record ________________

self = <django.db.backends.utils.CursorWrapper object at 0x7fa5fb784b50>
sql = 'INSERT INTO "store_provenancerecord" ("record_id", "betat_version", "timestamp", "hi_tag", "provenancier", "content",...ation", "record_signature", "correction_of_id", "disputes_id") VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
params = ('0000000000000000000000000000000000000000000000000000000000000000', '0.1', '2026-06-12T14:32:00Z', True, '{"identity"...", "title": "A test record", "location": "ipfs://bafytest", "content_hash": "sha256:testhash", "language": "en"}', ...)
ignored_wrapper_args = (False, {'connection': <DatabaseWrapper vendor='sqlite' alias='default'>, 'cursor': <django.db.backends.utils.CursorWrapper object at 0x7fa5fb784b50>})

    def _execute(self, sql, params, *ignored_wrapper_args):
        # Raise a warning during app initialization (stored_app_configs is only
        # ever set during testing).
        if not apps.ready and not apps.stored_app_configs:
            warnings.warn(self.APPS_NOT_READY_WARNING_MSG, category=RuntimeWarning)
        self.db.validate_no_broken_transaction()
        with self.db.wrap_database_errors:
            if params is None:
                # params default might be backend specific.
                return self.cursor.execute(sql)
            else:
>               return self.cursor.execute(sql, params)
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:105: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <django.db.backends.sqlite3.base.SQLiteCursorWrapper object at 0x7fa5fb9ec320>
query = 'INSERT INTO "store_provenancerecord" ("record_id", "betat_version", "timestamp", "hi_tag", "provenancier", "content",...on", "declaration", "record_signature", "correction_of_id", "disputes_id") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
params = ('0000000000000000000000000000000000000000000000000000000000000000', '0.1', '2026-06-12T14:32:00Z', True, '{"identity"...", "title": "A test record", "location": "ipfs://bafytest", "content_hash": "sha256:testhash", "language": "en"}', ...)

    def execute(self, query, params=None):
        if params is None:
            return super().execute(query)
        # Extract names if params is a mapping, i.e. "pyformat" style is used.
        param_names = list(params) if isinstance(params, Mapping) else None
        query = self.convert_query(query, param_names=param_names)
>       return super().execute(query, params)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       sqlite3.OperationalError: no such table: store_provenancerecord

../.venv/lib64/python3.11/site-packages/django/db/backends/sqlite3/base.py:360: OperationalError

The above exception was the direct cause of the following exception:

    def test_verify_integrity_fails_on_tampered_record():
        # bulk_create bypasses the append-only guard (it's an insert, not an
        # update/delete) — used here to simulate a corrupted row without
        # fighting the guards this module deliberately makes hard to bypass.
        tampered = ProvenanceRecord(
            record_id='0' * 64,
            betat_version='0.1',
            timestamp='2026-06-12T14:32:00Z',
            hi_tag=True,
            provenancier=_valid_record_data()['provenancier'],
            content=_valid_record_data()['content'],
            community=_valid_record_data()['community'],
            verification=_valid_record_data()['verification'],
            declaration=_valid_record_data()['declaration'],
        )
>       ProvenanceRecord.objects.bulk_create([tampered])

tests/test_store.py:146: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../.venv/lib64/python3.11/site-packages/django/db/models/manager.py:87: in manager_method
    return getattr(self.get_queryset(), name)(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../.venv/lib64/python3.11/site-packages/django/db/models/query.py:808: in bulk_create
    returned_columns = self._batched_insert(
../.venv/lib64/python3.11/site-packages/django/db/models/query.py:1912: in _batched_insert
    self._insert(
../.venv/lib64/python3.11/site-packages/django/db/models/query.py:1873: in _insert
    return query.get_compiler(using=using).execute_sql(returning_fields)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../.venv/lib64/python3.11/site-packages/django/db/models/sql/compiler.py:1882: in execute_sql
    cursor.execute(sql, params)
../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:79: in execute
    return self._execute_with_wrappers(
../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:92: in _execute_with_wrappers
    return executor(sql, params, many, context)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:100: in _execute
    with self.db.wrap_database_errors:
../.venv/lib64/python3.11/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:105: in _execute
    return self.cursor.execute(sql, params)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <django.db.backends.sqlite3.base.SQLiteCursorWrapper object at 0x7fa5fb9ec320>
query = 'INSERT INTO "store_provenancerecord" ("record_id", "betat_version", "timestamp", "hi_tag", "provenancier", "content",...on", "declaration", "record_signature", "correction_of_id", "disputes_id") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
params = ('0000000000000000000000000000000000000000000000000000000000000000', '0.1', '2026-06-12T14:32:00Z', True, '{"identity"...", "title": "A test record", "location": "ipfs://bafytest", "content_hash": "sha256:testhash", "language": "en"}', ...)

    def execute(self, query, params=None):
        if params is None:
            return super().execute(query)
        # Extract names if params is a mapping, i.e. "pyformat" style is used.
        param_names = list(params) if isinstance(params, Mapping) else None
        query = self.convert_query(query, param_names=param_names)
>       return super().execute(query, params)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       django.db.utils.OperationalError: no such table: store_provenancerecord

../.venv/lib64/python3.11/site-packages/django/db/backends/sqlite3/base.py:360: OperationalError
_________________________ test_queryset_update_blocked _________________________

self = <django.db.backends.utils.CursorWrapper object at 0x7fa5fb3497d0>
sql = 'UPDATE "store_provenancerecord" SET "betat_version" = %s, "timestamp" = %s, "hi_tag" = %s, "provenancier" = %s, "cont...ecord_signature" = %s, "correction_of_id" = NULL, "disputes_id" = NULL WHERE "store_provenancerecord"."record_id" = %s'
params = ('0.1', '2026-06-12T14:32:00Z', True, '{"identity": "did:key:z6Mkftest", "identity_type": "cryptographic_key", "authen...me": "Example Community", "domain": "testing", "content_type": "text", "store_uri": "https://example.org/store"}', ...)
ignored_wrapper_args = (False, {'connection': <DatabaseWrapper vendor='sqlite' alias='default'>, 'cursor': <django.db.backends.utils.CursorWrapper object at 0x7fa5fb3497d0>})

    def _execute(self, sql, params, *ignored_wrapper_args):
        # Raise a warning during app initialization (stored_app_configs is only
        # ever set during testing).
        if not apps.ready and not apps.stored_app_configs:
            warnings.warn(self.APPS_NOT_READY_WARNING_MSG, category=RuntimeWarning)
        self.db.validate_no_broken_transaction()
        with self.db.wrap_database_errors:
            if params is None:
                # params default might be backend specific.
                return self.cursor.execute(sql)
            else:
>               return self.cursor.execute(sql, params)
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:105: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <django.db.backends.sqlite3.base.SQLiteCursorWrapper object at 0x7fa5fbbd2c30>
query = 'UPDATE "store_provenancerecord" SET "betat_version" = ?, "timestamp" = ?, "hi_tag" = ?, "provenancier" = ?, "content"..."record_signature" = ?, "correction_of_id" = NULL, "disputes_id" = NULL WHERE "store_provenancerecord"."record_id" = ?'
params = ('0.1', '2026-06-12T14:32:00Z', True, '{"identity": "did:key:z6Mkftest", "identity_type": "cryptographic_key", "authen...me": "Example Community", "domain": "testing", "content_type": "text", "store_uri": "https://example.org/store"}', ...)

    def execute(self, query, params=None):
        if params is None:
            return super().execute(query)
        # Extract names if params is a mapping, i.e. "pyformat" style is used.
        param_names = list(params) if isinstance(params, Mapping) else None
        query = self.convert_query(query, param_names=param_names)
>       return super().execute(query, params)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       sqlite3.OperationalError: no such table: store_provenancerecord

../.venv/lib64/python3.11/site-packages/django/db/backends/sqlite3/base.py:360: OperationalError

The above exception was the direct cause of the following exception:

    def test_queryset_update_blocked():
>       store.append(_valid_record_data())

tests/test_store.py:156: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
betat_community/store/store.py:98: in append
    record.save()
../.venv/lib64/python3.11/site-packages/django/db/models/base.py:902: in save
    self.save_base(
../.venv/lib64/python3.11/site-packages/django/db/models/base.py:1008: in save_base
    updated = self._save_table(
../.venv/lib64/python3.11/site-packages/django/db/models/base.py:1138: in _save_table
    updated = self._do_update(
../.venv/lib64/python3.11/site-packages/django/db/models/base.py:1203: in _do_update
    return filtered._update(values) > 0
           ^^^^^^^^^^^^^^^^^^^^^^^^
../.venv/lib64/python3.11/site-packages/django/db/models/query.py:1288: in _update
    return query.get_compiler(self.db).execute_sql(ROW_COUNT)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../.venv/lib64/python3.11/site-packages/django/db/models/sql/compiler.py:2060: in execute_sql
    row_count = super().execute_sql(result_type)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../.venv/lib64/python3.11/site-packages/django/db/models/sql/compiler.py:1623: in execute_sql
    cursor.execute(sql, params)
../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:79: in execute
    return self._execute_with_wrappers(
../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:92: in _execute_with_wrappers
    return executor(sql, params, many, context)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:100: in _execute
    with self.db.wrap_database_errors:
../.venv/lib64/python3.11/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:105: in _execute
    return self.cursor.execute(sql, params)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <django.db.backends.sqlite3.base.SQLiteCursorWrapper object at 0x7fa5fbbd2c30>
query = 'UPDATE "store_provenancerecord" SET "betat_version" = ?, "timestamp" = ?, "hi_tag" = ?, "provenancier" = ?, "content"..."record_signature" = ?, "correction_of_id" = NULL, "disputes_id" = NULL WHERE "store_provenancerecord"."record_id" = ?'
params = ('0.1', '2026-06-12T14:32:00Z', True, '{"identity": "did:key:z6Mkftest", "identity_type": "cryptographic_key", "authen...me": "Example Community", "domain": "testing", "content_type": "text", "store_uri": "https://example.org/store"}', ...)

    def execute(self, query, params=None):
        if params is None:
            return super().execute(query)
        # Extract names if params is a mapping, i.e. "pyformat" style is used.
        param_names = list(params) if isinstance(params, Mapping) else None
        query = self.convert_query(query, param_names=param_names)
>       return super().execute(query, params)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       django.db.utils.OperationalError: no such table: store_provenancerecord

../.venv/lib64/python3.11/site-packages/django/db/backends/sqlite3/base.py:360: OperationalError
_________________________ test_instance_delete_blocked _________________________

self = <django.db.backends.utils.CursorWrapper object at 0x7fa5fb436b50>
sql = 'UPDATE "store_provenancerecord" SET "betat_version" = %s, "timestamp" = %s, "hi_tag" = %s, "provenancier" = %s, "cont...ecord_signature" = %s, "correction_of_id" = NULL, "disputes_id" = NULL WHERE "store_provenancerecord"."record_id" = %s'
params = ('0.1', '2026-06-12T14:32:00Z', True, '{"identity": "did:key:z6Mkftest", "identity_type": "cryptographic_key", "authen...me": "Example Community", "domain": "testing", "content_type": "text", "store_uri": "https://example.org/store"}', ...)
ignored_wrapper_args = (False, {'connection': <DatabaseWrapper vendor='sqlite' alias='default'>, 'cursor': <django.db.backends.utils.CursorWrapper object at 0x7fa5fb436b50>})

    def _execute(self, sql, params, *ignored_wrapper_args):
        # Raise a warning during app initialization (stored_app_configs is only
        # ever set during testing).
        if not apps.ready and not apps.stored_app_configs:
            warnings.warn(self.APPS_NOT_READY_WARNING_MSG, category=RuntimeWarning)
        self.db.validate_no_broken_transaction()
        with self.db.wrap_database_errors:
            if params is None:
                # params default might be backend specific.
                return self.cursor.execute(sql)
            else:
>               return self.cursor.execute(sql, params)
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:105: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <django.db.backends.sqlite3.base.SQLiteCursorWrapper object at 0x7fa5fb9cbb60>
query = 'UPDATE "store_provenancerecord" SET "betat_version" = ?, "timestamp" = ?, "hi_tag" = ?, "provenancier" = ?, "content"..."record_signature" = ?, "correction_of_id" = NULL, "disputes_id" = NULL WHERE "store_provenancerecord"."record_id" = ?'
params = ('0.1', '2026-06-12T14:32:00Z', True, '{"identity": "did:key:z6Mkftest", "identity_type": "cryptographic_key", "authen...me": "Example Community", "domain": "testing", "content_type": "text", "store_uri": "https://example.org/store"}', ...)

    def execute(self, query, params=None):
        if params is None:
            return super().execute(query)
        # Extract names if params is a mapping, i.e. "pyformat" style is used.
        param_names = list(params) if isinstance(params, Mapping) else None
        query = self.convert_query(query, param_names=param_names)
>       return super().execute(query, params)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       sqlite3.OperationalError: no such table: store_provenancerecord

../.venv/lib64/python3.11/site-packages/django/db/backends/sqlite3/base.py:360: OperationalError

The above exception was the direct cause of the following exception:

    def test_instance_delete_blocked():
>       record = store.append(_valid_record_data())
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/test_store.py:162: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
betat_community/store/store.py:98: in append
    record.save()
../.venv/lib64/python3.11/site-packages/django/db/models/base.py:902: in save
    self.save_base(
../.venv/lib64/python3.11/site-packages/django/db/models/base.py:1008: in save_base
    updated = self._save_table(
../.venv/lib64/python3.11/site-packages/django/db/models/base.py:1138: in _save_table
    updated = self._do_update(
../.venv/lib64/python3.11/site-packages/django/db/models/base.py:1203: in _do_update
    return filtered._update(values) > 0
           ^^^^^^^^^^^^^^^^^^^^^^^^
../.venv/lib64/python3.11/site-packages/django/db/models/query.py:1288: in _update
    return query.get_compiler(self.db).execute_sql(ROW_COUNT)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../.venv/lib64/python3.11/site-packages/django/db/models/sql/compiler.py:2060: in execute_sql
    row_count = super().execute_sql(result_type)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../.venv/lib64/python3.11/site-packages/django/db/models/sql/compiler.py:1623: in execute_sql
    cursor.execute(sql, params)
../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:79: in execute
    return self._execute_with_wrappers(
../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:92: in _execute_with_wrappers
    return executor(sql, params, many, context)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:100: in _execute
    with self.db.wrap_database_errors:
../.venv/lib64/python3.11/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:105: in _execute
    return self.cursor.execute(sql, params)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <django.db.backends.sqlite3.base.SQLiteCursorWrapper object at 0x7fa5fb9cbb60>
query = 'UPDATE "store_provenancerecord" SET "betat_version" = ?, "timestamp" = ?, "hi_tag" = ?, "provenancier" = ?, "content"..."record_signature" = ?, "correction_of_id" = NULL, "disputes_id" = NULL WHERE "store_provenancerecord"."record_id" = ?'
params = ('0.1', '2026-06-12T14:32:00Z', True, '{"identity": "did:key:z6Mkftest", "identity_type": "cryptographic_key", "authen...me": "Example Community", "domain": "testing", "content_type": "text", "store_uri": "https://example.org/store"}', ...)

    def execute(self, query, params=None):
        if params is None:
            return super().execute(query)
        # Extract names if params is a mapping, i.e. "pyformat" style is used.
        param_names = list(params) if isinstance(params, Mapping) else None
        query = self.convert_query(query, param_names=param_names)
>       return super().execute(query, params)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       django.db.utils.OperationalError: no such table: store_provenancerecord

../.venv/lib64/python3.11/site-packages/django/db/backends/sqlite3/base.py:360: OperationalError
________________ test_raw_sql_update_blocked_by_sqlite_trigger _________________

self = <django.db.backends.utils.CursorWrapper object at 0x7fa5fb8e8b10>
sql = 'UPDATE "store_provenancerecord" SET "betat_version" = %s, "timestamp" = %s, "hi_tag" = %s, "provenancier" = %s, "cont...ecord_signature" = %s, "correction_of_id" = NULL, "disputes_id" = NULL WHERE "store_provenancerecord"."record_id" = %s'
params = ('0.1', '2026-06-12T14:32:00Z', True, '{"identity": "did:key:z6Mkftest", "identity_type": "cryptographic_key", "authen...me": "Example Community", "domain": "testing", "content_type": "text", "store_uri": "https://example.org/store"}', ...)
ignored_wrapper_args = (False, {'connection': <DatabaseWrapper vendor='sqlite' alias='default'>, 'cursor': <django.db.backends.utils.CursorWrapper object at 0x7fa5fb8e8b10>})

    def _execute(self, sql, params, *ignored_wrapper_args):
        # Raise a warning during app initialization (stored_app_configs is only
        # ever set during testing).
        if not apps.ready and not apps.stored_app_configs:
            warnings.warn(self.APPS_NOT_READY_WARNING_MSG, category=RuntimeWarning)
        self.db.validate_no_broken_transaction()
        with self.db.wrap_database_errors:
            if params is None:
                # params default might be backend specific.
                return self.cursor.execute(sql)
            else:
>               return self.cursor.execute(sql, params)
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:105: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <django.db.backends.sqlite3.base.SQLiteCursorWrapper object at 0x7fa5fb9c9760>
query = 'UPDATE "store_provenancerecord" SET "betat_version" = ?, "timestamp" = ?, "hi_tag" = ?, "provenancier" = ?, "content"..."record_signature" = ?, "correction_of_id" = NULL, "disputes_id" = NULL WHERE "store_provenancerecord"."record_id" = ?'
params = ('0.1', '2026-06-12T14:32:00Z', True, '{"identity": "did:key:z6Mkftest", "identity_type": "cryptographic_key", "authen...me": "Example Community", "domain": "testing", "content_type": "text", "store_uri": "https://example.org/store"}', ...)

    def execute(self, query, params=None):
        if params is None:
            return super().execute(query)
        # Extract names if params is a mapping, i.e. "pyformat" style is used.
        param_names = list(params) if isinstance(params, Mapping) else None
        query = self.convert_query(query, param_names=param_names)
>       return super().execute(query, params)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       sqlite3.OperationalError: no such table: store_provenancerecord

../.venv/lib64/python3.11/site-packages/django/db/backends/sqlite3/base.py:360: OperationalError

The above exception was the direct cause of the following exception:

    def test_raw_sql_update_blocked_by_sqlite_trigger():
        if connection.vendor != 'sqlite':
            pytest.skip('guard trigger is the SQLite-specific enforcement seam')
>       record = store.append(_valid_record_data())
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/test_store.py:170: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
betat_community/store/store.py:98: in append
    record.save()
../.venv/lib64/python3.11/site-packages/django/db/models/base.py:902: in save
    self.save_base(
../.venv/lib64/python3.11/site-packages/django/db/models/base.py:1008: in save_base
    updated = self._save_table(
../.venv/lib64/python3.11/site-packages/django/db/models/base.py:1138: in _save_table
    updated = self._do_update(
../.venv/lib64/python3.11/site-packages/django/db/models/base.py:1203: in _do_update
    return filtered._update(values) > 0
           ^^^^^^^^^^^^^^^^^^^^^^^^
../.venv/lib64/python3.11/site-packages/django/db/models/query.py:1288: in _update
    return query.get_compiler(self.db).execute_sql(ROW_COUNT)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../.venv/lib64/python3.11/site-packages/django/db/models/sql/compiler.py:2060: in execute_sql
    row_count = super().execute_sql(result_type)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../.venv/lib64/python3.11/site-packages/django/db/models/sql/compiler.py:1623: in execute_sql
    cursor.execute(sql, params)
../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:79: in execute
    return self._execute_with_wrappers(
../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:92: in _execute_with_wrappers
    return executor(sql, params, many, context)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:100: in _execute
    with self.db.wrap_database_errors:
../.venv/lib64/python3.11/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:105: in _execute
    return self.cursor.execute(sql, params)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <django.db.backends.sqlite3.base.SQLiteCursorWrapper object at 0x7fa5fb9c9760>
query = 'UPDATE "store_provenancerecord" SET "betat_version" = ?, "timestamp" = ?, "hi_tag" = ?, "provenancier" = ?, "content"..."record_signature" = ?, "correction_of_id" = NULL, "disputes_id" = NULL WHERE "store_provenancerecord"."record_id" = ?'
params = ('0.1', '2026-06-12T14:32:00Z', True, '{"identity": "did:key:z6Mkftest", "identity_type": "cryptographic_key", "authen...me": "Example Community", "domain": "testing", "content_type": "text", "store_uri": "https://example.org/store"}', ...)

    def execute(self, query, params=None):
        if params is None:
            return super().execute(query)
        # Extract names if params is a mapping, i.e. "pyformat" style is used.
        param_names = list(params) if isinstance(params, Mapping) else None
        query = self.convert_query(query, param_names=param_names)
>       return super().execute(query, params)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       django.db.utils.OperationalError: no such table: store_provenancerecord

../.venv/lib64/python3.11/site-packages/django/db/backends/sqlite3/base.py:360: OperationalError
________________ test_raw_sql_delete_blocked_by_sqlite_trigger _________________

self = <django.db.backends.utils.CursorWrapper object at 0x7fa5fb645690>
sql = 'UPDATE "store_provenancerecord" SET "betat_version" = %s, "timestamp" = %s, "hi_tag" = %s, "provenancier" = %s, "cont...ecord_signature" = %s, "correction_of_id" = NULL, "disputes_id" = NULL WHERE "store_provenancerecord"."record_id" = %s'
params = ('0.1', '2026-06-12T14:32:00Z', True, '{"identity": "did:key:z6Mkftest", "identity_type": "cryptographic_key", "authen...me": "Example Community", "domain": "testing", "content_type": "text", "store_uri": "https://example.org/store"}', ...)
ignored_wrapper_args = (False, {'connection': <DatabaseWrapper vendor='sqlite' alias='default'>, 'cursor': <django.db.backends.utils.CursorWrapper object at 0x7fa5fb645690>})

    def _execute(self, sql, params, *ignored_wrapper_args):
        # Raise a warning during app initialization (stored_app_configs is only
        # ever set during testing).
        if not apps.ready and not apps.stored_app_configs:
            warnings.warn(self.APPS_NOT_READY_WARNING_MSG, category=RuntimeWarning)
        self.db.validate_no_broken_transaction()
        with self.db.wrap_database_errors:
            if params is None:
                # params default might be backend specific.
                return self.cursor.execute(sql)
            else:
>               return self.cursor.execute(sql, params)
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:105: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <django.db.backends.sqlite3.base.SQLiteCursorWrapper object at 0x7fa5fb9c91c0>
query = 'UPDATE "store_provenancerecord" SET "betat_version" = ?, "timestamp" = ?, "hi_tag" = ?, "provenancier" = ?, "content"..."record_signature" = ?, "correction_of_id" = NULL, "disputes_id" = NULL WHERE "store_provenancerecord"."record_id" = ?'
params = ('0.1', '2026-06-12T14:32:00Z', True, '{"identity": "did:key:z6Mkftest", "identity_type": "cryptographic_key", "authen...me": "Example Community", "domain": "testing", "content_type": "text", "store_uri": "https://example.org/store"}', ...)

    def execute(self, query, params=None):
        if params is None:
            return super().execute(query)
        # Extract names if params is a mapping, i.e. "pyformat" style is used.
        param_names = list(params) if isinstance(params, Mapping) else None
        query = self.convert_query(query, param_names=param_names)
>       return super().execute(query, params)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       sqlite3.OperationalError: no such table: store_provenancerecord

../.venv/lib64/python3.11/site-packages/django/db/backends/sqlite3/base.py:360: OperationalError

The above exception was the direct cause of the following exception:

    def test_raw_sql_delete_blocked_by_sqlite_trigger():
        if connection.vendor != 'sqlite':
            pytest.skip('guard trigger is the SQLite-specific enforcement seam')
>       record = store.append(_valid_record_data())
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/test_store.py:182: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
betat_community/store/store.py:98: in append
    record.save()
../.venv/lib64/python3.11/site-packages/django/db/models/base.py:902: in save
    self.save_base(
../.venv/lib64/python3.11/site-packages/django/db/models/base.py:1008: in save_base
    updated = self._save_table(
../.venv/lib64/python3.11/site-packages/django/db/models/base.py:1138: in _save_table
    updated = self._do_update(
../.venv/lib64/python3.11/site-packages/django/db/models/base.py:1203: in _do_update
    return filtered._update(values) > 0
           ^^^^^^^^^^^^^^^^^^^^^^^^
../.venv/lib64/python3.11/site-packages/django/db/models/query.py:1288: in _update
    return query.get_compiler(self.db).execute_sql(ROW_COUNT)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../.venv/lib64/python3.11/site-packages/django/db/models/sql/compiler.py:2060: in execute_sql
    row_count = super().execute_sql(result_type)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../.venv/lib64/python3.11/site-packages/django/db/models/sql/compiler.py:1623: in execute_sql
    cursor.execute(sql, params)
../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:79: in execute
    return self._execute_with_wrappers(
../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:92: in _execute_with_wrappers
    return executor(sql, params, many, context)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:100: in _execute
    with self.db.wrap_database_errors:
../.venv/lib64/python3.11/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
../.venv/lib64/python3.11/site-packages/django/db/backends/utils.py:105: in _execute
    return self.cursor.execute(sql, params)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <django.db.backends.sqlite3.base.SQLiteCursorWrapper object at 0x7fa5fb9c91c0>
query = 'UPDATE "store_provenancerecord" SET "betat_version" = ?, "timestamp" = ?, "hi_tag" = ?, "provenancier" = ?, "content"..."record_signature" = ?, "correction_of_id" = NULL, "disputes_id" = NULL WHERE "store_provenancerecord"."record_id" = ?'
params = ('0.1', '2026-06-12T14:32:00Z', True, '{"identity": "did:key:z6Mkftest", "identity_type": "cryptographic_key", "authen...me": "Example Community", "domain": "testing", "content_type": "text", "store_uri": "https://example.org/store"}', ...)

    def execute(self, query, params=None):
        if params is None:
            return super().execute(query)
        # Extract names if params is a mapping, i.e. "pyformat" style is used.
        param_names = list(params) if isinstance(params, Mapping) else None
        query = self.convert_query(query, param_names=param_names)
>       return super().execute(query, params)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       django.db.utils.OperationalError: no such table: store_provenancerecord

../.venv/lib64/python3.11/site-packages/django/db/backends/sqlite3/base.py:360: OperationalError
=========================== short test summary info ============================
FAILED tests/test_store.py::test_append_writes_valid_record - django.db.utils...
FAILED tests/test_store.py::test_record_id_computed_server_side_ignores_caller_value
FAILED tests/test_store.py::test_round_trip_byte_identical - django.db.utils....
FAILED tests/test_store.py::test_correction_references_original - django.db.u...
FAILED tests/test_store.py::test_list_records_newest_first_and_since_filter
FAILED tests/test_store.py::test_verify_integrity_passes_on_clean_record - dj...
FAILED tests/test_store.py::test_verify_integrity_fails_on_tampered_record - ...
FAILED tests/test_store.py::test_queryset_update_blocked - django.db.utils.Op...
FAILED tests/test_store.py::test_instance_delete_blocked - django.db.utils.Op...
FAILED tests/test_store.py::test_raw_sql_update_blocked_by_sqlite_trigger - d...
FAILED tests/test_store.py::test_raw_sql_delete_blocked_by_sqlite_trigger - d...
======================== 11 failed, 11 passed in 1.68s =========================

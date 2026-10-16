#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""Tests for osprofiler tracing of the database engine."""

from unittest import mock

import sqlalchemy as sa

from cinder.db import api as db_api
from cinder.tests.unit import test


class SQLAlchemyTracingTestCase(test.TestCase):

    def setUp(self):
        super().setUp()
        self.osprofiler_sqlalchemy = mock.Mock()
        self.patch('cinder.db.api.osprofiler_sqlalchemy',
                   self.osprofiler_sqlalchemy)

    def _new_engine(self):
        # A copy of the real context manager, so that the engine is created
        # with the hooks the services get, without touching the engine the
        # tests share.
        manager = db_api.main_context_manager.make_new_manager()
        manager.configure(connection='sqlite://')
        return manager.writer.get_engine()

    def test_tracing_added_when_enabled(self):
        self.override_config('enabled', True, group='profiler')
        self.override_config('trace_sqlalchemy', True, group='profiler')

        engine = self._new_engine()

        self.osprofiler_sqlalchemy.add_tracing.assert_called_once_with(
            sa, engine, 'db')

    def test_tracing_not_added_when_profiler_disabled(self):
        self.override_config('enabled', False, group='profiler')
        self.override_config('trace_sqlalchemy', True, group='profiler')

        self._new_engine()

        self.osprofiler_sqlalchemy.add_tracing.assert_not_called()

    def test_tracing_not_added_without_trace_sqlalchemy(self):
        self.override_config('enabled', True, group='profiler')
        self.override_config('trace_sqlalchemy', False, group='profiler')

        self._new_engine()

        self.osprofiler_sqlalchemy.add_tracing.assert_not_called()

    def test_osprofiler_not_installed(self):
        self.patch('cinder.db.api.osprofiler_sqlalchemy', None)
        self.override_config('enabled', True, group='profiler')
        self.override_config('trace_sqlalchemy', True, group='profiler')

        engine = self._new_engine()

        with engine.connect() as conn:
            self.assertEqual(1, conn.execute(sa.text('SELECT 1')).scalar())

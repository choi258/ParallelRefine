#!/usr/bin/env python


import sys
import os
import zipimport
from time import sleep
import csv
import json
import gzip
import os
import re
import StringIO
import time
import urllib
import urllib2_file
import urllib2
import urlparse
import StringIO

reload(sys)
sys.setdefaultencoding('utf-8')

req_importer = zipimport.zipimporter('requests.mod')
requests = req_importer.load_module('requests')
#ref_importer = zipimport.zipimporter('refine.mod')
#refine = ref_importer.load_module('refine')
#sys.stderr.write(str(dir(refine)))
sys.stderr.write("sadfsdfvsdf")
#filename = os.path.join(os.path.dirname(__file__), 'data', 'header.csv')
filename = "header.csv"
headerfile = open(filename)
headers = [headerfile.readline()]
headerfile.close()


    








REFINE_HOST = os.environ.get('OPENREFINE_HOST', os.environ.get('GOOGLE_REFINE_HOST', '127.0.0.1'))
REFINE_PORT = os.environ.get('OPENREFINE_PORT', os.environ.get('GOOGLE_REFINE_PORT', '3333'))


class RefineServer(object):
    """Communicate with a Refine server."""

    @staticmethod
    def url():
        """Return the URL to the Refine server."""
        server = 'http://' + REFINE_HOST
        if REFINE_PORT != '80':
            server += ':' + REFINE_PORT
        return server

    def __init__(self, server=None):
        if server is None:
            server = self.url()
        self.server = server[:-1] if server.endswith('/') else server
        self.__version = None     # see version @property below

    def urlopen(self, command, data=None, params=None, project_id=None):
        """Open a Refine URL and with optional query params and POST data.

        data: POST data dict
        param: query params dict
        project_id: project ID as string

        Returns urllib2.urlopen iterable."""
        url = self.server + '/command/core/' + command
        if data is None:
            data = {}
        if params is None:
            params = {}
        if project_id:
            # XXX haven't figured out pattern on qs v body
            if 'delete' in command or data:
                data['project'] = project_id
            else:
                params['project'] = project_id
        if params:
            url += '?' + urllib.urlencode(params)
        req = urllib2.Request(url)
        if data:
            req.add_data(data)  # data = urllib.urlencode(data)
        #req.add_header('Accept-Encoding', 'gzip')
        try:
            response = urllib2.urlopen(req)
        except urllib2.HTTPError as e:
            raise Exception('HTTP %d "%s" for %s\n\t%s' % (e.code, e.msg, e.geturl(), data))
        except urllib2.URLError as e:
            raise urllib2.URLError(
                '%s for %s. No Refine server reachable/running; ENV set?' %
                (e.reason, self.server))
        if response.info().get('Content-Encoding', None) == 'gzip':
            # Need a seekable filestream for gzip
            gzip_fp = gzip.GzipFile(fileobj=StringIO.StringIO(response.read()))
            # XXX Monkey patch response's filehandle. Better way?
            urllib.addbase.__init__(response, gzip_fp)
        return response

    def urlopen_json(self, *args, **kwargs):
        """Open a Refine URL, optionally POST data, and return parsed JSON."""
        response = json.loads(self.urlopen(*args, **kwargs).read())
        if 'code' in response and response['code'] not in ('ok', 'pending'):
            error_message = ('server ' + response['code'] + ': ' +
                             response.get('message', response.get('stack', response)))
            raise Exception(error_message)
        return response

    def get_version(self):
        """Return version data.

        {"revision":"r1836","full_version":"2.0 [r1836]",
         "full_name":"Google Refine 2.0 [r1836]","version":"2.0"}"""
        return self.urlopen_json('get-version')

    @property
    def version(self):
        if self.__version is None:
            self.__version = self.get_version()['version']
        return self.__version


class Refine:
    """Class representing a connection to a Refine server."""
    def __init__(self, server):
        if isinstance(server, RefineServer):
            self.server = server
        else:
            self.server = RefineServer(server)

    def list_projects(self):
        """Return a dict of projects indexed by id.

        {u'1877818633188': {
            'id': u'1877818633188', u'name': u'akg',
            u'modified': u'2011-04-07T12:30:07Z',
            u'created': u'2011-04-07T12:30:07Z'
        },
        """
        # It's tempting to add in an index by name but there can be
        # projects with the same name.
        return self.server.urlopen_json('get-all-project-metadata')['projects']

    def get_project_name(self, project_id):
        """Returns project name given project_id."""
        projects = self.list_projects()
        return projects[project_id]['name']

    def open_project(self, project_id):
        """Open a Refine project."""
        return RefineProject(self.server, project_id)

    # These aren't used yet but are included for reference
    new_project_defaults = {
        'text/line-based/*sv': {
            'encoding': '',
            'separator': ',',
            'ignore_lines': -1,
            'header_lines': 1,
            'skip_data_lines': 0,
            'limit': -1,
            'store_blank_rows': True,
            'guess_cell_value_types': True,
            'process_quotes': True,
            'store_blank_cells_as_nulls': True,
            'include_file_sources': False},
        'text/line-based': {
            'encoding': '',
            'lines_per_row': 1,
            'ignore_lines': -1,
            'limit': -1,
            'skip_data_lines': -1,
            'store_blank_rows': True,
            'store_blank_cells_as_nulls': True,
            'include_file_sources': False},
        'text/line-based/fixed-width': {
            'encoding': '',
            'column_widths': [20],
            'ignore_lines': -1,
            'header_lines': 0,
            'skip_data_lines': 0,
            'limit': -1,
            'guess_cell_value_types': False,
            'store_blank_rows': True,
            'store_blank_cells_as_nulls': True,
            'include_file_sources': False},
        'text/line-based/pc-axis': {
            'encoding': '',
            'limit': -1,
            'skip_data_lines': -1,
            'include_file_sources': False},
        'text/rdf+n3': {'encoding': ''},
        'text/xml/ods': {
            'sheets': [],
            'ignore_lines': -1,
            'header_lines': 1,
            'skip_data_lines': 0,
            'limit': -1,
            'store_blank_rows': True,
            'store_blank_cells_as_nulls': True,
            'include_file_sources': False},
        'binary/xls': {
            'xml_based': False,
            'sheets': [],
            'ignore_lines': -1,
            'header_lines': 1,
            'skip_data_lines': 0,
            'limit': -1,
            'store_blank_rows': True,
            'store_blank_cells_as_nulls': True,
            'include_file_sources': False}
    }

    def new_project(self, project_file=None, project_url=None, project_name=None, project_format='text/line-based/*sv',
                    encoding='',
                    separator=',',
                    ignore_lines=-1,
                    header_lines=1,
                    skip_data_lines=0,
                    limit=-1,
                    store_blank_rows=True,
                    guess_cell_value_types=True,
                    process_quotes=True,
                    store_blank_cells_as_nulls=True,
                    include_file_sources=False,
                    **opts):

        if (project_file and project_url) or (not project_file and not project_url):
            raise ValueError('One (only) of project_file and project_url must be set')

        def s(opt):
            if isinstance(opt, bool):
                return 'true' if opt else 'false'
            if opt is None:
                return ''
            return str(opt)

        # the new APIs requires a json in the 'option' POST or GET argument
        # POST is broken at the moment, so we send it in the URL
        new_style_options = dict(opts, **{
            'encoding': s(encoding),
        })
        params = {
            'options': json.dumps(new_style_options),
        }

        # old style options
        options = {
            'format': project_format,
            'separator': s(separator),
            'ignore-lines': s(ignore_lines),
            'header-lines': s(header_lines),
            'skip-data-lines': s(skip_data_lines),
            'limit': s(limit),
            'guess-value-type': s(guess_cell_value_types),
            'process-quotes': s(process_quotes),
            'store-blank-rows': s(store_blank_rows),
            'store-blank-cells-as-nulls': s(store_blank_cells_as_nulls),
            'include-file-sources': s(include_file_sources),
        }

        if project_url is not None:
            options['url'] = project_url
        elif project_file is not None:
            options['project-file'] = {
                'fd': open(project_file),
                'filename': project_file,
            }
        if project_name is None:
            # make a name for itself by stripping extension and directories
            project_name = (project_file or 'New project').rsplit('.', 1)[0]
            project_name = os.path.basename(project_name)
        options['project-name'] = project_name
        response = self.server.urlopen(
            'create-project-from-upload', options, params
        )
        # expecting a redirect to the new project containing the id in the url
        url_params = urlparse.parse_qs(
            urlparse.urlparse(response.geturl()).query)
        if 'project' in url_params:
            project_id = url_params['project'][0]
            return RefineProject(self.server, project_id)
        else:
            raise Exception('Project not created')

    def new_project_data(self, project_data=None, project_url=None, project_name="abc", project_format='text/line-based/*sv',
                    encoding='',
                    separator=',',
                    ignore_lines=-1,
                    header_lines=1,
                    skip_data_lines=0,
                    limit=-1,
                    store_blank_rows=True,
                    guess_cell_value_types=True,
                    process_quotes=True,
                    store_blank_cells_as_nulls=True,
                    include_file_sources=False,
                    **opts):

        if (project_data and project_url) or (not project_data and not project_url):
            raise ValueError('One (only) of project_file and project_url must be set')

        def s(opt):
            if isinstance(opt, bool):
                return 'true' if opt else 'false'
            if opt is None:
                return ''
            return str(opt)

        # the new APIs requires a json in the 'option' POST or GET argument
        # POST is broken at the moment, so we send it in the URL
        new_style_options = dict(opts, **{
            'encoding': s(encoding),
        })
        params = {
            'options': json.dumps(new_style_options),
        }

        # old style options
        options = {
            'format': project_format,
            'separator': s(separator),
            'ignore-lines': s(ignore_lines),
            'header-lines': s(header_lines),
            'skip-data-lines': s(skip_data_lines),
            'limit': s(limit),
            'guess-value-type': s(guess_cell_value_types),
            'process-quotes': s(process_quotes),
            'store-blank-rows': s(store_blank_rows),
            'store-blank-cells-as-nulls': s(store_blank_cells_as_nulls),
            'include-file-sources': s(include_file_sources),
        }

        if project_url is not None:
            options['url'] = project_url
        elif project_data is not None:
            options['project-file'] = {
                'fd': StringIO.StringIO(project_data),
                'filename': "blah",
            }
        if project_name is None:
            # make a name for itself by stripping extension and directories
            project_name = (project_file or 'New project').rsplit('.', 1)[0]
            project_name = os.path.basename(project_name)
        options['project-name'] = project_name
        response = self.server.urlopen(
            'create-project-from-upload', options, params
        )
        # expecting a redirect to the new project containing the id in the url
        url_params = urlparse.parse_qs(
            urlparse.urlparse(response.geturl()).query)
        if 'project' in url_params:
            project_id = url_params['project'][0]
            return RefineProject(self.server, project_id)
        else:
            raise Exception('Project not created')

def RowsResponseFactory(column_index):
    """Factory for the parsing the output from get_rows().

    Uses the project's model's row cell index so that a row can be used
    as a dict by column name."""

    class RowsResponse(object):
        class RefineRows(object):
            class RefineRow(object):
                def __init__(self, row_response):
                    self.flagged = row_response['flagged']
                    self.starred = row_response['starred']
                    self.index = row_response['i']
                    self.row = [c['v'] if c else None
                                for c in row_response['cells']]

                def __getitem__(self, column):
                    # Trailing nulls seem to be stripped from row data
                    try:
                        return self.row[column_index[column]]
                    except IndexError:
                        return None

            def __init__(self, rows_response):
                self.rows_response = rows_response

            def __iter__(self):
                for row_response in self.rows_response:
                    yield self.RefineRow(row_response)

            def __getitem__(self, index):
                return self.RefineRow(self.rows_response[index])

            def __len__(self):
                return len(self.rows_response)

        def __init__(self, response):
            self.mode = response['mode']
            self.filtered = response['filtered']
            self.start = response['start']
            self.limit = response['limit']
            self.total = response['total']
            self.rows = self.RefineRows(response['rows'])

    return RowsResponse


class RefineProject:
    """An OpenRefine project."""

    def __init__(self, server, project_id=None):
        if not isinstance(server, RefineServer):
            if '/project?project=' in server:
                server, project_id = server.split('/project?project=')
                server = RefineServer(server)
            elif re.match(r'\d+$', server):     # just digits => project ID
                server, project_id = RefineServer(), server
            else:
                server = RefineServer(server)
        self.server = server
        if not project_id:
            raise Exception('Missing Refine project ID')
        self.project_id = project_id
        self.engine = Engine()
        self.sorting = Sorting()
        self.history_entry = None
        # following filled in by get_models()
        self.key_column = None
        self.has_records = False
        self.columns = None
        self.column_order = {}  # map of column names to order in UI
        self.rows_response_factory = None   # for parsing get_rows()
        self.get_models()
        # following filled in by get_reconciliation_services
        self.recon_services = None

    def project_name(self):
        return Refine(self.server).get_project_name(self.project_id)

    def project_url(self):
        """Return a URL to the project."""
        return '%s/project?project=%s' % (self.server.server, self.project_id)

    def do_raw(self, command, data):
        """Issue a command to the server & return a response object."""
        return self.server.urlopen(command, project_id=self.project_id,
                                   data=data)

    def do_json(self, command, data=None, include_engine=True):
        """Issue a command to the server, parse & return decoded JSON."""
        if include_engine:
            if data is None:
                data = {}
            data['engine'] = self.engine.as_json()
        response = self.server.urlopen_json(command,
                                            project_id=self.project_id,
                                            data=data)
        if 'historyEntry' in response:
            # **response['historyEntry'] won't work as keys are unicode :-/
            he = response['historyEntry']
            self.history_entry = history.HistoryEntry(he['id'], he['time'],
                                                      he['description'])
        return response

    def get_models(self):
        """Fill out column metadata.

        Column structure is a list of columns in their order.
        The cellIndex is an index for that column's data into the list returned
        from get_rows()."""
        response = self.do_json('get-models', include_engine=False)
        column_model = response['columnModel']
        column_index = {}   # map of column name to index into get_rows() data
        self.columns = [column['name'] for column in column_model['columns']]
        for i, column in enumerate(column_model['columns']):
            name = column['name']
            self.column_order[name] = i
            column_index[name] = column['cellIndex']
        self.key_column = column_model['keyColumnName']
        self.has_records = response['recordModel'].get('hasRecords', False)
        self.rows_response_factory = RowsResponseFactory(column_index)
        # TODO: implement rest
        return response

    def get_preference(self, name):
        """Returns the (JSON) value of a given preference setting."""
        response = self.server.urlopen_json('get-preference',
                                            params={'name': name})
        return json.loads(response['value'])

    def wait_until_idle(self, polling_delay=0.5):
        while True:
            response = self.do_json('get-processes', include_engine=False)
            if 'processes' in response and len(response['processes']) > 0:
                time.sleep(polling_delay)
            else:
                return

    def apply_operations_from_file(self, file_path, wait=True):
        json_data = open(file_path).read()
        response_json = self.do_json('apply-operations', {'operations': json_data})
        if response_json['code'] == 'pending' and wait:
            self.wait_until_idle()
            return 'ok'
        return response_json['code']  # can be 'ok' or 'pending'
        
	def apply_operations(self, json_data, wait=True):
		response_json = self.do_json('apply-operations', {'operations': json_data})
        if response_json['code'] == 'pending' and wait:
            self.wait_until_idle()
            return 'ok'
        return response_json['code']  # can be 'ok' or 'pending'

    def export(self, export_format='tsv'):
        """Return a fileobject of a project's data."""
        url = ('export-rows/' + urllib.quote(self.project_id) + '.' +
               export_format)
        return self.do_raw(url, data={'format': export_format})

    def export_rows(self, **kwargs):
        """Return an iterable of parsed rows of a project's data."""
        return csv.reader(self.export(**kwargs), dialect='excel-tab')

    def delete(self):
        response_json = self.do_json('delete-project', include_engine=False)
        return 'code' in response_json and response_json['code'] == 'ok'

    def compute_facets(self, facets=None):
        """Compute facets as per the project's engine.

        The response object has two attributes, mode & facets. mode is one of
        'row-based' or 'record-based'. facets is a magic list of facets in the
        same order as they were specified in the Engine. Magic allows the
        original Engine's facet as index into the response, e.g.,

        name_facet = TextFacet('name')
        response = project.compute_facets(name_facet)
        response.facets[name_facet]     # same as response.facets[0]
        """
        if facets:
            self.engine.set_facets(facets)
        response = self.do_json('compute-facets')
        return self.engine.facets_response(response)

    def get_rows(self, facets=None, sort_by=None, start=0, limit=10):
        if facets:
            self.engine.set_facets(facets)
        if sort_by is not None:
            self.sorting = Sorting(sort_by)
        response = self.do_json('get-rows', {'sorting': self.sorting.as_json(),
                                             'start': start, 'limit': limit})
        return self.rows_response_factory(response)

    def reorder_rows(self, sort_by=None):
        if sort_by is not None:
            self.sorting = Sorting(sort_by)
        response = self.do_json('reorder-rows',
                                {'sorting': self.sorting.as_json()})
        # clear sorting
        self.sorting = Sorting()
        return response

    def remove_rows(self, facets=None):
        if facets:
            self.engine.set_facets(facets)
        return self.do_json('remove-rows')

    def text_transform(self, column, expression, on_error='set-to-blank',
                       repeat=False, repeat_count=10):
        response = self.do_json('text-transform', {
            'columnName': column, 'expression': expression,
            'onError': on_error, 'repeat': repeat,
            'repeatCount': repeat_count})
        return response

    def edit(self, column, edit_from, edit_to):
        edits = [{'from': [edit_from], 'to': edit_to}]
        return self.mass_edit(column, edits)

    def mass_edit(self, column, edits, expression='value'):
        """edits is [{'from': ['foo'], 'to': 'bar'}, {...}]"""
        edits = json.dumps(edits)
        response = self.do_json('mass-edit', {
            'columnName': column, 'expression': expression, 'edits': edits})
        return response

    clusterer_defaults = {
        'binning': {
            'type': 'binning',
            'function': 'fingerprint',
            'params': {},
        },
        'knn': {
            'type': 'knn',
            'function': 'levenshtein',
            'params': {
                'radius': 1,
                'blocking-ngram-size': 6,
            },
        },
    }

    def compute_clusters(self, column, clusterer_type='binning',
                         function=None, params=None):
        """Returns a list of clusters of {'value': ..., 'count': ...}."""
        clusterer = self.clusterer_defaults[clusterer_type]
        if params is not None:
            clusterer['params'] = params
        if function is not None:
            clusterer['function'] = function
        clusterer['column'] = column
        response = self.do_json('compute-clusters', {
            'clusterer': json.dumps(clusterer)})
        return [[{'value': x['v'], 'count': x['c']} for x in cluster]
                for cluster in response]

    def annotate_one_row(self, row, annotation, state=True):
        if annotation not in ('starred', 'flagged'):
            raise ValueError('annotation must be one of starred or flagged')
        state = 'true' if state is True else 'false'
        return self.do_json('annotate-one-row', {'row': row.index,
                                                 annotation: state})

    def flag_row(self, row, flagged=True):
        return self.annotate_one_row(row, 'flagged', flagged)

    def star_row(self, row, starred=True):
        return self.annotate_one_row(row, 'starred', starred)

    def add_column(self, column, new_column, expression='value',
                   column_insert_index=None, on_error='set-to-blank'):
        if column_insert_index is None:
            column_insert_index = self.column_order[column] + 1
        response = self.do_json('add-column', {
            'baseColumnName': column, 'newColumnName': new_column,
            'expression': expression, 'columnInsertIndex': column_insert_index,
            'onError': on_error})
        self.get_models()
        return response

    def split_column(self, column, separator=',', mode='separator',
                     regex=False, guess_cell_type=True,
                     remove_original_column=True):
        response = self.do_json('split-column', {
            'columnName': column, 'separator': separator, 'mode': mode,
            'regex': regex, 'guessCellType': guess_cell_type,
            'removeOriginalColumn': remove_original_column})
        self.get_models()
        return response

    def rename_column(self, column, new_column):
        response = self.do_json('rename-column', {'oldColumnName': column,
                                                  'newColumnName': new_column})
        self.get_models()
        return response

    def reorder_columns(self, new_column_order):
        """Takes an array of column names in the new order."""
        response = self.do_json('reorder-columns', {
            'columnNames': new_column_order})
        self.get_models()
        return response

    def move_column(self, column, index):
        """Move column to a new position."""
        if index == 'end':
            index = len(self.columns) - 1
        response = self.do_json('move-column', {'columnName': column,
                                                'index': index})
        self.get_models()
        return response

    def blank_down(self, column):
        response = self.do_json('blank-down', {'columnName': column})
        self.get_models()
        return response

    def fill_down(self, column):
        response = self.do_json('fill-down', {'columnName': column})
        self.get_models()
        return response

    def transpose_columns_into_rows(
            self, start_column, column_count,
            combined_column_name, separator=':', prepend_column_name=True,
            ignore_blank_cells=True):

        response = self.do_json('transpose-columns-into-rows', {
            'startColumnName': start_column, 'columnCount': column_count,
            'combinedColumnName': combined_column_name,
            'prependColumnName': prepend_column_name,
            'separator': separator, 'ignoreBlankCells': ignore_blank_cells})
        self.get_models()
        return response

    def transpose_rows_into_columns(self, column, row_count):
        response = self.do_json('transpose-rows-into-columns', {
            'columnName': column, 'rowCount': row_count})
        self.get_models()
        return response

    # Reconciliation
    # http://code.google.com/p/google-refine/wiki/ReconciliationServiceApi
    def guess_types_of_column(self, column, service):
        """Query the reconciliation service for what it thinks this column is.

        service: reconciliation endpoint URL

        Returns [
           {"id":"/domain/type","name":"Type Name","score":10.2,"count":18},
           ...
        ]
        """
        response = self.do_json('guess-types-of-column', {
            'columnName': column, 'service': service}, include_engine=False)
        return response['types']

    def get_reconciliation_services(self):
        response = self.get_preference('reconciliation.standardServices')
        self.recon_services = response
        return response

    def get_reconciliation_service_by_name_or_url(self, name):
        recon_services = self.get_reconciliation_services()
        for recon_service in recon_services:
            if recon_service['name'] == name or recon_service['url'] == name:
                return recon_service
        return None

    def reconcile(self, column, service, reconciliation_type=None,
                  reconciliation_config=None):
        """Perform a reconciliation asynchronously.

        config: {
            "mode": "standard-service",
            "service": "http://.../reconcile/",
            "identifierSpace": "http://.../ns/authority",
            "schemaSpace": "http://.../ns/type",
            "type": {
                "id": "/domain/type",
                "name": "Type Name"
            },
            "autoMatch": true,
            "columnDetails": []
        }

        Returns typically {'code': 'pending'}; call wait_until_idle() to wait
        for reconciliation to complete.
        """
        # Create a reconciliation config by looking up recon service info
        if reconciliation_config is None:
            service = self.get_reconciliation_service_by_name_or_url(service)
            if reconciliation_type is None:
                raise ValueError('Must have at least one of config or type')
            reconciliation_config = {
                'mode': 'standard-service',
                'service': service['url'],
                'identifierSpace': service['identifierSpace'],
                'schemaSpace': service['schemaSpace'],
                'type': {
                    'id': reconciliation_type['id'],
                    'name': reconciliation_type['name'],
                },
                'autoMatch': True,
                'columnDetails': [],
            }
        return self.do_json('reconcile', {
            'columnName': column, 'config': json.dumps(reconciliation_config)})


class HistoryEntry(object):
    # N.B. e.g. **response['historyEntry'] won't work as keys are unicode :-/
    #noinspection PyUnusedLocal
    def __init__(self, history_entry_id=None, time=None, description=None, **kwargs):
        if history_entry_id is None:
            raise ValueError('History entry id must be set')
        self.id = history_entry_id
        self.description = description
        self.time = time




def to_camel(attr):
    """convert this_attr_name to thisAttrName."""
    # Do lower case first letter
    return (attr[0].lower() +
            re.sub(r'_(.)', lambda x: x.group(1).upper(), attr[1:]))


def from_camel(attr):
    """convert thisAttrName to this_attr_name."""
    # Don't add an underscore for capitalized first letter
    return re.sub(r'(?<=.)([A-Z])', lambda x: '_' + x.group(1), attr).lower()


class Facet(object):
    def __init__(self, column, facet_type, **options):
        self.type = facet_type
        self.name = column
        self.column_name = column
        for k, v in options.items():
            setattr(self, k, v)

    def as_dict(self):
        return dict([(to_camel(k), v) for k, v in self.__dict__.items()
                     if v is not None])


class TextFilterFacet(Facet):
    def __init__(self, column, query, **options):
        super(TextFilterFacet, self).__init__(
            column, query=query, case_sensitive=False, facet_type='text',
            mode='text', **options)


class TextFacet(Facet):
    def __init__(self, column, selection=None, expression='value',
                 omit_blank=False, omit_error=False, select_blank=False,
                 select_error=False, invert=False, **options):
        super(TextFacet, self).__init__(
            column,
            facet_type='list',
            omit_blank=omit_blank,
            omit_error=omit_error,
            select_blank=select_blank,
            select_error=select_error,
            invert=invert,
            **options)
        self.expression = expression
        self.selection = []
        if selection is None:
            selection = []
        elif not isinstance(selection, list):
            selection = [selection]
        for value in selection:
            self.include(value)

    def include(self, value):
        for s in self.selection:
            if s['v']['v'] == value:
                return
        self.selection.append({'v': {'v': value, 'l': value}})
        return self

    def exclude(self, value):
        self.selection = [s for s in self.selection
                          if s['v']['v'] != value]
        return self

    def reset(self):
        self.selection = []
        return self


class BoolFacet(TextFacet):
    def __init__(self, column, expression=None, selection=None):
        if selection is not None and not isinstance(selection, bool):
            raise ValueError('selection must be True or False.')
        if expression is None:
            raise ValueError('Missing expression')
        super(BoolFacet, self).__init__(
            column, expression=expression, selection=selection)


class StarredFacet(BoolFacet):
    def __init__(self, selection=None):
        super(StarredFacet, self).__init__(
            '', expression='row.starred', selection=selection)


class FlaggedFacet(BoolFacet):
    def __init__(self, selection=None):
        super(FlaggedFacet, self).__init__(
            '', expression='row.flagged', selection=selection)


class BlankFacet(BoolFacet):
    def __init__(self, column, selection=None):
        super(BlankFacet, self).__init__(
            column, expression='isBlank(value)', selection=selection)


class ReconJudgmentFacet(TextFacet):
    def __init__(self, column, **options):
        super(ReconJudgmentFacet, self).__init__(
            column,
            expression=('forNonBlank(cell.recon.judgment, v, v, '
                        'if(isNonBlank(value), "(unreconciled)", "(blank)"))'),
            **options)


# Capitalize 'From' to get around python's reserved word.
#noinspection PyPep8Naming
class NumericFacet(Facet):
    def __init__(self, column, From=None, to=None, expression='value',
                 select_blank=True, select_error=True, select_non_numeric=True,
                 select_numeric=True, **options):
        super(NumericFacet, self).__init__(
            column,
            From=From,
            to=to,
            expression=expression,
            facet_type='range',
            select_blank=select_blank,
            select_error=select_error,
            select_non_numeric=select_non_numeric,
            select_numeric=select_numeric,
            **options)

    def reset(self):
        self.From = None
        self.to = None
        return self


class FacetResponse(object):
    """Class for unpacking an individual facet response."""
    def __init__(self, facet):
        self.name = None
        for k, v in facet.items():
            if isinstance(k, bool) or isinstance(k, basestring):
                setattr(self, from_camel(k), v)
        self.choices = {}

        class FacetChoice(object):
            def __init__(self, c):
                self.count = c['c']
                self.selected = c['s']

        if 'choices' in facet:
            for choice in facet['choices']:
                self.choices[choice['v']['v']] = FacetChoice(choice)
            if 'blankChoice' in facet:
                self.blank_choice = FacetChoice(facet['blankChoice'])
            else:
                self.blank_choice = None
        if 'bins' in facet:
            self.bins = facet['bins']
            self.base_bins = facet['baseBins']


class FacetsResponse(object):
    """FacetsResponse unpacking the compute-facets response.

    It has two attributes: facets & mode. Mode is either 'row-based' or
    'record-based'. facets is a list of facets produced by compute-facets, in
    the same order as they were specified in the Engine. By coupling the engine
    object with a custom container it's possible to look up the computed facet
    by the original facet's object.
    """
    def __init__(self, engine, facets):
        class FacetResponseContainer(object):
            facets = None

            def __init__(self, facet_responses):
                self.facets = [FacetResponse(fr) for fr in facet_responses]

            def __iter__(self):
                for facet in self.facets:
                    yield facet

            def __getitem__(self, index):
                if not isinstance(index, int):
                    index = engine.facet_index_by_id[id(index)]
                assert self.facets[index].name == engine.facets[index].name
                return self.facets[index]

        self.facets = FacetResponseContainer(facets['facets'])
        self.mode = facets['mode']


class Engine(object):
    """An Engine keeps track of Facets, and responses to facet computation."""

    def __init__(self, *facets, **kwargs):
        self.facets = []
        self.facet_index_by_id = {}  # dict of facets by Facet object id
        self.set_facets(*facets)
        self.mode = kwargs.get('mode', 'row-based')

    def set_facets(self, *facets):
        """facets may be a Facet or list of Facets."""
        self.remove_all()
        for facet in facets:
            self.add_facet(facet)

    def facets_response(self, response):
        """Unpack a compute-facets response."""
        return FacetsResponse(self, response)

    def __len__(self):
        return len(self.facets)

    def as_json(self):
        """Return a JSON string suitable for use as a POST parameter."""
        return json.dumps({
            'facets': [f.as_dict() for f in self.facets],  # XXX how with json?
            'mode': self.mode,
        })

    def add_facet(self, facet):
        # Record the facet's object id so facet response can be looked up by id
        self.facet_index_by_id[id(facet)] = len(self.facets)
        self.facets.append(facet)

    def remove_all(self):
        """Remove all facets."""
        self.facet_index_by_id = {}
        self.facets = []

    def reset_all(self):
        """Reset all facets."""
        for facet in self.facets:
            facet.reset()


class Sorting(object):
    """Class representing the current sorting order for a project.

    Used in RefineProject.get_rows()"""
    def __init__(self, criteria=None):
        self.criteria = []
        if criteria is None:
            criteria = []
        if not isinstance(criteria, list):
            criteria = [criteria]
        for criterion in criteria:
            # A string criterion defaults to a string sort on that column
            if isinstance(criterion, basestring):
                criterion = {
                    'column': criterion,
                    'valueType': 'string',
                    'caseSensitive': False,
                }
            criterion.setdefault('reverse', False)
            criterion.setdefault('errorPosition', 1)
            criterion.setdefault('blankPosition', 2)
            self.criteria.append(criterion)

    def as_json(self):
        return json.dumps({'criteria': self.criteria})

    def __len__(self):
        return len(self.criteria)


_format = 'text/line-based/csv'
_options = {}
i=0
# input comes from STDIN (standard input)
#import pdb
for chunk in sys.stdin:
    # process chunk and split on custom delimiter
    chunk = chunk.split('#####')
    #append to headers
    x = headers + chunk
    
    #pdb.set_trace()
    #print str(headers)
    #sys.stderr.write(str(headers))
    server = RefineServer()
    refine_object = Refine(server)
    project = refine_object.new_project_data(project_data="\n".join(x), \
                                     project_format=_format, \
                                     project_options=_options)       
    project.apply_operations_from_file("operations.json",False)
    csv_iterable = project.export_rows()
    project.delete()
    
    i=i+1
    sleep(0.005)
    
    out_string = ""
   
    
    for row in csv_iterable:
	    print ', '.join(row)
		
    #print out_string	
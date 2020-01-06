"""Generated client library for fusiontables version v1."""
# NOTE: This file is autogenerated and should not be edited by hand.
from apitools.base.py import base_api
from samples.fusiontables_sample.fusiontables_v1 import fusiontables_v1_messages as messages


class FusiontablesV1(base_api.BaseApiClient):
  """Generated client library for service fusiontables version v1."""

  MESSAGES_MODULE = messages
  BASE_URL = u'https://www.googleapis.com/fusiontables/v1/'

  _PACKAGE = u'fusiontables'
  _SCOPES = [u'https://www.googleapis.com/auth/fusiontables', u'https://www.googleapis.com/auth/fusiontables.readonly']
  _VERSION = u'v1'
  _CLIENT_ID = '1042881264118.apps.googleusercontent.com'
  _CLIENT_SECRET = 'x_Tw5K8nnjoRAqULM9PFAC2b'
  _USER_AGENT = 'x_Tw5K8nnjoRAqULM9PFAC2b'
  _CLIENT_CLASS_NAME = u'FusiontablesV1'
  _URL_VERSION = u'v1'
  _API_KEY = None

  def __init__(self, url='', credentials=None,
               get_credentials=True, http=None, model=None,
               log_request=False, log_response=False,
               credentials_args=None, default_global_params=None,
               additional_http_headers=None, response_encoding=None):
    """Create a new fusiontables handle."""
    url = url or self.BASE_URL
    super(FusiontablesV1, self).__init__(
        url, credentials=credentials,
        get_credentials=get_credentials, http=http, model=model,
        log_request=log_request, log_response=log_response,
        credentials_args=credentials_args,
        default_global_params=default_global_params,
        additional_http_headers=additional_http_headers,
        response_encoding=response_encoding)
    self.column = self.ColumnService(self)
    self.query = self.QueryService(self)
    self.style = self.StyleService(self)
    self.table = self.TableService(self)
    self.task = self.TaskService(self)
    self.template = self.TemplateService(self)

  class ColumnService(base_api.BaseApiService):
    """Service class for the column resource."""

    _NAME = u'column'

    def __init__(self, client):
      super(FusiontablesV1.ColumnService, self).__init__(client)
      self._upload_configs = {
          }

    def Delete(self, request, global_params=None):
      r"""Deletes the column.

      Args:
        request: (FusiontablesColumnDeleteRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (FusiontablesColumnDeleteResponse) The response message.
      """
      config = self.GetMethodConfig('Delete')
      return self._RunMethod(
          config, request, global_params=global_params)

    Delete.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'DELETE',
        method_id=u'fusiontables.column.delete',
        ordered_params=[u'tableId', u'columnId'],
        path_params=[u'columnId', u'tableId'],
        query_params=[],
        relative_path=u'tables/{tableId}/columns/{columnId}',
        request_field='',
        request_type_name=u'FusiontablesColumnDeleteRequest',
        response_type_name=u'FusiontablesColumnDeleteResponse',
        supports_download=False,
    )

    def Get(self, request, global_params=None):
      r"""Retrieves a specific column by its id.

      Args:
        request: (FusiontablesColumnGetRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Column) The response message.
      """
      config = self.GetMethodConfig('Get')
      return self._RunMethod(
          config, request, global_params=global_params)

    Get.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'GET',
        method_id=u'fusiontables.column.get',
        ordered_params=[u'tableId', u'columnId'],
        path_params=[u'columnId', u'tableId'],
        query_params=[],
        relative_path=u'tables/{tableId}/columns/{columnId}',
        request_field='',
        request_type_name=u'FusiontablesColumnGetRequest',
        response_type_name=u'Column',
        supports_download=False,
    )

    def Insert(self, request, global_params=None):
      r"""Adds a new column to the table.

      Args:
        request: (FusiontablesColumnInsertRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Column) The response message.
      """
      config = self.GetMethodConfig('Insert')
      return self._RunMethod(
          config, request, global_params=global_params)

    Insert.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'POST',
        method_id=u'fusiontables.column.insert',
        ordered_params=[u'tableId'],
        path_params=[u'tableId'],
        query_params=[],
        relative_path=u'tables/{tableId}/columns',
        request_field=u'column',
        request_type_name=u'FusiontablesColumnInsertRequest',
        response_type_name=u'Column',
        supports_download=False,
    )

    def List(self, request, global_params=None):
      r"""Retrieves a list of columns.

      Args:
        request: (FusiontablesColumnListRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (ColumnList) The response message.
      """
      config = self.GetMethodConfig('List')
      return self._RunMethod(
          config, request, global_params=global_params)

    List.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'GET',
        method_id=u'fusiontables.column.list',
        ordered_params=[u'tableId'],
        path_params=[u'tableId'],
        query_params=[u'maxResults', u'pageToken'],
        relative_path=u'tables/{tableId}/columns',
        request_field='',
        request_type_name=u'FusiontablesColumnListRequest',
        response_type_name=u'ColumnList',
        supports_download=False,
    )

    def Patch(self, request, global_params=None):
      r"""Updates the name or type of an existing column. This method supports patch semantics.

      Args:
        request: (FusiontablesColumnPatchRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Column) The response message.
      """
      config = self.GetMethodConfig('Patch')
      return self._RunMethod(
          config, request, global_params=global_params)

    Patch.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'PATCH',
        method_id=u'fusiontables.column.patch',
        ordered_params=[u'tableId', u'columnId'],
        path_params=[u'columnId', u'tableId'],
        query_params=[],
        relative_path=u'tables/{tableId}/columns/{columnId}',
        request_field=u'column',
        request_type_name=u'FusiontablesColumnPatchRequest',
        response_type_name=u'Column',
        supports_download=False,
    )

    def Update(self, request, global_params=None):
      r"""Updates the name or type of an existing column.

      Args:
        request: (FusiontablesColumnUpdateRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Column) The response message.
      """
      config = self.GetMethodConfig('Update')
      return self._RunMethod(
          config, request, global_params=global_params)

    Update.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'PUT',
        method_id=u'fusiontables.column.update',
        ordered_params=[u'tableId', u'columnId'],
        path_params=[u'columnId', u'tableId'],
        query_params=[],
        relative_path=u'tables/{tableId}/columns/{columnId}',
        request_field=u'column',
        request_type_name=u'FusiontablesColumnUpdateRequest',
        response_type_name=u'Column',
        supports_download=False,
    )

  class QueryService(base_api.BaseApiService):
    """Service class for the query resource."""

    _NAME = u'query'

    def __init__(self, client):
      super(FusiontablesV1.QueryService, self).__init__(client)
      self._upload_configs = {
          }

    def Sql(self, request, global_params=None, download=None):
      r"""Executes an SQL SELECT/INSERT/UPDATE/DELETE/SHOW/DESCRIBE/CREATE statement.

      Args:
        request: (FusiontablesQuerySqlRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
        download: (Download, default: None) If present, download
            data from the request via this stream.
      Returns:
        (Sqlresponse) The response message.
      """
      config = self.GetMethodConfig('Sql')
      return self._RunMethod(
          config, request, global_params=global_params,
          download=download)

    Sql.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'POST',
        method_id=u'fusiontables.query.sql',
        ordered_params=[u'sql'],
        path_params=[],
        query_params=[u'hdrs', u'sql', u'typed'],
        relative_path=u'query',
        request_field='',
        request_type_name=u'FusiontablesQuerySqlRequest',
        response_type_name=u'Sqlresponse',
        supports_download=True,
    )

    def SqlGet(self, request, global_params=None, download=None):
      r"""Executes an SQL SELECT/SHOW/DESCRIBE statement.

      Args:
        request: (FusiontablesQuerySqlGetRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
        download: (Download, default: None) If present, download
            data from the request via this stream.
      Returns:
        (Sqlresponse) The response message.
      """
      config = self.GetMethodConfig('SqlGet')
      return self._RunMethod(
          config, request, global_params=global_params,
          download=download)

    SqlGet.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'GET',
        method_id=u'fusiontables.query.sqlGet',
        ordered_params=[u'sql'],
        path_params=[],
        query_params=[u'hdrs', u'sql', u'typed'],
        relative_path=u'query',
        request_field='',
        request_type_name=u'FusiontablesQuerySqlGetRequest',
        response_type_name=u'Sqlresponse',
        supports_download=True,
    )

  class StyleService(base_api.BaseApiService):
    """Service class for the style resource."""

    _NAME = u'style'

    def __init__(self, client):
      super(FusiontablesV1.StyleService, self).__init__(client)
      self._upload_configs = {
          }

    def Delete(self, request, global_params=None):
      r"""Deletes a style.

      Args:
        request: (FusiontablesStyleDeleteRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (FusiontablesStyleDeleteResponse) The response message.
      """
      config = self.GetMethodConfig('Delete')
      return self._RunMethod(
          config, request, global_params=global_params)

    Delete.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'DELETE',
        method_id=u'fusiontables.style.delete',
        ordered_params=[u'tableId', u'styleId'],
        path_params=[u'styleId', u'tableId'],
        query_params=[],
        relative_path=u'tables/{tableId}/styles/{styleId}',
        request_field='',
        request_type_name=u'FusiontablesStyleDeleteRequest',
        response_type_name=u'FusiontablesStyleDeleteResponse',
        supports_download=False,
    )

    def Get(self, request, global_params=None):
      r"""Gets a specific style.

      Args:
        request: (FusiontablesStyleGetRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (StyleSetting) The response message.
      """
      config = self.GetMethodConfig('Get')
      return self._RunMethod(
          config, request, global_params=global_params)

    Get.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'GET',
        method_id=u'fusiontables.style.get',
        ordered_params=[u'tableId', u'styleId'],
        path_params=[u'styleId', u'tableId'],
        query_params=[],
        relative_path=u'tables/{tableId}/styles/{styleId}',
        request_field='',
        request_type_name=u'FusiontablesStyleGetRequest',
        response_type_name=u'StyleSetting',
        supports_download=False,
    )

    def Insert(self, request, global_params=None):
      r"""Adds a new style for the table.

      Args:
        request: (StyleSetting) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (StyleSetting) The response message.
      """
      config = self.GetMethodConfig('Insert')
      return self._RunMethod(
          config, request, global_params=global_params)

    Insert.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'POST',
        method_id=u'fusiontables.style.insert',
        ordered_params=[u'tableId'],
        path_params=[u'tableId'],
        query_params=[],
        relative_path=u'tables/{tableId}/styles',
        request_field='<request>',
        request_type_name=u'StyleSetting',
        response_type_name=u'StyleSetting',
        supports_download=False,
    )

    def List(self, request, global_params=None):
      r"""Retrieves a list of styles.

      Args:
        request: (FusiontablesStyleListRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (StyleSettingList) The response message.
      """
      config = self.GetMethodConfig('List')
      return self._RunMethod(
          config, request, global_params=global_params)

    List.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'GET',
        method_id=u'fusiontables.style.list',
        ordered_params=[u'tableId'],
        path_params=[u'tableId'],
        query_params=[u'maxResults', u'pageToken'],
        relative_path=u'tables/{tableId}/styles',
        request_field='',
        request_type_name=u'FusiontablesStyleListRequest',
        response_type_name=u'StyleSettingList',
        supports_download=False,
    )

    def Patch(self, request, global_params=None):
      r"""Updates an existing style. This method supports patch semantics.

      Args:
        request: (StyleSetting) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (StyleSetting) The response message.
      """
      config = self.GetMethodConfig('Patch')
      return self._RunMethod(
          config, request, global_params=global_params)

    Patch.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'PATCH',
        method_id=u'fusiontables.style.patch',
        ordered_params=[u'tableId', u'styleId'],
        path_params=[u'styleId', u'tableId'],
        query_params=[],
        relative_path=u'tables/{tableId}/styles/{styleId}',
        request_field='<request>',
        request_type_name=u'StyleSetting',
        response_type_name=u'StyleSetting',
        supports_download=False,
    )

    def Update(self, request, global_params=None):
      r"""Updates an existing style.

      Args:
        request: (StyleSetting) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (StyleSetting) The response message.
      """
      config = self.GetMethodConfig('Update')
      return self._RunMethod(
          config, request, global_params=global_params)

    Update.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'PUT',
        method_id=u'fusiontables.style.update',
        ordered_params=[u'tableId', u'styleId'],
        path_params=[u'styleId', u'tableId'],
        query_params=[],
        relative_path=u'tables/{tableId}/styles/{styleId}',
        request_field='<request>',
        request_type_name=u'StyleSetting',
        response_type_name=u'StyleSetting',
        supports_download=False,
    )

  class TableService(base_api.BaseApiService):
    """Service class for the table resource."""

    _NAME = u'table'

    def __init__(self, client):
      super(FusiontablesV1.TableService, self).__init__(client)
      self._upload_configs = {
          'ImportRows': base_api.ApiUploadInfo(
              accept=['application/octet-stream'],
              max_size=262144000,
              resumable_multipart=True,
              resumable_path=u'/resumable/upload/fusiontables/v1/tables/{tableId}/import',
              simple_multipart=True,
              simple_path=u'/upload/fusiontables/v1/tables/{tableId}/import',
          ),
          'ImportTable': base_api.ApiUploadInfo(
              accept=['application/octet-stream'],
              max_size=262144000,
              resumable_multipart=True,
              resumable_path=u'/resumable/upload/fusiontables/v1/tables/import',
              simple_multipart=True,
              simple_path=u'/upload/fusiontables/v1/tables/import',
          ),
          }

    def Copy(self, request, global_params=None):
      r"""Copies a table.

      Args:
        request: (FusiontablesTableCopyRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Table) The response message.
      """
      config = self.GetMethodConfig('Copy')
      return self._RunMethod(
          config, request, global_params=global_params)

    Copy.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'POST',
        method_id=u'fusiontables.table.copy',
        ordered_params=[u'tableId'],
        path_params=[u'tableId'],
        query_params=[u'copyPresentation'],
        relative_path=u'tables/{tableId}/copy',
        request_field='',
        request_type_name=u'FusiontablesTableCopyRequest',
        response_type_name=u'Table',
        supports_download=False,
    )

    def Delete(self, request, global_params=None):
      r"""Deletes a table.

      Args:
        request: (FusiontablesTableDeleteRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (FusiontablesTableDeleteResponse) The response message.
      """
      config = self.GetMethodConfig('Delete')
      return self._RunMethod(
          config, request, global_params=global_params)

    Delete.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'DELETE',
        method_id=u'fusiontables.table.delete',
        ordered_params=[u'tableId'],
        path_params=[u'tableId'],
        query_params=[],
        relative_path=u'tables/{tableId}',
        request_field='',
        request_type_name=u'FusiontablesTableDeleteRequest',
        response_type_name=u'FusiontablesTableDeleteResponse',
        supports_download=False,
    )

    def Get(self, request, global_params=None):
      r"""Retrieves a specific table by its id.

      Args:
        request: (FusiontablesTableGetRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Table) The response message.
      """
      config = self.GetMethodConfig('Get')
      return self._RunMethod(
          config, request, global_params=global_params)

    Get.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'GET',
        method_id=u'fusiontables.table.get',
        ordered_params=[u'tableId'],
        path_params=[u'tableId'],
        query_params=[],
        relative_path=u'tables/{tableId}',
        request_field='',
        request_type_name=u'FusiontablesTableGetRequest',
        response_type_name=u'Table',
        supports_download=False,
    )

    def ImportRows(self, request, global_params=None, upload=None):
      r"""Import more rows into a table.

      Args:
        request: (FusiontablesTableImportRowsRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
        upload: (Upload, default: None) If present, upload
            this stream with the request.
      Returns:
        (Import) The response message.
      """
      config = self.GetMethodConfig('ImportRows')
      upload_config = self.GetUploadConfig('ImportRows')
      return self._RunMethod(
          config, request, global_params=global_params,
          upload=upload, upload_config=upload_config)

    ImportRows.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'POST',
        method_id=u'fusiontables.table.importRows',
        ordered_params=[u'tableId'],
        path_params=[u'tableId'],
        query_params=[u'delimiter', u'encoding', u'endLine', u'isStrict', u'startLine'],
        relative_path=u'tables/{tableId}/import',
        request_field='',
        request_type_name=u'FusiontablesTableImportRowsRequest',
        response_type_name=u'Import',
        supports_download=False,
    )

    def ImportTable(self, request, global_params=None, upload=None):
      r"""Import a new table.

      Args:
        request: (FusiontablesTableImportTableRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
        upload: (Upload, default: None) If present, upload
            this stream with the request.
      Returns:
        (Table) The response message.
      """
      config = self.GetMethodConfig('ImportTable')
      upload_config = self.GetUploadConfig('ImportTable')
      return self._RunMethod(
          config, request, global_params=global_params,
          upload=upload, upload_config=upload_config)

    ImportTable.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'POST',
        method_id=u'fusiontables.table.importTable',
        ordered_params=[u'name'],
        path_params=[],
        query_params=[u'delimiter', u'encoding', u'name'],
        relative_path=u'tables/import',
        request_field='',
        request_type_name=u'FusiontablesTableImportTableRequest',
        response_type_name=u'Table',
        supports_download=False,
    )

    def Insert(self, request, global_params=None):
      r"""Creates a new table.

      Args:
        request: (Table) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Table) The response message.
      """
      config = self.GetMethodConfig('Insert')
      return self._RunMethod(
          config, request, global_params=global_params)

    Insert.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'POST',
        method_id=u'fusiontables.table.insert',
        ordered_params=[],
        path_params=[],
        query_params=[],
        relative_path=u'tables',
        request_field='<request>',
        request_type_name=u'Table',
        response_type_name=u'Table',
        supports_download=False,
    )

    def List(self, request, global_params=None):
      r"""Retrieves a list of tables a user owns.

      Args:
        request: (FusiontablesTableListRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (TableList) The response message.
      """
      config = self.GetMethodConfig('List')
      return self._RunMethod(
          config, request, global_params=global_params)

    List.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'GET',
        method_id=u'fusiontables.table.list',
        ordered_params=[],
        path_params=[],
        query_params=[u'maxResults', u'pageToken'],
        relative_path=u'tables',
        request_field='',
        request_type_name=u'FusiontablesTableListRequest',
        response_type_name=u'TableList',
        supports_download=False,
    )

    def Patch(self, request, global_params=None):
      r"""Updates an existing table. Unless explicitly requested, only the name, description, and attribution will be updated. This method supports patch semantics.

      Args:
        request: (FusiontablesTablePatchRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Table) The response message.
      """
      config = self.GetMethodConfig('Patch')
      return self._RunMethod(
          config, request, global_params=global_params)

    Patch.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'PATCH',
        method_id=u'fusiontables.table.patch',
        ordered_params=[u'tableId'],
        path_params=[u'tableId'],
        query_params=[u'replaceViewDefinition'],
        relative_path=u'tables/{tableId}',
        request_field=u'table',
        request_type_name=u'FusiontablesTablePatchRequest',
        response_type_name=u'Table',
        supports_download=False,
    )

    def Update(self, request, global_params=None):
      r"""Updates an existing table. Unless explicitly requested, only the name, description, and attribution will be updated.

      Args:
        request: (FusiontablesTableUpdateRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Table) The response message.
      """
      config = self.GetMethodConfig('Update')
      return self._RunMethod(
          config, request, global_params=global_params)

    Update.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'PUT',
        method_id=u'fusiontables.table.update',
        ordered_params=[u'tableId'],
        path_params=[u'tableId'],
        query_params=[u'replaceViewDefinition'],
        relative_path=u'tables/{tableId}',
        request_field=u'table',
        request_type_name=u'FusiontablesTableUpdateRequest',
        response_type_name=u'Table',
        supports_download=False,
    )

  class TaskService(base_api.BaseApiService):
    """Service class for the task resource."""

    _NAME = u'task'

    def __init__(self, client):
      super(FusiontablesV1.TaskService, self).__init__(client)
      self._upload_configs = {
          }

    def Delete(self, request, global_params=None):
      r"""Deletes the task, unless already started.

      Args:
        request: (FusiontablesTaskDeleteRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (FusiontablesTaskDeleteResponse) The response message.
      """
      config = self.GetMethodConfig('Delete')
      return self._RunMethod(
          config, request, global_params=global_params)

    Delete.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'DELETE',
        method_id=u'fusiontables.task.delete',
        ordered_params=[u'tableId', u'taskId'],
        path_params=[u'tableId', u'taskId'],
        query_params=[],
        relative_path=u'tables/{tableId}/tasks/{taskId}',
        request_field='',
        request_type_name=u'FusiontablesTaskDeleteRequest',
        response_type_name=u'FusiontablesTaskDeleteResponse',
        supports_download=False,
    )

    def Get(self, request, global_params=None):
      r"""Retrieves a specific task by its id.

      Args:
        request: (FusiontablesTaskGetRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Task) The response message.
      """
      config = self.GetMethodConfig('Get')
      return self._RunMethod(
          config, request, global_params=global_params)

    Get.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'GET',
        method_id=u'fusiontables.task.get',
        ordered_params=[u'tableId', u'taskId'],
        path_params=[u'tableId', u'taskId'],
        query_params=[],
        relative_path=u'tables/{tableId}/tasks/{taskId}',
        request_field='',
        request_type_name=u'FusiontablesTaskGetRequest',
        response_type_name=u'Task',
        supports_download=False,
    )

    def List(self, request, global_params=None):
      r"""Retrieves a list of tasks.

      Args:
        request: (FusiontablesTaskListRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (TaskList) The response message.
      """
      config = self.GetMethodConfig('List')
      return self._RunMethod(
          config, request, global_params=global_params)

    List.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'GET',
        method_id=u'fusiontables.task.list',
        ordered_params=[u'tableId'],
        path_params=[u'tableId'],
        query_params=[u'maxResults', u'pageToken', u'startIndex'],
        relative_path=u'tables/{tableId}/tasks',
        request_field='',
        request_type_name=u'FusiontablesTaskListRequest',
        response_type_name=u'TaskList',
        supports_download=False,
    )

  class TemplateService(base_api.BaseApiService):
    """Service class for the template resource."""

    _NAME = u'template'

    def __init__(self, client):
      super(FusiontablesV1.TemplateService, self).__init__(client)
      self._upload_configs = {
          }

    def Delete(self, request, global_params=None):
      r"""Deletes a template.

      Args:
        request: (FusiontablesTemplateDeleteRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (FusiontablesTemplateDeleteResponse) The response message.
      """
      config = self.GetMethodConfig('Delete')
      return self._RunMethod(
          config, request, global_params=global_params)

    Delete.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'DELETE',
        method_id=u'fusiontables.template.delete',
        ordered_params=[u'tableId', u'templateId'],
        path_params=[u'tableId', u'templateId'],
        query_params=[],
        relative_path=u'tables/{tableId}/templates/{templateId}',
        request_field='',
        request_type_name=u'FusiontablesTemplateDeleteRequest',
        response_type_name=u'FusiontablesTemplateDeleteResponse',
        supports_download=False,
    )

    def Get(self, request, global_params=None):
      r"""Retrieves a specific template by its id.

      Args:
        request: (FusiontablesTemplateGetRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Template) The response message.
      """
      config = self.GetMethodConfig('Get')
      return self._RunMethod(
          config, request, global_params=global_params)

    Get.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'GET',
        method_id=u'fusiontables.template.get',
        ordered_params=[u'tableId', u'templateId'],
        path_params=[u'tableId', u'templateId'],
        query_params=[],
        relative_path=u'tables/{tableId}/templates/{templateId}',
        request_field='',
        request_type_name=u'FusiontablesTemplateGetRequest',
        response_type_name=u'Template',
        supports_download=False,
    )

    def Insert(self, request, global_params=None):
      r"""Creates a new template for the table.

      Args:
        request: (Template) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Template) The response message.
      """
      config = self.GetMethodConfig('Insert')
      return self._RunMethod(
          config, request, global_params=global_params)

    Insert.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'POST',
        method_id=u'fusiontables.template.insert',
        ordered_params=[u'tableId'],
        path_params=[u'tableId'],
        query_params=[],
        relative_path=u'tables/{tableId}/templates',
        request_field='<request>',
        request_type_name=u'Template',
        response_type_name=u'Template',
        supports_download=False,
    )

    def List(self, request, global_params=None):
      r"""Retrieves a list of templates.

      Args:
        request: (FusiontablesTemplateListRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (TemplateList) The response message.
      """
      config = self.GetMethodConfig('List')
      return self._RunMethod(
          config, request, global_params=global_params)

    List.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'GET',
        method_id=u'fusiontables.template.list',
        ordered_params=[u'tableId'],
        path_params=[u'tableId'],
        query_params=[u'maxResults', u'pageToken'],
        relative_path=u'tables/{tableId}/templates',
        request_field='',
        request_type_name=u'FusiontablesTemplateListRequest',
        response_type_name=u'TemplateList',
        supports_download=False,
    )

    def Patch(self, request, global_params=None):
      r"""Updates an existing template. This method supports patch semantics.

      Args:
        request: (Template) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Template) The response message.
      """
      config = self.GetMethodConfig('Patch')
      return self._RunMethod(
          config, request, global_params=global_params)

    Patch.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'PATCH',
        method_id=u'fusiontables.template.patch',
        ordered_params=[u'tableId', u'templateId'],
        path_params=[u'tableId', u'templateId'],
        query_params=[],
        relative_path=u'tables/{tableId}/templates/{templateId}',
        request_field='<request>',
        request_type_name=u'Template',
        response_type_name=u'Template',
        supports_download=False,
    )

    def Update(self, request, global_params=None):
      r"""Updates an existing template.

      Args:
        request: (Template) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Template) The response message.
      """
      config = self.GetMethodConfig('Update')
      return self._RunMethod(
          config, request, global_params=global_params)

    Update.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'PUT',
        method_id=u'fusiontables.template.update',
        ordered_params=[u'tableId', u'templateId'],
        path_params=[u'tableId', u'templateId'],
        query_params=[],
        relative_path=u'tables/{tableId}/templates/{templateId}',
        request_field='<request>',
        request_type_name=u'Template',
        response_type_name=u'Template',
        supports_download=False,
    )

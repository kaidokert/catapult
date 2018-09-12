import logging
from google.appengine.ext import deferred
from dashboard.models.graph_data import TestMetadata, Row
from dashboard.common import utils
from dashboard.common import datastore_hooks

def findro(bs):
  test = TestMetadata.query(
    TestMetadata.master_name==bs.master_name,
    TestMetadata.bot_name==bs.bot_name,
    TestMetadata.suite_name==bs.suite_name,
    TestMetadata.deprecated==False,
    TestMetadata.has_rows==True).get()
  if not test: return
  return Row.query(Row.parent_test==utils.OldStyleTestKey(test.key)).order(-Row.revision).get()

def revs(cursor=None):
  datastore_hooks.SetPrivilegedRequest()
  query = TestMetadata.query(TestMetadata.test_part1_name=='')
  botsuites, next_cursor, more = query.fetch_page(1000, start_cursor=cursor)
  for bs in botsuites:
    r = findro(bs)
    if r is None: continue
    nrs = {n: v for n, v in r.to_dict().iteritems() if n.startswith('r_') and v.isdigit()}
    if not nrs: continue
    logging.info('occam %s %d %r', utils.TestMetadataKey(r.parent_test).id(), r.revision, nrs)
  if next_cursor and more:
    deferred.defer(revs, next_cursor)

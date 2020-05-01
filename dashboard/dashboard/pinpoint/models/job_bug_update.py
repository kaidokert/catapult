# Copyright 2020 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Logic for posting Job updates to the issue tracker."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from dashboard import update_bug_with_results
from dashboard.common import utils
from dashboard.services import issue_tracker_service
from dashboard.models import histogram
from dashboard.pinpoint.models import job_state

from tracing.value.diagnostics import reserved_infos


_INFINITY = u'\u221e'
_RIGHT_ARROW = u'\u2192'
_ROUND_PUSHPIN = u'\U0001f4cd'


class DifferenceBugCommentBuilder(object):
  """Builder for bug comments about differences in a metric."""

  def __init__(self, metric):
    self._metric = metric
    self._differences = []

  def AddDifference(self, commit, values_a, values_b):
    """Add a difference (a commit where the metric changed significantly).

    Args:
      commit: a Commit.
      values_a: (list) result values for the prior commit.
      values_b: (list) result values for this commit.
    """
    commit_info = commit.AsDict()
    self._differences.append(_Difference(commit_info, values_a, values_b))

  def BuildComment(self, tags, url):
    commits_with_deltas = [
        (diff.MeanDelta(), diff._commit_info) for diff in self._differences
        if diff._values_a and diff._values_b]
    owner, sheriff, cc_list, roll_commit = _ComputePostOwnerSheriffCCList(commits_with_deltas)

    # TODO: return a namedtuple
    return (
        _FormatComment(self._differences, self._metric, sheriff, roll_commit, tags, url),
        owner, cc_list)

  def BugLabel(self):
    # TODO: return this from BuildComment instead
    return 'Pinpoint-Culprit-Found' if len(
        self._differences) == 1 else 'Pinpoint-Multiple-Culprits'

  def _GenerateCommitCacheKey(self):
    commit_cache_key = None
    if len(self._differences) == 1:
      commit_cache_key = update_bug_with_results._GetCommitHashCacheKey(
          self._differences[0]._commit_info.get('git_hash'))
    return commit_cache_key



# TODO: define with namedtuple
class _Difference(object):
  def __init__(self, commit_info, values_a, values_b):
    self._commit_info = commit_info
    self._values_a = values_a
    self._values_b = values_b

  def MeanDelta(self):
    return job_state.Mean(self._values_b) - job_state.Mean(self._values_a)

  def FormatForBug(self, metric):
    commit_info = self._commit_info
    values_a = self._values_a
    values_b = self._values_b

    subject = '<b>%s</b> by %s' % (commit_info['subject'], commit_info['author'])

    if values_a:
      mean_a = job_state.Mean(values_a)
      formatted_a = '%.4g' % mean_a
    else:
      mean_a = None
      formatted_a = 'No values'

    if values_b:
      mean_b = job_state.Mean(values_b)
      formatted_b = '%.4g' % mean_b
    else:
      mean_b = None
      formatted_b = 'No values'

    metric = '%s: ' % metric if metric else ''

    difference = '%s%s %s %s' % (metric, formatted_a, _RIGHT_ARROW, formatted_b)
    if values_a and values_b:
      difference += ' (%+.4g)' % (mean_b - mean_a)
      if mean_a:
        difference += ' (%+.4g%%)' % ((mean_b - mean_a) / mean_a * 100)
      else:
        difference += ' (+%s%%)' % _INFINITY

    return '\n'.join((subject, commit_info['url'], difference))


## def UpdatePostAndMergeDeferredOld(difference_details, commit_infos,
##                                commits_with_deltas, bug_id, tags, url):
##   """Finish creating a bug update and post it.
## 
##   Args:
##     difference_details: (list of str) textual descriptions of differences found
##         (basic commit metadata and change magnitude).
##     commit_infos: (list of dict) commit info dicts (in the same order as
##         difference_details, e.g. element 0 is the commit info for the commit in the
##         first difference).
##     commits_with_deltas: list of (mean_delta, commit_info) tuples in no particular
##         order.  May have fewer elements than difference_details (and commit_infos).
##     bug_id: Monorail issue ID.
##     tags: Job tags.
##     url: Job URL.
##   """
##   if not bug_id:
##     return
## 
##   commit_cache_key = _GenerateCommitCacheKey(commit_infos)
## 
##   # Bring it all together.
##   owner, sheriff, cc_list, roll_commit = _ComputePostOwnerSheriffCCList(commits_with_deltas)
##   comment = _FormatComment(difference_details, commit_infos, sheriff, roll_commit, tags, url)
##   issue_tracker = issue_tracker_service.IssueTrackerService(
##       utils.ServiceAccountHttp())
##   merge_details, cc_list = _ComputePostMergeDetails(issue_tracker,
##                                                     commit_cache_key, cc_list)
##   current_bug_status = _GetBugStatus(issue_tracker, bug_id)
##   if not current_bug_status:
##     return
## 
##   status = None
##   bug_owner = None
##   label = 'Pinpoint-Culprit-Found' if len(
##       difference_details) == 1 else 'Pinpoint-Multiple-Culprits'
## 
##   if current_bug_status in ['Untriaged', 'Unconfirmed', 'Available']:
##     # Set the bug status and owner if this bug is opened and unowned.
##     status = 'Assigned'
##     bug_owner = owner
## 
##   issue_tracker.AddBugComment(
##       bug_id,
##       comment,
##       status=status,
##       cc_list=sorted(cc_list),
##       owner=bug_owner,
##       labels=[label],
##       merge_issue=merge_details.get('id'))
##   update_bug_with_results.UpdateMergeIssue(commit_cache_key, merge_details,
##                                            bug_id)
## 

## def _GenerateCommitCacheKey(commit_infos):
##   commit_cache_key = None
##   if len(commit_infos) == 1:
##     commit_cache_key = update_bug_with_results._GetCommitHashCacheKey(
##         commit_infos[0].get('git_hash'))
##   return commit_cache_key


def _ComputePostOwnerSheriffCCList(commits_with_deltas):
  owner = None
  sheriff = None
  roll_commit = None
  cc_list = set()

  # First, we sort the list of commits by absolute change.
  ordered_commits_by_delta = [
      commit for _, commit in sorted(
          commits_with_deltas, key=lambda i: abs(i[0]), reverse=True)
  ]

  # We assign the issue to the author of the CL at the head of the ordered list.
  # Then we only CC the folks in the top two commits.
  for commit in ordered_commits_by_delta[:2]:
    if not owner:
      owner = commit['author']
    sheriff = utils.GetSheriffForAutorollCommit(owner, commit['message'])
    cc_list.add(commit['author'])
    if sheriff:
      owner = sheriff
      roll_commit = commit

  return owner, sheriff, cc_list, roll_commit


def _FormatComment(differences, metric, sheriff, roll_commit, tags, url):
  if len(differences) == 1:
    status = 'Found a significant difference after 1 commit.'
  else:
    status = ('Found significant differences after each of %d commits.' %
              len(differences))

  title = '<b>%s %s</b>' % (_ROUND_PUSHPIN, status)
  header = '\n'.join((title, url))
  body = '\n\n'.join(diff.FormatForBug(metric) for diff in differences)
  if sheriff:
    body += '\n\nAssigning to sheriff %s because "%s" is a roll.' % (
        sheriff, roll_commit['subject'])

  footer = ('Understanding performance regressions:\n'
            '  http://g.co/ChromePerformanceRegressions')

  if differences:
    footer += _FormatDocumentationUrls(tags)

  comment = '\n\n'.join((header, body, footer))
  return comment


def _ComputePostMergeDetails(issue_tracker, commit_cache_key, cc_list):
  merge_details = {}
  if commit_cache_key:
    merge_details = update_bug_with_results.GetMergeIssueDetails(
        issue_tracker, commit_cache_key)
    if merge_details['id']:
      cc_list = []
  return merge_details, cc_list


def _GetBugStatus(issue_tracker, bug_id):
  if not bug_id:
    return None

  issue_data = issue_tracker.GetIssue(bug_id)
  if not issue_data:
    return None

  return issue_data.get('status')


def _FormatDocumentationUrls(tags):
  if not tags:
    return ''

  # TODO(simonhatch): Tags isn't the best way to get at this, but wait until
  # we move this back into the dashboard so we have a better way of getting
  # at the test path.
  # crbug.com/876899
  test_path = tags.get('test_path')
  if not test_path:
    return ''

  test_suite = utils.TestKey('/'.join(test_path.split('/')[:3]))
  docs = histogram.SparseDiagnostic.GetMostRecentDataByNamesSync(
      test_suite, [reserved_infos.DOCUMENTATION_URLS.name])

  if not docs:
    return ''

  docs = docs[reserved_infos.DOCUMENTATION_URLS.name].get('values')
  footer = '\n\n%s:\n  %s' % (docs[0][0], docs[0][1])
  return footer


def UpdatePostAndMergeDeferred(comment_builder, bug_id, tags, url):
  if not bug_id:
    return
  commit_cache_key = comment_builder._GenerateCommitCacheKey()
  comment, owner, cc_list = comment_builder.BuildComment(tags, url)
  issue_tracker = issue_tracker_service.IssueTrackerService(
      utils.ServiceAccountHttp())
  merge_details, cc_list = _ComputePostMergeDetails(issue_tracker,
                                                    commit_cache_key, cc_list)
  current_bug_status = _GetBugStatus(issue_tracker, bug_id)
  if not current_bug_status:
    return

  status = None
  bug_owner = None
  label = comment_builder.BugLabel()

  if current_bug_status in ['Untriaged', 'Unconfirmed', 'Available']:
    # Set the bug status and owner if this bug is opened and unowned.
    status = 'Assigned'
    bug_owner = owner

  issue_tracker.AddBugComment(
      bug_id,
      comment,
      status=status,
      cc_list=sorted(cc_list),
      owner=bug_owner,
      labels=[label],
      merge_issue=merge_details.get('id'))
  update_bug_with_results.UpdateMergeIssue(commit_cache_key, merge_details,
                                           bug_id)

/**
 * @fileoverview UDF for Datastore Bulk Delete.
 *
 * Provides a function to limit upload token deletion to tokens older than 3
 * hours.
 *
 * https://cloud.google.com/dataflow/docs/guides/templates/provided-utilities#datastore-bulk-delete
 */

/* Pass through entities to delete, return null for entities to retain */
function expiredTokenFilter(inJson) {
  // JSON string for an entity looks like:
  // {"key":{"partitionId":{"projectId":"chromeperf"},
  //         "path":[{"kind":"Token","name":"2fbc3815-717c-46b5-9d3f-5c331dbb206f"}]},
  //  "properties":{"error_message":{"nullValue":null,"excludeFromIndexes":true},
  //                ...
  //                "update_time":{"timestampValue":"2020-09-23T10:36:27.725640Z"},...
  var tokenEntity = JSON.parse(inJson);

  // Timestamp values are in RFC3339 format, unless this is result came from a
  // projection query, in which case they are integers of microseconds (and it's
  // unclear if those integers are string-formatted or not).  So try to cope
  // with either format, in case the GQL this is deployed with changes.  See:
  // https://cloud.google.com/datastore/docs/concepts/entities#date_and_time
  var updateTimeStr = tokenEntity.properties.update_time.timestampValue;
  var updateTime;
  if (String(updateTimeStr).indexOf("T") == -1) {
    updateTime = new Date(parseInt(updateTimeStr) / 1000);
  } else {
    updateTime = new Date(updateTimeStr);
  }

  // Exclude tokens updated in the last 3 hours.
  var now = new Date();
  var threeHoursMs = 3 * 60 * 60 * 1000;
  var threeHoursAgo = new Date(now.getTime() - threeHoursMs);
  if (updateTime > threeHoursAgo) {
    return undefined;
  }

  // Return the rest (i.e. delete them).
  return inJson;
}

<!-- Copyright 2016 The Chromium Authors. All rights reserved.
     Use of this source code is governed by a BSD-style license that can be
     found in the LICENSE file.
-->

# HistogramSet JSON Format

This document assumes familiarity with the concepts introduced in
[how-to-write-metrics](/docs/how-to-write-metrics.md).

HistogramSet JSON is an object containing

 * `n`: String intern table: array of strings.
 * `d`: All diagnostics in all Histograms, both Histogram-diagnostics and
   sample-diagnostics, organized into nested objects like
   `{<type name>: {<diagnostic name>: {<identifier>: <value>}}}`
   Type names include
    * `Breakdown` values are dictionaries containing an optional string
      `colorScheme` and a dictionary mapping from string category names to
      number values.
    * `DateRange` represents a Range of Dates as unix timestamps in ms.
    * `GenericSet` values are arrays containing arbitrary untyped data.
    * `RelatedEventSet` values are arrays of dictionaries containing `stableId`,
      `title`, `start`, `duration` fields of trace Events.
    * `RelatedNameMap` values are dictionaries mapping short descriptive strings
      to indexes of Histogram names in the string intern table.
    * `Scalar` values are tuples containing a unit name and a number value.
      Scalar diagnostics should not be used by metrics because they cannot be
      merged.
 * `h`: Flat unordered array of all Histograms. Each Histogram is represented as
   an object like
    * `n`: The index of the Histogram's name in the HistogramSet's string intern
      table. This is the only required field.
    * `u`: The name of the unit is an underscore-separated string of 1 or 2 parts:
       * The required unit base name must be one of
         * ms
         * tsMs
         * n%
         * sizeInBytes
         * J
         * W
         * unitless
         * count
         * sigma
       * Optional improvement direction must be one of
         * biggerIsBetter
         * smallerIsBetter
    * `d`: A longer string description of the measurement.
    * `b`: Array that describes how to build bin boundaries.
      The first element must be a number that specifies the boundary between the
      underflow bin and the first central bin. Subsequent elements can be either
       * numbers specifying bin boundaries, or
       * arrays of 3 numbers that specify how to build sequences of bin boundaries:
          * The first of which is an enum:
             * 0 (LINEAR)
             * 1 (EXPONENTIAL)
          * The second number is the maximum bin boundary of the sequence.
          * The third and final number is the number of bin boundaries in the
            sequence.
      If `binBoundaries` is undefined, then the Histogram contains single bin whose
      range spans `-Number.MAX_VALUE` to `Number.MAX_VALUE`
    * `D`: Array of Diagnostic identifiers that is used to reconstruct a
      DiagnosticMap that pertains to the entire Histogram, allows metrics to
      help users diagnose regressions and other problems.
      This can reference shared Diagnostics by `guid`.
    * `v`: Array of sample values to support Mann-Whitney U hypothesis
      testing to determine the significance of the difference between two
      Histograms.
    * `maxNumSampleValues`: maximum number of sample values
      If undefined, defaults to allBins.length * 10.
    * `a`: The nan bin is represented as a tuple 
    * `nanDiagnostics`: an array of DiagnosticMaps for non-numeric samples
    * `running`: running statistics, an array of 7 numbers: count, max, meanlogs,
      mean, min, sum, variance
    * `B`: either an array of Bins or a dictionary mapping from index to Bin:
      A Bin is an array containing either 1 or 2 elements:
       * Required number bin count,
       * Optional array of sample DiagnosticMaps
    * `o`: Summary options is a dictionary mapping from option names `avg, geometricMean,
      std, count, sum, min, max, nans` to boolean flags. The special option
      `percentile` is an array of numbers between 0 and 1. This allows metrics to
      specify which summary statistics are interesting and should be displayed.

## Example

```javascript
{
  "n": [
    "memory:chrome:all_processes:all_components:effective_size",
  ],
  "d": {
    "DateRange": {
      "traceStart": {
        "20": [1545676485994],
      },
    },
    "GenericSet": {
      "stories": {
        "10": ["browse:news:cnn"],
      },
    },
    "RelatedEventSet": {
      "events": {
        "100": [
          {"stableId": "a.b.c", "title": "Title", "start": 0, "duration": 1},
        ],
      },
    },
  },
  "h": [
    {
      "n": 0,
      "u": "ms",
      "b": [0, [0, 100, 10]],
      "d": "total memory effective size",
      "D": [10, 20, 30],
      "v": [0, 1, 42, -999999999.99999, null],
      "a": [1, [100]],
      "r": [5, 42, 0, -1, -999, -900, 100],
      "B": {
        "0": [1],
        "1": [1],
      },
      "o": {
        "nans": true,
        "percentile": [0.5, 0.95, 0.99],
      },
    },
  ],
}
```

# Pinpoint Quests and Executions

A **Quest** is a description of work to do on a Change. For example, a Quest might say to kick off a build or test run, then check the result. When bound to a specific Change, an **Execution** is created.

Users wishing to spin up a version of Pinpoint might want to write their own set of Quests and Executions to integrate with their infrastructure or build system. The Quests and Executions must define the following methods.

## Quest

A **Quest** defines the following methods.

```python
def __str__(self)
```
Returns a short name to distinguish the Quest from other Quests in the same Job. E.g. "Build" and "Test".

```python
def Start(self, change, *args)
```
Returns an **Execution**, which is this Quest bound to a Change. `args` includes any arguments returned by the previous Execution's `Poll()` method. For example, the *Build* Execution might return the location of the build, which is then passed to the *Test* Execution to run a test on that build.

## Execution

`Quest.Start()` pulls in arguments from 3 sources to create the **Execution**:
* Arguments global to the Job that are used to create the Quest.
* The Change to bind the Execution to.
* Any `result_arguments` produced by the previous Execution.

With all this information, an Execution becomes a self-contained description of work to do. It defines the following methods.

```python
def _AsDict(self)
```
Returns a list of links and other debug information used to track the status of the Execution. Each entry of the list is a dict with the fields `key`, `value`, and `url`. Example:
```json
{
  "key": "Bot ID",
  "value": "build5-a4",
  "url": "https://chromium-swarm.appspot.com/bot?id=build5-a4",
}
```

```python
def _Poll(self)
```
Does all the work of the Execution. When the work is complete, it should call `self._Complete([result_values], [result_arguments])`. `result_values` contains any numeric results, like the value of a performance metric, and `result_arguments` is a dict containing any arguments to pass to the following Execution.

`_Poll()` can raise two kinds of Exceptions: Job-level Exceptions, which are fatal and cause the Job to fail; and Execution-level errors, which only cause that one Execution to fail. If something might pass at one commit and fail at another, it should be an Execution-level error. An Exception is Job-level if it inherits from `StandardError`, and Execution-level otherwise. This is so that things like `ImportError` and `SyntaxError` fail fast.

### Sharing information between Executions

Sometimes, a Quest's Executions don't want to run completely independently, but rather require some coordination between them. For example, maybe we want the first *Test* Execution to pick a device, and all following *Test* Executions to run on the same device. Any shared information can be stored on the Quest object and passed to the Executions via `Quest.Start()`.

# Commentary on the current state of Quest api usage
At request time, `pinpoint.handlers.new._GenerateQuests` will use the `quests` and/or `target` request parameters to choose concrete implementations from the following class hierarchy, to create an ordered list of one or more parameterized Quests to execute with a new `pinpoint.models.job.Job` entity:
- `quest.Quest`
  - `run_test.RunTest` "This is the only Quest/Execution where the Execution has a reference back to modify the Quest."
    - `run_instrumentation_test.RunInstrumentationTest` "Quest for running an Android instrumentation test in Swarming."
    - `run_browser_test.RunBrowserTest` "Quest for running a browser test in Swarming."
    - `run_webrtc_test.RunWebRtcTest` "Quest for running WebRTC perf tests in Swarming."
    - `run_performance_test.RunPerformanceTest` "Quest and Execution for running a performance test in Swarming."
      - `run_gtest.RunGTest` "Quest for running a GTest in Swarming."
      - `run_telemetry_test.RunTelemetryTest` "Quest for running a Telemetry benchmark in Swarming."
        - `run_lacros_telemetry_test.RunLacrosTelemetryTest` "Quest for running Lacros perf tests in Swarming."
        - `run_vr_telemetry_test.RunVrTelemetryTest` "Quest for running a VR Telemetry benchmark in Swarming."
        - `run_web_engine_telemetry_test.RunWebEngineTelemetryTest` "Quest for running Fuchsia perf tests in Swarming."
  - `find_isolate.FindIsolate`
  - `read_value.ReadValue`
  - `read_value.ReadHistogramsJsonValue` [deprecated]
  - `read_value.ReadGraphJsonValue` [deprecated]

[`pinpoint.handlers.new._GenerateQuests`](../../handlers/new.py) contains a lot of embedded knowledge about dependencies between the quest types, and how to map user-specified `target` values to sequences of `quest.Quest`s.  This logic is implemented with a block of nested condionals and a mix of named string sets and hard-coded, anonymous string literals.

Unrolling it all out into a mape of which quests get run in what order for the various `target`s, we get:

- `REGULAR_TELEMETRY_TESTS`:
  1. `quest_module.FindIsolate`
  1. `quest_module.RunTelemetryTest`
  1. `quest_module.ReadValue`
- `REGULAR_TELEMETRY_TESTS_WITH_FALLBACKS`:
  1. `quest_module.FindIsolate`
  1. `quest_module.RunTelemetryTest`
  1. `quest_module.ReadValue`
- `'performance_test_suite_eve' or 'performance_test_suite_octopus'` in `target`:
  1. `quest_module.FindIsolate`
  1. `quest_module.RunLacrosTelemetryTest`
  1. `quest_module.ReadValue`
- `'performance_web_engine_test_suite'` in `target`:
  1. `quest_module.FindIsolate`
  1. `quest_module.RunWebEngineTelemetryTest`
  1. `quest_module.ReadValue`
- `'vr_perf_tests'`:
  1. `quest_module.FindIsolate`
  1. `quest_module.RunVrTelemetryTest`
  1. `quest_module.ReadValue`
- `'browser_test' in target`:
  1. `quest_module.FindIsolate`
  1. `quest_module.RunBrowserTest`
  1. `quest_module.ReadValue`
- `'instrumentation_test' in target`:
  1. `quest_module.FindIsolate`
  1. `quest_module.RunInstrumentationTest`
  1. `quest_module.ReadValue`
- `'webrtc_perf_tests' in target`:
  1. `quest_module.FindIsolate`
  1. `quest_module.RunWebRtcTest`
  1. `quest_module.ReadValue`
- everything else:
  1. `quest_module.FindIsolate`
  1. `quest_module.RunGTest`
  1. `quest_module.ReadValue`

A distinct pattern should be obvious at this point. Always three quests and the fist and last quests are `quest_module.FindIsolate` and `quest_module.ReadValue`, respectively. The only real variaton between these cases is the middle quest, which always runs a test of some sort. 5 of the 9 different cases run a test via `quest_module.RunTelemetryTest` or one of its subclasses, so even that level of variation is perhaps overstated here.

Whatever benefits were originally intended with the general purpose Quest API, in practice they don't seem to have materialized. We have a general-pupose framework that is used in one specific way.

I would suggest that any refactoring or migration work involving the Quest API seriously consider starting from scratch instead of directly porting or transliterating the Quest API use cases.

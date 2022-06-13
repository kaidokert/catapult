load("@io_bazel_rules_appengine//appengine:py_appengine.bzl", "py_appengine_binary", "py_appengine_test")

filegroup(
    name = "pinpoint_srcs",
    srcs = glob(include = ["dashboard/*.py"]),
)

py_appengine_binary(
    name = "pinpoint_gae",
    srcs = ["dashboard/pinpoint/dispatcher.py"],
    configs = [
        "pinpoint.yaml",
    ],
)

py_binary(
    name = "pinpoint_bin",
    srcs = [":pinpoint_srcs"],
    main = "dispatcher.py",
    python_version = "PY2",
)

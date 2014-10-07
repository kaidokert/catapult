# Copyright (c) 2013 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

{
  'variables': {
    'tracing_css_files': [
      'trace_viewer/about_tracing/common.css',
      'trace_viewer/base/ui/common.css',
      'trace_viewer/base/ui/drag_handle.css',
      'trace_viewer/base/ui/info_bar.css',
      'trace_viewer/base/ui/line_chart.css',
      'trace_viewer/base/ui/list_view.css',
      'trace_viewer/base/ui/mouse_mode_selector.css',
      'trace_viewer/base/ui/pie_chart.css',
      'trace_viewer/base/ui/sortable_table.css',
      'trace_viewer/base/ui/sunburst_chart.css',
      'trace_viewer/base/ui/tool_button.css',
      'trace_viewer/cc/layer_picker.css',
      'trace_viewer/cc/layer_tree_host_impl_view.css',
      'trace_viewer/cc/layer_view.css',
      'trace_viewer/cc/picture_ops_chart_summary_view.css',
      'trace_viewer/cc/picture_ops_chart_view.css',
      'trace_viewer/cc/picture_ops_list_view.css',
      'trace_viewer/cc/picture_view.css',
      'trace_viewer/gpu/state_view.css',
      'trace_viewer/system_stats/system_stats_instance_track.css',
      'trace_viewer/system_stats/system_stats_snapshot_view.css',
      'trace_viewer/tcmalloc/heap_instance_track.css',
      'trace_viewer/tcmalloc/tcmalloc_instance_view.css',
      'trace_viewer/tcmalloc/tcmalloc_snapshot_view.css',
      'trace_viewer/tracing/analysis/analysis_link.css',
      'trace_viewer/tracing/analysis/analysis_results.css',
      'trace_viewer/tracing/analysis/default_object_view.css',
      'trace_viewer/tracing/analysis/generic_object_view.css',
      'trace_viewer/tracing/side_panel/timeline_view.css',
      'trace_viewer/tracing/timeline_track_view.css',
      'trace_viewer/tracing/timeline_view.css',
      'trace_viewer/tracing/tracks/counter_track.css',
      'trace_viewer/tracing/tracks/drawing_container.css',
      'trace_viewer/tracing/tracks/heading_track.css',
      'trace_viewer/tracing/tracks/object_instance_track.css',
      'trace_viewer/tracing/tracks/process_track_base.css',
      'trace_viewer/tracing/tracks/rect_track.css',
      'trace_viewer/tracing/tracks/ruler_track.css',
      'trace_viewer/tracing/tracks/spacing_track.css',
      'trace_viewer/tracing/tracks/thread_track.css',
      'trace_viewer/tracing/tracks/trace_model_track.css',
      'trace_viewer/tracing/tracks/track.css',
    ],
    'tracing_js_html_files': [
      'trace_viewer/about_tracing.html',
      'trace_viewer/about_tracing/features.html',
      'trace_viewer/about_tracing/inspector_connection.html',
      'trace_viewer/about_tracing/inspector_tracing_controller_client.html',
      'trace_viewer/about_tracing/profiling_view.html',
      'trace_viewer/about_tracing/record_and_capture_controller.html',
      'trace_viewer/about_tracing/record_selection_dialog.html',
      'trace_viewer/about_tracing/tracing_controller_client.html',
      'trace_viewer/about_tracing/xhr_based_tracing_controller_client.html',
      'trace_viewer/base.html',
      'trace_viewer/base/base64.html',
      'trace_viewer/base/bbox2.html',
      'trace_viewer/base/color.html',
      'trace_viewer/base/event_target.html',
      'trace_viewer/base/events.html',
      'trace_viewer/base/gl_matrix.html',
      'trace_viewer/base/guid.html',
      'trace_viewer/base/interval_tree.html',
      'trace_viewer/base/iteration_helpers.html',
      'trace_viewer/base/key_event_manager.html',
      'trace_viewer/base/measuring_stick.html',
      'trace_viewer/base/properties.html',
      'trace_viewer/base/quad.html',
      'trace_viewer/base/raf.html',
      'trace_viewer/base/range.html',
      'trace_viewer/base/rect.html',
      'trace_viewer/base/settings.html',
      'trace_viewer/base/sorted_array_utils.html',
      'trace_viewer/base/statistics.html',
      'trace_viewer/base/ui.html',
      'trace_viewer/base/ui/animation.html',
      'trace_viewer/base/ui/animation_controller.html',
      'trace_viewer/base/ui/camera.html',
      'trace_viewer/base/ui/chart_base.html',
      'trace_viewer/base/ui/color_scheme.html',
      'trace_viewer/base/ui/container_that_decorates_its_children.html',
      'trace_viewer/base/ui/d3.html',
      'trace_viewer/base/ui/dom_helpers.html',
      'trace_viewer/base/ui/drag_handle.html',
      'trace_viewer/base/ui/info_bar.html',
      'trace_viewer/base/ui/line_chart.html',
      'trace_viewer/base/ui/list_view.html',
      'trace_viewer/base/ui/mouse_mode_selector.html',
      'trace_viewer/base/ui/mouse_tracker.html',
      'trace_viewer/base/ui/overlay.html',
      'trace_viewer/base/ui/pie_chart.html',
      'trace_viewer/base/ui/quad_stack_view.html',
      'trace_viewer/base/ui/sortable_table.html',
      'trace_viewer/base/ui/sunburst_chart.html',
      'trace_viewer/base/utils.html',
      'trace_viewer/cc.html',
      "trace_viewer/cc/chrome_browser.html",
      'trace_viewer/cc/constants.html',
      'trace_viewer/cc/debug_colors.html',
      'trace_viewer/cc/layer_impl.html',
      'trace_viewer/cc/layer_picker.html',
      'trace_viewer/cc/layer_tree_host_impl.html',
      'trace_viewer/cc/layer_tree_host_impl_view.html',
      'trace_viewer/cc/layer_tree_impl.html',
      'trace_viewer/cc/layer_tree_quad_stack_view.html',
      'trace_viewer/cc/layer_view.html',
      'trace_viewer/cc/picture.html',
      'trace_viewer/cc/picture_as_image_data.html',
      'trace_viewer/cc/picture_debugger.html',
      'trace_viewer/cc/picture_ops_chart_summary_view.html',
      'trace_viewer/cc/picture_ops_chart_view.html',
      'trace_viewer/cc/picture_ops_list_view.html',
      'trace_viewer/cc/picture_view.html',
      'trace_viewer/cc/raster_task.html',
      'trace_viewer/cc/raster_task_selection.html',
      'trace_viewer/cc/raster_task_sub_view.html',
      'trace_viewer/cc/raster_task_sub_view_for_tasks_from_different_lthi.html',
      'trace_viewer/cc/raster_task_sub_view_for_tasks_from_same_lthi.html',
      'trace_viewer/cc/region.html',
      'trace_viewer/cc/render_pass.html',
      'trace_viewer/cc/selection.html',
      'trace_viewer/cc/tile.html',
      'trace_viewer/cc/tile_coverage_rect.html',
      'trace_viewer/cc/tile_view.html',
      'trace_viewer/cc/util.html',
      'trace_viewer/gpu.html',
      'trace_viewer/gpu/state.html',
      'trace_viewer/gpu/state_view.html',
      'trace_viewer/system_stats.html',
      'trace_viewer/system_stats/system_stats_instance_track.html',
      'trace_viewer/system_stats/system_stats_snapshot.html',
      'trace_viewer/system_stats/system_stats_snapshot_view.html',
      'trace_viewer/tcmalloc.html',
      'trace_viewer/tcmalloc/heap.html',
      'trace_viewer/tcmalloc/heap_instance_track.html',
      'trace_viewer/tcmalloc/tcmalloc_instance_view.html',
      'trace_viewer/tcmalloc/tcmalloc_snapshot_view.html',
      'trace_viewer/tracing/analysis/analysis_link.html',
      'trace_viewer/tracing/analysis/analysis_results.html',
      'trace_viewer/tracing/analysis/analysis_sub_view.html',
      'trace_viewer/tracing/analysis/analysis_view.html',
      'trace_viewer/tracing/analysis/analyze_counters.html',
      'trace_viewer/tracing/analysis/analyze_objects.html',
      'trace_viewer/tracing/analysis/analyze_samples.html',
      'trace_viewer/tracing/analysis/analyze_slices.html',
      'trace_viewer/tracing/analysis/cpu_slice_view.html',
      'trace_viewer/tracing/analysis/default_object_view.html',
      'trace_viewer/tracing/analysis/generic_object_view.html',
      'trace_viewer/tracing/analysis/object_instance_view.html',
      'trace_viewer/tracing/analysis/object_snapshot_view.html',
      'trace_viewer/tracing/analysis/slice_view.html',
      'trace_viewer/tracing/analysis/tab_view.html',
      'trace_viewer/tracing/analysis/thread_time_slice_view.html',
      'trace_viewer/tracing/analysis/util.html',
      'trace_viewer/tracing/color_scheme.html',
      'trace_viewer/tracing/constants.html',
      'trace_viewer/tracing/draw_helpers.html',
      'trace_viewer/tracing/elided_cache.html',
      'trace_viewer/tracing/fast_rect_renderer.html',
      'trace_viewer/tracing/filter.html',
      'trace_viewer/tracing/find_control.html',
      'trace_viewer/tracing/find_controller.html',
      'trace_viewer/tracing/importer.html',
      'trace_viewer/tracing/importer/etw/eventtrace_parser.html',
      'trace_viewer/tracing/importer/etw/parser.html',
      'trace_viewer/tracing/importer/etw/process_parser.html',
      'trace_viewer/tracing/importer/etw/thread_parser.html',
      'trace_viewer/tracing/importer/etw_importer.html',
      'trace_viewer/tracing/importer/gzip_importer.html',
      'trace_viewer/tracing/importer/importer.html',
      'trace_viewer/tracing/importer/jszip.html',
      'trace_viewer/tracing/importer/linux_perf/android_parser.html',
      'trace_viewer/tracing/importer/linux_perf/bus_parser.html',
      'trace_viewer/tracing/importer/linux_perf/clock_parser.html',
      'trace_viewer/tracing/importer/linux_perf/cpufreq_parser.html',
      'trace_viewer/tracing/importer/linux_perf/disk_parser.html',
      'trace_viewer/tracing/importer/linux_perf/drm_parser.html',
      'trace_viewer/tracing/importer/linux_perf/exynos_parser.html',
      'trace_viewer/tracing/importer/linux_perf/gesture_parser.html',
      'trace_viewer/tracing/importer/linux_perf/i915_parser.html',
      'trace_viewer/tracing/importer/linux_perf/kfunc_parser.html',
      'trace_viewer/tracing/importer/linux_perf/mali_parser.html',
      'trace_viewer/tracing/importer/linux_perf/parser.html',
      'trace_viewer/tracing/importer/linux_perf/power_parser.html',
      'trace_viewer/tracing/importer/linux_perf/sched_parser.html',
      'trace_viewer/tracing/importer/linux_perf/sync_parser.html',
      'trace_viewer/tracing/importer/linux_perf/workqueue_parser.html',
      'trace_viewer/tracing/importer/linux_perf_importer.html',
      'trace_viewer/tracing/importer/simple_line_reader.html',
      'trace_viewer/tracing/importer/task.html',
      'trace_viewer/tracing/importer/trace2html_importer.html',
      'trace_viewer/tracing/importer/trace_event_importer.html',
      'trace_viewer/tracing/importer/v8/codemap.html',
      'trace_viewer/tracing/importer/v8/log_reader.html',
      'trace_viewer/tracing/importer/v8/splaytree.html',
      'trace_viewer/tracing/importer/v8_log_importer.html',
      'trace_viewer/tracing/importer/zip_importer.html',
      'trace_viewer/tracing/selection.html',
      'trace_viewer/tracing/side_panel/input_latency.html',
      'trace_viewer/tracing/side_panel/sampling_summary.html',
      'trace_viewer/tracing/side_panel/time_summary.html',
      'trace_viewer/tracing/side_panel/timeline_view.html',
      'trace_viewer/tracing/timeline_display_transform.html',
      'trace_viewer/tracing/timeline_display_transform_animations.html',
      'trace_viewer/tracing/timeline_interest_range.html',
      'trace_viewer/tracing/timeline_track_view.html',
      'trace_viewer/tracing/timeline_view.html',
      'trace_viewer/tracing/timeline_viewport.html',
      'trace_viewer/tracing/timing_tool.html',
      'trace_viewer/tracing/trace_model.html',
      'trace_viewer/tracing/trace_model/async_slice.html',
      'trace_viewer/tracing/trace_model/async_slice_group.html',
      'trace_viewer/tracing/trace_model/counter.html',
      'trace_viewer/tracing/trace_model/counter_sample.html',
      'trace_viewer/tracing/trace_model/counter_series.html',
      'trace_viewer/tracing/trace_model/cpu.html',
      'trace_viewer/tracing/trace_model/event.html',
      'trace_viewer/tracing/trace_model/flow_event.html',
      'trace_viewer/tracing/trace_model/instant_event.html',
      'trace_viewer/tracing/trace_model/kernel.html',
      'trace_viewer/tracing/trace_model/object_collection.html',
      'trace_viewer/tracing/trace_model/object_instance.html',
      'trace_viewer/tracing/trace_model/object_snapshot.html',
      'trace_viewer/tracing/trace_model/process.html',
      'trace_viewer/tracing/trace_model/process_base.html',
      'trace_viewer/tracing/trace_model/sample.html',
      'trace_viewer/tracing/trace_model/slice.html',
      'trace_viewer/tracing/trace_model/slice_group.html',
      'trace_viewer/tracing/trace_model/stack_frame.html',
      'trace_viewer/tracing/trace_model/thread.html',
      'trace_viewer/tracing/trace_model/time_to_object_instance_map.html',
      'trace_viewer/tracing/trace_model/timed_event.html',
      'trace_viewer/tracing/trace_model_settings.html',
      'trace_viewer/tracing/tracks/async_slice_group_track.html',
      'trace_viewer/tracing/tracks/container_track.html',
      'trace_viewer/tracing/tracks/counter_track.html',
      'trace_viewer/tracing/tracks/cpu_track.html',
      'trace_viewer/tracing/tracks/drawing_container.html',
      'trace_viewer/tracing/tracks/heading_track.html',
      'trace_viewer/tracing/tracks/kernel_track.html',
      'trace_viewer/tracing/tracks/multi_row_track.html',
      'trace_viewer/tracing/tracks/object_instance_group_track.html',
      'trace_viewer/tracing/tracks/object_instance_track.html',
      'trace_viewer/tracing/tracks/process_track.html',
      'trace_viewer/tracing/tracks/process_track_base.html',
      'trace_viewer/tracing/tracks/rect_track.html',
      'trace_viewer/tracing/tracks/ruler_track.html',
      'trace_viewer/tracing/tracks/sample_track.html',
      'trace_viewer/tracing/tracks/slice_group_track.html',
      'trace_viewer/tracing/tracks/slice_track.html',
      'trace_viewer/tracing/tracks/spacing_track.html',
      'trace_viewer/tracing/tracks/stacked_bars_track.html',
      'trace_viewer/tracing/tracks/thread_track.html',
      'trace_viewer/tracing/tracks/trace_model_track.html',
      'trace_viewer/tracing/tracks/track.html',
    ],
    'tracing_img_files': [
      'trace_viewer/base/images/chrome-left.png',
      'trace_viewer/base/images/chrome-mid.png',
      'trace_viewer/base/images/chrome-right.png',
      'trace_viewer/base/images/ui-states.png',
      'trace_viewer/images/checkerboard.png',
      'trace_viewer/images/collapse.png',
      'trace_viewer/images/expand.png',
      'trace_viewer/images/input-event.png',
    ],
    'tracing_files': [
      '<@(tracing_css_files)',
      '<@(tracing_js_html_files)',
      '<@(tracing_img_files)',
    ],
  },
  'targets': [
    {
      'target_name': 'generate_about_tracing',
      'type': 'none',
      'actions': [
        {
          'action_name': 'generate_about_tracing',
          'script_name': 'trace_viewer/build/generate_about_tracing_contents',
          'inputs': [
            '<@(tracing_files)',
          ],
          'outputs': [
            '<(SHARED_INTERMEDIATE_DIR)/content/browser/tracing/about_tracing.js',
            '<(SHARED_INTERMEDIATE_DIR)/content/browser/tracing/about_tracing.html'
          ],
          'action': ['python', '<@(_script_name)',
                     '--outdir', '<(SHARED_INTERMEDIATE_DIR)/content/browser/tracing']
        }
      ]
    }
  ]
}

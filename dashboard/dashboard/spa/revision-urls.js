/* Copyright 2019 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  const REVISION_URLS = {
    r_android_base_version: {
      name: 'Android Base Version',
      url: 'https://googleplex-android.googlesource.com/platform/frameworks/base/+/{{R1}}..{{R2}}',
    },
    r_arc: {
      name: 'ARC Revision',
      url: 'https://chrome-internal.googlesource.com/arc/arc/+log/{{R1}}..{{R2}}',
    },
    r_cdm_git: {
      name: 'CDM Git Hash',
      url: 'https://chrome-internal.googlesource.com/cdm/src/+log/{{R1}}..{{R2}}',
    },
    r_cdm_version: {
      name: 'CDM Version',
      url: '',
    },
    r_chrome_version: {
      name: 'Chrome Version',
      url: 'https://omahaproxy.appspot.com/changelog?old_version={{R1}}&new_version={{R2}}',
    },
    r_chromium: {
      name: 'Chromium Git Hash',
      url: 'https://chromium.googlesource.com/chromium/src/+log/{{R1}}..{{R2}}',
    },
    r_chromium_commit_pos: {
      name: 'Chromium Commit Position',
      url: 'http://test-results.appspot.com/revision_range?start={{R1}}&end={{R2}}',
    },
    r_chromium_git: {
      name: 'Chromium Git Hash',
      url: 'https://chromium.googlesource.com/chromium/src/+log/{{R1}}..{{R2}}',
    },
    r_chromium_rev: {
      name: 'Chromium Git Hash',
      url: 'https://chromium.googlesource.com/chromium/src/+log/{{R1}}..{{R2}}',
    },
    r_clang_rev: {
      name: 'Clang Revision',
      url: 'http://llvm.org/viewvc/llvm-project?view=revision&revision={{R2}}#start={{R1}}',
    },
    r_clank: {
      name: 'Clank Apps Git Hash',
      url: 'https://chrome-internal.googlesource.com/clank/internal/apps/+log/{{R1}}..{{R2}}',
    },
    r_commit_pos: {
      name: 'Chromium Commit Position',
      url: 'http://test-results.appspot.com/revision_range?start={{R1}}&end={{R2}}&n=1000',
    },
    r_cros_version: {
      name: 'ChromeOS Version',
      url: '',  // TODO find a non-corp server
    },
    r_deps: {
      name: 'Clank Deps Git Hash',
      url: 'https://chrome-internal.googlesource.com/clank/internal/deps/+log/{{R1}}..{{R2}}',
    },
    r_fuchsia_garnet_git: {
      name: 'Garnet Git Hash',
      url: 'https://fuchsia.googlesource.com/garnet/src/+log/{{R1}}..{{R2}}',
    },
    r_fuchsia_peridot_git: {
      name: 'Peridot Git Hash',
      url: 'https://fuchsia.googlesource.com/peridot/src/+log/{{R1}}..{{R2}}',
    },
    r_fuchsia_topaz_git: {
      name: 'Topaz Git Hash',
      url: 'https://fuchsia.googlesource.com/topaz/src/+log/{{R1}}..{{R2}}',
    },
    r_fuchsia_zircon_git: {
      name: 'Zircon Git Hash',
      url: 'https://fuchsia.googlesource.com/zircon/src/+log/{{R1}}..{{R2}}',
    },
    r_infra_infra_git: {
      name: 'Infra/Infra Git Hash',
      url: 'https://chromium.googlesource.com/infra/infra/+log/{{R1}}..{{R2}}',
    },
    r_lbshell: {
      name: 'Leanback Shell Revision',
      url: 'https://lbshell-internal.googlesource.com/lbshell/+/{{R1}}..{{R2}}',
    },
    r_mojo: {
      name: 'Mojo Git Hash',
      url: 'https://chromium.googlesource.com/external/mojo/+log/{{R1}}..{{R2}}',
    },
    r_v8_git: {
      name: 'V8 Git Hash',
      url: 'https://chromium.googlesource.com/v8/v8/+log/{{R1}}..{{R2}}',
    },
    r_v8_js_comp_milestone: {
      name: 'Milestone',
      url: '',
    },
    r_v8_perf_git: {
      name: 'V8 Perf Git Hash',
      url: 'https://chrome-internal.googlesource.com/v8/v8-perf/+log/{{R1}}..{{R2}}',
    },
    r_v8_rev: {
      name: 'V8 Commit Position',
      url: 'https://chromium.googlesource.com/v8/v8/+log/{{R1}}..{{R2}}',
    },
    r_v8_revision: {
      name: 'V8 Git Hash',
      url: 'https://chromium.googlesource.com/v8/v8/+log/{{R1}}..{{R2}}',
    },
    r_webrtc_git: {
      name: 'WebRTC Git Hash',
      url: 'https://webrtc.googlesource.com/src/+log/{{R1}}..{{R2}}',
    },
    r_webrtc_rev: {
      name: 'WebRTC Git Hash',
      url: 'https://webrtc.googlesource.com/src/+log/{{R1}}..{{R2}}',
    },
    r_webrtc_subtree_git: {
      name: 'WebRTC Git Hash',
      url: 'https://webrtc.googlesource.com/src/webrtc/+log/{{R1}}..{{R2}}',
    },
  };

  function revisionUrl(rName, r1, r2) {
    const info = REVISION_URLS[rName];
    if (!info) return {};
    const url = info.url.replace('{{R1}}', r1 || r2).replace('{{R2}}', r2);
    return {name: info.name, url};
  }

  return {revisionUrl};
});

/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class CpLoading extends cp.ElementBase {
  }

  CpLoading.properties = {};

  cp.ElementBase.register(CpLoading);

  return {
    CpLoading,
  };
});

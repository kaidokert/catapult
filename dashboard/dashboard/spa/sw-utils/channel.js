/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

// Create a communication channel between clients and the service worker to
// allow for post-installation configuration. This is curretly used for
// retrieving Google Analytics tracking and client ids.
export const channel = new BroadcastChannel('service-worker');

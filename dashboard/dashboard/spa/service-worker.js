/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
self.addEventListener('fetch', async event => {
  // Skip cross-origin requests, like those for Google Analytics.
  if (!event.request.url.startsWith(self.location.origin)) return;

  const cachedResponse = await caches.match(event.request);
  if (cachedResponse) {
    event.respondWith(cachedResponse);
    return;
  }

  const responsePromise = fetch(event.request);
  const cachePromise = caches.open('api');
  const response = await reponsePromise;
  event.respondWith(response.clone());
  const cache = await cachePromise;
  cache.put(event.request, response);
});

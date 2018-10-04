/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

const path = require('path');

const {
  WEBPACK_OUTPUT_PATH: outputPath,
  WEBPACK_NODE_MODULES: nodeModules,
  WEBPACK_THIRD_PARTY: thirdParty,
} = process.env;

const UglifyJsPlugin = require(`${nodeModules}/uglifyjs-webpack-plugin`);
const terser = require(`${nodeModules}/terser`);
const terserPackage = require(`${nodeModules}/terser/package.json`);

const uglifier = new UglifyJsPlugin({
  minify(file, sourceMap) {
    const terserOptions = {};
    if (sourceMap) terserOptions.sourceMap = {content: sourceMap};
    return terser.minify(file, terserOptions);
  },

  cache: true,
  cacheKeys(defaultCacheKeys) {
    // Invalidate cache based on terser's version.
    return {...defaultCacheKeys, terser: terserPackage.version};
  },
  sourceMap: true,
});

module.exports = {
  entry: {
    'service-worker': path.resolve(__dirname, 'service-worker.js'),
  },
  output: {
    filename: '[name].js',
    sourceMapFilename: '[name].js.map',
    path: outputPath,
  },
  optimization: {
    minimizer: [uglifier],
  },
  resolve: {
    modules: [thirdParty],
    alias: {
      '/idb/idb.js': path.resolve(thirdParty, 'idb', 'idb.js'),
    },
  },
  resolveLoader: {
    modules: [nodeModules],
  },
  mode: 'production',
  devtool: 'source-map',
};

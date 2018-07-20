/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

const path = require('path');

const {
  WEBPACK_OUTPUT_PATH: outputPath,
  WEBPACK_NODE_MODULES: nodeModules,
} = process.env;

module.exports = {
  entry: {
    'service-worker': path.resolve(__dirname, 'service-worker.js'),
  },
  output: {
    filename: '[name].bundle.js',
    path: outputPath,
  },
  module: {
    rules: [{
      test: /\.js$/,
      exclude: /(node_modules|bower_components)/,
      use: {
        loader: 'babel-loader',
        options: {
          presets: [
            [path.resolve(nodeModules, '@babel/preset-env'), {
              exclude: ['transform-regenerator'],
              debug: true,
            }],
            path.resolve(nodeModules, 'babel-preset-minify'),
          ],
        },
      },
    }],
  },
  resolve: {
    modules: [nodeModules],
  },
  resolveLoader: {
    modules: [nodeModules],
  },
  mode: 'production',
};

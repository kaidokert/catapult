/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

const path = require('path');

process.env.CHROME_BIN = require('puppeteer').executablePath();

module.exports = function(config) {
  const isDebug = process.argv.some((arg) => arg === '--debug');
  const coverage = process.argv.some((arg) => arg === '--coverage');
  config.set({

    basePath: '',

    client: {
      mocha: {
        reporter: 'html',
        ui: 'tdd',
      },
    },

    mochaReporter: {
      showDiff: true,
    },

    frameworks: ['mocha', 'sinon'],

    // list of files / patterns to load in the browser
    files: [
      'static_src/test/setup.js',
      'static_src/test/index.js',
    ],

    exclude: [],

    // preprocess matching files before serving them to the browser
    // available preprocessors: https://npmjs.org/browse/keyword/karma-preprocessor
    preprocessors: {
      'tests.js': ['webpack', 'sourcemap'],
    },

    plugins: [
      'karma-chrome-launcher',
      'karma-coverage',
      'karma-mocha',
      'karma-sinon',
      'karma-sourcemap-loader',
      'karma-webpack',
    ],

    webpack: {
      // webpack configuration
      devtool: 'inline-source-map',
      mode: 'development',
      module: {
        rules: [
          {
            test: /\.js$/,
            loader: 'istanbul-instrumenter-loader',
            include: path.resolve('static_src/'),
            exclude: [/\.test.js$/],
            query: {esModules: true},
          },
        ],
      },
    },

    // test results reporter to use
    // possible values: 'dots', 'progress'
    // available reporters: https://npmjs.org/browse/keyword/karma-reporter
    reporters: ['progress'].concat(coverage ? ['coverage'] : []),

    // configure coverage reporter
    coverageReporter: {
      check: {
        global: {
          statements: 75,
          branches: 67,
          functions: 75,
          lines: 75,
        },
      },
      dir: 'coverage',
      reporters: [
        {type: 'lcovonly', subdir: '.'},
        {type: 'json', subdir: '.', file: 'coverage.json'},
        {type: 'html'},
        {type: 'text'},
      ],
    },

    // web server port
    port: 9876,

    // enable / disable colors in the output (reporters and logs)
    colors: true,

    logLevel: config.LOG_INFO,

    autoWatch: true,

    browsers: isDebug ? ['Chrome_latest'] : ['ChromeHeadless'],

    customLaunchers: {
      Chrome_latest: {
        base: 'Chrome',
        version: 'latest',
      },
    },

    // Continuous Integration mode
    // if true, Karma captures browsers, runs the tests and exits
    singleRun: isDebug ? false : true,

    // Concurrency level
    // how many browser should be started simultaneous
    concurrency: Infinity,
  });
};


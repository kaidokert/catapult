<!-- Copyright 2017 The Chromium Authors. All rights reserved.
     Use of this source code is governed by a BSD-style license that can be
     found in the LICENSE file.
-->

# Chromeperf Frontend Architecture

Documentation for users is at TODO

This document outlines the MVC architecture of the chromeperf.appspot.com v2.0
frontend.

TODO Polymer is, does, why

TODO Redux is, does, why
Reducers MUST NOT have side effects.
Reducers MUST NOT modify state.
Reducers MUST return a new object.
Reducers MAY copy properties from state.

TODO Polymer-Redux is, does, why
Action creators SHOULD contain all async code in the app.
Action creators MAY have side-effects.
Action creators MAY take any number of parameters.

TODO instance methods vs static methods

TODO ElementBase.statePathProperties
TODO ElementBase.getStateAtPath

TODO ElementBase.setStateAtPath/updateObjectAtPath
TODO ElementBase.actions.setStateAtPath/updateObjectAtPath
TODO ElementBase.statePathReducer/updatingReducer

/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  const fetchAuthorization = async() => {
    const user = gapi.auth2.getAuthInstance().currentUser.get();
    const response = await user.reloadAuthResponse();
    return {
      userEmail: user.getBasicProfile().getEmail(),
      expiration: response.expires_at,
      headers: {
        Authorization: response.token_type + ' ' + response.access_token,
      },
    };
  };

  class AuthorizationCache extends cp.CacheBase {
    computeCacheKey_() {
      return 'authorization';
    }

    get isInCache_() {
      const authResponse = this.rootState_[this.cacheKey_];
      if (authResponse === undefined) return false;
      return authResponse.expiration < new Date();
    }

    async readFromCache_() {
      return await this.rootState_[this.cacheKey_];
    }

    createRequest_() {
      return {response: fetchAuthorization()};
    }

    onStartRequest_(request) {
      this.dispatch_(cp.ElementBase.actions.updateObject('', {
        [this.cacheKey_]: request.response,
      }));
    }

    onFinishRequest_(response) {
      this.dispatch_(cp.ElementBase.actions.updateObject('', {
        [this.cacheKey_]: response,
      }));
    }
  }

  const readAuthorization = () => async(dispatch, getState) =>
    await new AuthorizationCache({}, dispatch, getState).read();

  const writeAuthorization = () => async(dispatch, getState) => {
    // TODO share code with fetchAuthorization
    const user = gapi.auth2.getAuthInstance().currentUser.get();
    const response = user.getAuthResponse();
    dispatch(cp.ElementBase.actions.updateObject('', {
      authorization: {
        userEmail: user.getBasicProfile().getEmail(),
        expiration: response.expires_at,
        headers: {
          Authorization: response.token_type + ' ' + response.access_token,
        },
      },
    }));
  };

  return {
    readAuthorization,
    writeAuthorization,
  };
});

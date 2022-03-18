// Copyright 2022 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

package main

import (
	"testing"

	"github.com/urfave/cli/v2"
)

func validateFlagArray(t *testing.T, methodName string, expectedFlags []string, actualFlags []cli.Flag) {
	if len(expectedFlags) != len(actualFlags) {
		t.Fatalf("Incorrect '%s' returned, expected:%d, actual:%d", methodName, len(expectedFlags), len(actualFlags))
	}
	for i, f := range actualFlags {
		actualFlagName := f.Names()[0]
		t.Logf("%s[%d] = %s", methodName, i, actualFlagName)
		if actualFlagName != expectedFlags[i] {
			t.Fatalf("Incorrect flag for '%s' in position %d. expected:%s, actual:%s", methodName, i, expectedFlags[i], actualFlagName)
		}
	}
}

func TestDefaultFlags(t *testing.T) {
	cfg := &Config{}
	expectedFlags := []string{"command", "host", "full_path", "decode_response_body"}
	validateFlagArray(t, "DefaultFlags", expectedFlags, cfg.DefaultFlags())
}

func TestTrimFlags(t *testing.T) {
	cfg := &Config{}
	expectedFlags := []string{"invert-match", "command", "host", "full_path", "decode_response_body"}
	validateFlagArray(t, "TrimFlags", expectedFlags, cfg.TrimFlags())
}

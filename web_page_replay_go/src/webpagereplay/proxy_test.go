// Copyright 2017 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

package webpagereplay

import (
	"bytes"
	"flag"
	"fmt"
	"io"
	"io/ioutil"
	"net/http"
	"net/http/httptest"
	"net/url"
	"os"
	"path/filepath"
	"reflect"
	"strconv"
	"strings"
	"testing"
	"time"
)

var (
	tmpdir    string
	nocleanup = flag.Bool("nocleanup", false, "If true, don't cleanup temp files on shutdown.")
)

func TestMain(m *testing.M) {
	flag.Parse()
	var err error
	tmpdir, err = ioutil.TempDir("", "webpagereplay_proxy_test")
	if err != nil {
		fmt.Fprintf(os.Stderr, "cannot make tempdir: %v", err)
		os.Exit(1)
	}
	ret := m.Run()
	if !*nocleanup {
		os.RemoveAll(tmpdir)
	}
	os.Exit(ret)
}

func TestDoNotSaveDeterministicJS(t *testing.T) {
	archiveFile := filepath.Join(tmpdir, "TestDoNotSaveDeterministicjs.json")
	originalBody := "<html><head></head><p>hello!</p></html>"
	origin := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, req *http.Request) {
		switch req.URL.Path {
		case "/":
			w.Header().Set("Cache-Control", "public, max-age=3600")
			w.Header().Set("Content-Type", "text/html")
			w.WriteHeader(http.StatusOK)
			fmt.Fprint(w, originalBody)
		default:
			w.WriteHeader(http.StatusOK)
			fmt.Fprint(w, "default response")
		}
	}))
	defer origin.Close()

	// Start a proxy for the origin server that will construct an archive file.
	recordArchive, err := OpenWritableArchive(archiveFile)
	if err != nil {
		t.Fatalf("OpenWritableArchive: %v", err)
	}
	now := time.Now().AddDate(0, 0, -1).Unix() * 1000
	replacements := map[string]string{"{{WPR_TIME_SEED_TIMESTAMP}}": strconv.FormatInt(now, 10)}

	si, err := NewScriptInjectorFromFile("../../deterministic.js", replacements)
	if err != nil {
		t.Fatalf("failed to create script injector: %v", err)
	}
	transformers := []ResponseTransformer{si}
	recordServer := httptest.NewServer(NewRecordingProxy(recordArchive, "http", transformers))
	recordTransport := &http.Transport{
		Proxy: func(*http.Request) (*url.URL, error) {
			return url.Parse(recordServer.URL)
		},
	}

	u := origin.URL + "/"
	req := httptest.NewRequest("GET", u, nil)
	resp, err := recordTransport.RoundTrip(req)
	if err != nil {
		t.Fatalf("unexpected error : %v", err)
	}
	defer resp.Body.Close()
	body, err := ioutil.ReadAll(resp.Body)
	fmt.Printf("body: %s", string(body))
	if err != nil {
		t.Fatalf("unexpected error : %v", err)
	}
	// Shutdown and flush the archive.
	recordServer.Close()
	if err := recordArchive.Close(); err != nil {
		t.Fatalf("CloseArchive: %v", err)
	}
	// Open a replay server using the saved archive.
	replayArchive, err := OpenArchive(archiveFile)
	if err != nil {
		t.Fatalf("OpenArchive: %v", err)
	}
	_, recordedResp, _, err := replayArchive.FindRequest(req)
	if err != nil {
		t.Fatalf("unexpected error : %v", err)
	}
	defer recordedResp.Body.Close()
	recordedBody, err := ioutil.ReadAll(recordedResp.Body)
	if err != nil {
		t.Fatalf("unexpected error : %v", err)
	}
	if got, want := string(recordedBody), originalBody; got != want {
		t.Errorf("response doesn't match:\n%q\n%q", got, want)
	}
	if reflect.DeepEqual(body, recordedBody) {
		t.Fatal("served response body and recorded response body should not be equal")
	}
}

func TestEndToEnd(t *testing.T) {
	archiveFile := filepath.Join(tmpdir, "TestEndToEnd.json")

	// We will record responses from this server.
	origin := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, req *http.Request) {
		switch req.URL.Path {
		case "/img":
			w.Header().Set("Cache-Control", "public, max-age=3600")
			w.Header().Set("Content-Type", "image/webp")
			w.WriteHeader(http.StatusOK)
			fmt.Fprint(w, "fake image body")
		case "/206":
			w.Header().Set("Content-Type", "text/plain")
			w.Header().Set("Content-Length", "4")
			w.WriteHeader(http.StatusPartialContent)
			fmt.Fprint(w, "body")
		case "/post":
			w.Header().Set("Cache-Control", "private")
			w.Header().Set("Content-Type", "text/plain")
			w.WriteHeader(http.StatusOK)
			io.Copy(w, req.Body)
		default:
			w.WriteHeader(http.StatusOK)
			fmt.Fprint(w, "default response")
		}
	}))
	defer origin.Close()

	// Start a proxy for the origin server that will construct an archive file.
	recordArchive, err := OpenWritableArchive(archiveFile)
	if err != nil {
		t.Fatalf("OpenWritableArchive: %v", err)
	}
	var transformers []ResponseTransformer
	recordServer := httptest.NewServer(NewRecordingProxy(recordArchive, "http", transformers))
	recordTransport := &http.Transport{
		Proxy: func(*http.Request) (*url.URL, error) {
			return url.Parse(recordServer.URL)
		},
	}

	// Send a bunch of URLs to the server and record the responses.
	urls := []string{
		origin.URL + "/img",
		origin.URL + "/206",
		origin.URL + "/post",
	}
	type RecordedResponse struct {
		Code   int
		Header http.Header
		Body   string
	}
	recordResponse := func(u string, tr *http.Transport) (*RecordedResponse, error) {
		var req *http.Request
		var err error
		if strings.HasSuffix(u, "/post") {
			req, err = http.NewRequest("POST", u, strings.NewReader("this is the POST body"))
		} else {
			req, err = http.NewRequest("GET", u, nil)
		}
		if err != nil {
			return nil, fmt.Errorf("NewRequest(%s): %v", u, err)
		}
		resp, err := tr.RoundTrip(req)
		if err != nil {
			return nil, fmt.Errorf("RoundTrip(%s): %v", u, err)
		}
		defer resp.Body.Close()
		body, err := ioutil.ReadAll(resp.Body)
		if err != nil {
			return nil, fmt.Errorf("ReadBody(%s): %v", u, err)
		}
		return &RecordedResponse{resp.StatusCode, resp.Header, string(body)}, nil
	}
	recorded := make(map[string]*RecordedResponse)
	for _, u := range urls {
		resp, err := recordResponse(u, recordTransport)
		if err != nil {
			t.Fatal(err)
		}
		recorded[u] = resp
	}

	// Shutdown and flush the archive.
	recordServer.Close()
	if err := recordArchive.Close(); err != nil {
		t.Fatalf("CloseArchive: %v", err)
	}
	recordArchive = nil
	recordServer = nil
	recordTransport = nil

	// Open a replay server using the saved archive.
	replayArchive, err := OpenArchive(archiveFile)
	if err != nil {
		t.Fatalf("OpenArchive: %v", err)
	}
	replayServer := httptest.NewServer(NewReplayingProxy(replayArchive, "http", transformers, false))
	replayTransport := &http.Transport{
		Proxy: func(*http.Request) (*url.URL, error) {
			return url.Parse(replayServer.URL)
		},
	}

	// Re-send the same URLs and ensure we get the same response.
	for _, u := range urls {
		resp, err := recordResponse(u, replayTransport)
		if err != nil {
			t.Fatal(err)
		}
		if got, want := resp, recorded[u]; !reflect.DeepEqual(got, want) {
			t.Errorf("response doesn't match for %v:\n%+v\n%+v", u, got, want)
		}
	}
	// Check that a URL not found in the archive returns 404.
	resp, err := recordResponse(origin.URL+"/not_found_in_archive", replayTransport)
	if err != nil {
		t.Fatal(err)
	}
	if got, want := resp.Code, http.StatusNotFound; got != want {
		t.Errorf("status code for /not_found_in_archive: got: %v want: %v", got, want)
	}
}

func TestUpdateDates(t *testing.T) {
	const (
		oldDate         = "Thu, 17 Aug 2017 12:00:00 GMT"
		oldLastModified = "Thu, 17 Aug 2017 09:00:00 GMT"
		oldExpires      = "Thu, 17 Aug 2017 17:00:00 GMT"
		newDate         = "Fri, 17 Aug 2018 12:00:00 GMT"
		newLastModified = "Fri, 17 Aug 2018 09:00:00 GMT"
		newExpires      = "Fri, 17 Aug 2018 17:00:00 GMT"
	)
	now, err := http.ParseTime(newDate)
	if err != nil {
		t.Fatal(err)
	}

	responseHeader := http.Header{
		"Date":          {oldDate},
		"Last-Modified": {oldLastModified},
		"Expires":       {oldExpires},
	}
	updateDates(responseHeader, now)

	wantHeader := http.Header{
		"Date":          {newDate},
		"Last-Modified": {newLastModified},
		"Expires":       {newExpires},
	}
	// Check if dates are updated as expected.
	if !reflect.DeepEqual(responseHeader, wantHeader) {
		t.Errorf("got: %v\nwant: %v\n", responseHeader, wantHeader)
	}
}

type BytesTime struct {
	bytes []byte
	time  uint32
}
type ResponseTimingTestcase struct {
	url          string
	bytesAndTime []BytesTime
}

func testEndToEndResponseTiming(t *testing.T, testcase ResponseTimingTestcase) {
	archiveFile := filepath.Join(tmpdir, "TestRecordSlowResponseTime.json")

	timingApproximatelyEqual := func(a uint32, b uint32) bool {
		const responseTimeTolerance = uint32(20)
		if a > b {
			return a-b <= responseTimeTolerance
		} else {
			return b-a <= responseTimeTolerance
		}
	}

	// We will record responses from this server.
	origin := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, req *http.Request) {
		if testcase.url == req.URL.Path {
			// Simulate writing the testcase response from the server.
			didWriteHeader := false
			for i, bytesAndTime := range testcase.bytesAndTime {
				time.Sleep(time.Duration(bytesAndTime.time) * time.Millisecond)
				if !didWriteHeader {
					w.WriteHeader(http.StatusOK)
					didWriteHeader = true
				}
				w.Write(bytesAndTime.bytes)
				var isLastRequest = i == len(testcase.bytesAndTime)-1
				// Explicitly flush the output after each chunk of bytes except for the
				// last chunk, which will automatically be flushed, along with the EOF,
				// when this function returns. Not flushing before the last chunk lets
				// the EOF be returned along with the last chunk.
				if !isLastRequest {
					if f, ok := w.(http.Flusher); ok {
						f.Flush()
					}
				}
			}
			if !didWriteHeader {
				w.WriteHeader(http.StatusOK)
				didWriteHeader = true
			}
		} else {
			t.Fatalf("No testcase response available for url: %s", req.URL.Path)
		}
	}))
	defer origin.Close()

	// Start a proxy for the origin server that will construct an archive file.
	recordArchive, err := OpenWritableArchive(archiveFile)
	if err != nil {
		t.Fatalf("OpenWritableArchive: %v", err)
	}
	var transformers []ResponseTransformer
	recordServer := httptest.NewServer(NewRecordingProxy(recordArchive, "http", transformers))
	recordTransport := &http.Transport{
		Proxy: func(*http.Request) (*url.URL, error) {
			return url.Parse(recordServer.URL)
		},
	}

	recordResponse := func(u string, tr *http.Transport) ([]byte, error) {
		var req *http.Request
		var err error
		req, err = http.NewRequest("GET", u, nil)
		if err != nil {
			return nil, fmt.Errorf("NewRequest(%s): %v", u, err)
		}
		resp, err := tr.RoundTrip(req)
		if err != nil {
			return nil, fmt.Errorf("RoundTrip(%s): %v", u, err)
		}
		defer resp.Body.Close()
		var body []byte
		body, err = ioutil.ReadAll(resp.Body)
		if err != nil {
			return nil, fmt.Errorf("ReadBody(%s): %v", u, err)
		}
		return body, nil
	}
	_, err = recordResponse(origin.URL+testcase.url, recordTransport)
	if err != nil {
		t.Fatal(err)
	}

	// Shutdown and flush the archive.
	recordServer.Close()
	if err := recordArchive.Close(); err != nil {
		t.Fatalf("CloseArchive: %v", err)
	}

	// Verify that the archive has the expected request body and timing.
	req, _ := http.NewRequest("GET", origin.URL+testcase.url, nil)
	_, archiveResp, archiveRespTiming, err := recordArchive.FindRequest(req)
	if err != nil {
		t.Fatal(err)
	}
	if len(archiveRespTiming) != len(testcase.bytesAndTime) {
		t.Fatalf("expected %s record to have response count of %d, actual %d\n", testcase.url, len(testcase.bytesAndTime), len(archiveRespTiming))
	}
	expectedResponseBody := []byte{}
	for i, expectedBytesAndTime := range testcase.bytesAndTime {
		if !timingApproximatelyEqual(archiveRespTiming[i].Time, expectedBytesAndTime.time) {
			t.Fatalf("expected chunk %d of %s record to have timing %d, actual %d\n", i, testcase.url, expectedBytesAndTime.time, archiveRespTiming[i].Time)
		}
		expectedResponseBody = append(expectedResponseBody, expectedBytesAndTime.bytes...)
	}
	archiveBody, _ := io.ReadAll(archiveResp.Body)
	if !reflect.DeepEqual(archiveBody, expectedResponseBody) {
		t.Fatalf("expected replayed %s to have body %s, actual %s\n", testcase.url, expectedResponseBody, archiveBody)
	}

	recordArchive = nil
	recordServer = nil
	recordTransport = nil

	// Open a replay server using the saved archive.
	replayArchive, err := OpenArchive(archiveFile)
	if err != nil {
		t.Fatalf("OpenArchive: %v", err)
	}
	replayServer := httptest.NewServer(NewReplayingProxy(replayArchive, "http", transformers, false))
	replayTransport := &http.Transport{
		Proxy: func(*http.Request) (*url.URL, error) {
			return url.Parse(replayServer.URL)
		},
	}

	// Verify that the replayed response body and timing are correct.
	start := time.Now()
	replayedBody, err := recordResponse(origin.URL+testcase.url, replayTransport)
	if err != nil {
		t.Fatal(err)
	}
	replayedResponseTime := uint32(time.Since(start).Milliseconds())

	expectedResponseTime := uint32(0)
	expectedResponseBody = []byte{}
	for _, bytesAndTime := range testcase.bytesAndTime {
		expectedResponseTime = expectedResponseTime + bytesAndTime.time
		expectedResponseBody = append(expectedResponseBody, bytesAndTime.bytes...)
	}
	if !timingApproximatelyEqual(replayedResponseTime, expectedResponseTime) {
		t.Fatalf("expected replayed %s to have timing %d, actual %d\n", testcase.url, expectedResponseTime, replayedResponseTime)
	}
	if !reflect.DeepEqual(replayedBody, expectedResponseBody) {
		t.Fatalf("expected replayed %s to have body %s, actual %s\n", testcase.url, expectedResponseBody, replayedBody)
	}
}

func TestEndToEndResponseTiming(t *testing.T) {
	const slowResponseTimeMs = uint32(100)
	testcases := []ResponseTimingTestcase{
		{
			url: "/empty_slow",
			bytesAndTime: []BytesTime{
				BytesTime{bytes: []byte{}, time: slowResponseTimeMs},
			},
		},
		{
			url: "/fast_small",
			bytesAndTime: []BytesTime{
				BytesTime{bytes: []byte{'f'}, time: uint32(0)},
			},
		},
		{
			url: "/slow_small",
			bytesAndTime: []BytesTime{
				BytesTime{bytes: []byte{'s'}, time: slowResponseTimeMs},
			},
		},
		{
			url: "/fast_big",
			bytesAndTime: []BytesTime{
				BytesTime{bytes: bytes.Repeat([]byte{'f'}, recordingProxyChunkSize), time: uint32(0)},
			},
		},
		{
			url: "/slow_big",
			bytesAndTime: []BytesTime{
				BytesTime{bytes: bytes.Repeat([]byte{'s'}, recordingProxyChunkSize), time: slowResponseTimeMs},
			},
		},
		{
			url: "/slow_fast_slow",
			bytesAndTime: []BytesTime{
				BytesTime{bytes: bytes.Repeat([]byte{'s'}, recordingProxyChunkSize), time: slowResponseTimeMs},
				BytesTime{bytes: bytes.Repeat([]byte{'f'}, recordingProxyChunkSize), time: uint32(0)},
				BytesTime{bytes: bytes.Repeat([]byte{'s'}, recordingProxyChunkSize), time: slowResponseTimeMs},
			},
		},
		{
			url: "/fast_slow_fast",
			bytesAndTime: []BytesTime{
				BytesTime{bytes: bytes.Repeat([]byte{'f'}, recordingProxyChunkSize), time: uint32(0)},
				BytesTime{bytes: bytes.Repeat([]byte{'s'}, recordingProxyChunkSize), time: slowResponseTimeMs},
				BytesTime{bytes: bytes.Repeat([]byte{'f'}, recordingProxyChunkSize), time: uint32(0)},
			},
		},
	}
	for _, testcase := range testcases {
		testEndToEndResponseTiming(t, testcase)
	}
}

func roundTripWriteResponseWithTiming(t *testing.T, body []byte, responseTiming []SizeAndTime) {
	w := httptest.NewRecorder()
	var statusCode = 200
	writeResponseWithTiming(w, body, statusCode, responseTiming)
	resp := w.Result()
	actualBody, _ := io.ReadAll(resp.Body)

	if !bytes.Equal(actualBody, body) {
		t.Fatalf("expected body did not round trip. Expected %s, actual %s\n", body, actualBody)
	}
}

func TestWriteResponseWithTiming(t *testing.T) {
	roundTripWriteResponseWithTiming(t, []byte("hello"), []SizeAndTime{
		{Size: 3, Time: 1},
		{Size: 2, Time: 2},
	})

	// A transformer can shrink the body without updating the response timing.
	// Ensure that a body smaller than the expected timing still works.
	roundTripWriteResponseWithTiming(t, []byte("hello"), []SizeAndTime{
		{Size: 5, Time: 1},
		{Size: 2, Time: 2},
	})
	roundTripWriteResponseWithTiming(t, []byte("hello"), []SizeAndTime{
		{Size: 10, Time: 1},
		{Size: 2, Time: 2},
	})

	// A transformer can grow the body without updating the response timing.
	// Ensure that a body larger than the expected timing still works.
	roundTripWriteResponseWithTiming(t, []byte("hello"), []SizeAndTime{
		{Size: 1, Time: 1},
		{Size: 2, Time: 2},
	})
	roundTripWriteResponseWithTiming(t, []byte("hello"), []SizeAndTime{})
}

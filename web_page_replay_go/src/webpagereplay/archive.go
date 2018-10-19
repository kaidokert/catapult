// Copyright 2017 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

package webpagereplay

import (
	"bufio"
	"bytes"
	"compress/gzip"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"io/ioutil"
	"log"
	"net/http"
	"net/url"
	"os"
	"reflect"
	"strings"
	"sync"
)

const AutofillTypePredictionQuery = "https://clients1.google.com/tbproxy/af/query?"

var ErrNotFound = errors.New("not found")

// ArchivedRequest contains a single request and its response.
// Immutable after creation.
type ArchivedRequest struct {
	SerializedRequest	[]byte
	SerializedResponse []byte // if empty, the request failed
	Served bool
}

// RequestMatch represents a match when querying the archive for responses to a request
type RequestMatch struct {
	Match *ArchivedRequest
	Request *http.Request
	Response *http.Response
	MatchRatio float64
	Index int
}

func serializeRequest(req *http.Request, resp *http.Response) (*ArchivedRequest, error) {
	url := req.URL.String()
	ar := &ArchivedRequest{}
	{
		var buf bytes.Buffer
		if err := req.Write(&buf); err != nil {
			return nil, fmt.Errorf("failed writing request for %s: %v", url, err)
		}
		ar.SerializedRequest = buf.Bytes()
	}
	{
		var buf bytes.Buffer
		if err := resp.Write(&buf); err != nil {
			return nil, fmt.Errorf("failed writing response for %s: %v", url, err)
		}
		ar.SerializedResponse = buf.Bytes()
	}
	return ar, nil
}

func (ar *ArchivedRequest) unmarshal() (*http.Request, *http.Response, error) {
	req, err := http.ReadRequest(bufio.NewReader(bytes.NewReader(ar.SerializedRequest)))
	if err != nil {
		return nil, nil, fmt.Errorf("couldn't unmarshal request: %v", err)
	}
	resp, err := http.ReadResponse(bufio.NewReader(bytes.NewReader(ar.SerializedResponse)), req)
	if err != nil {
		if req.Body != nil {
			req.Body.Close()
		}
		return nil, nil, fmt.Errorf("couldn't unmarshal response: %v", err)
	}
	return req, resp, nil
}

// Archive contains an archive of requests. Immutable except when embedded in a WritableArchive.
// Fields are exported to enabled JSON encoding.
type Archive struct {
	// Requests maps host(url) => url => []request.
	// The two-level mapping makes it easier to search for similar requests.
	// There may be multiple requests for a given URL.
	Requests map[string]map[string][]*ArchivedRequest
	// Maps host string to DER encoded certs.
	Certs map[string][]byte
	// Maps host string to the negotiated protocol. eg. "http/1.1" or "h2"
	// If absent, will default to "http/1.1".
	NegotiatedProtocol map[string]string
	// The time seed that was used to initialize deterministic.js.
	DeterministicTimeSeedMs int64
	// Whether to prefer unserved matches over previously served matches.
	PreferUnservedMatches bool
}

func newArchive() Archive {
	return Archive{Requests: make(map[string]map[string][]*ArchivedRequest)}
}

// OpenArchive opens an archive file previously written by OpenWritableArchive.
func OpenArchive(path string) (*Archive, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, fmt.Errorf("could not open %s: %v", path, err)
	}
	defer f.Close()

	gz, err := gzip.NewReader(f)
	if err != nil {
		return nil, fmt.Errorf("gunzip failed: %v", err)
	}
	defer gz.Close()
	buf, err := ioutil.ReadAll(gz)
	if err != nil {
		return nil, fmt.Errorf("read failed: %v", err)
	}
	a := newArchive()
	if err := json.Unmarshal(buf, &a); err != nil {
		return nil, fmt.Errorf("json unmarshal failed: %v", err)
	}
	return &a, nil
}

// ForEach applies f to all requests in the archive.
func (a *Archive) ForEach(f func(req *http.Request, resp *http.Response)) {
	for _, urlmap := range a.Requests {
		for url, requests := range urlmap {
			for k, ar := range requests {
				req, resp, err := ar.unmarshal()
				if err != nil {
					log.Printf("Error unmarshaling request #%d for %s: %v", k, url, err)
					continue
				}
				f(req, resp)
			}
		}
	}
}

// Returns the der encoded cert and negotiated protocol.
func (a *Archive) FindHostTlsConfig(host string) ([]byte, string, error) {
	if cert, ok := a.Certs[host]; ok {
		return cert, a.findHostNegotiatedProtocol(host), nil
	}
	return nil, "", ErrNotFound
}

func (a *Archive) findHostNegotiatedProtocol(host string) string {
	if negotiatedProtocol, ok := a.NegotiatedProtocol[host]; ok {
		return negotiatedProtocol
	}
	return "http/1.1"
}

// FindRequest searches for the given request in the archive.
// Returns ErrNotFound if the request could not be found. Does not consume req.Body.
// TODO: conditional requests
func (a *Archive) FindRequest(req *http.Request, scheme string) (*http.Request, *http.Response, error) {
	hostMap := a.Requests[req.Host]
	if len(hostMap) == 0 {
		return nil, nil, ErrNotFound
	}

	// Exact match. Note that req may be relative, but hostMap keys are always absolute.
	u := *req.URL
	if u.Host == "" {
		u.Host = req.Host
		u.Scheme = scheme
	}
	reqUrl := u.String()

	if len(hostMap[reqUrl]) > 0 {
		return findBestMatchInArchivedRequestSet(req, hostMap[reqUrl])
	}

	// For all URLs with a matching path, pick the URL that has the most matching query parameters.
	// The match ratio is defined to be 2*M/T, where
	//   M = number of matches x where a.Query[x]=b.Query[x]
	//   T = sum(len(a.Query)) + sum(len(b.Query))
	aq := req.URL.Query()

	var bestURL string
	var bestRatio float64

	for ustr := range hostMap {
		u, err := url.Parse(ustr)
		if err != nil {
			continue
		}
		if u.Path != req.URL.Path {
			continue
		}
		bq := u.Query()
		m := 1
		t := len(aq) + len(bq)
		for k, v := range aq {
			if reflect.DeepEqual(v, bq[k]) {
				m++
			}
		}
		ratio := 2 * float64(m) / float64(t)
		if ratio > bestRatio ||
			// Map iteration order is non-deterministic, so we must break ties.
			(ratio == bestRatio && ustr < bestURL) {
			bestURL = ustr
			bestRatio = ratio
		}
	}

	if bestURL != "" {
		return findBestMatchInArchivedRequestSet(req, hostMap[bestURL])
	}

	return nil, nil, ErrNotFound
}

// Given an incoming request and a set of matches in the archive, identify the best match,
// based on request headers, request cookies, data and other information.
func findBestMatchInArchivedRequestSet(req *http.Request, archivedReqs []*ArchivedRequest) (*http.Request, *http.Response, error) {
	if len(archivedReqs) == 1 {
		archivedReq, archivedResp, err := archivedReqs[0].unmarshal()
		if err == nil {
			return archivedReq, archivedResp, err
		}
	} else if len(archivedReqs) > 0 {
		var bestMatch RequestMatch

		// There can be multiple requests with the same URL string. If that's the case,
		// break the tie by the number of headers that match, and in the case of a POST,
		// PUT or a PATCH request, also by the number of data entries that match.
		reqHeaders := req.Header
		reqCookies := req.Cookies()
		parseForm(req);

		for index, r := range archivedReqs {
			archivedReq, archivedResp, err := r.unmarshal()
			if err != nil {
				log.Println("Error unmarshaling request")
				continue
			}

			// Skip if the request methods does not match.
			if archivedReq.Method != req.Method {
				continue
			}

			matches := 1
			total := 1

			// Count the number of header matches
			archivedHeaders := archivedReq.Header
			total += len(reqHeaders) + len(archivedHeaders)
			for key, val := range archivedHeaders {
				if reflect.DeepEqual(val, reqHeaders[key]) {
					matches++
				}
			}

			// Count the number of cookie entry matches
			archivedCookies := archivedReq.Cookies()
			total += len(reqCookies) + len(archivedCookies)
			for _, cookie := range archivedCookies {
				val, err := req.Cookie(cookie.Name)
				if err == nil {
					// If both the archived request and the current request has the same cookie name,
					// increment the match score by 1.
					matches++
					// If both the archived request and the current request has the same cookie name
					// and the exact same cookie value, increment the match score by 2.
					if reflect.DeepEqual(val, cookie) {
						matches ++
					}
				}
			}

			// Count the number of data matches
			parseForm(archivedReq)
			total += len(archivedReq.PostForm) + len(req.PostForm)
			for key, val := range archivedReq.PostForm {
				if reflect.DeepEqual(val, req.PostForm[key]) {
					matches++
				}
			}

			ratio := 2 * float64(matches) / float64(total)
			if ratio > bestMatch.MatchRatio {
				bestMatch.Match = r
				bestMatch.Request = archivedReq
				bestMatch.Response = archivedResp
				bestMatch.MatchRatio = ratio
				bestMatch.Index = index
			}
		}
		return bestMatch.Request, bestMatch.Response, nil
	}
	return nil, nil, ErrNotFound
}

func parseForm(r *http.Request) {
	r.ParseForm()
	method := strings.ToUpper(r.Method)
	// Custom parser. Golang's http.Request class's ParseForm function can only handle
	// a limited set of data content types. The following section implement a number of
	// customize parsers for custom data content types
	if len(r.PostForm) == 0 && method == "POST" {
		// Limit the amount of data to read to 2 MB.
		maxFormSize := int64(2 << 20)
		switch ct := r.Header.Get("Content-Type"); ct {
		// Some sites, notably Gap, Banana Republic and Old Navy, issue post requests
		// in plain text using the new-line character as a delimiter.
		case "text/plain":
			var reader io.Reader = io.LimitReader(r.Body, maxFormSize + 1)
			b, e := ioutil.ReadAll(reader)
			if e != nil {
				return
			}
			r.PostForm, e = url.ParseQuery(strings.Replace(string(b), "\n", "&", -1))
			break
		// All else failing, insert a single entry with the entire POST text.
		default:
			var reader io.Reader = io.LimitReader(r.Body, maxFormSize + 1)
			b, e := ioutil.ReadAll(reader)
			if e != nil {
				return
			}
			r.PostForm["raw"] = append(r.PostForm["raw"], string(b))
		}
	}
}

func (a *Archive) addArchivedRequest(scheme string, req *http.Request, resp *http.Response) error {
	ar, err := serializeRequest(req, resp)
	if err != nil {
		return err
	}
	if a.Requests[req.Host] == nil {
		a.Requests[req.Host] = make(map[string][]*ArchivedRequest)
	}
	// Always use the absolute URL in this mapping.
	u := *req.URL
	if u.Host == "" {
		u.Host = req.Host
		u.Scheme = scheme
	}
	ustr := u.String()
	a.Requests[req.Host][ustr] = append(a.Requests[req.Host][ustr], ar)
	return nil
}

// Edit iterates over all requests in the archive. For each request, it calls f to
// edit the request. If f returns a nil pair, the request is deleted.
// The edited archive is returned, leaving the current archive is unchanged.
func (a *Archive) Edit(f func(req *http.Request, resp *http.Response) (*http.Request, *http.Response, error)) (*Archive, error) {
	clone := newArchive()
	for _, urlmap := range a.Requests {
		for ustr, requests := range urlmap {
			u, _ := url.Parse(ustr)
			for k, ar := range requests {
				oldReq, oldResp, err := ar.unmarshal()
				if err != nil {
					return nil, fmt.Errorf("Error unmarshaling request #%d for %s: %v", k, ustr, err)
				}
				newReq, newResp, err := f(oldReq, oldResp)
				if err != nil {
					return nil, err
				}
				if newReq == nil || newResp == nil {
					if newReq != nil || newResp != nil {
						panic("programming error: newReq/newResp must both be nil or non-nil")
					}
					continue
				}
				// TODO: allow changing scheme or protocol?
				if err := clone.addArchivedRequest(u.Scheme, newReq, newResp); err != nil {
					return nil, err
				}
			}
		}
	}
	return &clone, nil
}

// Serialize serializes this archive to the given writer.
func (a *Archive) Serialize(w io.Writer) error {
	gz := gzip.NewWriter(w)
	if err := json.NewEncoder(gz).Encode(a); err != nil {
		return fmt.Errorf("json marshal failed: %v", err)
	}
	return gz.Close()
}

// WriteableArchive wraps an Archive with writable methods for recording.
// The file is not flushed until Close is called. All methods are thread-safe.
type WritableArchive struct {
	Archive
	f  *os.File
	mu sync.Mutex
}

// OpenWritableArchive opens an archive file for writing.
// The output is gzipped JSON.
func OpenWritableArchive(path string) (*WritableArchive, error) {
	f, err := os.Create(path)
	if err != nil {
		return nil, fmt.Errorf("could not open %s: %v", path, err)
	}
	return &WritableArchive{Archive: newArchive(), f: f}, nil
}

// RecordRequest records a request/response pair in the archive.
func (a *WritableArchive) RecordRequest(scheme string, req *http.Request, resp *http.Response) error {
	a.mu.Lock()
	defer a.mu.Unlock()
	return a.addArchivedRequest(scheme, req, resp)
}

// RecordTlsConfig records the cert used and protocol negotiated for a host.
func (a *WritableArchive) RecordTlsConfig(host string, der_bytes []byte, negotiatedProtocol string) {
	a.mu.Lock()
	defer a.mu.Unlock()
	if a.Certs == nil {
		a.Certs = make(map[string][]byte)
	}
	if _, ok := a.Certs[host]; !ok {
		a.Certs[host] = der_bytes
	}
	if a.NegotiatedProtocol == nil {
		a.NegotiatedProtocol = make(map[string]string)
	}
	a.NegotiatedProtocol[host] = negotiatedProtocol
}

// Close flushes the the archive and closes the output file.
func (a *WritableArchive) Close() error {
	a.mu.Lock()
	defer a.mu.Unlock()
	defer func() { a.f = nil }()
	if a.f == nil {
		return errors.New("already closed")
	}

	if err := a.Serialize(a.f); err != nil {
		return err
	}
	return a.f.Close()
}

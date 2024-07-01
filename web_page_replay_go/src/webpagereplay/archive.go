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

var ErrNotFound = errors.New("not found")

var goodURLs = []string{
"https://globo.com/",
"https://www.globo.com/",
"https://fonts.googleapis.com/css2?family=Inter:wght@100..900&display=swap",
"https://securepubads.g.doubleclick.net/tag/js/gpt.js",
"https://s3.glbimg.com/v1/AUTH_da787d4f4e8d46e3ad76d5fa568fe786/profiling/profiling.min.js",
"https://s3.glbimg.com/v1/AUTH_acd8438fd650434baa93efc372c066a1/libs/lib-pub-relay/home/prod/lib-pub-relay-home-latest.js",
"https://s3.glbimg.com/v1/AUTH_b922f1376f6c452e9bb337cc7d996a6e/codex/foundation/typefaces/globotipo-ui-bold.woff2",
"https://s3.glbimg.com/v1/AUTH_b922f1376f6c452e9bb337cc7d996a6e/codex/foundation/typefaces/globotipo-ui-semibold.woff2",
"https://s3.glbimg.com/v1/AUTH_b922f1376f6c452e9bb337cc7d996a6e/codex/foundation/typefaces/globotipo-ui-regular.woff2",
"https://www.googletagmanager.com/gtag/js?id=AW-319734835",
"https://cdn.polyfill.io/v2/polyfill.min.js",
"https://www.googletagmanager.com/gtm.js?id=GTM-WQBMQ52",
"https://s3.glbimg.com/v1/AUTH_b002e0039b9f46a5a4a94ff667d31e2d/assets/dist/41986aef3515efd9448bb6050a18f4eb.css",
"https://aswpsdkus.com/notify/v1/ua-sdk.min.js",
"https://s3.glbimg.com/cdn/libs/tv4/1.3.0/tv4.min.js",
"https://fonts.gstatic.com/s/inter/v13/UcC73FwrK3iLTeHuS_fvQtMwCp50KnMa1ZL7W0Q5nw.woff2",
"https://securepubads.g.doubleclick.net/pagead/managed/js/gpt/m202404290101/pubads_impl.js?cb=31083203",
"https://s3.glbimg.com/v1/AUTH_e1b09a2d222b4900a437a46914be81e5/web/settings/stable/settings.min.js",
"https://s3.glbimg.com/v1/AUTH_89c6d9f49eec4e768bc6ccddcb31a34b/lgpd-lib/lgpd-lib.min.css",
"https://s3.glbimg.com/v1/AUTH_89c6d9f49eec4e768bc6ccddcb31a34b/lgpd-lib/lgpd-lib.min.js",
"https://s3.glbimg.com/v1/AUTH_05f06ca986b54d6e9c5df94927ccf7fc/libs/clappr-plugins/viewport-play/v1.1.4/viewport-play-plugin.js",
"https://s3.glbimg.com/v1/AUTH_b002e0039b9f46a5a4a94ff667d31e2d/assets/dist/2e17e7b259bbebc7d029878930dfd556.js",
"https://s3.glbimg.com/v1/AUTH_acd8438fd650434baa93efc372c066a1/home-globo-prod/lib-pub-core/lib-pub-core-home-globo-latest.js",
"https://horizon-schemas.globo.com/schemas",
"https://googleads.g.doubleclick.net/pagead/viewthroughconversion/319734835/?random=1714563959050&cv=11&fst=1714563959050&bg=ffffff&guid=ON&async=1&gtm=45be44t0v9181806107za200&gcd=13l3l3l3l1&dma=0&u_w=412&u_h=915&url=https%3A%2F%2Fwww.globo.com%2F&hn=www.googleadservices.com&frm=0&tiba=globo.com%20-%20Absolutamente%20tudo%20sobre%20not%C3%ADcias%2C%20esportes%20e%20entretenimento&npa=0&pscdl=noapi&auid=1636382539.1714563959&uaa=&uab=&uafvl=Not%252FA)Brand%3B8.0.0.0%7CChromium%3B126.0.6478.122%7CGoogle%2520Chrome%3B126.0.6478.122&uamb=1&uam=&uap=Android&uapv=14.0.0&uaw=0&fdr=QA&data=event%3Dgtag.config&rfmt=3&fmt=4",
"https://www.googleadservices.com/pagead/conversion/319734835/?random=1714563959050&cv=11&fst=1714563959050&bg=ffffff&guid=ON&async=1&gtm=45be44t0v9181806107za200&gcd=13l3l3l3l1&dma=0&u_w=412&u_h=915&url=https%3A%2F%2Fwww.globo.com%2F&label=JyTBCPSm9N8DELOIu5gB&hn=www.googleadservices.com&frm=0&tiba=globo.com%20-%20Absolutamente%20tudo%20sobre%20not%C3%ADcias%2C%20esportes%20e%20entretenimento&npa=0&pscdl=noapi&auid=1636382539.1714563959&uaa=&uab=&uafvl=Not%252FA)Brand%3B8.0.0.0%7CChromium%3B126.0.6478.122%7CGoogle%2520Chrome%3B126.0.6478.122&uamb=1&uam=&uap=Android&uapv=14.0.0&uaw=0&fdr=QA&capi=1&data=event%3Dconversion&rfmt=3&fmt=4",
"https://www.googleadservices.com/pagead/conversion/319734835/?random=1714563959100&cv=11&fst=1714563959100&bg=ffffff&guid=ON&async=1&gtm=45be44t0v9181806107za200&gcd=13l3l3l3l1&dma=0&u_w=412&u_h=915&url=https%3A%2F%2Fwww.globo.com%2F&label=GV4wCKv-0fQCELOIu5gB&hn=www.googleadservices.com&frm=0&tiba=globo.com%20-%20Absolutamente%20tudo%20sobre%20not%C3%ADcias%2C%20esportes%20e%20entretenimento&gtm_ee=1&npa=0&pscdl=noapi&auid=1636382539.1714563959&uaa=&uab=&uafvl=Not%252FA)Brand%3B8.0.0.0%7CChromium%3B126.0.6478.122%7CGoogle%2520Chrome%3B126.0.6478.122&uamb=1&uam=&uap=Android&uapv=14.0.0&uaw=0&fdr=QA&capi=1&data=event%3Dconversion&rfmt=3&fmt=4",
"https://vitrine-bff.sales.globo.com/hero/recommendation?channel=W",
"data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0iI0NFRDFENyI+PHBhdGggZmlsbD0ibm9uZSIgZD0iTTAgMGgyNHYyNEgwVjB6Ii8+PHBhdGggZD0iTTguNTkgMTYuNTlMMTMuMTcgMTIgOC41OSA3LjQxIDEwIDZsNiA2LTYgNi0xLjQxLTEuNDF6Ii8+PC9zdmc+",
"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAAAXNSR0IArs4c6QAAAbVJREFUOBGtVD1Lw1AUzYvFKYtLEWtwV3+CWyluXYouWbqk/QGCP8J/kIRClyyWuIu4OXcUnRUpWVw6ldL0nOS+8FKjVfBC++6795xz39eNsr6xLMtUFEXHtm27hKxWqzff95+VUlkdRW0G4zjem8/n14j38dvfyM8wHzuOc+N53qeZqwgFQXCGZIJf0wTV+CliveFw+KRzpRBFsOxHbGlXJ38agV0A29ZiNsHcDobktyLkCDYRrpULyZlUtoOKD8AvSRJbSkzPOTaFa9lQ5vb6jGojATd0jtFDjGIU8STGAqb1qbHjuu4pHN6SaUfT6fRlMBjcdrvdV4jc0W+1WpfAXgGY70QIDrCTBiaHpoL4DRDiMAwtCjAGnyIxXHIqxrdmKleSf51Q/b2GlJ8JV8OVMC8+b+vLqvjqFRIK4A9gy1esDxstciFESw57gtg9Yh2j+AxFDmwA2DtjI8GqHSHo6vmZ1YiQNqZGfkbsHQT47EuTqubBUsxcCbGpcItrlAbsQXlRKm1xBNvTzVveGnsGFdusskWD6ZRY3WcMlE3LCe1fPiOFVPGPimo0Gp1glj/YbR+2NSFj3+g1K1ZnAAAAAElFTkSuQmCC",
"https://www.googletagmanager.com/gtm.js?id=GTM-T2WNWT2&l=dataLayer",
"https://www.googletagmanager.com/gtm.js?id=GTM-PFFQ4H9&l=dataLayer",
"https://www.googletagmanager.com/gtm.js?id=GTM-MGM2D7G&l=dataLayer",
"https://s3.glbimg.com/v1/AUTH_acd8438fd650434baa93efc372c066a1/libs/lib-pub-external-tags/home/prod/lib-pub-ext-tags-home-latest.js",
"https://sb.scorecardresearch.com/cs/6035227/beacon.js",
"https://globo-ab.globo.com/v2/selected-alternatives?experiments=player-isolated-experiment-02&skipImpressions=true",
"https://fundingchoicesmessages.google.com/i/21737107378?ers=3",
"https://api-content.personare.com.br/wp-json/personare/v1/daily-horoscope/horoscopoetc?cache=1&token=a15a195095b80527a38993295adaa8c6",
"https://ads.rubiconproject.com/prebid/11366_globocom.js",
"https://s3.glbimg.com/cdn/libs/publicidade/1.2.2/publicidade.css",
"https://horizon-track.globo.com/event/home-globo",
"https://s3.glbimg.com/v1/AUTH_3ed1877db4dd4c6b9b8f505e9d4fab03/globoid-js/v1.13.0/globoid-js.min.js?loading-agent=global-webdeps",
"https://s3.glbimg.com/v1/AUTH_448612afd5444aab9ff73ea54413fbd1/js/rec-lib.min.js?loading-agent=global-webdeps",
"https://cdn.ravenjs.com/3.19.1/raven.min.js?loading-agent=global-webdeps",
"https://s3.glbimg.com/v1/AUTH_da787d4f4e8d46e3ad76d5fa568fe786/globo-ab/3.4.0/globo-ab.min.js?loading-agent=global-webdeps",
"https://s3.glbimg.com/v1/AUTH_da787d4f4e8d46e3ad76d5fa568fe786/globo-ab/globo-ab-v2.min.js?loading-agent=global-webdeps",
"https://s3.glbimg.com/v1/AUTH_da787d4f4e8d46e3ad76d5fa568fe786/globo-ab/3.0/globo-ab.min.js?loading-agent=global-webdeps",
"https://s3.glbimg.com/v1/AUTH_448612afd5444aab9ff73ea54413fbd1/js/video-player-abstractor.umd.js?loading-agent=global-webdeps",
"https://sb.scorecardresearch.com/internal-cs/default/beacon-and.js",
"https://www.google.com/pagead/1p-user-list/319734835/?random=1714564046050&cv=11&fst=1714561200000&bg=ffffff&guid=ON&async=1&gtm=45be44t0v9181806107za200&gcd=13l3l3l3l1&dma=0&u_w=412&u_h=915&url=https%3A%2F%2Fwww.globo.com%2F&hn=www.googleadservices.com&frm=0&tiba=globo.com%20-%20Absolutamente%20tudo%20sobre%20not%C3%ADcias%2C%20esportes%20e%20entretenimento&npa=0&pscdl=noapi&auid=1636382539.1714564046&uaa=&uab=&uafvl=Not%252FA)Brand%3B8.0.0.0%7CChromium%3B126.0.6433.0%7CGoogle%2520Chrome%3B126.0.6433.0&uamb=1&uam=&uap=Android&uapv=14.0.0&uaw=0&fdr=QA&data=event%3Dgtag.config&rfmt=3&fmt=3&is_vtc=1&cid=CAQSGwB7FLtqFu4u_rVEey3Lcbuiiy4Pt3rI6ZfEFA&random=1885564751&rmt_tld=0&ipr=y",
"https://www.google.co.uk/pagead/1p-user-list/319734835/?random=1714564046050&cv=11&fst=1714561200000&bg=ffffff&guid=ON&async=1&gtm=45be44t0v9181806107za200&gcd=13l3l3l3l1&dma=0&u_w=412&u_h=915&url=https%3A%2F%2Fwww.globo.com%2F&hn=www.googleadservices.com&frm=0&tiba=globo.com%20-%20Absolutamente%20tudo%20sobre%20not%C3%ADcias%2C%20esportes%20e%20entretenimento&npa=0&pscdl=noapi&auid=1636382539.1714564046&uaa=&uab=&uafvl=Not%252FA)Brand%3B8.0.0.0%7CChromium%3B126.0.6433.0%7CGoogle%2520Chrome%3B126.0.6433.0&uamb=1&uam=&uap=Android&uapv=14.0.0&uaw=0&fdr=QA&data=event%3Dgtag.config&rfmt=3&fmt=3&is_vtc=1&cid=CAQSGwB7FLtqFu4u_rVEey3Lcbuiiy4Pt3rI6ZfEFA&random=1885564751&rmt_tld=1&ipr=y",
"https://googleads.g.doubleclick.net/pagead/viewthroughconversion/319734835/?random=1658954904&cv=11&fst=1714564046050&bg=ffffff&guid=ON&async=1&gtm=45be44t0v9181806107za200&gcd=13l3l3l3l1&dma=0&u_w=412&u_h=915&url=https%3A%2F%2Fwww.globo.com%2F&label=JyTBCPSm9N8DELOIu5gB&hn=www.googleadservices.com&frm=0&tiba=globo.com%20-%20Absolutamente%20tudo%20sobre%20not%C3%ADcias%2C%20esportes%20e%20entretenimento&npa=0&pscdl=noapi&auid=1636382539.1714564046&uaa=&uab=&uafvl=Not%252FA)Brand%3B8.0.0.0%7CChromium%3B126.0.6433.0%7CGoogle%2520Chrome%3B126.0.6433.0&uamb=1&uam=&uap=Android&uapv=14.0.0&uaw=0&fdr=QA&capi=1&data=event%3Dconversion&fmt=3&ct_cookie_present=false&sscte=1&crd=CJW3sQIIscGxAgiwwbECCLnBsQIImMGxAiIBAUABSidldmVudC1zb3VyY2U9bmF2aWdhdGlvbi1zb3VyY2UsIHRyaWdnZXJaAwoBAWIECgICAw&pscrd=COafjqTB9PmHhwEiEwjGxJrrsOyFAxUQXh0JHc4CBloyAggDMgIIBDICCAcyAggIMgIICTICCAoyAggCMgIICzoWaHR0cHM6Ly93d3cuZ2xvYm8uY29tLw",
"https://googleads.g.doubleclick.net/pagead/viewthroughconversion/319734835/?random=1743595238&cv=11&fst=1714564046100&bg=ffffff&guid=ON&async=1&gtm=45be44t0v9181806107za200&gcd=13l3l3l3l1&dma=0&u_w=412&u_h=915&url=https%3A%2F%2Fwww.globo.com%2F&label=GV4wCKv-0fQCELOIu5gB&hn=www.googleadservices.com&frm=0&tiba=globo.com%20-%20Absolutamente%20tudo%20sobre%20not%C3%ADcias%2C%20esportes%20e%20entretenimento&gtm_ee=1&npa=0&pscdl=noapi&auid=1636382539.1714564046&uaa=&uab=&uafvl=Not%252FA)Brand%3B8.0.0.0%7CChromium%3B126.0.6433.0%7CGoogle%2520Chrome%3B126.0.6433.0&uamb=1&uam=&uap=Android&uapv=14.0.0&uaw=0&fdr=QA&capi=1&data=event%3Dconversion&fmt=3&ct_cookie_present=false&sscte=1&crd=CJW3sQIIscGxAgiwwbECCLnBsQIImMGxAiIBAUABSid0cmlnZ2VyPW5hdmlnYXRpb24tc291cmNlLCBldmVudC1zb3VyY2VaAwoBAWIECgICAw&pscrd=CLfHuOSew4Sa5AEiEwjqwZrrsOyFAxUxRx0JHfgXBBgyAggDMgIIBDICCAcyAggIMgIICTICCAoyAggCMgIICzoWaHR0cHM6Ly93d3cuZ2xvYm8uY29tLw",
"https://tag.navdmp.com/tm13574.js",
"https://s3.glbimg.com/v1/AUTH_acd8438fd650434baa93efc372c066a1/libs/lib-double-verify/prod/lib-double-verify-latest.js",
"https://fundingchoicesmessages.google.com/i/pub-8380869337985741?ers=1",
"https://s3.glbimg.com/v1/AUTH_acd8438fd650434baa93efc372c066a1/libs/liveramp/ats/prod/lib-liveramp-ats-latest.js",
"https://www.google.com/pagead/1p-conversion/319734835/?random=1658954904&cv=11&fst=1714564046050&bg=ffffff&guid=ON&async=1&gtm=45be44t0v9181806107za200&gcd=13l3l3l3l1&dma=0&u_w=412&u_h=915&url=https%3A%2F%2Fwww.globo.com%2F&label=JyTBCPSm9N8DELOIu5gB&hn=www.googleadservices.com&frm=0&tiba=globo.com%20-%20Absolutamente%20tudo%20sobre%20not%C3%ADcias%2C%20esportes%20e%20entretenimento&npa=0&pscdl=noapi&auid=1636382539.1714564046&uaa=&uab=&uafvl=Not%252FA)Brand%3B8.0.0.0%7CChromium%3B126.0.6433.0%7CGoogle%2520Chrome%3B126.0.6433.0&uamb=1&uam=&uap=Android&uapv=14.0.0&uaw=0&fdr=QA&capi=1&data=event%3Dconversion&fmt=3&ct_cookie_present=false&sscte=1&crd=CJW3sQIIscGxAgiwwbECCLnBsQIImMGxAiIBAUABSidldmVudC1zb3VyY2U9bmF2aWdhdGlvbi1zb3VyY2UsIHRyaWdnZXJaAwoBAWIECgICAw&pscrd=COafjqTB9PmHhwEiEwjGxJrrsOyFAxUQXh0JHc4CBloyAggDMgIIBDICCAcyAggIMgIICTICCAoyAggCMgIICzoWaHR0cHM6Ly93d3cuZ2xvYm8uY29tLw&is_vtc=1&cid=CAQSKQB7FLtqueYGqpaJ34Yl31VYUGrFiSxjnyGf5DcNT4gj97-5FUM1Ihcq&random=3828476436",
"https://affiliates.video.globo.com/affiliates/info",
"https://s3.glbimg.com/v1/AUTH_da787d4f4e8d46e3ad76d5fa568fe786/dmp/dmp.min.js",
"https://horizon-track.globo.com/event/home-globo",
"https://www.google.com/pagead/1p-conversion/319734835/?random=1743595238&cv=11&fst=1714564046100&bg=ffffff&guid=ON&async=1&gtm=45be44t0v9181806107za200&gcd=13l3l3l3l1&dma=0&u_w=412&u_h=915&url=https%3A%2F%2Fwww.globo.com%2F&label=GV4wCKv-0fQCELOIu5gB&hn=www.googleadservices.com&frm=0&tiba=globo.com%20-%20Absolutamente%20tudo%20sobre%20not%C3%ADcias%2C%20esportes%20e%20entretenimento&gtm_ee=1&npa=0&pscdl=noapi&auid=1636382539.1714564046&uaa=&uab=&uafvl=Not%252FA)Brand%3B8.0.0.0%7CChromium%3B126.0.6433.0%7CGoogle%2520Chrome%3B126.0.6433.0&uamb=1&uam=&uap=Android&uapv=14.0.0&uaw=0&fdr=QA&capi=1&data=event%3Dconversion&fmt=3&ct_cookie_present=false&sscte=1&crd=CJW3sQIIscGxAgiwwbECCLnBsQIImMGxAiIBAUABSid0cmlnZ2VyPW5hdmlnYXRpb24tc291cmNlLCBldmVudC1zb3VyY2VaAwoBAWIECgICAw&pscrd=CLfHuOSew4Sa5AEiEwjqwZrrsOyFAxUxRx0JHfgXBBgyAggDMgIIBDICCAcyAggIMgIICTICCAoyAggCMgIICzoWaHR0cHM6Ly93d3cuZ2xvYm8uY29tLw&is_vtc=1&cid=CAQSKQB7FLtqDRHWHYSW5gpN5yKDZ8yM1bHER8Z2wVW4ODRDqFBOcWpR1saG&random=926542359",
"https://ab.g.globo/choose",
"https://www.google.co.uk/pagead/1p-conversion/319734835/?random=1658954904&cv=11&fst=1714564046050&bg=ffffff&guid=ON&async=1&gtm=45be44t0v9181806107za200&gcd=13l3l3l3l1&dma=0&u_w=412&u_h=915&url=https%3A%2F%2Fwww.globo.com%2F&label=JyTBCPSm9N8DELOIu5gB&hn=www.googleadservices.com&frm=0&tiba=globo.com%20-%20Absolutamente%20tudo%20sobre%20not%C3%ADcias%2C%20esportes%20e%20entretenimento&npa=0&pscdl=noapi&auid=1636382539.1714564046&uaa=&uab=&uafvl=Not%252FA)Brand%3B8.0.0.0%7CChromium%3B126.0.6433.0%7CGoogle%2520Chrome%3B126.0.6433.0&uamb=1&uam=&uap=Android&uapv=14.0.0&uaw=0&fdr=QA&capi=1&data=event%3Dconversion&fmt=3&ct_cookie_present=false&sscte=1&crd=CJW3sQIIscGxAgiwwbECCLnBsQIImMGxAiIBAUABSidldmVudC1zb3VyY2U9bmF2aWdhdGlvbi1zb3VyY2UsIHRyaWdnZXJaAwoBAWIECgICAw&pscrd=COafjqTB9PmHhwEiEwjGxJrrsOyFAxUQXh0JHc4CBloyAggDMgIIBDICCAcyAggIMgIICTICCAoyAggCMgIICzoWaHR0cHM6Ly93d3cuZ2xvYm8uY29tLw&is_vtc=1&cid=CAQSKQB7FLtqueYGqpaJ34Yl31VYUGrFiSxjnyGf5DcNT4gj97-5FUM1Ihcq&random=3828476436&ipr=y",
"https://www.google.co.uk/pagead/1p-conversion/319734835/?random=1743595238&cv=11&fst=1714564046100&bg=ffffff&guid=ON&async=1&gtm=45be44t0v9181806107za200&gcd=13l3l3l3l1&dma=0&u_w=412&u_h=915&url=https%3A%2F%2Fwww.globo.com%2F&label=GV4wCKv-0fQCELOIu5gB&hn=www.googleadservices.com&frm=0&tiba=globo.com%20-%20Absolutamente%20tudo%20sobre%20not%C3%ADcias%2C%20esportes%20e%20entretenimento&gtm_ee=1&npa=0&pscdl=noapi&auid=1636382539.1714564046&uaa=&uab=&uafvl=Not%252FA)Brand%3B8.0.0.0%7CChromium%3B126.0.6433.0%7CGoogle%2520Chrome%3B126.0.6433.0&uamb=1&uam=&uap=Android&uapv=14.0.0&uaw=0&fdr=QA&capi=1&data=event%3Dconversion&fmt=3&ct_cookie_present=false&sscte=1&crd=CJW3sQIIscGxAgiwwbECCLnBsQIImMGxAiIBAUABSid0cmlnZ2VyPW5hdmlnYXRpb24tc291cmNlLCBldmVudC1zb3VyY2VaAwoBAWIECgICAw&pscrd=CLfHuOSew4Sa5AEiEwjqwZrrsOyFAxUxRx0JHfgXBBgyAggDMgIIBDICCAcyAggIMgIICTICCAoyAggCMgIICzoWaHR0cHM6Ly93d3cuZ2xvYm8uY29tLw&is_vtc=1&cid=CAQSKQB7FLtqDRHWHYSW5gpN5yKDZ8yM1bHER8Z2wVW4ODRDqFBOcWpR1saG&random=926542359&ipr=y",
"https://globo-ab.globo.com/v2/selected-alternatives?skipImpressions=false&experiments=home-trending-top-globo",
"https://globo-mab.globo.com/mab/home-globo:prod:banner-home1-m:bottom-top:v2/choose",
"https://globo-mab.globo.com/mab/home-globo:prod:banner-home2-m:top-bottom:v2/choose",
"https://globo-mab.globo.com/mab/home-globo:prod:banner-home3-m:top-bottom:v4/choose",
"https://globo-mab.globo.com/mab/home-globo:prod:banner-home4-m:top-bottom:v4/choose",
"https://globo-mab.globo.com/mab/home-globo:prod:banner-home5-m:top-bottom:v4/choose",
"https://globo-mab.globo.com/mab/home-globo:prod:banner-home6-m:top-bottom:v4/choose",
"https://globo-mab.globo.com/mab/home-globo:prod:banner-home7-m:top-bottom:v4/choose",
"https://globo-mab.globo.com/mab/home-globo:prod:banner-home8-m:top-bottom:v4/choose",
"https://globo-mab.globo.com/mab/home-globo:prod:banner-home9-m:top-bottom:v4/choose",
"https://globo-mab.globo.com/mab/home-globo:prod:banner-home10-m:top-bottom:v4/choose",
"https://globo-ab.globo.com/v2/selected-alternatives?skipImpressions=true&experiments=home-globo-tp-bottom-v2",
"https://s3.glbimg.com/v1/AUTH_da787d4f4e8d46e3ad76d5fa568fe786/Delivery/lib-analytics%20(data%20loader)/lib-analytics.js",
"https://s3.glbimg.com/v1/AUTH_da787d4f4e8d46e3ad76d5fa568fe786/Delivery/libanalytics/prod/1.0.6/libanalytics.js",
"https://s.glbimg.com/bu/rt/js/glb-pv-min.js",
"https://sb.scorecardresearch.com/b?c1=2&c2=6035227&cs_it=m8&cv=4.0.0%2B2301240627&ns__t=1714563959550&ns_c=UTF-8&c7=https%3A%2F%2Fwww.globo.com%2F&c8=globo.com%20-%20Absolutamente%20tudo%20sobre%20not%C3%ADcias%2C%20esportes%20e%20entretenimento&c9=",
"https://fundingchoicesmessages.google.com/f/AGSKWxWAbLGKx_Lpp3X7miMCc3qWF3epvCnyLNWf67dyGIPQnNv5mRzRYbvfvEpFZm4yPcIUketZFyCAOLy6doNHB46e5gv4LgSZyxBfJTNTi0M0fTCT7PL6XE7OXNmSKeTLWX3nYJrirA==?fccs=W251bGwsbnVsbCxudWxsLG51bGwsbnVsbCxudWxsLFsxNzE0NTYzOTU5LDU1MDAwMDAwMF0sbnVsbCxudWxsLG51bGwsW251bGwsWzddXSwiaHR0cHM6Ly93d3cuZ2xvYm8uY29tLyIsbnVsbCxbWzgsInhrY1F6RkFsVWV3Il0sWzksImVuLVVTIl0sWzE5LCIxIl0sWzE3LCJbMF0iXV1d",
"https://s3.glbimg.com/v1/AUTH_e1b09a2d222b4900a437a46914be81e5/web/player/stable/player.min.js",
"https://pub.doubleverify.com/signals/pub.js#ctx=27566431&cmp=DV1036776",
"https://cdn.jsdelivr.net/gh/prebid/currency-file@1/latest.json?date=20240501",
"https://id.globo.com/auth/realms/globo.com/protocol/openid-connect/3p-cookies/step1.html",
"https://globo-mab.globo.com/mab/home-globo:prod:banner-home2-m:bottom-top:v2/choose",
"https://globo-mab.globo.com/mab/home-globo:prod:banner-home3-m:bottom-top:v4/choose",
"https://globo-mab.globo.com/mab/home-globo:prod:banner-home4-m:bottom-top:v4/choose",
"https://globo-mab.globo.com/mab/home-globo:prod:banner-home5-m:bottom-top:v4/choose",
"https://globo-mab.globo.com/mab/home-globo:prod:banner-home6-m:bottom-top:v4/choose",
"https://globo-mab.globo.com/mab/home-globo:prod:banner-home7-m:bottom-top:v4/choose",
"https://globo-mab.globo.com/mab/home-globo:prod:banner-home8-m:bottom-top:v4/choose",
"https://globo-mab.globo.com/mab/home-globo:prod:banner-home9-m:bottom-top:v4/choose",
"https://globo-mab.globo.com/mab/home-globo:prod:banner-home10-m:bottom-top:v4/choose",
"https://d39f98ec-9259-4f8b-896d-7ab58be1f900.edge.permutive.app/d39f98ec-9259-4f8b-896d-7ab58be1f900-web.js",
"https://usr.navdmp.com/usr?v=7&acc=13574&upd=1&new=1&wst=0&wct=1&wla=1&dsy=0&wni=1",
"https://cloud-products-jarvis.globo.com/graphql?operationName=getHighlightBroadcasts&variables=%7B%22affiliateCode%22%3A%22SP%22%7D&extensions=%7B%22persistedQuery%22%3A%7B%22version%22%3A1%2C%22sha256Hash%22%3A%221e9ab3f0bef05e3f14e7fcb7a632249fc94a835a15b39633e6edd7c369e9e353%22%7D%7D",
"https://usergate.globo.com/",
"https://securepubads.g.doubleclick.net/pagead/ppub_config",
"https://usergate.globo.com/",
"https://s3.glbimg.com/v1/AUTH_da787d4f4e8d46e3ad76d5fa568fe786/horizon-client/horizon-client-js.min.js",
"https://id.globo.com/auth/realms/globo.com/protocol/openid-connect/3p-cookies/step2.html",
"https://fonts.googleapis.com/css?family=Archivo:400,500|Arimo:400,500|Bitter:400,500|EB+Garamond:400,500|Lato|Libre+Baskervill|Libre+Franklin:400,500|Lora:400,500|Google+Sans:regular,medium:400,500|Material+Icons|Google+Symbols|Merriweather|Montserrat:400,500|Mukta:400,500|Muli:400,500|Nunito:400,500|Open+Sans:400,500,600|Open+Sans+Condensed:400,600|Oswald:500|Playfair+Display:400,500|Poppins:400,500|Raleway:400,500|Roboto:400,500|Roboto+Condensed:400,500|Roboto+Slab:400,500|Slabo+27px|Source+Sans+Pro|Ubuntu:400,500|Volkhov&display=swap",
"https://www.globo.com/manifest.json",
"https://pub.doubleverify.com/dvtag/signals/ids/pub.json?ctx=27566431&cmp=DV1036776&url=https%3A%2F%2Fglobo.com&ids=1&token=default",
"https://pub.doubleverify.com/dvtag/signals/bsc/pub.json?ctx=27566431&cmp=DV1036776&url=https%3A%2F%2Fglobo.com&bsc=1&abs=1&token=default",
"https://fonts.gstatic.com/s/opensans/v40/memvYaGs126MiZpBA-UvWbX2vVnXBbObj2OVTS-mu0SC55I.woff2",
"https://fonts.gstatic.com/s/materialicons/v142/flUhRq6tzZclQEJ-Vdg-IuiaDsNcIhQ8tQ.woff2",
"https://fundingchoicesmessages.google.com/el/AGSKWxUWBouH6yMIwWBucGxpZ_7_PAWo_9xGUN8TDR3xIBF7-C-PnkCjDzDf57BKMa0nuWVVSKTbudG0cuHDxsgiYcrmqCu6rFa3Aouge40rdYDLbKV4oB94sUy0xj9ClcJw627aqmAZnA==",
"https://imasdk.googleapis.com/js/sdkloader/ima3.js",
"https://cdn.navdmp.com/req?v=7&upd=1&new=1&id=1490e77c823214a515794811ad10&acc=13574&url=https%3A//www.globo.com/&tit=globo.com%20-%20Absolutamente%20tudo%20sobre%20not%EDcias%2C%20esportes%20e%20entretenimento",
"https://beacon.krxd.net/usermatch.gif?partner=navegg&partner_uid=1490e77c823214a515794811ad10",
"https://www.googletagmanager.com/gtag/js?id=G-P4F3TC8HVE&l=dataLayer&cx=c",
"https://www.googletagmanager.com/gtag/destination?id=AW-319734835&l=dataLayer&cx=c",
"https://www.google-analytics.com/analytics.js",
"https://sdk.mrf.io/statics/marfeel-sdk.js?id=3838",
"https://horizon.globo.com/auth-session/activity/home_2016/horizon-pageview?object=http%3A%2F%2Fwww.globo.com%2F&Referrer=&tags=portal&client_version=0.3.11",
"https://d39f98ec-9259-4f8b-896d-7ab58be1f900.prmutv.co/v2.0/pxid?k=cccecec5-8228-435e-81d1-33c4eccc78e6",
"https://ib.adnxs.com/getuidj",
"https://s3.glbimg.com/v1/AUTH_da787d4f4e8d46e3ad76d5fa568fe786/horizon-client/horizon-common-hit.js",
"https://id.globo.com/auth/realms/globo.com/protocol/openid-connect/auth?client_id=barra%40apps.globoid&redirect_uri=https%3A%2F%2Fwww.globo.com%2Flogin-callback.ghtml&state=99993333-3333-4333-b333-33333ccccccc&response_mode=fragment&response_type=code&scope=openid&nonce=cccccccc-cccc-4ccc-a666-666666666666&prompt=none&code_challenge=h67mV4wca_UU0NYpxiEsqq0TlndAqdlsJTVC7G8c5rY&code_challenge_method=S256",
"https://www.globo.com/login-callback.ghtml#error=login_required&state=99999999-9999-4933-b333-333333333333",
"https://s3.glbimg.com/v1/AUTH_05f06ca986b54d6e9c5df94927ccf7fc/libs/globoid-js/prod/callback.min.js",
"https://pub.doubleverify.com/dvtag/metrics/event.png?b11=legacy-success&d6=0&d7=150&b12=legacy&b2=72c5a3d&b3=&b7=83ffa2e6-1fa7-4f69-bf44-937975290ad0&b9=legacy&b8=&b5=27566431&b6=DV1036776&b4=www.globo.com&b1=ad-request&d1=1&d2=1",
"blob:https://www.globo.com/51da8fac-e6b1-4efe-9f1c-0714d316a8ed",
"blob:https://www.globo.com/27e54dd0-80a8-4d55-8740-b11ee45906b2",
"https://securepubads.g.doubleclick.net/pagead/ima_ppub_config?ippd=https%3A%2F%2Fwww.globo.com%2F",
"https://api.permutive.com/v2.0/geoip?include=geo&include=isp&include=ip_hash&k=cccecec5-8228-435e-81d1-33c4eccc78e6",
"https://www.google-analytics.com/j/collect?v=1&_v=j101&a=1851130904&t=pageview&_s=1&dl=https%3A%2F%2Fwww.globo.com%2F&dr=&ul=en-us&de=UTF-8&dt=globo.com%20-%20Absolutamente%20tudo%20sobre%20not%C3%ADcias%2C%20esportes%20e%20entretenimento&sd=24-bit&sr=412x915&vp=412x784&je=0&_u=YEBAAEABAAAAACABI~&jid=2065879268&gjid=2065879268&cid=1813739783.1714563960&uid=&tid=UA-296593-2&_gid=1813739783.1714563960&_r=1&_slc=1&gtm=45He44t0n81WQBMQ52v893644053za200&cd1=web&cd10=&cd11=&cd12=False&cd23=direct&cd52=Mozilla%2F5.0%20(Linux%3B%20Android%2010%3B%20K)%20AppleWebKit%2F537.36%20(KHTML%2C%20like%20Gecko)%20Chrome%2F126.0.0.0%20Mobile%20Safari%2F537.36&gcd=13l3l3l3l1&dma=0&tcfd=10000&z=1984274890",
"https://cdn.permutive.com/models/v2/d39f98ec-9259-4f8b-896d-7ab58be1f900-models.bin",
"https://api.permutive.com/v2.0/identify?k=cccecec5-8228-435e-81d1-33c4eccc78e6",
"https://googleads.g.doubleclick.net/pagead/viewthroughconversion/319734835/?random=1714563959950&cv=11&fst=1714563959950&bg=ffffff&guid=ON&async=1&gtm=45be44t0v9181806107z8893644053za201&gcd=13l3l3l3l1&dma=0&tcfd=10000&u_w=412&u_h=915&url=https%3A%2F%2Fwww.globo.com%2F&hn=www.googleadservices.com&frm=0&tiba=globo.com%20-%20Absolutamente%20tudo%20sobre%20not%C3%ADcias%2C%20esportes%20e%20entretenimento&npa=0&pscdl=noapi&auid=1636382539.1714563959&uaa=&uab=&uafvl=Not%252FA)Brand%3B8.0.0.0%7CChromium%3B126.0.6478.122%7CGoogle%2520Chrome%3B126.0.6478.122&uamb=1&uam=&uap=Android&uapv=14.0.0&uaw=0&fdr=QA&rfmt=3&fmt=4",
"https://region1.analytics.google.com/g/collect?v=2&tid=G-P4F3TC8HVE&gtm=45je44t0v888886305z8893644053za200&_p=1714563959000&_gaz=1&gcd=13l3l3l3l1&npa=0&dma=0&tcfd=10000&cid=1813739783.1714563960&ul=en-us&sr=412x915&uaa=&uab=&uafvl=Not%252FA)Brand%3B8.0.0.0%7CChromium%3B126.0.6478.122%7CGoogle%2520Chrome%3B126.0.6478.122&uamb=1&uam=&uap=Android&uapv=14.0.0&uaw=0&are=1&pscdl=noapi&_s=1&dr=&sid=1714563960&sct=1&seg=0&dl=https%3A%2F%2Fwww.globo.com%2F&dt=globo.com%20-%20Absolutamente%20tudo%20sobre%20not%C3%ADcias%2C%20esportes%20e%20entretenimento&en=page_view&_fv=1&_ss=1&ep.consumption_environment=web&ep.logged_visit=&ep.adblock=False&ep.last_referrer=direct&ep.user_agent=Mozilla%2F5.0%20(Linux%3B%20Android%2010%3B%20K)%20AppleWebKit%2F537.36%20(KHTML%2C%20like%20Gecko)%20Chrome%2F126.0.0.0%20Mobile%20Safari%2F537.36&ep.user_code_provider_hit=&ep.user_code_hit=&up.user_code=&up.user_code_provider=&up.logged_visitor=&tfd=2034",
"https://stats.g.doubleclick.net/g/collect?v=2&tid=G-P4F3TC8HVE&cid=1813739783.1714563960&gtm=45je44t0v888886305z8893644053za200&aip=1&dma=0&gcd=13l3l3l3l1&npa=0",
"https://www.google.co.uk/ads/ga-audiences?v=1&t=sr&slf_rd=1&_r=4&tid=G-P4F3TC8HVE&cid=1813739783.1714563960&gtm=45je44t0v888886305z8893644053za200&aip=1&dma=0&gcd=13l3l3l3l1&npa=0&z=2065879269",
"https://marfeelexperimentsexperienceengine.mrf.io/experimentsexperience/render?id=AC_ad6Etl3xROWaKP9FG_5Qrg&experimentType=HeadlineAB&version=esnext",
"https://horizon-track.globo.com/event/home-globo",
"https://stats.g.doubleclick.net/j/collect?t=dc&aip=1&_r=3&v=1&_v=j101&tid=UA-296593-2&cid=1813739783.1714563960&jid=2065879268&gjid=2065879268&_gid=1813739783.1714563960&_u=YEBAAEAAAAAAACABI~&z=2065879268",
"https://fundingchoicesmessages.google.com/el/AGSKWxVvoIo0ThVomAUIrvFBaDb_MkBJPPK9Jaq4mVXuCZZsaKNB8N9UeOeRGrvtF8kvGYmBHwr27lPBcmcxvcgc5yl_PWd-2TasfY24QdLcrJ2Cic1lgadWNjOMBRW5iLCTjKBYzirsPA==?dmid=be58ca16f9bb7f96",
"https://fundingchoicesmessages.google.com/el/AGSKWxUWBouH6yMIwWBucGxpZ_7_PAWo_9xGUN8TDR3xIBF7-C-PnkCjDzDf57BKMa0nuWVVSKTbudG0cuHDxsgiYcrmqCu6rFa3Aouge40rdYDLbKV4oB94sUy0xj9ClcJw627aqmAZnA==",
"https://events.newsroom.bi/ingest.php",
"https://fundingchoicesmessages.google.com/f/AGSKWxXlq9Uqz4XLumdFhss5slR25IhUILw2zrb1GBJRdfmjiRFaNoD5uUY9EdDJwOTRIaUimD18Eet1FOFaQ0_fv9xYIW7dy8Oq1Nkk2evfy3-5pK85RROQhjZwRY2Pz_c4DFSSSdGVRA==?fccs=W251bGwsbnVsbCxbIkNQOTd6d0FQOTd6d0FFc0FDQkVOQXlFb0FQX2dBRVBnQUNpUUlTSkI3RDdGYlNGQ3dINXphTHNRTUFoSFJzQ0FZb1FBQUFTQkFtQUJRQUtRSUFRQ2drQVFGQVNnQkFBQ0FBQUFJQ1pCSVFJRUNBQUFDVUFBUUFBQUFBQUVBQUFBQUFBSUlBQUFnQUVBQUFBSUFBQUNBQUFBRUFBSUFBQUFFQUFBbUFnQUFJSUFDQUFBaEFBQUFBQUFBQUFBQUFBQUFnQUFBQUFBQUFBQUFBQUFBQUFBQVFCQTZGQVBZWFlyYVFvV1E4S1pCWmlCQUVLS05nUURGQUFBQUNRSUVnQUNBQlNCQUNBVWdnQ0FBZ1VBQUFBQUFBQUJBU0FKQUFCQUFFQUFBZ0FLQUFBQUFBQWdBQUFBQUFCQkFBQUFBQWdBQUFBQUFBQVFBQUFBQUFCQUFBQUFnQUFFU0VJQUJCQUFRQUFBQUFBQkFBQUFBQUFBQUFBQUVBQSIsIjJ-MjA3Mi43MC44OS45My4xMDguMTIyLjE0OS4xOTYuMjI1My4yMjk5LjI1OS4yMzU3LjMxMS4zMTMuMzIzLjIzNzMuMzU4LjI0MTUuNDE1LjQ0OS4yNTA2LjI1MjYuMjUzNC40ODYuNDk0LjQ5NS4yNTY4LjI1NzEuMjU3NS41NDAuNTc0LjI2MjQuNjA5LjI2NzcuODI3Ljg2NC45ODEuMTAyOS4xMDQ4LjEwNTEuMTA5NS4xMDk3LjExMjYuMTIwNS4xMjExLjEyNzYuMTMwMS4xMzY1LjE0MTUuMTQyMy4xNDQ5LjE1NzAuMTU3Ny4xNTk4LjE2NTEuMTcxNi4xNzM1LjE3NTMuMTc2NS4xODcwLjE4NzguMTg4OS4xOTU4fmR2LiJdLG51bGwsbnVsbCxudWxsLFsxNzE0NTYzOTYwLDMwMDAwMDAwMF0sbnVsbCxudWxsLG51bGwsW251bGwsWzcsOF0sbnVsbCwxLG51bGwsImVuIl0sImh0dHBzOi8vd3d3Lmdsb2JvLmNvbS8iLG51bGwsW1s4LCJ4a2NRekZBbFVldyJdLFs5LCJlbi1VUyJdLFsxOSwiMSJdLFsxNywiWzBdIl1dXQ",
"https://oa.openxcdn.net/esp.js",
"https://static.criteo.net/js/ld/publishertag.ids.js",
"https://cdn.jsdelivr.net/gh/prebid/shared-id/pubcid.js/docs/pubcid.min.js",
"https://cdn.id5-sync.com/api/1.0/esp.js",
"https://tags.crwdcntrl.net/lt/c/16589/sync.min.js",
"https://cdn.prod.uidapi.com/uid2SecureSignal.js",
"https://securepubads.g.doubleclick.net/gampad/ads?pvsid=2981382953319268&correlator=2080663027845171&eid=31083220%2C31083222%2C31083226%2C31083203%2C31078663%2C31078668%2C31078670&output=ldjh&gdfp_req=1&vrg=202404290101&ptt=17&impl=fif&gdpr_consent=CP97zwAP97zwAEsACBENAyEoAP_gAEPgACiQISJB7D7FbSFCwH5zaLsQMAhHRsCAYoQAAASBAmABQAKQIAQCgkAQFASgBAACAAAAICZBIQIECAAACUAAQAAAAAAEAAAAAAAIIAAAgAEAAAAIAAACAAAAEAAIAAAAEAAAmAgAAIIACAAAhAAAAAAAAAAAAAAAAgAAAAAAAAAAAAAAAAAAAQBA6FAPYXYraQoWQ8KZBZiBAEKKNgQDFAAAACQIEgACABSBACAUggCAAgUAAAAAAAABASAJAABAAEAAAgAKAAAAAAAgAAAAAABBAAAAAAgAAAAAAAAQAAAAAABAAAAAgAAESEIABBAAQAAAAAABAAAAAAAAAAAAEAA&gdpr=1&addtl_consent=2~2072.70.89.93.108.122.149.196.2253.2299.259.2357.311.313.323.2373.358.2415.415.449.2506.2526.2534.486.494.495.2568.2571.2575.540.574.2624.609.2677.827.864.981.1029.1048.1051.1095.1097.1126.1205.1211.1276.1301.1365.1415.1423.1449.1570.1577.1598.1651.1716.1735.1753.1765.1870.1878.1889.1958~dv.&iu_parts=95377733%2Ctvg_Globo.com.Home&enc_prev_ius=%2F0%2F1&prev_iu_szs=320x50%7C80x35&fluid=height&ifi=1&didk=1023590695&sfv=1-0-40&eri=1&sc=1&cookie_enabled=1&abxe=1&dt=1714563960300&lmt=1719833313&adxs=166&adys=10638&biw=412&bih=784&scr_x=0&scr_y=0&btvi=1&ucis=1&oid=2&u_his=4&u_h=915&u_w=412&u_ah=915&u_aw=412&u_cd=24&u_sd=2.625&u_tz=-480&dmc=8&bc=31&nvt=1&uach=WyJBbmRyb2lkIiwiMTQuMC4wIiwiIiwiIiwiMTI2LjAuNjQ3OC4xMjIiLG51bGwsMSxudWxsLCIiLFtbIk5vdC9BKUJyYW5kIiwiOC4wLjAuMCJdLFsiQ2hyb21pdW0iLCIxMjYuMC42NDc4LjEyMiJdLFsiR29vZ2xlIENocm9tZSIsIjEyNi4wLjY0NzguMTIyIl1dLDBd&url=https%3A%2F%2Fwww.globo.com%2F&vis=1&psz=340x227&msz=340x0&fws=4&ohw=412&ga_vid=1813739783.1714563960&ga_sid=1714563960&ga_hid=1851130904&ga_fc=true&topics=9&tps=9&htps=10&nt=1&psd=WzE0LG51bGwsbnVsbCwzXQ..&dlt=1719833311883&idt=661&prev_scp=tvg_pos%3DEXTRA%26matchId%3D320717%26leagueId%3D31%26rc%3DEXTRA_0&cust_params=ext-bsafety%3D%26safe%3D%26ambient%3Dweb%26cor_pagina%3D0669DE%26ext-ctx-mc%3D%26tipo_pagina%3Dgcom%26tvg_cma%3Dhome-globo%26tvg_pgName%3Dgcom%26tvg_pgStr%3Dhome-globo%26tvg_random%3D3%26tvg_temas%3D%26tvg_topico%3D%26tvg_url%3Dwww.globo.com%252F%26as_obra%3D%26as_tempo%3D%26as_assun%3D%26as_canal%3D%26ext-canal%3D%26ext-obra%3D%26tvg_prop%3D%26glb_id%3Dna%26glb_tipo%3Danonimo%26pgv_id%3D76767676-7676-4676-b676-767676767676%26permutive%3D%26permutive-id%3D%26ptime%3D1714563959350%26prmtvvid%3D%26prmtvwid%3D&adks=2201165584&frm=20&eoidce=1",
"https://securepubads.g.doubleclick.net/gampad/ads?pvsid=2981382953319268&correlator=2531022990582224&eid=31083220%2C31083222%2C31083226%2C31083203%2C31078663%2C31078668%2C31078670&output=ldjh&gdfp_req=1&vrg=202404290101&ptt=17&impl=fif&gdpr_consent=CP97zwAP97zwAEsACBENAyEoAP_gAEPgACiQISJB7D7FbSFCwH5zaLsQMAhHRsCAYoQAAASBAmABQAKQIAQCgkAQFASgBAACAAAAICZBIQIECAAACUAAQAAAAAAEAAAAAAAIIAAAgAEAAAAIAAACAAAAEAAIAAAAEAAAmAgAAIIACAAAhAAAAAAAAAAAAAAAAgAAAAAAAAAAAAAAAAAAAQBA6FAPYXYraQoWQ8KZBZiBAEKKNgQDFAAAACQIEgACABSBACAUggCAAgUAAAAAAAABASAJAABAAEAAAgAKAAAAAAAgAAAAAABBAAAAAAgAAAAAAAAQAAAAAABAAAAAgAAESEIABBAAQAAAAAABAAAAAAAAAAAAEAA&gdpr=1&addtl_consent=2~2072.70.89.93.108.122.149.196.2253.2299.259.2357.311.313.323.2373.358.2415.415.449.2506.2526.2534.486.494.495.2568.2571.2575.540.574.2624.609.2677.827.864.981.1029.1048.1051.1095.1097.1126.1205.1211.1276.1301.1365.1415.1423.1449.1570.1577.1598.1651.1716.1735.1753.1765.1870.1878.1889.1958~dv.&iu_parts=95377733%2Ctvg_Globo.com.Home&enc_prev_ius=%2F0%2F1&prev_iu_szs=320x50%7C320x100%7C300x250&ifi=2&didk=2758904661&sfv=1-0-40&eri=1&sc=1&cookie_enabled=1&abxe=1&dt=1714563960300&lmt=1719833313&adxs=46&adys=919&biw=412&bih=784&scr_x=0&scr_y=0&btvi=2&ucis=2&oid=2&u_his=4&u_h=915&u_w=412&u_ah=915&u_aw=412&u_cd=24&u_sd=2.625&u_tz=-480&dmc=8&bc=31&nvt=1&uach=WyJBbmRyb2lkIiwiMTQuMC4wIiwiIiwiIiwiMTI2LjAuNjQ3OC4xMjIiLG51bGwsMSxudWxsLCIiLFtbIk5vdC9BKUJyYW5kIiwiOC4wLjAuMCJdLFsiQ2hyb21pdW0iLCIxMjYuMC42NDc4LjEyMiJdLFsiR29vZ2xlIENocm9tZSIsIjEyNi4wLjY0NzguMTIyIl1dLDBd&url=https%3A%2F%2Fwww.globo.com%2F&vis=1&psz=380x300&msz=412x300&fws=4&ohw=412&ga_vid=1813739783.1714563960&ga_sid=1714563960&ga_hid=1851130904&ga_fc=true&topics=9&tps=9&htps=10&nt=1&psd=WzE0LG51bGwsbnVsbCwzXQ..&dlt=1719833311883&idt=661&prev_scp=tvg_pos%3DHOME1_M%26mab%3D0%26rc%3DHOME1_M_0&cust_params=ext-bsafety%3D%26safe%3D%26ambient%3Dweb%26cor_pagina%3D0669DE%26ext-ctx-mc%3D%26tipo_pagina%3Dgcom%26tvg_cma%3Dhome-globo%26tvg_pgName%3Dgcom%26tvg_pgStr%3Dhome-globo%26tvg_random%3D3%26tvg_temas%3D%26tvg_topico%3D%26tvg_url%3Dwww.globo.com%252F%26as_obra%3D%26as_tempo%3D%26as_assun%3D%26as_canal%3D%26ext-canal%3D%26ext-obra%3D%26tvg_prop%3D%26glb_id%3Dna%26glb_tipo%3Danonimo%26pgv_id%3D76767676-7676-4676-b676-767676767676%26permutive%3D%26permutive-id%3D%26ptime%3D1714563959350%26prmtvvid%3D%26prmtvwid%3D&adks=2887157373&frm=20&eoidce=1",
"https://id.globo.com/auth/realms/globo.com/protocol/openid-connect/3p-cookies/step1.html",
"https://www.google.com/ads/ga-audiences?t=sr&aip=1&_r=4&slf_rd=1&v=1&_v=j101&tid=UA-296593-2&cid=1813739783.1714563960&jid=2065879268&_u=YEBAAEAAAAAAACABI~&z=2065879268",
"https://www.google.co.uk/ads/ga-audiences?t=sr&aip=1&_r=4&slf_rd=1&v=1&_v=j101&tid=UA-296593-2&cid=1813739783.1714563960&jid=2065879268&_u=YEBAAEAAAAAAACABI~&z=2065879268",
"https://flowcards.mrf.io/json/experiences?url=https%3A%2F%2Fwww.globo.com%2F&clid=0f0f0f0f-0f0f-4929-a929-292929292929&fvst=1714563960&geo=__INJECT_GEO__&ptch=0&pgv=1&sdu=0&sid=3838&mrfExperiment_destaque_test=1&useg=&utyp=0&vfrq=6",
"https://www.google.com/pagead/1p-user-list/319734835/?random=1714564046850&cv=11&fst=1714561200000&bg=ffffff&guid=ON&async=1&gtm=45be44t0v9181806107z8893644053za201&gcd=13l3l3l3l1&dma=0&tcfd=10000&u_w=412&u_h=915&url=https%3A%2F%2Fwww.globo.com%2F&hn=www.googleadservices.com&frm=0&tiba=globo.com%20-%20Absolutamente%20tudo%20sobre%20not%C3%ADcias%2C%20esportes%20e%20entretenimento&npa=0&pscdl=noapi&auid=1636382539.1714564046&uaa=&uab=&uafvl=Not%252FA)Brand%3B8.0.0.0%7CChromium%3B126.0.6433.0%7CGoogle%2520Chrome%3B126.0.6433.0&uamb=1&uam=&uap=Android&uapv=14.0.0&uaw=0&fdr=QA&rfmt=3&fmt=3&is_vtc=1&cid=CAQSKQB7FLtqPmjxa9CFgaHoxiUTE4de8qawcUfGoosGi5d34PkyW4TOEKHh&random=2078733799&rmt_tld=0&ipr=y",
"https://www.google.co.uk/pagead/1p-user-list/319734835/?random=1714564046850&cv=11&fst=1714561200000&bg=ffffff&guid=ON&async=1&gtm=45be44t0v9181806107z8893644053za201&gcd=13l3l3l3l1&dma=0&tcfd=10000&u_w=412&u_h=915&url=https%3A%2F%2Fwww.globo.com%2F&hn=www.googleadservices.com&frm=0&tiba=globo.com%20-%20Absolutamente%20tudo%20sobre%20not%C3%ADcias%2C%20esportes%20e%20entretenimento&npa=0&pscdl=noapi&auid=1636382539.1714564046&uaa=&uab=&uafvl=Not%252FA)Brand%3B8.0.0.0%7CChromium%3B126.0.6433.0%7CGoogle%2520Chrome%3B126.0.6433.0&uamb=1&uam=&uap=Android&uapv=14.0.0&uaw=0&fdr=QA&rfmt=3&fmt=3&is_vtc=1&cid=CAQSKQB7FLtqPmjxa9CFgaHoxiUTE4de8qawcUfGoosGi5d34PkyW4TOEKHh&random=2078733799&rmt_tld=1&ipr=y",
"https://id.globo.com/auth/realms/globo.com/protocol/openid-connect/3p-cookies/step2.html",
"https://events.newsroom.bi/recirculation.php",
"https://id5-sync.com/api/esp/increment?counter=no-config",
};

// ArchivedRequest contains a single request and its response.
// Immutable after creation.
type ArchivedRequest struct {
	SerializedRequest   []byte
	SerializedResponse  []byte // if empty, the request failed
	LastServedSessionId uint32
	SequenceId uint32
}

// RequestMatch represents a match when querying the archive for responses to a request
type RequestMatch struct {
	Match      *ArchivedRequest
	Request    *http.Request
	Response   *http.Response
	MatchRatio float64
	SequenceId uint32
}

func (requestMatch *RequestMatch) SetMatch(
	match *ArchivedRequest,
	request *http.Request,
	response *http.Response,
	ratio float64,
	sequenceId uint32) {
	requestMatch.Match = match
	requestMatch.Request = request
	requestMatch.Response = response
	requestMatch.MatchRatio = ratio
	requestMatch.SequenceId = sequenceId
}

func serializeRequest(req *http.Request, resp *http.Response) (*ArchivedRequest, error) {
	ar := &ArchivedRequest{}
	{
		var buf bytes.Buffer
		if err := req.Write(&buf); err != nil {
			return nil, fmt.Errorf("failed writing request for %s: %v", req.URL.String(), err)
		}
		ar.SerializedRequest = buf.Bytes()
	}
	{
		var buf bytes.Buffer
		if err := resp.Write(&buf); err != nil {
			return nil, fmt.Errorf("failed writing response for %s: %v", req.URL.String(), err)
		}
		ar.SerializedResponse = buf.Bytes()
	}
	return ar, nil
}

func (ar *ArchivedRequest) unmarshal(scheme string) (*http.Request, *http.Response, error) {
	req, err := http.ReadRequest(bufio.NewReader(bytes.NewReader(ar.SerializedRequest)))
	if err != nil {
		return nil, nil, fmt.Errorf("couldn't unmarshal request: %v", err)
	}

	if req.URL.Host == "" {
		req.URL.Host = req.Host
		req.URL.Scheme = scheme
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

// Archive contains an archive of requests. Immutable except when embedded in
// a WritableArchive.
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
	// When an incoming request matches multiple recorded responses, whether to
	// serve the responses in the chronological sequence in which wpr_go
	// recorded them.
	ServeResponseInChronologicalSequence bool
	// Records the current session id.
	// Archive can serve responses in chronological order. If a client wants to
	// reset the Archive to serve responses from the start, the client may do so
	// by incrementing its session id.
	CurrentSessionId uint32
	// If an incoming URL doesn't exactly match an entry in the archive,
	// skip fuzzy matching and return nothing.
	DisableFuzzyURLMatching bool
}

func newArchive() Archive {
	return Archive{Requests: make(map[string]map[string][]*ArchivedRequest)}
}

func prepareArchiveForReplay(a *Archive) {
	// Initialize the session id mechanism that Archive uses to keep state
	// information about clients.
	a.CurrentSessionId = 1
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
	prepareArchiveForReplay(&a)
	return &a, nil
}

// ForEach applies f to all requests in the archive.
func (a *Archive) ForEach(f func(req *http.Request, resp *http.Response) error) error {
	for _, urlmap := range a.Requests {
		for urlString, requests := range urlmap {
			fullURL, _ := url.Parse(urlString)
			for index, archivedRequest := range requests {
				req, resp, err := archivedRequest.unmarshal(fullURL.Scheme)
				if err != nil {
					log.Printf("Error unmarshaling request #%d for %s: %v", index, urlString, err)
					continue
				}
				if err := f(req, resp); err != nil {
					return err
				}
			}
		}
	}
	return nil
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

func assertCompleteURL(url *url.URL) {
	if url.Host == "" || url.Scheme == "" {
		log.Printf("Missing host and scheme: %v\n", url)
		os.Exit(1)
	}
}

func isGoodURL(reqUrl string) bool {
	for _, goodUrl := range goodURLs {
		if (reqUrl == goodUrl) {
			return true
		}
	}
	return false
}

func isGoodPath(path string) bool {
	for _, goodUrl := range goodURLs {
		u, err := url.Parse(goodUrl)
		if err != nil {
			continue
		}
		if u.Path == path {
			return true
		}
	}
	return false
}

// FindRequest searches for the given request in the archive.
// Returns ErrNotFound if the request could not be found.
//
// Does not use the request body, but reads the request body to
// prevent WPR from issuing a Connection Reset error when
// handling large upload requests.
// (https://bugs.chromium.org/p/chromium/issues/detail?id=1215668)
//
// TODO: conditional requests
func (a *Archive) FindRequest(req *http.Request, newSequenceId uint32) (*http.Request, *http.Response, uint32, error) {
	// Clear the input channel on large uploads to prevent WPR
	// from resetting the connection, and causing the upload
	// to fail.
	// Large upload is an uncommon scenario for WPR users. To
	// avoid exacting an overhead on every request, restrict
	// the operation to large uploads only (size > 1MB).
	if req.Body != nil &&
		(strings.EqualFold("POST", req.Method) || strings.EqualFold("PUT", req.Method)) &&
		req.ContentLength > 2<<20 {
		buf := make([]byte, 1024)
		for {
			_, read_err := req.Body.Read(buf)
			if read_err == io.EOF {
				break
			}
		}
	}

	hostMap := a.Requests[req.Host]
	if len(hostMap) == 0 {
		return nil, nil, 0, ErrNotFound
	}

	// Exact match. Note that req may be relative, but hostMap keys are always absolute.
	assertCompleteURL(req.URL)
	reqUrl := req.URL.String()

	if len(hostMap[reqUrl]) > 0 {
		if (!isGoodURL(reqUrl)) {
			newSequenceId = 0
		}
		log.Printf("Determenistic: url=%s, good?=%t newSequenceId=%d", reqUrl, isGoodURL(reqUrl), newSequenceId)
		return a.findBestMatchInArchivedRequestSet(req, hostMap[reqUrl], newSequenceId)
	}

	// For all URLs with a matching path, pick the URL that has the most matching query parameters.
	// The match ratio is defined to be 2*M/T, where
	//   M = number of matches x where a.Query[x]=b.Query[x]
	//   T = sum(len(a.Query)) + sum(len(b.Query))
	aq := req.URL.Query()

	var bestURL string
	var bestURLs []string // For debugging fuzzy matching
	var bestRatio float64
	var isBestGood bool

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

		if ratio > bestRatio {
			bestURLs = nil
		}
		// In case of multiple best urls we say at least one good => the request is good.
		bestURLs = append(bestURLs, bestURL)

		if ratio > bestRatio ||
			// Map iteration order is non-deterministic, so we must break ties.
			(ratio == bestRatio && ustr < bestURL) {
			bestURL = ustr
			bestRatio = ratio
			isBestGood = isGoodPath(u.Path)
		}
	}

	if bestURL != "" && !a.DisableFuzzyURLMatching {
		log.Printf("Fuzzy: url=%s, bestUrl=%s, good?=%t newSequenceId=%d", reqUrl, bestURL, isBestGood, newSequenceId)
		// TODO: this is a hack to ignore all fuzzily matches urls.
		newSequenceId = 0
		return a.findBestMatchInArchivedRequestSet(req, hostMap[bestURL], newSequenceId)
	} else if a.DisableFuzzyURLMatching {
		logStr := "No exact match found for %s.\nFuzzy matching would have returned one of the following %d matches:\n%v\n"
		if len(bestURLs) > 0 {
			logStr += "\n"
		}
		log.Printf(logStr, reqUrl, len(bestURLs), strings.Join(bestURLs[:], "\n"))
	}

	return nil, nil, 0, ErrNotFound
}

// Given an incoming request and a set of matches in the archive, identify the best match,
// based on request headers.
func (a *Archive) findBestMatchInArchivedRequestSet(
	incomingReq *http.Request,
	archivedReqs []*ArchivedRequest,
	newSequenceId uint32) (
	*http.Request, *http.Response, uint32, error) {
	scheme := incomingReq.URL.Scheme

	if len(archivedReqs) == 0 {
		return nil, nil, 0, ErrNotFound
	} else if len(archivedReqs) == 1 {
		archivedReq, archivedResp, err := archivedReqs[0].unmarshal(scheme)
		if err != nil {
			log.Println("Error unmarshaling request")
			return nil, nil, 0, err
		}
		if newSequenceId > 0 && archivedReqs[0].SequenceId == 0 && archivedResp.StatusCode == 200 {
			archivedReqs[0].SequenceId = newSequenceId
		}
		return archivedReq, archivedResp, archivedReqs[0].SequenceId, err
	}

	// There can be multiple requests with the same URL string. If that's the
	// case, break the tie by the number of headers that match.
	var bestMatch RequestMatch
	var bestInSequenceMatch RequestMatch

	for _, r := range archivedReqs {
		archivedReq, archivedResp, err := r.unmarshal(scheme)
		if err != nil {
			log.Println("Error unmarshaling request")
			continue
		}

		// Skip this archived request if the request methods does not match that
		// of the incoming request.
		if archivedReq.Method != incomingReq.Method {
			continue
		}

		// Count the number of header matches
		numMatchingHeaders := 1
		numTotalHeaders := len(incomingReq.Header) + len(archivedReq.Header)
		for key, val := range archivedReq.Header {
			if reflect.DeepEqual(val, incomingReq.Header[key]) {
				numMatchingHeaders++
			}
		}
		// Note that since |m| starts from 1. The ratio will be more than 0
		// even if no header matches.
		ratio := 2 * float64(numMatchingHeaders) / float64(numTotalHeaders)

		if a.ServeResponseInChronologicalSequence &&
			r.LastServedSessionId != a.CurrentSessionId &&
			ratio > bestInSequenceMatch.MatchRatio {
			bestInSequenceMatch.SetMatch(r, archivedReq, archivedResp, ratio, r.SequenceId)
		}
		if ratio > bestMatch.MatchRatio {
			bestMatch.SetMatch(r, archivedReq, archivedResp, ratio, r.SequenceId)
		}
	}

	if a.ServeResponseInChronologicalSequence &&
		bestInSequenceMatch.Match != nil {
		bestInSequenceMatch.Match.LastServedSessionId = a.CurrentSessionId
		if newSequenceId > 0 && bestInSequenceMatch.Match.SequenceId == 0 && bestInSequenceMatch.Response.StatusCode == 200 {
			bestInSequenceMatch.Match.SequenceId = newSequenceId
		}
		return bestInSequenceMatch.Request, bestInSequenceMatch.Response, bestInSequenceMatch.SequenceId, nil
	} else if bestMatch.Match != nil {
		bestMatch.Match.LastServedSessionId = a.CurrentSessionId
		if newSequenceId > 0 && bestMatch.Match.SequenceId == 0 && bestMatch.Response.StatusCode == 200 {
			bestMatch.Match.SequenceId = newSequenceId
		}
		return bestMatch.Request, bestMatch.Response, bestMatch.SequenceId, nil
	}

	return nil, nil, 0, ErrNotFound
}

type AddMode int

const (
	AddModeAppend            AddMode = 0
	AddModeOverwriteExisting AddMode = 1
	AddModeSkipExisting      AddMode = 2
)

func (a *Archive) addArchivedRequest(req *http.Request, resp *http.Response, mode AddMode, sequenceId uint32) error {
	// Always use the absolute URL in this mapping.
	assertCompleteURL(req.URL)
	archivedRequest, err := serializeRequest(req, resp)
	archivedRequest.SequenceId = sequenceId
	if err != nil {
		return err
	}

	if a.Requests[req.Host] == nil {
		a.Requests[req.Host] = make(map[string][]*ArchivedRequest)
	}

	urlStr := req.URL.String()
	requests := a.Requests[req.Host][urlStr]
	if mode == AddModeAppend {
		requests = append(requests, archivedRequest)
	} else if mode == AddModeOverwriteExisting {
		log.Printf("Overwriting existing request")
		requests = []*ArchivedRequest{archivedRequest}
	} else if mode == AddModeSkipExisting {
		if requests != nil {
			log.Printf("Skipping existing request: %s", urlStr)
			return nil
		}
		requests = append(requests, archivedRequest)
	}
	a.Requests[req.Host][urlStr] = requests
	return nil
}

// Start a new replay session so that the archive serves responses from the start.
// If an archive contains multiple identical requests with different responses, the archive
// can serve the responses in chronological order. This function resets the archive serving
// order to the start.
func (a *Archive) StartNewReplaySession() {
	a.CurrentSessionId++
}

// Edit iterates over all requests in the archive. For each request, it calls f to
// edit the request. If f returns a nil pair, the request is deleted.
// The edited archive is returned, leaving the current archive is unchanged.
func (a *Archive) Edit(edit func(req *http.Request, resp *http.Response) (*http.Request, *http.Response, error)) (*Archive, error) {
	clone := newArchive()
	err := a.ForEach(func(oldReq *http.Request, oldResp *http.Response) error {
		newReq, newResp, err := edit(oldReq, oldResp)
		if err != nil {
			return err
		}
		if newReq == nil || newResp == nil {
			if newReq != nil || newResp != nil {
				panic("programming error: newReq/newResp must both be nil or non-nil")
			}
			return nil
		}
		// TODO: allow changing scheme or protocol?
		// TODO: handle sequence ids.
		return clone.addArchivedRequest(newReq, newResp, AddModeAppend, 0)
	})
	if err != nil {
		return nil, err
	}
	return &clone, nil
}

// Merge adds all the request of the provided archive to the receiver.
func (a *Archive) Merge(other *Archive) error {
	var numAddedRequests = 0
	var numSkippedRequests = 0
	err := other.ForEach(func(req *http.Request, resp *http.Response) error {
		foundReq, _, _, notFoundErr := a.FindRequest(req, 0)
		if notFoundErr == ErrNotFound || req.URL.String() != foundReq.URL.String() {
			// TODO: Handle sequence ids
			if err := a.addArchivedRequest(req, resp, AddModeAppend, 0); err != nil {
				return err
			}
			numAddedRequests++
		} else {
			numSkippedRequests++
		}
		return nil
	})
	log.Printf("Merged requests: added=%d duplicates=%d \n", numAddedRequests, numSkippedRequests)
	return err
}

// Trim iterates over all requests in the archive. For each request, it calls f
// to see if the request should be removed the archive.
// The trimmed archive is returned, leaving the current archive unchanged.
func (a *Archive) Trim(trimMatch func(req *http.Request, resp *http.Response) (bool, error)) (*Archive, error) {
	var numRemovedRequests = 0
	clone := newArchive()
	err := a.ForEach(func(req *http.Request, resp *http.Response) error {
		trimReq, err := trimMatch(req, resp)
		if err != nil {
			return err
		}
		if trimReq {
			numRemovedRequests++
		} else {
			// TODO: handle sequence ids
			clone.addArchivedRequest(req, resp, AddModeAppend, 0)
		}
		return nil
	})
	log.Printf("Trimmed requests: removed=%d", numRemovedRequests)
	if err != nil {
		return nil, err
	}
	return &clone, nil
}

// Add the result of a get request to the receiver.
func (a *Archive) Add(method string, urlString string, mode AddMode, sequenceId uint32) error {
	req, err := http.NewRequest(method, urlString, nil)
	if err != nil {
		return fmt.Errorf("Error creating request object: %v", err)
	}

	url, _ := url.Parse(urlString)
	// Print a warning for duplicate requests since the replay server will only
	// return the first found response.
	if mode == AddModeAppend || mode == AddModeSkipExisting {
		if foundReq, _, _, notFoundErr := a.FindRequest(req, 0); notFoundErr != ErrNotFound {
			if foundReq.URL.String() == url.String() {
				if mode == AddModeSkipExisting {
					log.Printf("Skipping existing request: %s %s", req.Method, urlString)
					return nil
				}
				log.Printf("Adding duplicate request:")
			}
		}
	}

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return fmt.Errorf("Error fetching url: %v", err)
	}

	if err = a.addArchivedRequest(req, resp, mode, sequenceId); err != nil {
		return err
	}

	fmt.Printf("Added request: (%s %s) %s\n", req.Method, resp.Status, urlString)
	return nil
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
func (a *WritableArchive) RecordRequest(req *http.Request, resp *http.Response, sequenceId uint32) error {
	a.mu.Lock()
	defer a.mu.Unlock()
	return a.addArchivedRequest(req, resp, AddModeAppend, sequenceId)
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

# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from google.appengine.ext import ndb

from dashboard.common import namespaced_stored_object
from dashboard.common import utils

import six
if six.PY2:
  import string

BOT_CONFIGURATIONS_KEY = 'bot_configurations'

BOT_CONFIG = """
{
  "Android Go": {
    "alias": "android-go-perf"
  },
  "Mojo Linux Perf": {
    "alias": "linux-perf-fyi"
  },
  "Win 10 Perf": {
    "alias": "win-10-perf"
  },
  "Win10 FYI Release XR Perf (NVIDIA)": {
    "browser": "release",
    "bucket": "luci.chromium.try",
    "builder": "gpu-fyi-try-win-xr-builder",
    "dimensions": [
      {
        "key": "os",
        "value": "Windows-10"
      },
      {
        "key": "pool",
        "value": "Chrome-GPU"
      },
      {
        "key": "gpu",
        "value": "nvidia-quadro-p400-win10-stable"
      }
    ],
    "repository": "chromium",
    "scheduler": {
      "budget": 3.0,
      "costs": {
        "functional": 0.5,
        "performance": 1.0,
        "try": 0.3
      }
    },
    "swarming_server": "https://chromium-swarm.appspot.com"
  },
  "android-go-perf": {
    "browser": "android-chrome",
    "bucket": "luci.chrome.try",
    "builder": "Android Compile Perf",
    "dimensions": [
      {
        "key": "pool",
        "value": "chrome.tests.pinpoint"
      },
      {
        "key": "device_type",
        "value": "gobo"
      },
      {
        "key": "device_os",
        "value": "OMB1.180119.001"
      }
    ],
    "repository": "chromium",
    "scheduler": {
      "budget": 3.0,
      "costs": {
        "functional": 0.5,
        "performance": 1.0,
        "try": 0.3
      }
    },
    "swarming_server": "https://chrome-swarming.appspot.com"
  },
  "android-go_webview-perf": {
    "browser": "android-webview-google",
    "bucket": "luci.chrome.try",
    "builder": "Android Compile Perf",
    "dimensions": [
      {
        "key": "pool",
        "value": "chrome.tests.pinpoint"
      },
      {
        "key": "device_type",
        "value": "gobo"
      },
      {
        "key": "device_os",
        "value": "OMB1.180119.001"
      }
    ],
    "repository": "chromium",
    "scheduler": {
      "budget": 3.0,
      "costs": {
        "functional": 0.5,
        "performance": 1.0,
        "try": 0.3
      }
    },
    "swarming_server": "https://chrome-swarming.appspot.com"
  },
  "android-pixel2-perf": {
    "browser": "android-chrome-64-bundle",
    "bucket": "luci.chrome.try",
    "builder": "Android arm64 Compile Perf",
    "dimensions": [
      {
        "key": "pool",
        "value": "chrome.tests.pinpoint"
      },
      {
        "key": "device_type",
        "value": "walleye"
      },
      {
        "key": "device_os",
        "value": "OPM1.171019.021"
      }
    ],
    "repository": "chromium",
    "scheduler": {
      "budget": 6.0,
      "costs": {
        "functional": 0.5,
        "performance": 1.0,
        "try": 0.3
      }
    },
    "swarming_server": "https://chrome-swarming.appspot.com"
  },
  "android-pixel2_weblayer-perf": {
    "browser": "android-weblayer",
    "bucket": "luci.chrome.try",
    "builder": "Android arm64 Compile Perf",
    "dimensions": [
      {
        "key": "pool",
        "value": "chrome.tests.pinpoint"
      },
      {
        "key": "device_type",
        "value": "walleye"
      },
      {
        "key": "device_os",
        "value": "OPM1.171019.021"
      }
    ],
    "repository": "chromium",
    "scheduler": {
      "budget": 6.0,
      "costs": {
        "functional": 0.5,
        "performance": 1.0,
        "try": 0.3
      }
    },
    "swarming_server": "https://chrome-swarming.appspot.com"
  },
  "android-pixel2_webview-perf": {
    "browser": "android-webview-google",
    "bucket": "luci.chrome.try",
    "builder": "Android arm64 Compile Perf",
    "dimensions": [
      {
        "key": "pool",
        "value": "chrome.tests.pinpoint"
      },
      {
        "key": "device_type",
        "value": "walleye"
      },
      {
        "key": "device_os",
        "value": "OPM1.171019.021"
      }
    ],
    "repository": "chromium",
    "scheduler": {
      "budget": 6.0,
      "costs": {
        "functional": 0.5,
        "performance": 1.0,
        "try": 0.3
      }
    },
    "swarming_server": "https://chrome-swarming.appspot.com"
  },
  "android-pixel4-perf": {
    "browser": "android-trichrome-bundle",
    "bucket": "luci.chrome.try",
    "builder": "Android arm64 Compile Perf",
    "dimensions": [
      {
        "key": "pool",
        "value": "chrome.tests.pinpoint"
      },
      {
        "key": "device_type",
        "value": "flame"
      },
      {
        "key": "device_os",
        "value": "R"
      }
    ],
    "repository": "chromium",
    "scheduler": {
      "budget": 6.0,
      "costs": {
        "functional": 0.5,
        "performance": 1.0,
        "try": 0.3
      }
    },
    "swarming_server": "https://chrome-swarming.appspot.com"
  },
  "android-pixel4_weblayer-perf": {
    "browser": "android-weblayer-trichrome-google-bundle",
    "bucket": "luci.chrome.try",
    "builder": "Android arm64 Compile Perf",
    "dimensions": [
      {
        "key": "pool",
        "value": "chrome.tests.pinpoint"
      },
      {
        "key": "device_type",
        "value": "flame"
      },
      {
        "key": "device_os",
        "value": "R"
      }
    ],
    "repository": "chromium",
    "scheduler": {
      "budget": 6.0,
      "costs": {
        "functional": 0.5,
        "performance": 1.0,
        "try": 0.3
      }
    },
    "swarming_server": "https://chrome-swarming.appspot.com"
  },
  "android-pixel4_webview-perf": {
    "browser": "android-webview-trichrome-google-bundle",
    "bucket": "luci.chrome.try",
    "builder": "Android arm64 Compile Perf",
    "dimensions": [
      {
        "key": "pool",
        "value": "chrome.tests.pinpoint"
      },
      {
        "key": "device_type",
        "value": "flame"
      },
      {
        "key": "device_os",
        "value": "R"
      }
    ],
    "repository": "chromium",
    "scheduler": {
      "budget": 6.0,
      "costs": {
        "functional": 0.5,
        "performance": 1.0,
        "try": 0.3
      }
    },
    "swarming_server": "https://chrome-swarming.appspot.com"
  },
  "chromium-rel-win10": {
    "alias": "win-10-perf"
  },
  "fuchsia-perf-fyi": {
    "browser": "web-engine-shell",
    "bucket": "luci.chrome.try",
    "builder": "Fuchsia Builder Perf",
    "dimensions": [
      {
        "key": "device_type",
        "value": "Astro"
      },
      {
        "key": "os",
        "value": "Fuchsia"
      },
      {
        "key": "pool",
        "value": "chrome.tests.pinpoint"
      }
    ],
    "repository": "chromium",
    "scheduler": {
      "budget": 3.0,
      "costs": {
        "functional": 0.5,
        "performance": 1.0,
        "try": 0.3
      }
    },
    "swarming_server": "https://chrome-swarming.appspot.com"
  },
  "lacros-eve-perf": {
    "browser": "lacros-chrome",
    "bucket": "luci.chrome.try",
    "builder": "Chromeos Amd64 Generic Lacros Builder Perf",
    "dimensions": [
      {
        "key": "pool",
        "value": "chrome.tests.pinpoint"
      },
      {
        "key": "device_type",
        "value": "eve"
      },
      {
        "key": "device_status",
        "value": "available"
      }
    ],
    "repository": "chromium",
    "scheduler": {
      "budget": 3.0,
      "costs": {
        "functional": 0.5,
        "performance": 1.0,
        "try": 0.3
      }
    },
    "swarming_server": "https://chrome-swarming.appspot.com"
  },
  "linux-perf": {
    "browser": "release",
    "bucket": "luci.chrome.try",
    "builder": "Linux Builder Perf",
    "dimensions": [
      {
        "key": "pool",
        "value": "chrome.tests.pinpoint"
      },
      {
        "key": "gpu",
        "value": "10de:1cb3-390.116"
      },
      {
        "key": "os",
        "value": "Ubuntu-18.04"
      },
      {
        "key": "synthetic_product_name",
        "value": "PowerEdge R230 (Dell Inc.)"
      }
    ],
    "repository": "chromium",
    "scheduler": {
      "budget": 4.0,
      "costs": {
        "functional": 0.5,
        "performance": 1.0,
        "try": 0.3
      }
    },
    "swarming_server": "https://chrome-swarming.appspot.com"
  },
  "linux-perf-fyi": {
    "browser": "release",
    "bucket": "luci.chrome.try",
    "builder": "Linux Builder Perf",
    "dimensions": [
      {
        "key": "pool",
        "value": "chrome.tests.pinpoint"
      },
      {
        "key": "gpu",
        "value": "10de:1cb3"
      },
      {
        "key": "os",
        "value": "Ubuntu"
      }
    ],
    "repository": "chromium",
    "scheduler": {
      "budget": 3.0,
      "costs": {
        "functional": 0.5,
        "performance": 1.0,
        "try": 0.3
      }
    },
    "swarming_server": "https://chrome-swarming.appspot.com"
  },
  "linux-release": {
    "alias": "linux-perf"
  },
  "mac-10_12_laptop_low_end-perf": {
    "browser": "release",
    "bucket": "luci.chrome.try",
    "builder": "Mac Builder Perf",
    "dimensions": [
      {
        "key": "pool",
        "value": "chrome.tests.pinpoint"
      },
      {
        "key": "mac_model",
        "value": "MacBookAir7,2"
      },
      {
        "key": "os",
        "value": "Mac-10.12.6"
      },
      {
        "key": "gpu",
        "value": "8086:1626"
      },
      {
        "key": "synthetic_product_name",
        "value": "MacBookAir7,2_x86-64-i5-5350U_Intel Broadwell HD Graphics 6000_8192_APPLE SSD SM0128G"
      }
    ],
    "repository": "chromium",
    "scheduler": {
      "budget": 3.0,
      "costs": {
        "functional": 0.5,
        "performance": 1.0,
        "try": 0.3
      }
    },
    "swarming_server": "https://chrome-swarming.appspot.com"
  },
  "mac-10_13_laptop_high_end-perf": {
    "browser": "release",
    "bucket": "luci.chrome.try",
    "builder": "Mac Builder Perf",
    "dimensions": [
      {
        "key": "pool",
        "value": "chrome.tests.pinpoint"
      },
      {
        "key": "mac_model",
        "value": "MacBookPro11,5"
      },
      {
        "key": "os",
        "value": "Mac-11.6.1"
      },
      {
        "key": "gpu",
        "value": "8086:0d26-4.0.20-3.2.8"
      },
      {
        "key": "synthetic_product_name",
        "value": "MacBookPro11,5_x86-64-i7-4870HQ_AMD Radeon R8 M370X 4.0.20 [3.2.8]_Intel Haswell Iris Pro Graphics 5200 4.0.20 [3.2.8]_16384_APPLE SSD SM0512G"
      }
    ],
    "repository": "chromium",
    "scheduler": {
      "budget": 3.0,
      "costs": {
        "functional": 0.5,
        "performance": 1.0,
        "try": 0.3
      }
    },
    "swarming_server": "https://chrome-swarming.appspot.com"
  },
  "mac-laptop_high_end-perf": {
    "browser": "release",
    "bucket": "luci.chrome.try",
    "builder": "Mac Builder Perf",
    "dimensions": [
      {
        "key": "pool",
        "value": "chrome.tests.pinpoint"
      },
      {
        "key": "mac_model",
        "value": "MacBookPro11,5"
      },
      {
        "key": "os",
        "value": "Mac-11.6.1"
      },
      {
        "key": "gpu",
        "value": "8086:0d26-4.0.20-3.2.8"
      },
      {
        "key": "synthetic_product_name",
        "value": "MacBookPro11,5_x86-64-i7-4870HQ_AMD Radeon R8 M370X 4.0.20 [3.2.8]_Intel Haswell Iris Pro Graphics 5200 4.0.20 [3.2.8]_16384_APPLE SSD SM0512G"
      }
    ],
    "repository": "chromium",
    "scheduler": {
      "budget": 3.0,
      "costs": {
        "functional": 0.5,
        "performance": 1.0,
        "try": 0.3
      }
    },
    "swarming_server": "https://chrome-swarming.appspot.com"
  },
  "mac-laptop_low_end-perf": {
    "browser": "release",
    "bucket": "luci.chrome.try",
    "builder": "Mac Builder Perf",
    "dimensions": [
      {
        "key": "pool",
        "value": "chrome.tests.pinpoint"
      },
      {
        "key": "mac_model",
        "value": "MacBookAir7,2"
      },
      {
        "key": "os",
        "value": "Mac-10.12.6"
      },
      {
        "key": "gpu",
        "value": "8086:1626"
      },
      {
        "key": "synthetic_product_name",
        "value": "MacBookAir7,2_x86-64-i5-5350U_Intel Broadwell HD Graphics 6000_8192_APPLE SSD SM0128G"
      }
    ],
    "repository": "chromium",
    "scheduler": {
      "budget": 3.0,
      "costs": {
        "functional": 0.5,
        "performance": 1.0,
        "try": 0.3
      }
    },
    "swarming_server": "https://chrome-swarming.appspot.com"
  },
  "mac-m1_mini_2020-perf": {
    "browser": "release",
    "bucket": "luci.chrome.try",
    "builder": "Mac arm Builder Perf",
    "dimensions": [
      {
        "key": "pool",
        "value": "chrome.tests.pinpoint"
      },
      {
        "key": "mac_model",
        "value": "Macmini9,1"
      },
      {
        "key": "os",
        "value": "Mac"
      },
      {
        "key": "cpu",
        "value": "arm"
      }
    ],
    "repository": "chromium",
    "scheduler": {
      "budget": 3.0,
      "costs": {
        "functional": 0.5,
        "performance": 1.0,
        "try": 0.3
      }
    },
    "swarming_server": "https://chrome-swarming.appspot.com"
  },
  "mojo-linux-perf": {
    "alias": "linux-perf-fyi"
  },
  "win-10-perf": {
    "browser": "release_x64",
    "bucket": "luci.chrome.try",
    "builder": "Win x64 Builder Perf",
    "dimensions": [
      {
        "key": "pool",
        "value": "chrome.tests.pinpoint"
      },
      {
        "key": "synthetic_product_name",
        "value": "OptiPlex 7050 (Dell Inc.)"
      },
      {
        "key": "os",
        "value": "Windows-10"
      }
    ],
    "repository": "chromium",
    "scheduler": {
      "budget": 3.0,
      "costs": {
        "functional": 0.5,
        "performance": 1.0,
        "try": 0.3
      }
    },
    "swarming_server": "https://chrome-swarming.appspot.com"
  },
  "win-10_amd-perf": {
    "browser": "release_x64",
    "bucket": "luci.chrome.try",
    "builder": "Win x64 Builder Perf",
    "dimensions": [
      {
        "key": "pool",
        "value": "chrome.tests.pinpoint"
      },
      {
        "key": "os",
        "value": "Windows-10-18363.476"
      },
      {
        "key": "gpu",
        "value": "1002:15d8-27.20.1034.6"
      },
      {
        "key": "synthetic_product_name",
        "value": "11A5S4L300 [ThinkCentre M75q-1] (LENOVO)"
      }
    ],
    "repository": "chromium",
    "scheduler": {
      "budget": 3.0,
      "costs": {
        "functional": 0.5,
        "performance": 1.0,
        "try": 0.3
      }
    },
    "swarming_server": "https://chrome-swarming.appspot.com"
  },
  "win-10_amd_laptop-perf": {
    "browser": "release_x64",
    "bucket": "luci.chrome.try",
    "builder": "Win x64 Builder Perf",
    "dimensions": [
      {
        "key": "pool",
        "value": "chrome.tests.pinpoint"
      },
      {
        "key": "os",
        "value": "Windows-10-19043.1052"
      },
      {
        "key": "gpu",
        "value": "1002:1638-10.0.19041.868"
      },
      {
        "key": "synthetic_product_name",
        "value": "OMEN by HP Laptop 16-c0xxx [ ] (HP)"
      }
    ],
    "repository": "chromium",
    "scheduler": {
      "budget": 3.0,
      "costs": {
        "functional": 0.5,
        "performance": 1.0,
        "try": 0.3
      }
    },
    "swarming_server": "https://chrome-swarming.appspot.com"
  },
  "win-10_laptop_low_end-perf": {
    "browser": "release_x64",
    "bucket": "luci.chrome.try",
    "builder": "Win x64 Builder Perf",
    "dimensions": [
      {
        "key": "pool",
        "value": "chrome.tests.pinpoint"
      },
      {
        "key": "synthetic_product_name",
        "value": "HP Laptop 15-bs1xx [Type1ProductConfigId] (HP)"
      },
      {
        "key": "gpu",
        "value": "8086:1616-20.19.15.5070"
      },
      {
        "key": "os",
        "value": "Windows-10-18363.476"
      }
    ],
    "repository": "chromium",
    "scheduler": {
      "budget": 3.0,
      "costs": {
        "functional": 0.5,
        "performance": 1.0,
        "try": 0.3
      }
    },
    "swarming_server": "https://chrome-swarming.appspot.com"
  }
}
"""

def Get(name):
  configurations = namespaced_stored_object.Get(BOT_CONFIGURATIONS_KEY) or {}
  configuration = configurations.get(name)
  if configuration is None:
    raise ValueError('Bot configuration not found: "%s"' % (name,))
  if 'alias' in configuration:
    return configurations[configuration['alias']]
  return configuration


@ndb.tasklet
def GetAliasesAsync(bot):
  aliases = {bot}
  configurations = yield namespaced_stored_object.GetAsync(
      BOT_CONFIGURATIONS_KEY)
  if not configurations or bot not in configurations:
    raise ndb.Return(aliases)
  if 'alias' in configurations[bot]:
    bot = configurations[bot]['alias']
    aliases.add(bot)
  for name, configuration in configurations.items():
    if configuration.get('alias') == bot:
      aliases.add(name)
  raise ndb.Return(aliases)


def List():
  try:
    bot_configurations = namespaced_stored_object.Get(BOT_CONFIGURATIONS_KEY)
    canonical_names = [
        name for name, value in bot_configurations.items() if 'alias' not in value
    ]
    if six.PY2:
      return sorted(canonical_names, key=string.lower)
    return sorted(canonical_names, key=str.lower)
  except Exception as e:
    if utils.IsStagingEnvironment():
      # staging environment does not have the setup with id=1 in multipart
      # entity. So we need a hack here to store the record there.
      import json
      key = BOT_CONFIGURATIONS_KEY
      config_value_json = BOT_CONFIG.strip()
      config_value = json.loads(config_value_json)
      namespaced_stored_object.SetExternal(key, config_value)
      namespaced_stored_object.Set(key, config_value)
    return []

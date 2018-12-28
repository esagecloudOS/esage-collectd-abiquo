# Introduction

collectd-abiquo is a [collectd](http://www.collectd.org/) writer plugin that sends the values collected by collectd to the Abiquo API.

The sent data is formatted as [PUTVAL JSON format](https://collectd.org/wiki/index.php/Plugin:Write_HTTP#JSON_Example) like in the collectd [write_http](https://collectd.org/wiki/index.php/Plugin:Write_HTTP) plugin

collectd-abiquo is largely influenced by [collectd-librato](https://github.com/librato/collectd-librato) and [collectd-carbon](https://github.com/indygreg/collectd-carbon)

# Installation

## Using chef

There is a [Chef cookbook](https://github.com/abiquo/collectd-abiquo-cookbook) available that will install and configure the collectd-abiquo plugin.

## From source

In collect's config file, load the python plugin:

```xml
<LoadPlugin "python">
	Globals true
</LoadPlugin>
```

And configure the collectd-abiquo plugin:

```xml
<Plugin "python">
	# abiquo-writer.py is at /opt/collectd-abiquo/abiquo-writer.py
    ModulePath "/opt/collectd-abiquo/"

    Import "abiquo-writer"

    <Module "abiquo-writer">
        URL "http://example.com/api/cloud/vdcs/1/vapps/1/vms/1/metrics/collectd"
        Authentication "basic"
        Username "xxx"
        Password "yyy"
    </Module>
</Plugin>
```

# Configuration

Available configuration parameters in <Module> config section in collectd config file:

Name | Description | Default value
-----|-------------| -------------
`URL` | URL to which the values are submitted to | None
`TypesDB` | File defining the collectd types | /usr/share/collectd/types.db
`FlushIntervalSecs` | Send values to Abiquo API each FlushIntervalSecs | 30
`Authentication` | Authorization protocol: 'oauth' or 'basic' | None
`ApplicationKey` | OAuth application key used to authenticate to the Abiquo API | None
`ApplicationSecret` | OAuth application secret used to authenticate to the Abiquo API | None
`AccessToken` | OAuth access token used to authenticate to the Atobiquo API | None
`AccessTokenSecret` | OAuth access token secret used to authenticate to the Abiquo API | None
`Username` | User for Basic authentication | None
`Password` | Password for Basic authentication | None
`VerifySSL` | Check host's SSL certificate | True

# License and authors

* Author: Enric Ruiz (enric.ruiz@abiquo.com)

Copyright 2015 Abiquo Holdings S.L.

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

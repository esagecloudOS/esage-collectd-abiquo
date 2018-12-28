#
# Copyright 2015 Abiquo Holdings S.L.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
import collectd
import json
import requests
import time
import threading

from requests_oauthlib import OAuth1

VERSION = '0.0.1'

OAUTH_PROTOCOL = 0
BASIC_AUTH_PROTOCOL = 1

AUTH_PROTOCOLS = {
    'oauth' : OAUTH_PROTOCOL,
    'basic' : BASIC_AUTH_PROTOCOL
}

plugin_name = 'abiquo-writer'

config = { 
    'url' : None,
    'types_db' : '/usr/share/collectd/types.db',
    'flush_interval_secs' : 30,
    'flush_max_values' : 600,
    'flush_timeout_secs' : 15,
    'authentication' : None,
    'app_key' : None,
    'app_secret' : None,
    'access_token' : None,
    'access_token_secret' : None,
    'username' : None,
    'password' : None,
    'auth' : None,
    'verify_ssl' : True
}

types_db = { }

def abiquo_config(c):
    global config

    for child in c.children:
        val = child.values[0]

        if child.key == 'URL':
            config['url'] = val
        elif child.key == 'Authentication':
            if not val in AUTH_PROTOCOLS:
                raise Exception("%s: Invalid authorization protocol '%s'" \
                    % (plugin_name, val))  
            config['authentication'] = AUTH_PROTOCOLS.get(val)
        elif child.key == 'ApplicationKey':
            config['app_key'] = val
        elif child.key == 'ApplicationSecret':
            config['app_secret'] = val
        elif child.key == 'AccessToken':
            config['access_token'] = val
        elif child.key == 'AccessTokenSecret':
            config['access_token_secret'] = val
        elif child.key == 'Username':
            config['username'] = val
        elif child.key == 'Password':
            config['password'] = val
        elif child.key == 'VerifySSL':
            config['verify_ssl'] = True
        elif child.key == 'TypesDB':
            config['types_db'] = val
        elif child.key == 'FlushIntervalSecs':
            try:
                config['flush_interval_secs'] = int(float(val))
            except:
                raise Exception("%s: Invalid value for FlushIntervalSecs: '%s'" \
                    % (plugin_name, val))

    if not config['url']:
        raise Exception("%s: Invalid URL: '%s'" % (plugin_name, config['url']))

    auth_protocol = config['authentication']
    if auth_protocol == OAUTH_PROTOCOL:
        app_key = config['app_key']
        app_secret = config['app_secret']
        access_token = config['access_token']
        access_token_secret = config['access_token_secret']
        config['auth'] = OAuth1(app_key, app_secret, access_token, access_token_secret)
    elif auth_protocol == BASIC_AUTH_PROTOCOL:
        username = config['username']
        password = config['password']
        config['auth'] = (username, password)

    parse_types_file(config['types_db'])

def abiquo_init():
    collectd.register_write(abiquo_write, data={ 'lock' : threading.Lock(), \
        'last_flush' : get_current_time(), 'values' : [] })

def parse_types_file(file):
    global types_db

    types = open(file, 'r')
    for line in types:
        fields = line.split()

        if len(fields) < 2:
            continue

        type_name = fields[0]
    
        if type_name[0] == '#':
            continue
    
        datasources = { 'dsnames' : [], 'dstypes' : [] }
        for ds in fields[1:]:
            ds = ds.rstrip(',')
            ds_fields = ds.split(':')
    
            if len(ds_fields) != 4:
                collectd.warning("%s: cannot parse data source '%s' of type '%s'" \
                    % (plugin_name, ds, type_name))
                continue
    
            datasources['dsnames'].append(ds_fields[0])
            datasources['dstypes'].append(ds_fields[1])

        datasources['length'] = len(datasources['dsnames'])
        types_db[type_name] = datasources
    
    types.close()

def abiquo_write(value_list, data):
    if value_list.type not in types_db:
        collectd.warning("%s: Unknown type '%s'. Types database (%s) properly configured?" % \
                         (plugin_name, value_list.type, config['types_db']))
        return

    value_type = types_db[value_list.type]
    if value_type['length'] != len(value_list.values):
        collectd.warning('%s: differing number of values for type %s' % \
                         (plugin_name, value_list.type))
        return

    data['lock'].acquire()

    data['values'].append({
        "values" : value_list.values,
        "dsnames" : value_type['dsnames'],
        "dstypes" : value_type['dstypes'],
        "time" : value_list.time,
        "interval" : value_list.interval,
        "host" : value_list.host,
        "plugin" : value_list.plugin,
        "plugin_instance" : value_list.plugin_instance,
        "type" : value_list.type,
        "type_instance" : value_list.type_instance
    })

    current_time = get_current_time()
    last_flush = current_time - data['last_flush']
    length = len(data['values'])

    if length == 0 or (last_flush < config['flush_interval_secs'] and \
        length < config['flush_max_values']):
        data['lock'].release()
        return

    request_body = json.dumps(data['values'])

    data['values'] = []
    data['last_flush'] = current_time
    data['lock'].release()

    try:
        response = requests.post(config['url'], 
                                headers={'Content-type' : 'application/json'},
                                auth=config['auth'],
                                data=request_body,
                                timeout=config['flush_timeout_secs'],
                                verify=config['verify_ssl'])
        if not response.ok:
            collectd.warning("%s: Failed to post metrics to '%s': Code: %d. Response: %s" % \
                             (plugin_name, config['url'], response.status_code, response.text))
    except Exception as e:
        collectd.warning("%s: Failed to post metrics to '%s': %s" % \
                             (plugin_name, config['url'], str(e)))

def get_current_time():
    """
    Return the current time as epoch seconds
    """
    return int(time.mktime(time.localtime()))

collectd.register_config(abiquo_config)
collectd.register_init(abiquo_init)
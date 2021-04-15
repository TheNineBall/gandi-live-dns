#!/usr/bin/env python
# encoding: utf-8
'''
Gandi v5 LiveDNS - DynDNS Update via REST API and CURL/requests

@author: cave
License GPLv3
https://www.gnu.org/licenses/gpl-3.0.html

Created on 13 Aug 2017
http://doc.livedns.gandi.net/ 
http://doc.livedns.gandi.net/#api-endpoint -> https://dns.gandi.net/api/v5/
'''

import requests, json
import config
import argparse

headers = {"Content-Type": "application/json", "Authorization": "Apikey " + config.api_secret}
api_endpoint = 'https://api.gandi.net/v5/livedns/'


def get_dynip(ifconfig_provider):
    ''' find out own IPv4 at home <-- this is the dynamic IP which changes more or less frequently
    similar to curl ifconfig.me/ip, see config.py for details to ifconfig providers
    ''' 
    r = requests.get(ifconfig_provider)
    r._content = r._content.decode('utf-8')
    print('Checking dynamic IP: ' , r._content.strip('\n'))
    return r.content.strip('\n')


def get_dnsip(subdomain):
    ''' find out IP from first Subdomain DNS-Record
    List all records with name "NAME" and type "TYPE" in the zone UUID
    GET /zones/<UUID>/records/<NAME>/<TYPE>:
    
    The first subdomain from config.subdomain will be used to get   
    the actual DNS Record IP
    '''

    url = api_endpoint + 'domains/' + config.domain + "/records/" + subdomain
    u = requests.get(url + "/A", headers=headers)
    json_object = json.loads(u._content)
    if u.status_code == 200:
        print('Checking IP from DNS Record' , config.subdomains[0], ':', json_object['rrset_values'][0].encode('ascii','ignore').decode('utf-8').strip('\n'))
        return u'{}'.format(json_object['rrset_values'][0].encode('ascii','ignore')).strip('\n')
    else:
        print('Error: HTTP Status Code ', u.status_code, 'when trying to get IP from subdomain', config.subdomains[0])
        print(json_object['message'])
        exit()


def update_records(dynIP, subdomain):
    ''' update DNS Records for Subdomains 
        Change the "NAME"/"TYPE" record from the zone UUID
        PUT /zones/<UUID>/records/<NAME>/<TYPE>:
        curl -X PUT -H "Content-Type: application/json" \
                    -H 'X-Api-Key: XXX' \
                    -d '{"rrset_ttl": 10800,
                         "rrset_values": ["<VALUE>"]}' \
                    https://dns.gandi.net/api/v5/zones/<UUID>/records/<NAME>/<TYPE>
    '''
    url = api_endpoint + 'domains/' + config.domain + '/records/' + subdomain
    payload = {"items": [{"rrset_ttl": config.ttl, "rrset_values": [dynIP], "rrset_type": "A"}]}
    u = requests.put(url, data=json.dumps(payload), headers=headers)
    json_object = json.loads(u._content)

    if u.status_code == 201:
        print('Status Code:', u.status_code, ',', json_object['message'], ', IP updated for', subdomain)
        return True
    else:
        print('Error: HTTP Status Code ', u.status_code, 'when trying to update IP from subdomain', subdomain)
        exit()


def main(force_update, verbosity):

    if verbosity:
        print("verbosity turned on - not implemented by now")
   
    # compare dynIP and DNS IP
    dynIP = get_dynip(config.ifconfig)
    
    if force_update:
        print("Going to update/create the DNS Records for the subdomains")
        for sub in config.subdomains:
            update_records(dynIP, sub)
    else:
        for sub in config.subdomains:
            if dynIP == get_dnsip(sub):
                print("IP Address Match - no further action")
            else:
                print("IP Address Mismatch - going to update the DNS Records for the subdomains with new IP", dynIP)
                update_records(dynIP, sub)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', help="increase output verbosity", action="store_true")
    parser.add_argument('-f', '--force', help="force an update/create", action="store_true")
    args = parser.parse_args()

    main(args.force, args.verbose)

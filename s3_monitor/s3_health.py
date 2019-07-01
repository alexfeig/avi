import logging
import requests
from avi.sdk.avi_api import ApiSession
import socket
import dns.resolver
import json
import sys
from requests.packages import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# Set to DEBUG for more information
logging.basicConfig(filename='s3_health.log', level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

# Controller connectivity
controller_ip = "5.5.5.5"
controller_username = "admin"
controller_password = "abcd123"
controller_tenant = "admin"

# Avi pool name
pool_name = "test"

# DNS
nameserver_1 = "8.8.8.8"
nameserver_2 = "8.8.4.4"

# S3 parameters
s3_bucket = "fsdafadsfd.s3-us-east-2.amazonaws.com"
s3_url = "s3.amazonaws.com"


class AviConfig:
    """
    Class that handles connection to the Avi API

    Functions:

        getPoolMembers: returns a dict of servers in a pool
        removePoolMember: removes a pool member by IP address
        addPoolMember: adds a pool member by IP address on port

    """
    api = ApiSession.get_session(
        controller_ip, controller_username, controller_password, controller_tenant)
    pool_obj = api.get_object_by_name('pool', pool_name)

    def getPoolMembers(self):
        try:
            poolmembers = self.pool_obj['servers']

            return poolmembers
        except:
            logging.critical('[FAIL] No members in pool!')
            sys.exit(1)

    def removePoolMember(self, addrip, hostname):
        pool_uuid = self.pool_obj['uuid']

        pool = {
            "delete": {
                "servers": [
                    {'ip': {
                    'addr': addrip,
                    'type': 'V4'}
                }]}
        }

        self.api.patch('pool/%s' % (pool_uuid), data=json.dumps(pool))
        logging.info('[REMOVE] Removing %s from pool', addrip)

    def addPoolMember(self):
        ip = getIP()
        pool_uuid = self.pool_obj['uuid']

        pool = {
            "add": {
                "servers": [{'ip': {
                    'addr': ip,
                    'type': 'V4'
                }}]
            }
        }

        self.api.patch('pool/%s' % (pool_uuid), data=json.dumps(pool))
        logging.info('[ADD] Adding %s to pool', ip)


def getIP():
    """
    Uses the dnspython library to look up IP addresses of the
    s3_url variable using nameserver_1 and nameserver_2.

    Returns an IP address as a string.
    """
    resolver = dns.resolver.Resolver(configure=False)
    resolver.nameservers = [nameserver_1, nameserver_2]

    try:
        answer = resolver.query(s3_url)
        # There may be multiple answers, select the first one.
        ip = answer[0]
    except:
        logging.critical('[FAIL] DNS not responding!')

    return str(ip)


def testPoolMember():
    """
    Runs an HTTPS request against the IP address. If it replies back with
    NoSuchBucket it will assume it's S3 and leave it in the pool. If it doesn't
    reply with NoSuchBucket or the host is offline, it will remove the IP and 
    run addPoolMember(). This will then find a new server and add it to the pool
    """
    Avi = AviConfig()
    pool = Avi.getPoolMembers()
    for index, item in enumerate(pool):
        addrip = item['ip']['addr']
        hostname = item['hostname']
        addr = "https://" + item['ip']['addr']

        try:
            r = requests.get(addr, headers={
                'Host': '%s' % (s3_bucket)}, verify=False, timeout=1)

            # If the host is S3, it'll reply back with NoSuchBucket based on the
            # phone S3 bucket specified in the s3_bucket variable.
            if "NoSuchBucket" in r.text:
                logging.info('[DETECTED] S3 detected on %s', addrip)

            else:
                logging.warning('[NOT DETECTED] S3 NOT detected on %s', addrip)
                Avi.removePoolMember(addrip, hostname)
                Avi.addPoolMember()

        # If the host is offline, remove/add
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            logging.warning('[OFFLINE] %s is offline', addrip)
            Avi.removePoolMember(addrip, hostname)
            Avi.addPoolMember()


if __name__ == "__main__":
    """
    Main function
    """
    testPoolMember()

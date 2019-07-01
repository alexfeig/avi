s3_health
=========

Monitors S3 endpoint health and adds/removes S3 endpoints from a pool if they are bad.

Meant to be run via cron.

# Variables
The following variables should be set:

| Variable              | Description                                                                                                                                                                       |
|-----------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `controller_ip`       | IP address of the controller. If this is a cluster, just pick one                                                                                                                 |
| `controller_username` | Username for accessing the controller. Needs administrator access on the `controller_tenant`.                                                                                     |
| `controller_password` | Password                                                                                                                                                                          |
| `controller_tenant`   | Tenant the pool is in                                                                                                                                                             |
| `pool_name`           | Pool name (must be unique)                                                                                                                                                        |
| `nameserver_1`        | First DNS to use                                                                                                                                                                  |
| `nameserver_2`        | Second DNS                                                                                                                                                                        |
| `s3_bucket`           | S3 bucket to test against. Note that this script expects `NoSuchBucket` as a return value to assume it's S3. This means this should be a unique and (very) unlikely bucket name.  |
| `s3_url`              | S3 URL to check against. This can be either global (s3.amazonaws.com) or something local, such as `s3.us-east-1.amazonaws.com`                                                    |

# Other bits
If you want to up the logging level, change `level=logging.INFO` to `level=logging.DEBUG`.

# Known Limitations
Servers in a pool must have a `Server Name` that is the IP address (or blank, Avi will change the `Server Name` to the IP once created). Failure to do so will result in the server not getting removed.

There is also a slight chance that if it has to remove multiple IP addresses (shouldn't happen often) that a DNS lookup could return the same IP address twice. If this happens, it only gets added once. The net
effect of this is that you may lose a pool member.
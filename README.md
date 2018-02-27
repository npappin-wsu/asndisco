# asndisco
A tool to discover your top ASN's by bandwidth.

## Splunk Search
```
host="bfwm-itb.net.wsu.edu" NOT (dest_ip="134.121.0.0/16" OR dest_ip="192.94.21.0/24" OR dest_ip="69.166.36.0/22") | rex field=dest_ip "(?<three_oct>\d+\.\d+\.\d+)" | stats sum(bytes),sum(bytes_in),sum(bytes_out),count by three_oct | sort 0 - sum(bytes)
```

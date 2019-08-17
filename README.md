# asndisco
A tool to discover your top ASN's by bandwidth.

## Splunk Search
```
host="bfwm-itb.net.wsu.edu" NOT (dest_ip="69.166.43.0/24" OR dest_ip="69.166.44.0/22" OR dest_ip="69.166.48.0/21" OR dest_ip="69.166.56.0/22" OR dest_ip="134.121.0.0/16" OR dest_ip="192.94.21.0/24" OR dest_ip="198.17.13.0/24") index=pan_logs | rex field=dest_ip "(?<three_oct>\d+\.\d+\.\d+)" | stats sum(bytes),sum(bytes_in),sum(bytes_out),count by three_oct | sort 0 - sum(bytes)
```

OR

```
host="bfwm-itb.net.wsu.edu" dest_zone=Untrust index=pan_logs | rex field=dest_ip "(?<three_oct>\d+\.\d+\.\d+)" | stats sum(bytes),sum(bytes_in),sum(bytes_out),count by three_oct | sort 0 - sum(bytes)
```
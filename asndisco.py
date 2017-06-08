#!/usr/bin/env python3

import ipaddress, requests, argparse

parser = argparse.ArgumentParser()
parser.add_argument('--cached', action="store_true", default=False)
args = parser.parse_args()

def getDataTable():
  if args.cached == True:
    data = open('data-raw-table', 'r')
    text = data.read()
    #print(text)
    pass
  else:
    print("begin download")
    data=requests.get("http://thyme.apnic.net/current/data-raw-table")
    print("finish download")
    print(data.status_code)
    text=data.text
  parsed=text.splitlines()[0:100]
  lookupDict = {}
  for line in parsed:
    lineDict = {}
    lineDict['subnet'] = line.split('\t')[0]
    lineDict['asn'] = line.split('\t')[1]
    print(lineDict)
  pass

def main():
  print(args.cached)
  getDataTable()
  pass

if __name__=="__main__":
  main()

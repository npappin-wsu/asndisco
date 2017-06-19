#!/usr/bin/env python3

import ipaddress, requests, argparse

parser = argparse.ArgumentParser()
parser.add_argument('--cached', action="store_true", default=False)
args = parser.parse_args()

def getDataTable():
  if args.cached == True:
    data = open('data-raw-table', 'r')
    text = data.read()
    data.close()
  else:
    print("begin download")
    data = requests.get("http://thyme.apnic.net/current/data-raw-table")
    print("finish download")
    text = data.text
    output = open('data-raw-table', 'w')
    output.write(text)
    output.close()
  parsed = text.splitlines()[0:100]
  lookupDict = []
  for line in parsed:
    lineDict = {}
    lineDict['subnet'] = line.split('\t')[0]
    lineDict['asn'] = line.split('\t')[1]
    print(lineDict)
    lookupDict.append(lineDict)
  return lookupDict

def main():
  asnTable=getDataTable()
  print(asnTable)
  pass

if __name__=="__main__":
  main()

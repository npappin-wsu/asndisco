#!/usr/bin/env python3

import ipaddress, requests, argparse

parser = argparse.ArgumentParser()
parser.add_argument('--cached', action="store_true", default=False)
args = parser.parse_args()

def getDataTable():
  # Use cached copy of datatable from apnic.
  if args.cached == True:
    data = open('data-raw-table', 'r')
    text = data.read()
    data.close()
  # Downlaod and write out a cache to be used later.
  else:
    print("begin download")
    data = requests.get("http://thyme.apnic.net/current/data-raw-table")
    print("finish download")
    # Write the cache.
    text = data.text
    output = open('data-raw-table', 'w')
    output.write(text)
    output.close()
  # debug line
  #parsed = text.splitlines()[0:10000]
  parsed = text.splitlines()
  lookupDict = []
  for line in parsed:
    lineDict = {}
    lineDict['subnet'] = line.split('\t')[0]
    lineDict['asn'] = line.split('\t')[1]
    lookupDict.append(lineDict)
  return lookupDict

def parseDataTable(dataTable):
  for lineDict in dataTable:
    lineDict['network'] = lineDict['subnet'].split('/')[0]
    lineDict['mask'] = int(lineDict['subnet'].split('/')[1])
  print("begin insertsort")
  sortTable = []
  for i in reversed(range(8,33)):
    sortTable.append((i,[]))
  for lineDict in dataTable:
    for thing in sortTable:
      if thing[0] == lineDict['mask']:
        thing[1].append(lineDict)
        break
  print("end insertsort")
  returnTable = []
  for item in sortTable:
    returnTable = returnTable+item[1]
  return returnTable

def main():
  asnTable=getDataTable()
  asnTable=parseDataTable(asnTable)
  print(asnTable)
  for line in asnTable:
    #print(line['mask'])
    pass
  pass

if __name__=="__main__":
  main()

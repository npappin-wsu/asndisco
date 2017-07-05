#!/usr/bin/env python3

import ipaddress, requests, argparse, csv

parser = argparse.ArgumentParser()
parser.add_argument('--cached', action="store_true", default=False)
parser.add_argument('--debug', action="store_true", default=False)
parser.add_argument('-i', '--infile', type=str, dest="infile", required=True)
parser.add_argument('-o', '--outfile', type=str, dest="outfile", required=True)
parser.add_argument('-al', '--asnlimit', type=int, dest="alimit", default=-1)
parser.add_argument('-dl', '--datalimit', type=int, dest="dlimit", default=-1)
args = parser.parse_args()

def getDataTable():
  # Use cached copy of datatable from apnic.
  if args.cached == True:
    data = open('data-raw-table', 'r')
    text = data.read()
    data.close()
  # Downlaod and write out a cache to be used later.
  else:
    if args.debug == True: print("begin download")
    data = requests.get("http://thyme.apnic.net/current/data-raw-table")
    if args.debug == True: print("finish download")
    # Write the cache.
    text = data.text
    output = open('data-raw-table', 'w')
    output.write(text)
    output.close()
  parsed = text.splitlines()[0:args.alimit]
  lookupDict = []
  for line in parsed:
    lineDict = {}
    lineDict['subnet'] = line.split('\t')[0]
    lineDict['asn'] = line.split('\t')[1]
    lookupDict.append(lineDict)
  return lookupDict

def parseDataTable(dataTable):
  for lineDict in dataTable:
    lineDict['network'] = ipaddress.IPv4Network(lineDict['subnet'])
    lineDict['mask'] = int(lineDict['subnet'].split('/')[1])
  if args.debug == True: print("begin insertsort")
  sortTable = []
  for i in reversed(range(8,33)):
    sortTable.append((i,[]))
  for lineDict in dataTable:
    for thing in sortTable:
      if thing[0] == lineDict['mask']:
        thing[1].append(lineDict)
        break
  returnTable = []
  for item in sortTable:
    returnTable = returnTable+item[1]
  if args.debug == True: print("end insertsort")
  return returnTable

def openDataFile(infile):
  data = open(infile, 'r')
  dataFile = csv.DictReader(data, delimiter=',', quotechar='"')
  #dataFile = dataFile.splitlines()[0:args.dlimit]
  outputList = []
  for row in dataFile:
    outputList.append(row)
    row["four_oct"]=ipaddress.ip_address("{}.1".format(row['three_oct']))
  data.close()
  outputList = outputList[0:args.dlimit]
  return outputList

def buildCombinedTable(asnTable,dataTable):
  combinedTable={}
  for dataRow in dataTable:
    if args.debug == True: print(dataRow)
    for asnRow in asnTable:
      if args.debug == True: print(asnRow)
      if dataRow["four_oct"] in asnRow["network"]:
        print("{} in {} at {}".format(dataRow["four_oct"],asnRow["network"],asnRow["asn"]))
        break
  return True

def main():
  asnTable=getDataTable()
  asnTable=parseDataTable(asnTable)
  dataTable=openDataFile(args.infile)
  if args.debug == True: print(asnTable)
  if args.debug == True: print(dataTable)
  combinedTable=buildCombinedTable(asnTable,dataTable)
  if args.debug == True: print(combinedTable)
  returnCode=True
  return returnCode

if __name__=="__main__":
  main()

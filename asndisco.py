#!/usr/bin/env python3

import ipaddress, requests, argparse, csv, time

parser = argparse.ArgumentParser()
parser.add_argument("--cached", action="store_true", default=False)
parser.add_argument("--debug", action="store_true", default=False)
parser.add_argument("-i", "--infile", type=str, dest="infile", required=True)
parser.add_argument("-o", "--outfile", type=str, dest="outfile", required=True)
parser.add_argument("-al", "--asnlimit", type=int, dest="alimit", default=-1)
parser.add_argument("-dl", "--datalimit", type=int, dest="dlimit", default=-1)
args = parser.parse_args()


def getDataTable():
    # Use cached copy of datatable from apnic.
    if args.cached == True:
        data = open("data-raw-table", "r")
        text = data.read()
        data.close()
    # Downlaod and write out a cache to be used later.
    else:
        if args.debug == True:
            print("begin download")
        data = requests.get("http://thyme.apnic.net/current/data-raw-table")
        if args.debug == True:
            print("finish download")
        # Write the cache.
        text = data.text
        output = open("data-raw-table", "w")
        output.write(text)
        output.close()
    parsed = text.splitlines()[0 : args.alimit]
    lookupDict = []
    for line in parsed:
        lineDict = {}
        lineDict["subnet"] = line.split("\t")[0]
        lineDict["asn"] = line.split("\t")[1]
        lookupDict.append(lineDict)
    return lookupDict


def parseDataTable(dataTable):
    if args.debug == True:
        print("build dict started")
    for lineDict in dataTable:
        lineDict["network"] = ipaddress.IPv4Network(lineDict["subnet"])
        lineDict["mask"] = int(lineDict["subnet"].split("/")[1])
    if args.debug == True:
        print("build dict complete")
    if args.debug == True:
        print("begin insertsort")
    sortTable = []
    for i in reversed(range(8, 33)):
        sortTable.append((i, []))
    for lineDict in dataTable:
        for thing in sortTable:
            if thing[0] == lineDict["mask"]:
                thing[1].append(lineDict)
                break
    returnTable = []
    for item in sortTable:
        returnTable = returnTable + item[1]
    if args.debug == True:
        print("end insertsort")
    return returnTable


def openDataFile(infile):
    data = open(infile, "r")
    dataFile = csv.DictReader(data, delimiter=",", quotechar='"')
    outputList = []
    for row in dataFile:
        outputList.append(row)
        row["four_oct"] = ipaddress.ip_address("{}.1".format(row["three_oct"]))
    data.close()
    outputList = outputList[0 : args.dlimit]
    return outputList


def buildCombinedTable(asnTable, dataTable):
    combinedTable = {}
    detailedTable = []
    dataTableLen = len(dataTable)
    progress = int()
    smoothedList = []
    startTime = time.time()
    for dataRow in dataTable:
        if args.debug == True:
            #            print(dataRow)
            pass
        for asnRow in asnTable:
            if args.debug == True:
                #                print(asnRow)
                pass
            if dataRow["four_oct"] in asnRow["network"]:
                dictToAppend = {}
                dictToAppend["asn"] = asnRow["asn"]
                dictToAppend["network"] = asnRow["network"]
                dictToAppend["sum(bytes)"] = dataRow["sum(bytes)"]
                dictToAppend["sum(bytes_in)"] = dataRow["sum(bytes_in)"]
                dictToAppend["sum(bytes_out)"] = dataRow["sum(bytes_out)"]
                dictToAppend["count"] = dataRow["count"]
                try:
                    combinedTable[asnRow["asn"]]
                except KeyError:
                    combinedTable[asnRow["asn"]] = {}
                try:
                    combinedTable[asnRow["asn"]]["sum(bytes)"] = combinedTable[
                        asnRow["asn"]
                    ]["sum(bytes)"] + int(dataRow["sum(bytes)"])
                    combinedTable[asnRow["asn"]]["sum(bytes_in)"] = combinedTable[
                        asnRow["asn"]
                    ]["sum(bytes_in)"] + int(dataRow["sum(bytes_in)"])
                    combinedTable[asnRow["asn"]]["sum(bytes_out)"] = combinedTable[
                        asnRow["asn"]
                    ]["sum(bytes_out)"] + int(dataRow["sum(bytes_out)"])
                    combinedTable[asnRow["asn"]]["count"] = combinedTable[
                        asnRow["asn"]
                    ]["count"] + int(dataRow["count"])
                except KeyError:
                    combinedTable[asnRow["asn"]]["sum(bytes)"] = 0
                    combinedTable[asnRow["asn"]]["sum(bytes)"] = combinedTable[
                        asnRow["asn"]
                    ]["sum(bytes)"] + int(dataRow["sum(bytes)"])
                    combinedTable[asnRow["asn"]]["sum(bytes_in)"] = 0
                    combinedTable[asnRow["asn"]]["sum(bytes_in)"] = combinedTable[
                        asnRow["asn"]
                    ]["sum(bytes_in)"] + int(dataRow["sum(bytes_in)"])
                    combinedTable[asnRow["asn"]]["sum(bytes_out)"] = 0
                    combinedTable[asnRow["asn"]]["sum(bytes_out)"] = combinedTable[
                        asnRow["asn"]
                    ]["sum(bytes_out)"] + int(dataRow["sum(bytes_out)"])
                    combinedTable[asnRow["asn"]]["count"] = 0
                    combinedTable[asnRow["asn"]]["count"] = combinedTable[
                        asnRow["asn"]
                    ]["count"] + int(dataRow["count"])
                print(
                    "{} in {} at {}".format(
                        dataRow["four_oct"], asnRow["network"], asnRow["asn"]
                    )
                )
                print(dictToAppend)
                detailedTable.append(dictToAppend)
                break
        progress = progress + 1
        timeElapsed = time.time() - startTime
        estimatedTime = (timeElapsed / (progress / dataTableLen)) - timeElapsed
        smoothedList.append(estimatedTime)
        if len(smoothedList) > 25:
            smoothedList = smoothedList[1:]
        smoothedTime = 0
        if len(smoothedList) > 0:
            smoothedTime = int((sum(smoothedList) / len(smoothedList)) - 12.5)
        if progress % 10 == 0:
            print(
                "{}/{} Elapsed:{} Estimated:{} Smoothed:{}".format(
                    progress,
                    dataTableLen,
                    int(timeElapsed),
                    int(estimatedTime),
                    smoothedTime,
                )
            )
    return combinedTable, detailedTable


def main():
    asnTable = getDataTable()
    asnTable = parseDataTable(asnTable)
    dataTable = openDataFile(args.infile)
    if args.debug == True:
        print("\nBegin AsnTable")
        # print(asnTable)
        print("\nEnd AsnTable\n\n")
    if args.debug == True:
        print("\nBegin dataTable")
        # print(dataTable)
        print("\nEnd dataTable\n\n")
    combinedTable, detailedTable = buildCombinedTable(asnTable, dataTable)
    if args.debug == True:
        print(detailedTable)
        print(len(combinedTable))
    returnCode = True
    return returnCode


if __name__ == "__main__":
    main()

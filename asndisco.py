#!/usr/bin/env python3

import ipaddress, requests, argparse, csv, time, pickle, requests, json

parser = argparse.ArgumentParser()
# parser.add_argument("--cached", action="store_true", default=True)
# parser.add_argument("--debug", action="store_true", default=True)
parser.add_argument("--cached", action="store_true", default=False)
parser.add_argument("--debug", action="store_true", default=False)
# parser.add_argument(
#     "-i", "--infile", type=str, dest="infile", default=".\\19sept15_outbound.csv"
# )
# parser.add_argument(
#     "-o", "--outfile", type=str, dest="outfile", default=".\\19sept15_obSummed.csv"
# )
parser.add_argument("-i", "--infile", type=str, dest="infile", required=True)
parser.add_argument("-o", "--outfile", type=str, dest="outfile", required=True)
parser.add_argument("-al", "--asnlimit", type=int, dest="alimit", default=-1)
parser.add_argument("-dl", "--datalimit", type=int, dest="dlimit", default=-1)
parser.add_argument("-nl", "--namelimit", type=int, dest="nlimit", default=-1)
args = parser.parse_args()


def getDataTable():
    # Downlaod IP network to ASN data table.
    if args.debug == True:
        print("begin download")
    data = requests.get("http://thyme.apnic.net/current/data-raw-table")
    if args.debug == True:
        print("finish download")
    # Write the cache.
    text = data.text
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
    # Builds the sorting table
    sortTable = []
    for i in reversed(range(8, 33)):
        sortTable.append((i, []))
    # Reads through the dataTable and sorts each line into a dictionary by subnet mask.
    for lineDict in dataTable:
        for thing in sortTable:
            if thing[0] == lineDict["mask"]:
                thing[1].append(lineDict)
                # print(lineDict)
                break
    sortedTable = []
    # Recombines the table sorted into a single list.
    for item in sortTable:
        sortedTable = sortedTable + item[1]
        # print(item)
    if args.debug == True:
        print("end insertsort")
    # Index based on first octet.
    if args.debug == True:
        print("begin indexing")
    returnTable = {}
    for i in range(1, 256):
        returnTable[int(i)] = []
    for line in sortedTable:
        first_oct = int(line["subnet"].split(".")[0])
        returnTable[first_oct].append(line)
        # for thing in returnTable:
        #     if thing[0] == int(line["subnet"].split(".")[0]):
        #         thing[1].append(line)
        #         break
    if args.debug == True:
        print("end indexing")
    return returnTable


def getNameTable():
    if args.debug == True:
        print("Begin name table")
    data = requests.get("http://ftp.arin.net/info/asn.txt")
    text = data.text
    asnDict = {}
    parsed = text.splitlines()[0:args.nlimit]
    for line in parsed:
        # print(line)
        try:
            asn=int(line.split()[0])
            asnDict[asn] = {}
            asnDict[asn]["name"] = line.split()[1]
        except ValueError:
            pass
        except IndexError:
            pass
    if args.debug == True:
        print("End name table")
    return asnDict


def openDataFile(infile):
    data = open(infile, "r")
    dataFile = csv.DictReader(data, delimiter=",", quotechar='"')
    outputList = []
    for row in dataFile:
        if row["sum(bytes)"] == "":
            row["sum(bytes)"] = 0
        if row["sum(bytes_in)"] == "":
            row["sum(bytes_in)"] = 0
        if row["sum(bytes_out)"] == "":
            row["sum(bytes_out)"] = 0
        outputList.append(row)
        row["four_oct"] = ipaddress.ip_address("{}.1".format(row["three_oct"]))
    data.close()
    outputList = outputList[0 : args.dlimit]
    return outputList


def buildCombinedTable(asnTable, dataTable, nameTable):
    combinedTable = {}
    detailedTable = []
    dataTableLen = len(dataTable)
    progress = int()
    smoothedList = []
    startTime = time.time()
    for dataRow in dataTable:
        if args.debug == True:
            # print(dataRow)
            pass
        first_oct = int(dataRow["three_oct"].split(".")[0])
        if first_oct == 0:
            continue
        for asnRow in asnTable[first_oct]:
            if args.debug == True:
                # print(asnRow)
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
                    asn = int(asnRow["asn"])
                    try:
                        combinedTable[asnRow["asn"]]["name"] = nameTable[asn]["name"]
                    except KeyError:
                        combinedTable[asnRow["asn"]]["name"] = "Unknown"
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
                if args.debug == True:
                    print(
                        "{} in {} at {}".format(
                            dataRow["four_oct"], asnRow["network"], asnRow["asn"]
                        )
                    )
                if args.debug == True:
                    print(dictToAppend)
                    pass
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
            smoothedTime = int((sum(smoothedList) / len(smoothedList)))
        if progress % 100 == 0:
            print(
                "{}/{} Percent:{} Elapsed:{} Estimated:{} Smoothed:{}".format(
                    progress,
                    dataTableLen,
                    int((progress/dataTableLen)*100),
                    int(timeElapsed),
                    int(estimatedTime),
                    smoothedTime,
                )
            )
    return combinedTable, detailedTable


def pickleAll(asnTable, dataTable, nameTable):
    with open("asnTable.pickle", "wb") as f:
        pickle.dump(asnTable, f, pickle.HIGHEST_PROTOCOL)
    with open("dataTable.pickle", "wb") as f:
        pickle.dump(dataTable, f, pickle.HIGHEST_PROTOCOL)
    with open("nameTable.pickle", "wb") as f:
        pickle.dump(nameTable, f , pickle.HIGHEST_PROTOCOL)
    pass


def outputData(combinedTable):
    # print(combinedTable.keys())
    outputList = []
    for key in combinedTable.keys():
        dictToAppend = {}
        dictToAppend["asn"] = key
        dictToAppend["name"] = combinedTable[key]["name"]
        dictToAppend["count"] = combinedTable[key]["count"]
        dictToAppend["sum(bytes)"] = combinedTable[key]["sum(bytes)"]
        dictToAppend["sum(bytes_in)"] = combinedTable[key]["sum(bytes_in)"]
        dictToAppend["sum(bytes_out)"] = combinedTable[key]["sum(bytes_out)"]
        outputList.append(dictToAppend)
    keys = outputList[0].keys()
    # print(sorted(outputList, key=lambda i: i["count"]))
    with open(args.outfile, "w", newline="") as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(outputList)
    return True


def main():
    if args.cached == True:
        with open("asnTable.pickle", "rb") as f:
            asnTable = pickle.load(f)
        with open("nameTable.pickle", "rb") as f:
            nameTable = pickle.load(f)
    else:
        asnTable = getDataTable()
        asnTable = parseDataTable(asnTable)
        nameTable = getNameTable()
    dataTable = openDataFile(args.infile)
    pickleAll(asnTable, dataTable, nameTable)
    if args.debug == True:
        print("\nBegin AsnTable")
        # print(asnTable)
        print("\nEnd AsnTable\n\n")
    if args.debug == True:
        print("\nBegin dataTable")
        # print(dataTable)
        print("\nEnd dataTable\n\n")
    combinedTable, detailedTable = buildCombinedTable(asnTable, dataTable, nameTable)
    if args.debug == True:
        print(detailedTable)
        print(len(combinedTable))
    outputData(combinedTable)
    returnCode = True
    return returnCode


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

import requests
import json
import datetime
import os
import re

class awlAPI():
    """ awlAPI - access to the (Neuss) AWL API

    """
    def __init__(self, configFile = None):
        self.apiUrl = 'https://buergerportal.awl-neuss.de/api/v1/calendar'
        self.strUrl = '/townarea-streets'
        self.townStreets = None

        # get configuration data
        self.confData = self.getconf(configFile)
        # get all streets
        self.townStreets = self.gettownstreets()

        # if we don't have correct data show help
        if not self.confData:
            self.help()
        #else:
        #    self.valstreet()   # not implemented yet


    def getconf(self, configFile):
        """get the config
        configFile = full path and name to the config file, 
                     if not specified awl.conf in script path
        """
        validConf = 0
        try:
            if not configFile:
                configFile = os.path.dirname(__file__) + '/awl.conf'
            with open(configFile) as jf:
                confData = json.load(jf) 

            if confData['config']:
                if confData['config']['StrasseNummer'] or confData['config']['StrasseName']:
                    # do we have a street number or name in the config
                    validConf += 1                  
                if confData['config']['HausNummer']:
                    # we need also the HouseNumnber
                    validConf += 1
            if validConf != 2:
                confData = None
            return confData
        
        except Exception as e:
            print("Error reading configuration file %s: %s -  " % (configFile,e))
            exit(1)

    def gettownstreets(self):
        """get all town streets from the website"""
        try:
            # returns all streetcodes from the website
            resTownStr = requests.get(self.apiUrl + self.strUrl) 
        except Exception as e:
            # we have a problem, then exit
            print('Error getting TownStreets: %s' % e)
            exit(1) 
        
        townStreets = json.loads(resTownStr.text)
        return townStreets

    def getschedule(self, monat = None, tonne = None, jahr = False):
        """ getschedule
        [monat] = the current month of if specified the month of interest 1-12
        [tonne] = all or the type of the waste basket (tonnen farbe: grau,pink - residual waste,
                    yellow - recycle,blue - paper)  
        [jahr] = current month or True for the full year
        """
        args = {
            "streetNum": self.confData['config']['StrasseNummer'],
            "homeNumber": self.confData['config']['HausNummer']
        }
        if not monat:
            args["startMonth"] = datetime.datetime.now().strftime('%b %Y')
        else:
            try:
                if 1 <= int(month) <= 12:
                    print("Valid month")
                else:
                    print("%s, does not look like a valid month" % month) 
                    return None
            except:
                print("%s is not a valid number between 1 and 12" % month)
                pass
                return None
      
        
        if jahr:
            #get the data for the full year
            args["isYear"] = "true" 
        else:
            args["isYear"] = "false" 

        # additional arguments (not used here) 
        args["isTreeMonthRange"] = "false"  # get 3 month range disables isYear
        
        try:
            resSchedule = requests.get(self.apiUrl, params=args)
        except Exception as e:
            print("Error trying to get schedule data: %s" % e)
            exit(1)
        
        scheduleData = json.loads(resSchedule.text)

        # if we got something return the data
        if scheduleData:
            return scheduleData
        else:
        # otherwise return None
            return None
        
    def valstreet(self):
        """ tries to validate the StreetName with HouseNumber to the StreetCode
        """
        if not self.townStreets:
            self.townStreets = self.gettownstreets()

        for item in townStreets:
            hNumbers = re.findall("[0-9]+", item["strasseBezeichnung"])
            if len(hNumbers) > 0:
                print("we have %i HomeNumber groups" % len(hNumbers))
                if len(hNumbers) % 2:
                    for hN in hNumbers:
                       print(hN)

            ## we have a street name but no street code try to match it to a street code 
            #if self.confData['config']['StrasseName'] and not self.confData['config']['StrasseNummer']:
            #    # do we found the street name in strasseBezeihnung
            #    if self.confData['config']['StrasseName'] in item['strasseBezeichnung']:
            #        # does the strasseBezeichnung has some numbers in
            #        self.confData['config']['StasseNummer'] = item['strasseNummer']
    
    def searchstr(self, searchStr = None):
        """search for a street(s) by pattern 
        then prints the strasseNummer and strasseBezeichnung that can be used for the conf file        
        """
        for item in self.townStreets:
            if searchStr:
                if searchStr in item['strasseBezeichnung']:
                    print("StrasseNummer: %s | StrasseName: %s | BlockedNR: %s" % 
                          (item['strasseNummer'], item['strasseBezeichnung'], 
                           item['blockedHomeNumbers']))
            else:
                print("StrasseNummer: %s | StrasseName: %s | BlockedNR: %s" % 
                (item['strasseNummer'], item['strasseBezeichnung'], 
                 item['blockedHomeNumbers']))
        
    def help(self):
        """display some help"""
        os.system('clear')
        print("No valid awl.conf provided!\n")
        print("You can call awlAPI.searchstr([searchStr='pattern'])")
        print("to retrieve a list of all streets. From that list get the correct streetCode") 
        print("and house number to be entered into the configuration file!")
        print("If more than one street name matches make sure to use the sreet number where the house number is in the list!")
        print("\n\n")


def main():
    apiUrl = 'https://buergerportal.awl-neuss.de/api/v1/calendar'
    streetName = 'Goethestrasse'
    HouseNumber = '39'
    streetCode = None

    chkStreet = requests.get(apiUrl + "/townarea-streets")
    if chkStreet.status_code == 200:
        dataStreet = json.loads(chkStreet.text)

        for item in dataStreet:
        #    print(item["strasseBezeichnung"])
            if item["strasseBezeichnung"] == streetName:
                print(item)
                if item["strasseNummer"] != streetCode:
                    streetCode = item["strasseNummer"]
                    break

        args = {
            "streetNum": streetCode,
            "homeNumber": HouseNumber
        }

        now = datetime.datetime.now()
        #args["startMonth"] = now.year + "-" + now.month
        #args["startMonth"] = "Thu Apr 11 2024" # working
        args["startMonth"] = "APR 2024" # needs to Mon-YYYY or MON YYYY
        args["isTreeMonthRange"] = "false"  # get 3 month range disables isYear
        args["isYear"] = "false"    # if true get the full year

        r = requests.get(apiUrl, params=args)

        data = json.loads(r.text)
        entries = []  # List that holds collection schedule
        for key, value in data.items():
            month_year: list[str] = key.split("-")
            month: int = int(month_year[0]) + 1
            year: int = int(month_year[1])

            for dayValue, wastes in value.items():
                day: int = int(dayValue)
                #for waste in wastes:
                #    entries.append(
                #        Collection(
                #                date=datetime.date(year, month, day),  # Collection date
                #                t=waste,  # Collection type
                #                icon=ICON_MAP.get(waste),  # Collection icon
                #            )
                #        )
                for waste in wastes:
                    print(datetime.date(year, month, day), waste)  # Collection date
                    # print()                               # Collection type

if __name__ == '__main__':
    awl = awlAPI('../littlet.conf')
    ##awl = awlAPI()
    #awl.searchstr("Bergheim")
    #print(awl.confData)
    #main()
    data = awl.getschedule(13)
    
    if data:
        for key, value in data.items():
            month_year: list[str] = key.split("-")
            month: int = int(month_year[0]) + 1
            year: int = int(month_year[1])
            for dayValue, wastes in value.items():
                day: int = int(dayValue)
                for waste in wastes:
                        print(datetime.date(year, month, day), waste)  # Collection date
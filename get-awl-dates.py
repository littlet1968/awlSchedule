#!/usr/bin/env python3

import requests
import json
import datetime
import os

class awlAPI():
    """ awlAPI - access to the (Neuss) AWL API

    """
    def __init__(self, configFile = None):
        self.apiUrl = 'https://buergerportal.awl-neuss.de/api/v1/calendar'
        self.strUrl = '/townarea-streets'
        # get configuration data
        confData = self.getconf(configFile)
        # if we don't have correct data show help
        if not confData:
            self.help() 

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

    def getschedule(self):
        self.confData = self.getconf(self.configFile)
        if self.confData['config']:
            if self.confData['config']['StreetNumber']:
                self.streetNumber = self.confData['config']['StreetNumber']
            if self.confData['config']['StreetName']:
                self.streetName = self.confData['config']['StreetName']

            if not self.streetName or not self.streetName:
                raise Exception(
                    'StreetName or StreetNumber needed but not found in config.')
                      
            if self.confData['config']['HouseNumber']:
                self.bldNumber = self.confData['config']['HouseNumber']
            else:
                raise Exception('Bulding Number needed but not found in config.')


    def valstreet(self):
        """ tries to validate the StreetName with HouseNumber to the StreetCode
        """
        try:
            # returns all streetcodes from the website
            resTownStr = requests.get(self.apiUrl + self.strUrl) 
        except Exception as e:
            # we have a problem, then exit
            print('Error getting TownStreets: %s' % e)
            exit(1)
        
        townStreets = json.loads(resTownStr.text)
        # first case we have already a streetNumber
        # if self.streetNumber:
    
    def getstreets(self, searchStr = None):
        'get all registered streets'
        try:
            # returns all streetcodes from the website
            resTownStr = requests.get(self.apiUrl + self.strUrl) 
        except Exception as e:
            # we have a problem, then exit
            print('Error getting TownStreets: %s' % e)
            exit(1) 
        allStreets = json.loads(resTownStr.text)

        for item in allStreets:
            print("StrasseName: %s | StrasseNummer: %s | BlockedNR: %s" % 
                  (item['strasseBezeichnung'], item['strasseNummer'],
                   item['blockedHomeNumbers']))
        
    def help(self):
        """display some help"""
        os.system('clear')
        print("No valid awl.conf provided!\n")
        print("You can call awlAPI.getstreets([searchStr='pattern'])")
        print("to retrieve a list of all streets. From that list get the correct streetCode") 
        print("and house number to be entered into the configuration file!")




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
    awl = awlAPI('../abfallKalender/awl.conf')
    awl.getstreets()
    #awl = awlAPI()

    #main()

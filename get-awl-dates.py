#!/usr/bin/env python3

import datetime
import json
import os
import re
import sys

import requests


class AwlAPI():
    """awlAPI - access to the (Neuss) AWL API.

    this is a python script to access the AWL API standalone
    """

    def __init__(self, config_file=None):
        """Script initialization stuff."""
        self.api_url = 'https://buergerportal.awl-neuss.de/api/v1/calendar'
        self.str_url = '/townarea-streets'
        self.town_streets = None
        self.waste_bins = ["blau", "braun", "gelb", "grau", "pink"]

        # get configuration data
        self.conf_data = self.getconf(config_file)
        # get all streets
        self.town_streets = self.gettownstreets()

        # if we don't have correct data show help"
        if not self.conf_data:
            self.help()
        # else:
        #    self.valstreet()   # not implemented yet

    def getconf(self, config_file):
        """Get the config.

        config_file = full path and name to the config file,
        if not specified awl.conf in script path
        """
        valid_conf = 0
        try:
            if not config_file:
                config_file = os.path.dirname(__file__) + '/awl.conf'
            with open(config_file, encoding='utf-8') as jf:
                conf_data = json.load(jf)

            if conf_data['config']:
                if conf_data['config']['StrasseNummer'] or \
                   conf_data['config']['StrasseName']:
                    # do we have a street number or name in the config
                    valid_conf += 1
                if conf_data['config']['HausNummer']:
                    # we need also the HouseNumnber
                    valid_conf += 1
            if valid_conf != 2:
                conf_data = None
            else:

            return conf_data

        except Exception as e:
            print(f"Error reading configuration file {config_file} - {e}")
            sys.exit(1)

    def gettownstreets(self):
        """Get all town streets from the website."""
        try:
            # returns all streetcodes from the website
            res_town_str = requests.get(self.api_url + self.str_url,
                                        timeout=10)
        except Exception as e:
            # we have a problem, then exit
            print('Error getting TownStreets: %s' % e)
            sys.exit(1)

        town_streets = json.loads(res_town_str.text)
        return town_streets

    def getschedule(self, monat=None, tonne=None, jahr=False):
        """[getschedule] - get the schedule.

        [monat] = the current month or if specified the month of interest 1-12
        [tonne] = all or the type of the waste bin (tonnen farbe: grau,
                  pink - residual waste,
                  yellow - recycle, blue - paper)  false
        [jahr] = current month or True for the full year
        """
        args = {
            "streetNum": self.conf_data['config']['StrasseNummer'],
            "homeNumber": self.conf_data['config']['HausNummer']
        }

        if not monat:
            args["startMonth"] = datetime.datetime.now().strftime('%b %Y')
        else:
            try:
                if 1 <= int(monat) <= 12:
                    # print("Valid month")
                    args["startMonth"] = datetime.date(
                        datetime.datetime.now().year, 5, 1).strftime('%b %Y')
                else:
                    print(
                        "%s, does not look like a valid month between 1 and 12"
                        % monat)
                    return None
            except Exception:
                print("%s is not a valid number between 1 and 12" % monat)
                pass
                return None

        if jahr:
            # get the data for the full year
            args["isYear"] = "true"
            # get 3 month range disables isYear
            args["isTreeMonthRange"] = "false"
        else:
            args["isYear"] = "false"
            # get 3 month range disables isYear
            args["isTreeMonthRange"] = "true"

        try:
            if tonne in self.waste_bins:
                args["tonne"] = tonne  # is getting ignored ?!?!?!
        except Exception as e:
            print("Not a valid waste bin type spezified: %s" % tonne)
            print("Error %s" % e)
            pass

        # print(args)
        try:
            resSchedule = requests.get(self.api_url, params=args)
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

    def nextpickup(self, tonne=None):
        """Show the next pickup date.

        [tonne] = the type of the waste bin, optional tonne shows the next
        pickup date for specified waste type
        """
        someThingFound = False
        toDay = datetime.datetime.now().day
        toMonth = datetime.datetime.now().month

        if tonne:
            if tonne not in self.waste_bins:
                # print("Not a valid waste type")
                return "Not valid tonne"

        # get the fixtures for the full year in case
        fixtureData = self.getschedule()

        if fixtureData:
            for mY, fixtures in fixtureData.items():
                monthYear = mY.split('-')
                month = int(monthYear[0]) + 1

                for day, pickupTonne in fixtures.items():
                    # do we have a tonne specified and is valid
                    if tonne in self.waste_bins:
                        # is the tonne what we are looking for
                        if tonne not in pickupTonne:
                            # if not continue the loop
                            continue

                    if int(day) >= toDay and int(month) == toMonth:
                        someThingFound = True
                        break
                    elif int(month) == toMonth + 1:
                        # get the first date from next month
                        someThingFound = True
                        # print("Next Month")
                        # print(day, month, pickupTonne)
                        break
                # we found a date break out of the loop
                if someThingFound:
                    break

            if someThingFound:
                year = int(monthYear[1])
                pickupDate = datetime.date(
                    year, month, int(day)).strftime('%A, %d %B %Y')
                # print("Next pickup date %s - %s" %(pickupDate, pickupTonne))
                return pickupDate, pickupTonne

        return None, None

    def valstreet(self):
        """Try to validate the StreetName with HouseNumber to the StreetCode."""
        if not self.town_streets:
            self.town_streets = self.gettownstreets()

        for item in self.town_streets:
            hNumbers = re.findall("[0-9]+", item["strasseBezeichnung"])
            if len(hNumbers) > 0:
                print("we have %i HomeNumber groups" % len(hNumbers))
                if len(hNumbers) % 2:
                    for hN in hNumbers:
                        print(hN)

            # we have a street name but no street code try to match it to a street code
            # if self.conf_data['config']['StrasseName'] and not self.conf_data['config']['StrasseNummer']:
            #    # do we found the street name in strasseBezeihnung
            #    if self.conf_data['config']['StrasseName'] in item['strasseBezeichnung']:
            #        # does the strasseBezeichnung has some numbers in
            #        self.conf_data['config']['StasseNummer'] = item['strasseNummer']

    def searchstr(self, searchStr=None):
        """Search for a street(s) by pattern.

        [searchStr] = the street to search for
        Prints the strasseNummer and strasseBezeichnung that can be used for
        the conf file
        """
        for item in self.town_streets:
            if searchStr:
                if searchStr in item['strasseBezeichnung']:
                    print("StrasseNummer: %s | StrasseName: %s | BlockedNR: %s"
                          % (item['strasseNummer'], item['strasseBezeichnung'],
                             item['blockedHomeNumbers']))
            else:
                print("StrasseNummer: %s | StrasseName: %s | BlockedNR: %s" %
                      (item['strasseNummer'], item['strasseBezeichnung'],
                       item['blockedHomeNumbers']))

    def help(self):
        """Display some help."""
        os.system('clear')
        print("No valid awl.conf provided!\n")
        print("You can call awlAPI.searchstr([searchStr='pattern'])")
        print("to retrieve a list of all streets. From that list get the correct")
        print("streetCode and house number to be entered into the configuration file!")
        print("If more than one street name matches make sure to use the sreet number")
        print("where your house number is in the list!")
        print("\n\n")


def main():
    """My main loop."""
    awl = AwlAPI('../littlet.conf')
    # awl.searchstr("Bergheim")
    # print(awl.conf_data)
    # main()
    # nextPD, nextPT = awl.nextpickup(tonne='blau')
    next_pd, next_pt = awl.nextpickup()

    if next_pd:
        print("Next pickup: %s %s" % (nextPD, ','.join(nextPT)))
    else:
        print("Did not found next pickup"

    # data = awl.getschedule()
    # if data:
    #    for key, value in data.items():
    #        month_year: list[str] = key.split("-")
    #        month: int = int(month_year[0]) + 1
    #        year: int = int(month_year[1])
    #        for dayValue, wastes in value.items():
    #            day: int = int(dayValue)
    #            for waste in wastes:
    #                    print(datetime.date(year, month, day), waste)  # Collection date


# "my Original test case"
def main_old():
    """Old main loop."""
    api_url='https://buergerportal.awl-neuss.de/api/v1/calendar'
    streetName='Goethestrasse'
    HouseNumber='39'
    streetCode=None

    chkStreet=requests.get(api_url + "/townarea-streets")
    if chkStreet.status_code == 200:
        dataStreet=json.loads(chkStreet.text)

        for item in dataStreet:
            #    print(item["strasseBezeichnung"])
            if item["strasseBezeichnung"] == streetName:
                print(item)
                if item["strasseNummer"] != streetCode:
                    streetCode=item["strasseNummer"]
                    break

        args={
            "streetNum": streetCode,
            "homeNumber": HouseNumber
        }

        now=datetime.datetime.now()
        # args["startMonth"] = now.year + "-" + now.month
        # args["startMonth"] = "Thu Apr 11 2024" # working
        args["startMonth"]="APR 2024"  # needs to Mon-YYYY or MON YYYY
        args["isTreeMonthRange"]="false"  # get 3 month range disables isYear
        args["isYear"]="false"    # if true get the full year

        r=requests.get(api_url, params=args)

        data=json.loads(r.text)
        entries=[]  # List that holds collection schedule
        for key, value in data.items():
            month_year: list[str]=key.split("-")
            month: int=int(month_year[0]) + 1
            year: int=int(month_year[1])

            for dayValue, wastes in value.items():
                day: int=int(dayValue)
                # for waste in wastes:
                #    entries.append(
                #        Collection(
                #                date=datetime.date(year, month, day),  # Collection date
                #                t=waste,  # Collection type
                #                icon=ICON_MAP.get(waste),  # Collection icon
                #            )
                #        )
                for waste in wastes:
                    print(datetime.date(year, month, day),
                          waste)  # Collection date
                    # print()                               # Collection type


if __name__ == '__main__':
    main()

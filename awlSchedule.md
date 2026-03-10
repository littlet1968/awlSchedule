## AWL Schedule - get next garbage date
This is a project is a class to collect data from the AWL Buergerportal for the garbage pick up dates

### Processing Flow & Safeguards

1. open a configuration file containing:
  If a configuration file awl.conf is found read the following data out of it:
  - API_URL:  'https://buergerportal.awl-neuss.de/api/v1/calendar'
  - STR_URL: '/townarea-streets'
  - WASTE_BINS: "blau", "braun", "gelb", "grau", "pink"
  - strasseNummer: used to identify the street the garbage is getting picked up
  - strassenBezeichnung: the street name, human readable interpretaion of the StrasseNumber used in the API
  

  If no configuration is found ask the user to enter the street name
  - read all available street names from the API_URL + STR_URL, the returned data is a json of ['strasseNummer', 'strasseBezeichnung', 'blockedHomeNumbers']
  - present a selection box with the collect street names in task before and let the user select which street to use
  - use an input field to ask for the StrasseName
  - compare the entry with the list of available street names collect before
  - save the result in the awl.conf file

2. Get Schedule for this Month
  - retrieve the actual month
  - get schedule dates from the API_URL with the following parameter: 
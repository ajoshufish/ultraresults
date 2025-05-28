#imports
import pandas as pd
import lxml
import openpyxl
import re


# Function to scrape results information from a single event (race) URL. Input is the URL to scrape. It reads the
# information from that URL and adds the event, race, participant, and results information to the database.
def single_event_scrape(url):
    #url = 'https://statistik.d-u-v.org/getresultevent.php?event=104431' #testing url
    
    #Pull basic information from the passed URL
    tables = pd.read_html(url)
    
    tmp = pd.read_html(url, extract_links='body')[5][pd.read_html(url, extract_links='body')[5].columns[2][0]].astype(str)
    tmp.columns = ['Name']
    ath_ids = pd.DataFrame(pd.DataFrame(tmp['Name'].str.split('=').tolist())[1].str.split('\'').tolist())[0]
    event_info = tables[3]
    results_info = tables[5].iloc[:, 0:10]

    race_duration = event_info[1][2].split(' ', 1)[0]
    if(not re.search('^[0-9]+', event_info[1][1])): #unique or first event
        event_title = event_info[1][1].rsplit(' ',1)[0]
    else:
        event_title = event_info[1][1].split(' ', 1)[1].rsplit(' ', 2)[0] #culls out which iteration of the race this is    
    
    if(len(event_info[1][0]) > 10): #multiday, take just the first day as the date the event took place
        race_startdate = event_info[1][0].split('.', 1)[0] + '.'+ event_info[1][0].split('.', 1)[1].split('.', 1)[1]
    else:
        race_startdate = event_info[1][0] 
    
    race_year = pd.to_numeric(race_startdate.rsplit('.',1)[1])

    results_info.columns = ['Rank', 'Time', 'Name', 'City', 'Nation', 'YOB', 'Gender', 'Gender_Rank', 'Category', 'Cat_Rank']
    results_info['Ath_ID'] = ath_ids

    times = results_info['Time']
    if(times[0].split(' ')[1] == 'km'): #dealing with a timed race, strip unit off the end (km)
        duration = times.str.split(' ', expand=True)[0]
    else: #distance event, convert times to seconds
        duration = pd.Series([])
        for i in range(len(times)):
            entry = times.iloc[i]
            if(re.search(r'^[0-9]+d', entry)): #multi-day time
                days = int(entry.split()[0].split('d')[0])
                hrs = int(entry.split()[1].split(':')[0])
                mins = int(entry.split()[1].split(':')[1])
                secs = int(entry.split()[1].split(':')[2])
            else:
                days = 0
                hrs = int(entry.split(':')[0])
                mins = int(entry.split(':')[0])
                secs = int(entry.split(':')[0])
            time = secs + (60 * mins) + (3600 * hrs) + (86400 * days)
            duration[i] = time
    duration.name = 'Duration'
    results_info = pd.concat([results_info, duration], axis = 1)

    path = 'ultra results.xlsx' # we start with a local db

    #gather existing info from the database
    wb = openpyxl.load_workbook(path)
    esh = wb['Event_Info']
    evs = pd.DataFrame(esh.values, columns=next(esh.values)[0:])
    rsh = wb['Race_Info']
    rcs = pd.DataFrame(rsh.values, columns=next(rsh.values)[0:])
    ressh = wb['Results']
    resdf = pd.DataFrame(ressh.values, columns=next(ressh.values)[0:])
    partsh = wb['Participant_Info']
    partdf = pd.DataFrame(partsh.values, columns=next(partsh.values)[0:])

    # Start by processing the Event aspect. Is it already in the database? If not, we gather relevant
    # event information from the event's basic information URL and then add it to our database. 
    # If it is found already then we're good.
    row = []
    if(len(evs['event_id']) > 1): #do we have anything in the list already?
    
        #yes, so let's search it for the event
        if(max(evs['title'].str.find(event_title)) < 0):
        #did not find it, so let's add it
            evid = max(evs['event_id'][1:]) + 1
        
            #first, we need more info about the event -- set up URL for getting more complete event info
            etmp = 'https://statistik.d-u-v.org/' + pd.read_html(url, extract_links='body')[3][2][1][1]
            etab = pd.read_html(etmp)

            #location info
            ev_location = etab[2][1][etab[2][0].str.find('Start in').idxmax()]
            ev_country = ev_location.rsplit('(', maxsplit=1)[1].split(')')[0]
            if(ev_country == 'USA'):
                ev_state = ev_location.rsplit(' ', maxsplit=2)[1]
                ev_city = ev_location.rsplit(' ', maxsplit=2)[0].split(',')[0]
            else: 
                ev_city = ev_location.rsplit(' ', maxsplit=1)[0]
                ev_state = 'N/A'
            ev_url = etab[2][1][etab[2][1].str.find('http').idxmax()]

            row = [evid, event_title, ev_city, ev_state, ev_country, ev_url]

            if len(row) > 0: #append it to table
                esh.append(row)
                wb.save(path)
        
            evs.loc[evid] = row #update our internal event list
        else: evid = evs['title'].str.contains(event_title).idxmax() #found it
    else:
        #no, so let's start the list. as above, gather basic info and add it (as first entry)
        evid = 1
        #first, we need more info about the event -- set up URL for getting more complete event info
        etmp = 'https://statistik.d-u-v.org/' + pd.read_html(url, extract_links='body')[3][2][1][1]
        etab = pd.read_html(etmp)

        #location info
        ev_location = etab[2][1][etab[2][0].str.find('Start in').idxmax()]
        ev_country = ev_location.rsplit('(', maxsplit=1)[1].split(')')[0]
        if(ev_country == 'USA'):
            ev_state = ev_location.rsplit(' ', maxsplit=2)[1]
            ev_city = ev_location.rsplit(' ', maxsplit=2)[0].split(',')[0]
        else: 
            ev_city = ev_location.rsplit(' ', maxsplit=1)[0]
            ev_state = 'N/A'
        ev_url = etab[2][1][etab[2][1].str.find('http').idxmax()]

        row = [evid, event_title, ev_city, ev_state, ev_country, ev_url]

        if len(row) > 0: #append it to table
            esh.append(row)
            wb.save(path)   
        evs.loc[evid] = row #update our internal event list 

    # Next we add Race Info to database (if necessary) -- search existing event list for matching event title to get event id, 
    # then pair with year of results to search event id + year pairs in race list

    evid = evs['event_id'][evs['title'].str.find(event_title).idxmax()] #get the event id
    if len(rcs[(rcs['event_id'] == evid) & (rcs['year'] == race_year) ]) == 0: #we have the event, but not this instance/race
        if(len(rcs['race_id']) > 1): #are we starting the race list from scratch or not
            race_id = max(rcs['race_id'][1:]) + 1 #no, so increment
        else:
            race_id = 1
        rsh.append([race_id, evid, race_duration, race_year])
        wb.save(path)

        rcs.loc[race_id] =  [race_id, evid, race_duration, race_year] #update our internal race list

    # Now to add participants and results -- for each item in the result table:
    # 1) Check the participant table to see if we want to write a new participant entry based on the ath_id, if we do then write it
    # 2) Check the results table for race id + ath_id pairs. if not found, write a result entry.
    resid = 1
    for i in range(len(results_info)): #for each result -- we first handle adding the participant, then adding their result
        entry = results_info.iloc[i]
    
        #does that result's participant already exist in our dataset?
        if(not partdf['ath_id'].eq(entry['Ath_ID']).any()):
            #athlete not found! Let's add them
            partsh.append([entry['Ath_ID'], entry['Name'], entry['YOB'], entry['Gender'], entry['Nation']])
    
        #does the result table already have this specific result for this athlete? (race id + ath_id pair)
        if resdf['race_id'].eq(evid).any(): #does this race have entries already in general?
            #it does, look for the athlete
            if not resdf[resdf['race_id'] == evid]['ath_id'].eq(entry['Ath_ID']).any(): #zero in on those entries, is this athlete yet among them?
                #no, so let's add them       
                if( len(resdf['result_id']) > 1 ):
                    resid = max(max(resdf['result_id'][1:]), resid) + 1   
                else:
                    resid = 1       
                ressh.append([resid, evid, entry['Ath_ID'], entry['Duration'], entry['Rank'], entry['Category'], entry['Cat_Rank'], entry['Gender_Rank']])

        else: #this race does not have any entries, so let's add new entries for this race
                ressh.append([resid, evid, entry['Ath_ID'], entry['Duration'], entry['Rank'], entry['Category'], entry['Cat_Rank'], entry['Gender_Rank']])
    wb.save(path)
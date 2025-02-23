#imports
import pandas as pd
import lxml

#Establish URL for particular event, and pull
url = 'https://statistik.d-u-v.org/getresultevent.php?event=104431'
tables = pd.read_html(url)

#parse results into an initial table
tmp = pd.read_html(url, extract_links='body')[5]['Surname, first name'].astype(str)
tmp.columns = ['Name']

#separate out event information
event_info = tables[3]
event_title = event_info[1][1]
event_distance = event_info[1][2]
event_date = event_info[1][0]

#separate out the results table, including athlete IDs from the relevant URLs
results_info = tables[5].iloc[:, 0:10]
results_info.columns = ['Rank', 'Time', 'Name', 'City', 'Nation', 'YOB', 'Gender', 'Gender_Rank', 'Category', 'Cat_Rank']
ath_ids = pd.DataFrame(pd.DataFrame(tmp['Name'].str.split('=').tolist())[1].str.split('\'').tolist())[0]
results_info['Ath_ID'] = ath_ids

#convert result time to seconds as a unified standard, to be expanded once processing multi-day-centered events 
if(results_info.at[0,'Time'][-1:] == 'h'): #based on hours, format= hh:mm:ss
    hrs = pd.DataFrame(results_info['Time'].str.slice(0,2)).astype(int)
    mins = pd.DataFrame(results_info['Time'].str.slice(3,5)).astype(int)
    secs = pd.DataFrame(results_info['Time'].str.slice(6,8)).astype(int)
    duration = (hrs * 3600) + (mins * 60) + (secs)

results_info['Duration'] = duration

# Add Event Info to database (if necessary) -- search existing event list for the the title
path = 'ultra results.xlsx' # we start with a local db
wb = openpyxl.load_workbook(path)
esh = wb['Event_Info']
evs = pd.DataFrame(esh.values, columns=next(esh.values)[0:])
rsh = wb['Race_Info']
rcs = pd.DataFrame(rsh.values, columns=next(rsh.values)[0:])
ressh = wb['Results']
resdf = pd.DataFrame(ressh.values, columns=next(ressh.values)[0:])
partsh = wb['Participant_Info']
partdf = pd.DataFrame(partsh.values, columns=next(partsh.values)[0:])

row = []
if(len(evs['id']) > 1): #do we have anything in the list already?
    
    #yes, so let's search it
    if(max(evs['Title'].str.find(event_title)) < 0):
    #did not find it, so let's add it
        #first, we need more info about the event -- set up URL for getting more complete event info
        etmp = 'https://statistik.d-u-v.org/' + pd.read_html(url, extract_links='body')[3][2][1][1]
        etab = pd.read_html(etmp)

        #location info
        ev_city = etab[2][1][etab[2][0].str.find('Start in').idxmax()].rsplit(' ', 1)[0].split(',')[0]
        ev_state = etab[2][1][etab[2][0].str.find('Start in').idxmax()].rsplit(' ', 1)[0].split(', ')[1]
        ev_country = etab[2][1][etab[2][0].str.find('Start in').idxmax()].rsplit(' ', 1)[1].replace('(', '').replace(')', '')
        ev_url = etab[2][1][etab[2][1].str.find('http').idxmax()]
        newid = max(evs['id'][1:]) + 1
        row = [newid, event_title, ev_city, ev_country, ev_url]
else:
    #no, so let's add to it
    etmp = 'https://statistik.d-u-v.org/' + pd.read_html(url, extract_links='body')[3][2][1][1]
    etab = pd.read_html(etmp)

    #location info
    ev_city = etab[2][1][etab[2][0].str.find('Start in').idxmax()].rsplit(' ', 1)[0].split(',')[0]
    ev_state = etab[2][1][etab[2][0].str.find('Start in').idxmax()].rsplit(' ', 1)[0].split(', ')[1]
    ev_country = etab[2][1][etab[2][0].str.find('Start in').idxmax()].rsplit(' ', 1)[1].replace('(', '').replace(')', '')
    ev_url = etab[2][1][etab[2][1].str.find('http').idxmax()]
    newid = 1
    row = [newid, event_title, ev_city, ev_state, ev_country, ev_url]

if len(row) > 0: #append it
    esh.append(row)
    wb.save(path)

# Add Race Info to database (if necessary) -- search existing event list for matching event title to get event id, then pair with year of results to search event id + year pairs in race list
if(max(evs['Title'].str.find(event_title))) > -1: #if we find the race
    evid = evs['id'][evs['Title'].str.find(event_title).idxmax()] #get the race id
    if len(rcs[(rcs['Event_ID'] == evid) & (rcs['Year'] == race_year) ]) == 0: #we have the event, but not this instance
        if(len(rcs['id']) > 1):
            newid = max(rcs['id'][1:]) + 1
        else:
            newid = 1
        rsh.append([newid, evid, race_distance, race_year])
        wb.save(path)

# Now to add participants and results -- for each item in the result table:
# 1) Check the participant table to see if we want to write a new participant entry based on the ath_id, if we do then write it
# 2) Check the results table for race id + ath_id pairs. if not found, write a result entry.
resid = 1
for i in range(len(results_info)): #for each result
    entry = results_info.iloc[i]
    #does participant already exist in our dataset?
    if(not partdf['ath_id'].eq(entry['Ath_ID']).any()):
        #athlete not found!
        partsh.append([entry['Ath_ID'], entry['Name'], entry['YOB'], entry['Gender'], entry['Nation']])
    
    #does the result table already have this specific result for this athlete? (race id + ath_id pair)
    if resdf['Race_ID'].eq(evid).any(): #race has entries already
        if not resdf[resdf['Race_ID'] == evid]['ath_id'].eq(entry['Ath_ID']).any(): #zero in on those entries, is this athlete yet among them?
            #no, so let's add them
            
            
            if( len(resdf['id']) > 1 ):
                resid = max(max(resdf['id'][1:]), resid) + 1   
            else:
                resid = 1       

            ressh.append([resid, evid, entry['Ath_ID'], entry['Duration'], entry['Rank'], entry['Category'], entry['Cat_Rank'], entry['Gender_Rank']])


wb.save(path)
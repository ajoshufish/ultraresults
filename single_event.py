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





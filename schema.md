# Results Database Schema

Overall Organization:

|Item | Explanation | Example |
|-----| ------------| ------- |
| Event_Info | Event as an overall category | Run Rabbit Run 100 Miler |
| Race_Info | Race as a particular instance of an event | The 2022 edition of the Run Rabbit Run 100 Miler specifically|
| Participant_Info | Information about a particular competitor | Each unique individual, e.g., a particular John Racer with a unique IDo |
| Results | Each indidivual result for a given race | The specific time information for each person's finish of each race, e.g., 23:24:56 as the finishing time for John Racer at the 2022 RRR 100|

## Table Schemas:

|Event_Info| Race_Info | Participant_Info | Results |
|----|----|----|----|
|event_id | race_id | ath_id  | result_id |
|title | event_id | name  | race_id |
|city | distance | dob_year | ath_id |
|state_code | year | gender | time |
|country | | country| place |
|website | | | category |
| | | | category_place |
| | | | gender_place |

from __future__ import print_function
import datetime
from datetime import timedelta
import math
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
# set this to Sunday prior to first recorded run
START_DATE = datetime.date.fromisoformat("2020-05-17")
# this sets how many miles each dot represents in our Weekly Totals graph 
GRAPH_INTERVAL = .5


def main():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    service = build("calendar", "v3", credentials=creds)

    # Call the Calendar API
    now = datetime.date.today()
    year_ago = datetime.datetime.utcnow() - datetime.timedelta(days=365)
    year_ago = year_ago.isoformat() + "Z"
    print("Getting all runs logged in the past year:")
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=year_ago,
            maxResults=300,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])
    miles_total = 0.0
    ctr = 0
    first_run = None
    runs_list = []

    if not events:
        print("No upcoming events found.")
    # print header
    print("__________________________")
    print("|  # |   Date     | Miles|")
    print("__________________________")

    for event in events:
        if "ran " in event["summary"]:
            ctr += 1
            # if first_run is unpopulated, get the date of the first logged run
            if first_run is None:
                first_run = datetime.date.fromisoformat(
                    event["start"].get("dateTime", event["start"].get("date"))
                )
            # chop off the word 'ran '
            miles = event["summary"].partition(" ")[2]
            # chop off the ':' if it exists and anything that follows
            miles = miles.partition(":")[0]
            start = event["start"].get("dateTime", event["start"].get("date"))
            miles_total = miles_total + float(miles)
            runs_list.append([datetime.date.fromisoformat(start), float(miles)])
            # individual run dates and mileages printed here
            print("|", format(ctr, "2d"), "|", start, "|", format(float(miles), ".1f"), " |")
    print("__________________________\n")
    print("Total mileage:", format(miles_total, ".1f"), " miles")
    print(
        "Average miles per week:",
        format(miles_total / ((now - first_run).days / 7), ".1f"),
    )
    print("Average miles per run:", format(miles_total / ctr, ".1f"))
    print("\nWeekly totals starting", START_DATE)
    print("Each dot represents", GRAPH_INTERVAL, "miles run that week")
    find_weekly_totals(now, START_DATE, runs_list)


def find_weekly_totals(now, START_DATE, runs_list):
    d = timedelta(days=7)
    i = 0
    week_ctr = 1
    cur_date = START_DATE

    while i <= (now - START_DATE).days:
        i += 7
        cur_week_total = 0
        cur_date += d
        for run in runs_list:
            if run[0] < cur_date and run[0] >= cur_date - d:
                cur_week_total += run[1]
        # setup for and create one row per week of dots, each representing .5 mi ran
        graph_string = ""
        j = 0
        while j < cur_week_total:
            graph_string += "."
            j += GRAPH_INTERVAL

        print(format(week_ctr, "2d"), ":", "{:>4.1f}".format(cur_week_total), graph_string)
        week_ctr += 1


if __name__ == "__main__":
    main()

# Cal2Busy

Have you ever wanted to share your busy schedule with others, but found yourself juggling too many different calendar apps? Maybe you use iCloud and would have to share each calendar individually.

Cal2Busy is a dead simple API service that merges all your calendars into a single iCalendar file endpoint. All events are titled “Busy.”

## Usage

Create a new file called `config.ini` and add your configuration:

```
[api]
endpoint = C6623218E8464154379966D718F12
base_path = /calendars

[calendars]
urls =
    https://calendar.google.com/calendar/ical/primary@gmail.com/public/basic.ics
    webcal://p62-caldav.icloud.com/published/2/somerandomstring
```

Then, simply run the following command:

```bash
uvicorn main:app
```

Now, you can access your merged calendar at `http://localhost:8000/calendars/C6623218E8464154379966D718F12/cal.ics`.

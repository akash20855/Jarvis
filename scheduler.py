import os,time,schedule,threading
from datetime import datetime
from brain import Brain
from services import morning_briefing,get_weather,get_sysinfo
brain = Brain()
CITY = os.getenv("CITY","London")

def job_briefing():
    brain.log_event("OBS","cron","Morning briefing running")
    try:
        text = morning_briefing(city=CITY)
        brain.log_event("FIX","cron","Briefing complete")
        print(text)
    except Exception as e:
        brain.log_event("ERR","cron",str(e))

def job_fitness():
    score = brain.calculate_fitness()
    brain.record_fitness(score)
    brain.log_event("EVO","brain",f"Fitness: {score}%")

def start():
    schedule.every().day.at("07:00").do(job_briefing)
    schedule.every(30).minutes.do(job_fitness)
    job_fitness()
    brain.log_event("OBS","scheduler","Scheduler started")
    while True:
        schedule.run_pending()
        time.sleep(30)

if __name__ == "__main__":
    start()

import os
import requests
from datetime import datetime
from core import self_healing
from brain import Brain
brain = Brain()

def _weather_fallback(city="London"):
    geo = requests.get(f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1",timeout=8).json()
    r = geo["results"][0]
    w = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={r['latitude']}&longitude={r['longitude']}&current_weather=true",timeout=8).json()
    cw = w["current_weather"]
    return {"source":"open-meteo","temp":cw["temperature"],"condition":"Clear" if cw["weathercode"]==0 else "Cloudy","wind":cw["windspeed"]}

@self_healing(retries=3,delay=1,fallback=_weather_fallback,tag="weather")
def get_weather(city="London"):
    key = os.getenv("OPENWEATHER_KEY")
    if not key:
        raise ValueError("No key")
    r = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={key}&units=metric",timeout=8)
    r.raise_for_status()
    d = r.json()
    return {"city":d["name"],"temp":round(d["main"]["temp"]),"condition":d["weather"][0]["description"].title(),"humidity":d["main"]["humidity"],"wind":round(d["wind"]["speed"]*3.6)}

def format_weather(w):
    return f"🌤 Weather\n  {w.get('temp')}°C · {w.get('condition')}\n  Wind: {w.get('wind')} km/h"

@self_healing(retries=3,delay=2,tag="github")
def get_github_prs(repo=None):
    repo = repo or os.getenv("GITHUB_REPO","user/repo")
    token = os.getenv("GITHUB_TOKEN")
    headers = {"Authorization":f"Bearer {token}","Accept":"application/vnd.github+json"}
    r = requests.get(f"https://api.github.com/repos/{repo}/pulls?state=open",headers=headers,timeout=10)
    r.raise_for_status()
    return [{"number":p["number"],"title":p["title"],"author":p["user"]["login"]} for p in r.json()]

@self_healing(retries=3,delay=2,tag="github")
def get_github_issues(repo=None):
    repo = repo or os.getenv("GITHUB_REPO","user/repo")
    token = os.getenv("GITHUB_TOKEN")
    headers = {"Authorization":f"Bearer {token}","Accept":"application/vnd.github+json"}
    r = requests.get(f"https://api.github.com/repos/{repo}/issues?state=open",headers=headers,timeout=10)
    r.raise_for_status()
    return [{"number":i["number"],"title":i["title"]} for i in r.json() if "pull_request" not in i]

def format_github(prs,issues):
    lines = ["📦 GitHub Status",f"  Open PRs: {len(prs)}"]
    for p in prs[:3]: lines.append(f"  #{p['number']} {p['title'][:40]}")
    lines.append(f"  Open Issues: {len(issues)}")
    return "\n".join(lines)

def get_sysinfo():
    info = {}
    try:
        import subprocess
        b = __import__("json").loads(subprocess.run(["termux-battery-status"],capture_output=True,text=True,timeout=5).stdout)
        info["battery"] = f"{b.get('percentage','?')}% ({b.get('status','?')})"
    except: info["battery"] = "N/A"
    try:
        mem = {}
        for line in open("/proc/meminfo").readlines()[:5]:
            k,v = line.split(":")
            mem[k.strip()] = int(v.strip().split()[0])
        total = mem["MemTotal"]//1024
        free = mem.get("MemAvailable",mem.get("MemFree",0))//1024
        info["ram"] = f"{total-free}MB / {total}MB"
    except: info["ram"] = "N/A"
    try:
        secs = float(open("/proc/uptime").read().split()[0])
        info["uptime"] = f"{int(secs//3600)}h {int((secs%3600)//60)}m"
    except: info["uptime"] = "N/A"
    return info

def format_sysinfo(info):
    return f"⚙️ System\n  Battery: {info.get('battery')}\n  RAM: {info.get('ram')}\n  Uptime: {info.get('uptime')}"

def morning_briefing(city="London",github_repo=None):
    parts = [f"☀️ Good morning! {datetime.now().strftime('%A, %d %b %Y · %H:%M')}\n{'─'*35}"]
    try: parts.append(format_weather(get_weather(city)))
    except Exception as e: parts.append(f"🌤 Weather unavailable: {e}")
    try:
        prs = get_github_prs(github_repo)
        issues = get_github_issues(github_repo)
        parts.append(format_github(prs,issues))
    except Exception as e: parts.append(f"📦 GitHub unavailable: {e}")
    try: parts.append(format_sysinfo(get_sysinfo()))
    except Exception as e: parts.append(f"⚙️ Sysinfo unavailable: {e}")
    s = brain.status_report()
    parts.append(f"🧠 Jarvis Brain\n  Fitness: {s['fitness']}%\n  Known fixes: {s['known_fixes']}")
    return "\n\n".join(parts)

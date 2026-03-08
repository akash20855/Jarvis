import os,re,sys,time,threading,subprocess
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
from brain import Brain
brain = Brain()

WAKE_WORD = "jarvis"
CITY = os.getenv("CITY","London")
OWNER_NAME = os.getenv("OWNER_NAME","Boss")
GROK_KEY = os.getenv("GROK_API_KEY","")
OPENAI_KEY = os.getenv("OPENAI_API_KEY","")

class Speaker:
    def __init__(self):
        self.engine = None
        try:
            import pyttsx3
            self.engine = pyttsx3.init()
            self.engine.setProperty("rate",162)
        except: pass

    def say(self,text):
        clean = re.sub(r"[*_`#•►→←\[\]]","",text)
        clean = re.sub(r"\n+"," . ",clean).strip()
        print(f"\n🔊 JARVIS: {clean}\n")
        if self.engine:
            try:
                self.engine.say(clean)
                self.engine.runAndWait()
                return
            except: pass
        try: subprocess.run(["termux-tts-speak",clean],timeout=30)
        except: pass

class Listener:
    def __init__(self):
        self.r = None
        self.mic = None
        try:
            import speech_recognition as sr
            self.sr = sr
            self.r = sr.Recognizer()
            self.mic = sr.Microphone()
            with self.mic as source:
                print("🎤 Calibrating mic...")
                self.r.adjust_for_ambient_noise(source,duration=2)
        except Exception as e:
            print(f"Mic error: {e}")

    def hear(self,timeout=3,limit=5):
        if not self.mic: return ""
        try:
            with self.mic as source:
                audio = self.r.listen(source,timeout=timeout,phrase_time_limit=limit)
            try: return self.r.recognize_google(audio).lower()
            except: return ""
        except: return ""

def ask_ai(question):
    import requests as req
    history = brain.get_history("voice",limit=6)
    system = f"You are Jarvis, a voice AI. User: {OWNER_NAME}. Max 2 short sentences. No markdown. Time: {datetime.now().strftime('%H:%M on %A')}."
    messages = [{"role":"system","content":system}]+history+[{"role":"user","content":question}]
    for key,url,model in [(GROK_KEY,"https://api.x.ai/v1/chat/completions","grok-beta"),(OPENAI_KEY,"https://api.openai.com/v1/chat/completions","gpt-4o-mini")]:
        if not key: continue
        try:
            r = req.post(url,headers={"Authorization":f"Bearer {key}"},json={"model":model,"messages":messages,"max_tokens":120},timeout=12)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except: continue
    return "AI brain offline. Check API key."

def handle(text):
    t = text.lower().strip()
    brain.add_message("voice","user",text)
    if any(w in t for w in ["goodbye","bye","stop","shut down"]): return "__EXIT__"
    if "time" in t and "weather" not in t: return f"It's {datetime.now().strftime('%I:%M %p')}."
    if any(w in t for w in ["date","today","what day"]): return f"Today is {datetime.now().strftime('%A, %d %B %Y')}."
    if "weather" in t:
        city = CITY
        if " in " in t: city = t.split(" in ")[-1].strip().title()
        try:
            from services import get_weather
            w = get_weather(city)
            return f"It's {w.get('temp')} degrees and {w.get('condition')} in {city}."
        except Exception as e: return f"Weather unavailable. {e}"
    if any(w in t for w in ["battery","sysinfo","system","ram"]):
        try:
            from services import get_sysinfo
            info = get_sysinfo()
            return f"Battery is {info.get('battery')}. RAM is {info.get('ram')}."
        except: return "System info unavailable."
    if any(w in t for w in ["briefing","morning","summary"]):
        try:
            from services import morning_briefing
            return " ".join([l for l in morning_briefing(city=CITY).splitlines() if l.strip()][:6])
        except Exception as e: return f"Briefing failed. {e}"
    if any(w in t for w in ["status","fitness","how are you"]):
        s = brain.status_report()
        return f"Running at {s['fitness']} percent fitness with {s['known_fixes']} known fixes."
    reply = ask_ai(text)
    brain.add_message("voice","assistant",reply)
    return reply

def main():
    speaker = Speaker()
    listener = Listener()
    if not listener.mic:
        print("❌ No microphone. Check Termux mic permission.")
        sys.exit(1)
    hour = datetime.now().hour
    greeting = f"Good {'morning' if hour<12 else 'afternoon' if hour<17 else 'evening'} {OWNER_NAME}. Jarvis online. Say Hey Jarvis to begin."
    speaker.say(greeting)
    print(f"\n{'═'*40}\n  ⚡ JARVIS VOICE ACTIVE\n  Say 'HEY JARVIS' to wake up\n{'═'*40}\n")
    while True:
        try:
            print("👂 Listening...", end="\r")
            heard = listener.hear(timeout=3,limit=4)
            if WAKE_WORD not in heard: continue
            speaker.say("Yes?")
            command = listener.hear(timeout=10,limit=12)
            if not command:
                speaker.say("I didn't catch that.")
                continue
            print(f"💬 Command: '{command}'")
            response = handle(command)
            if response == "__EXIT__":
                speaker.say(f"Goodbye {OWNER_NAME}.")
                break
            speaker.say(response)
        except KeyboardInterrupt:
            speaker.say("Shutting down.")
            break
        except Exception as e:
            brain.log_event("ERR","voice",str(e))
            time.sleep(1)

if __name__ == "__main__":
    main()

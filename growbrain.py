import os,sys,json,time,subprocess,importlib,threading
from datetime import datetime,timedelta
from pathlib import Path
from brain import Brain
brain = Brain()
SKILLS_DIR = Path(__file__).parent/"skills"
SKILLS_DIR.mkdir(exist_ok=True)
GROK_KEY = os.getenv("GROK_API_KEY","")
OPENAI_KEY = os.getenv("OPENAI_API_KEY","")

class PackageManager:
    def ensure(self,package,import_name=None):
        import_name = import_name or package
        try: importlib.import_module(import_name); return True
        except ImportError: pass
        brain.log_event("OBS","pkg",f"Installing {package}...")
        try:
            r = subprocess.run([sys.executable,"-m","pip","install",package,"--break-system-packages","--quiet"],capture_output=True,text=True,timeout=120)
            if r.returncode==0:
                brain.log_event("FIX","pkg",f"✓ Installed: {package}")
                return True
        except Exception as e: brain.log_event("ERR","pkg",str(e))
        return False

class SkillWriter:
    def create_skill(self,skill_name,description):
        brain.log_event("OBS","skill",f"Creating: {skill_name}")
        code = self._generate(skill_name,description)
        if not code: return {"success":False,"error":"AI failed"}
        try: compile(code,f"{skill_name}.py","exec")
        except SyntaxError as e: return {"success":False,"error":str(e)}
        path = SKILLS_DIR/f"{skill_name}.py"
        path.write_text(code)
        brain.remember(f"skill:{skill_name}",{"description":description,"created_at":datetime.now().isoformat(),"version":1})
        brain.log_event("EVO","skill",f"✓ Skill {skill_name} saved")
        return {"success":True,"skill":skill_name,"path":str(path)}

    def _generate(self,name,description):
        import requests
        prompt = f"Write a Python module '{name}.py'. Task: {description}. Must have run_{name}() returning a string. Under 60 lines. Only code, no markdown."
        messages = [{"role":"user","content":prompt}]
        for key,url,model in [(GROK_KEY,"https://api.x.ai/v1/chat/completions","grok-beta"),(OPENAI_KEY,"https://api.openai.com/v1/chat/completions","gpt-4o-mini")]:
            if not key: continue
            try:
                r = requests.post(url,headers={"Authorization":f"Bearer {key}"},json={"model":model,"messages":messages,"max_tokens":800},timeout=30)
                r.raise_for_status()
                code = r.json()["choices"][0]["message"]["content"]
                lines = code.strip().splitlines()
                if lines[0].startswith("```"): lines = lines[1:]
                if lines and lines[-1].strip()=="```": lines = lines[:-1]
                return "\n".join(lines)
            except: continue
        return ""

    def run_skill(self,skill_name):
        try:
            path = SKILLS_DIR/f"{skill_name}.py"
            if not path.exists(): return f"Skill {skill_name} not found."
            spec = importlib.util.spec_from_file_location(skill_name,path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            fn = getattr(mod,f"run_{skill_name}",None)
            return str(fn()) if fn else f"No run_{skill_name}() found."
        except Exception as e: return f"Skill error: {e}"

    def list_skills(self):
        return [{"name":f.stem,"description":(brain.recall(f"skill:{f.stem}") or {}).get("description","")} for f in SKILLS_DIR.glob("*.py")]

class HabitLearner:
    def record_usage(self,command):
        hour = datetime.now().hour
        key = f"habit:{command}:{hour}"
        brain.remember(key,(brain.recall(key,0))+1)

    def analyze_patterns(self):
        rows = brain.conn.execute("SELECT message,COUNT(*) as c FROM conversations WHERE role='user' GROUP BY message ORDER BY c DESC LIMIT 5").fetchall()
        return {"top_commands":[(r["message"],r["c"]) for r in rows],"total_interactions":brain.conn.execute("SELECT COUNT(*) as c FROM conversations").fetchone()["c"]}

class GrowBrain:
    def __init__(self):
        self.pm = PackageManager()
        self.sw = SkillWriter()
        self.hl = HabitLearner()

    def handle_unknown(self,request):
        brain.log_event("OBS","grow",f"Unknown: {request[:50]}")
        self.hl.record_usage(request.split()[0] if request else "unknown")
        skill_name,description = self._analyze(request)
        if not skill_name: return "I couldn't figure out how to handle that."
        if brain.recall(f"skill:{skill_name}"): return self.sw.run_skill(skill_name)
        result = self.sw.create_skill(skill_name,description)
        if not result["success"]: return f"Failed to build skill: {result.get('error')}"
        return f"I just learned how to do that. {self.sw.run_skill(skill_name)}"

    def _analyze(self,request):
        import requests as req
        prompt = f'User asked: "{request}". Respond JSON only: {{"skill_name":"name","description":"what it does"}}'
        for key,url,model in [(GROK_KEY,"https://api.x.ai/v1/chat/completions","grok-beta"),(OPENAI_KEY,"https://api.openai.com/v1/chat/completions","gpt-4o-mini")]:
            if not key: continue
            try:
                r = req.post(url,headers={"Authorization":f"Bearer {key}"},json={"model":model,"messages":[{"role":"user","content":prompt}],"max_tokens":100},timeout=15)
                r.raise_for_status()
                text = r.json()["choices"][0]["message"]["content"].strip()
                if text.startswith("```"): text = "\n".join(text.splitlines()[1:-1])
                data = json.loads(text)
                return data.get("skill_name",""),data.get("description","")
            except: continue
        return "",""

    def status(self):
        skills = self.sw.list_skills()
        patterns = self.hl.analyze_patterns()
        return f"🧠 Growth Status\nSkills: {len(skills)}\nInteractions: {patterns['total_interactions']}\nSkills: {', '.join(s['name'] for s in skills) or 'none yet'}"

    def start(self):
        brain.log_event("OBS","grow","GrowBrain started")

grow = GrowBrain()

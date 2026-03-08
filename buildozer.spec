[app]
title = JARVIS
package.name = jarvis
package.domain = com.akash20855
version = 1.0.0
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,db,txt,json
requirements = python3,kivy==2.2.1,requests,httpx,pyttsx3,SpeechRecognition,schedule,python-dotenv,android,pyjnius
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.permissions = INTERNET,RECORD_AUDIO,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,RECEIVE_BOOT_COMPLETED,FOREGROUND_SERVICE,REQUEST_INSTALL_PACKAGES,VIBRATE
[buildozer]
log_level = 1
warn_on_root = 1

[app]
title = Tasbih Counter
package.name = tasbihcounter
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.1
requirements = python3,kivy,cython==0.29.36
android.api = 33
android.minapi = 21
android.archs = arm64-v8a, armeabi-v7a
icon = icon.png
presplash = presplash.png
orientation = portrait
fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 1

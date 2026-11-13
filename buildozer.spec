[app]
title = Fandoq
package.name = fandoq
package.domain = ir.mrkiani
source.dir = .
source.include_exts = py,png,jpg,json,kv,atlas,ttf
version = 0.3.0
requirements = python3,kivy,arabic-reshaper,python-bidi
orientation = portrait
fullscreen = 0
android.permissions =
android.api = 35
android.minapi = 23
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
icon.filename = %(source.dir)s/assets/icon.png

[buildozer]
log_level = 2
warn_on_root = 1

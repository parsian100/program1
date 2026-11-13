# -*- coding: utf-8 -*-
__version__ = "0.3.0"
import json, os, random
from collections import Counter
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    def fa(s): return get_display(arabic_reshaper.reshape(str(s)))
except Exception:
    def fa(s): return str(s)

Window.clearcolor = (0.035, 0.105, 0.13, 1)
ROOT = os.path.dirname(os.path.abspath(__file__))
LEVELS_FILE = os.path.join(ROOT, "data", "levels.json")

def norm(s):
    return str(s).replace("ي","ی").replace("ك","ک").replace("‌","").replace(" ","").strip()

class PillButton(Button):
    def __init__(self, bg=(0.13,.43,.37,1), **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0,0,0,0)
        self.color = (1,.98,.9,1)
        self.bold = True
        self.font_size = "17sp"
        self._bg = bg
        with self.canvas.before:
            Color(*bg)
            self.shape = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(16)])
        self.bind(pos=self._sync, size=self._sync)
    def _sync(self,*_):
        self.shape.pos=self.pos; self.shape.size=self.size

class Fandoq(App):
    title = "فندوق"
    def build(self):
        self.levels = json.loads(open(LEVELS_FILE,encoding="utf-8").read())
        self.data = self.load_save()
        self.found_by_level = self.data.get("found_by_level", {})
        self.level_index = min(max(0,int(self.data.get("level",0))),len(self.levels)-1)
        self.coins = max(0,int(self.data.get("coins",30)))
        self.found = set(self.found_by_level.get(str(self.level_index), []))
        self.current_input = ""
        self.root_ui = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(9))
        self.draw()
        return self.root_ui

    @property
    def save_file(self): return os.path.join(self.user_data_dir,"save.json")

    def load_save(self):
        try:
            with open(self.save_file,encoding="utf-8") as f:
                data = json.load(f)
            # Migrate the early prototype's single-level "found" field if present.
            found_by_level = data.get("found_by_level", {})
            if not isinstance(found_by_level, dict):
                found_by_level = {}
            if data.get("found") and not found_by_level:
                found_by_level[str(data.get("level", 0))] = data.get("found", [])
            data["found_by_level"] = found_by_level
            return data
        except Exception:
            return {"level":0,"coins":30,"found_by_level":{}}

    def save(self):
        os.makedirs(self.user_data_dir,exist_ok=True)
        self.found_by_level[str(self.level_index)] = sorted(self.found)
        payload={"level":self.level_index,"coins":self.coins,"found_by_level":self.found_by_level}
        with open(self.save_file,"w",encoding="utf-8") as f:
            json.dump(payload,f,ensure_ascii=False)
        self.data = payload

    def fa_label(self,txt,size=17,color=(1,1,1,1),height=None,bold=False):
        x=Label(text=fa(txt),font_size=f"{size}sp",color=color,bold=bold,halign="center",valign="middle",
                size_hint_y=None if height else 1,height=dp(height) if height else 0)
        x.bind(size=lambda inst,val:setattr(inst,"text_size",val))
        return x

    def draw(self):
        self.root_ui.clear_widgets()
        lv=self.levels[self.level_index]
        top=BoxLayout(size_hint_y=None,height=dp(50),spacing=dp(6))
        top.add_widget(self.fa_label("🌰 فندوق",25,(1,.78,.32,1),bold=True))
        top.add_widget(self.fa_label(f"مرحله {self.level_index+1} از {len(self.levels)}",14,(.82,.94,.89,1),bold=True))
        top.add_widget(self.fa_label(f"🟡 {self.coins}",16,(1,.83,.4,1),bold=True))
        self.root_ui.add_widget(top)

        if self.level_index==0:
            try:
                art=Image(source=os.path.join(ROOT,"assets","fandoq_banner.jpg"),size_hint_y=None,height=dp(132),allow_stretch=True,keep_ratio=False)
                self.root_ui.add_widget(art)
            except Exception: pass
        self.root_ui.add_widget(self.fa_label(lv["title"],20,(1,.85,.54,1),38,True))
        self.root_ui.add_widget(self.fa_label("حروف را به هم وصل کن و واژه‌های پنهان را پیدا کن",14,(.74,.86,.84,1),32))

        self.current_word=self.fa_label("حروف را انتخاب کن",25,(1,.95,.77,1),55,True)
        self.root_ui.add_widget(self.current_word)
        self.current_input = ""
        letters=list(lv["letters"]); random.shuffle(letters)
        grid=GridLayout(cols=min(4,len(letters)),spacing=dp(8),size_hint_y=None,
                        height=dp(62)*((len(letters)+3)//4))
        self.letter_buttons=[]
        for ch in letters:
            b=PillButton(text=fa(ch),font_size="24sp",bg=(.18,.39,.42,1))
            b.bind(on_release=lambda btn,c=ch:self.add_char(c))
            grid.add_widget(b); self.letter_buttons.append(b)
        self.root_ui.add_widget(grid)

        row=BoxLayout(size_hint_y=None,height=dp(48),spacing=dp(7))
        row.add_widget(PillButton(text=fa("پاک‌کردن"),bg=(.45,.25,.25,1),font_size="14sp",on_release=lambda *_:self.reset_word()))
        row.add_widget(PillButton(text=fa("بررسی"),bg=(.12,.53,.38,1),font_size="16sp",on_release=lambda *_:self.check()))
        row.add_widget(PillButton(text=fa("راهنما"),bg=(.55,.39,.15,1),font_size="14sp",on_release=lambda *_:self.hint()))
        self.root_ui.add_widget(row)

        self.found_lbl=self.fa_label(self.found_text(),14,(.82,.92,.86,1),72)
        self.root_ui.add_widget(self.found_lbl)
        self.root_ui.add_widget(Widget())
        nav=BoxLayout(size_hint_y=None,height=dp(45),spacing=dp(7))
        nav.add_widget(PillButton(text=fa("نقشه مراحل"),font_size="14sp",bg=(.22,.34,.42,1),on_release=lambda *_:self.level_map()))
        nav.add_widget(PillButton(text=fa("تنظیمات و درباره"),font_size="14sp",bg=(.22,.34,.42,1),on_release=lambda *_:self.about()))
        self.root_ui.add_widget(nav)
        self.root_ui.add_widget(self.fa_label("طراح: محمدرضا کیانی | mrkiani100@gmail.com",10,(.58,.72,.69,1),22))

    def found_text(self):
        return "واژه‌های کشف‌شده: " + ("، ".join(sorted(self.found)) if self.found else "هنوز واژه‌ای پیدا نشده")

    def add_char(self,c):
        self.current_input += c
        self.current_word.text = fa(self.current_input)

    def reset_word(self):
        self.current_input = ""
        self.current_word.text = fa("حروف را انتخاب کن")

    def popup(self,title,msg,callback=None):
        box=BoxLayout(orientation="vertical",padding=dp(12),spacing=dp(10))
        lab=Label(text=fa(msg),color=(.12,.2,.19,1),font_size="16sp",halign="center",valign="middle")
        lab.bind(size=lambda i,v:setattr(i,"text_size",v)); box.add_widget(lab)
        b=PillButton(text=fa("ادامه"),size_hint_y=None,height=dp(44))
        box.add_widget(b)
        p=Popup(title=fa(title),content=box,size_hint=(.86,.42),auto_dismiss=False)
        def done(*_):
            p.dismiss()
            if callback: callback()
        b.bind(on_release=done); p.open()

    def check(self):
        word=norm(self.current_input)
        self.reset_word()
        lv=self.levels[self.level_index]
        valid={norm(x) for x in lv["words"]}
        if word not in valid:
            self.popup("این واژه ثبت نشد","این ترکیب در واژه‌نامه این مرحله نیست؛ دوباره امتحان کن.")
            return
        if word in {norm(x) for x in self.found}:
            self.popup("تکراری","این واژه را قبلاً پیدا کرده‌ای.")
            return
        self.found.add(word); self.coins+=max(1,len(word)//2)
        self.save(); self.found_lbl.text=fa(self.found_text())
        if word==norm(lv["answer"]):
            self.coins+=5; self.save()
            self.popup("آفرین! 🌟","واژه اصلی مرحله پیدا شد؛ ۵ سکه جایزه گرفتی.",self.advance)
        else:
            self.popup("درست بود!","یک واژه تازه کشف کردی؛ سکه گرفتی.")

    def advance(self):
        if self.level_index < len(self.levels)-1:
            self.level_index+=1
            self.found=set(self.found_by_level.get(str(self.level_index), []))
            self.save(); self.draw()
        else:
            self.popup("تبریک!","همه ۵۰۰ مرحله فندوق را به پایان رساندی. آفرین!")

    def hint(self):
        if self.coins<5:
            self.popup("سکه کافی نیست","برای دریافت راهنما به ۵ سکه نیاز داری."); return
        self.coins-=5
        answer=self.levels[self.level_index]["answer"]
        self.save(); self.draw()
        self.popup("راهنمای فندوق",f"واژه اصلی با «{answer[0]}» شروع می‌شود و {len(answer)} حرف دارد.")

    def level_map(self):
        scroll=ScrollView()
        col=GridLayout(cols=1,spacing=dp(5),padding=dp(8),size_hint_y=None)
        col.bind(minimum_height=col.setter("height"))
        for i,lv in enumerate(self.levels):
            locked=i>self.level_index
            txt=f"{i+1}. {lv['title']}"+("  🔒" if locked else "  ✓" if i<self.level_index else "  ▶")
            b=PillButton(text=fa(txt),size_hint_y=None,height=dp(42),font_size="14sp",
                         bg=(.25,.29,.31,1) if locked else (.14,.42,.36,1),disabled=locked)
            b.bind(on_release=lambda btn,n=i:self.go_level(n)); col.add_widget(b)
        scroll.add_widget(col)
        p=Popup(title=fa("نقشه مراحل"),content=scroll,size_hint=(.88,.82)); p.open()

    def go_level(self,n):
        self.level_index=n
        self.found=set(self.found_by_level.get(str(n), []))
        self.save(); self.draw()

    def about(self):
        self.popup("درباره فندوق","فندوق یک بازی مستقل واژه‌سازی فارسی است. نسخه ۰٫۳ شامل ۵۰۰ مرحله در ۲۵ فصل، نقشه مراحل و ذخیره پیشرفت است. طراح: محمدرضا کیانی | mrkiani100@gmail.com")

if __name__=="__main__":
    Fandoq().run()

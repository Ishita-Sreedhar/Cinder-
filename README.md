<div align="center">

# 🐾 Cinder 🐾

### a small cat for long work days

*A little white cat with a pink collar and a golden bell, who lives on your desktop and keeps you company while you work.*

<br>

[**✨ Visit the website ✨**](https://ishita-sreedhar.github.io/Cinder-/)  ·  [**⬇️ Download for Windows**](https://github.com/Ishita-Sreedhar/Cinder-/releases/latest/download/Cinder.exe)  ·  [**🍎 Download for macOS**](https://github.com/Ishita-Sreedhar/Cinder-/releases/latest/download/Cinder-macOS.zip)

<br>

![Python](https://img.shields.io/badge/Python-3.11-f5c6d0?style=for-the-badge&logo=python&logoColor=white)
![PyQt6](https://img.shields.io/badge/PyQt6-desktop-e8d5c0?style=for-the-badge)
![Made with love](https://img.shields.io/badge/made%20with-%E2%99%A1-f4a6b8?style=for-the-badge)

</div>

---

## 🌸 Meet Cinder

Cinder is a tiny desktop companion who sits on top of your work, wags her tail, blinks at you, and quietly looks after your day. She's always on top, never in the way, and you can drag her wherever you like.

Everything she does lives in small cream-and-brown windows that pop up right where she sits.

## 🧶 What she does

| | |
|---|---|
| ⏲️ **Timer & Pomodoro** | Focus sessions with a soft little countdown |
| ⏱️ **Stopwatch** | Start, pause and reset, nice and simple |
| ✅ **To-do list** | Add tasks and strike them off. Confetti time, and Cinder celebrates with you 🎉 |
| 💧 **Water reminder** | A gentle nudge to drink some water |
| 💗 **Pet her** | Circle your cursor around her three times and she smiles and sends up tiny hearts |
| 🖱️ **Right-click menu** | Open every tool from one pretty menu |
| 🪟 **Draggable & always on top** | Frameless, so she stays with you while you work |

## 📖 How to use her

Drag Cinder anywhere, and **right-click** her to open the menu with every tool. The full manual is on the [website](https://ishita-sreedhar.github.io/Cinder-/#manual).

## 🍵 Install

### Windows

1. Download [**Cinder.exe**](https://github.com/Ishita-Sreedhar/Cinder-/releases/latest/download/Cinder.exe)
2. Double-click it, and she'll appear on your desktop
3. Right-click her to open the menu

> 💡 If a blue **SmartScreen** box appears, choose **More info → Run anyway**. Cinder isn't code-signed yet.

### macOS (Apple Silicon)

1. Download [**Cinder-macOS.zip**](https://github.com/Ishita-Sreedhar/Cinder-/releases/latest/download/Cinder-macOS.zip) and unzip it
2. Right-click **Cinder.app** → **Open** → **Open** again
3. If she doesn't respond to clicks, allow Cinder under **System Settings → Privacy & Security → Accessibility**

> 🐛 The Mac version is brand new. If you find a bug, please [open an issue](https://github.com/Ishita-Sreedhar/Cinder-/issues).

## 🧑‍💻 Run from source

```bash
# clone
git clone https://github.com/Ishita-Sreedhar/Cinder-.git
cd Cinder-

# set up a virtual environment
python -m venv venv
venv\Scripts\activate        # on macOS/Linux: source venv/bin/activate

# install and run
pip install PyQt6
python widget.py
```

## 📦 Build your own exe

```bash
pip install pyinstaller
pyinstaller Cinder.spec
```

Your build will appear in the `dist/` folder.

## 🎀 Built with

- **Python 3.11**
- **PyQt6**, where Cinder is drawn by hand with `QGraphicsScene` and `QPainterPath`, with no image files for the cat

## 💌 Feedback

Found a bug? Have an idea for something Cinder should do? [Open an issue](https://github.com/Ishita-Sreedhar/Cinder-/issues), or leave a ⭐ if she made your day a little softer.

---

<div align="center">

Made with 🤍 by **Ishita** · *keep going, Cinder believes in you*

</div>

#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import os
import sys
import time
from enum import IntEnum, auto
import abc
from typing import override

import mp3play


class SysTyp(IntEnum):
    WIN = auto()
    LIN = auto()
    MAC = auto()
    UNKOWN = auto()


class ActTyp(IntEnum):
    SPEECH_TEXT = auto()
    PLAY_MP3 = auto()
    LOCK_SCREEN = auto()
    SHUTDOWN = auto()
    NOACTION = auto()


class Action(abc.ABC):
    def __init__(self):
        self._sys_typ: SysTyp = SysTyp.UNKOWN

    @abc.abstractmethod
    def speech_text(self, text: str):
        pass

    @abc.abstractmethod
    def play_mp3(self, mp3file: str):
        pass

    @abc.abstractmethod
    def lock_screen(self):
        pass

    @abc.abstractmethod
    def shutdown(self):
        pass


class ActionWin(Action):
    def __init__(self):
        super().__init__()
        self._sys_typ: SysTyp = SysTyp.WIN

    @override
    def speech_text(self, text: str):
        md = f'''powershell -Command "Add-Type -AssemblyName System.Speech;$Speak = New-Object System.Speech.Synthesis.SpeechSynthesizer;$speak.rate =  1;$speak.SelectVoice('Microsoft Zira Desktop');$speak.Speak('{text}');"'''
        _ = os.system(md)

    @override
    def play_mp3(self, mp3file: str):
        if not os.path.isfile(mp3file):
            raise FileNotFoundError(f"The is no mp3: {mp3file}")
        try:
            clip = mp3play.load(mp3file)
            clip.play()
            time.sleep(min(30, clip.seconds() + 0.3))
            clip.stop()
        except Exception as e:
            # 访问异常的错误编号和详细信息
            print(e.args)
            print(str(e))
            print(repr(e))
            print(f"wrong mp3: {mp3file}")

    @override
    def lock_screen(self):
        _ = os.system("rundll32.exe user32.dll, LockWorkStation")

    @override
    def shutdown(self):
        pass


class ActionLin(Action):
    def __init__(self):
        super().__init__()
        self._sys_typ: SysTyp = SysTyp.LIN

    @override
    def speech_text(self, text: str):
        pass

    @override
    def play_mp3(self, mp3file: str):
        pass

    @override
    def lock_screen(self):
        _ = os.system("gnome-screensaver-command -l")

    @override
    def shutdown(self):
        pass


class ActionMac(Action):
    def __init__(self):
        super().__init__()
        self._sys_typ: SysTyp = SysTyp.MAC

    @override
    def speech_text(self, text: str):
        pass

    @override
    def play_mp3(self, mp3file: str):
        pass

    @override
    def lock_screen(self):
        _ = os.system("osascript -e " + 'tell application "System Events" to keystroke "q" using {control down, command down}')

    @override
    def shutdown(self):
        pass


class ActionSys:

    def __init__(self):
        self._action: Action = ActionWin()
        if sys.platform.startswith('linux'):
            self._action = ActionLin()
        elif sys.platform.startswith('win'):
            self._action = ActionWin()
        elif sys.platform.startswith('darwin'):
            self._action = ActionMac()
        else:
            pass

    def exec_action(self, action: ActTyp, paras: str = ""):
        match action:
            case ActTyp.SPEECH_TEXT:
                self._action.speech_text(paras)
            case ActTyp.PLAY_MP3:
                self._action.play_mp3(paras)
            case ActTyp.LOCK_SCREEN:
                self._action.lock_screen()
            case ActTyp.SHUTDOWN:
                self._action.shutdown()
            case _:
                pass


if __name__ == "__main__":
    import datetime
    action = ActionSys()
    # action.exec_action(ActTyp.LOCK_SCREEN)
    now = datetime.datetime.now()
    action.exec_action(ActTyp.SPEECH_TEXT,
        f'北京时间{now.hour}点{now.minute}分{now.second}秒')

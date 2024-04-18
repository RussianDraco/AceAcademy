import pygame as pg
import math
import time
import cv2, pyautogui
import mediapipe as mp
import hand_tracking_landmarks as htl
import numpy as np
import speech_recognition as sr
import pyttsx3
import json
import os, sys
from collections import deque
import datetime as dt

def today(): return dt.datetime.today().strftime('%Y-%m-%d')
def days_ago(d): return (dt.datetime.today() - dt.timedelta(days=d)).strftime('%Y-%m-%d')

# Initialize pg
pg.init()
PYTengine = pyttsx3.init()


#Init speech recognition
mic = sr.Microphone()
r = sr.Recognizer()

def tts(txt):
    PYTengine.say(txt)
    PYTengine.runAndWait()


# Constants
WIDTH, HEIGHT = 1200, 600
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BACKGROUND = (23, 4, 25)
TEXT_LIMIT = 19

DARK_BUTTON_COLOUR = (90, 66, 107)
LIGHT_BUTTON_COLOUR = (142, 115, 162)
BUTTON_TEXT_COLOR = (255, 255, 255)
FONT = pg.font.Font('resources/etna.ttf', 20)
FONT28 = pg.font.Font(None, 25)

# Accessibility
full_hand_tracking = False
camera_width, camera_height = 640, 480
Screen_Width, Screen_Height = pyautogui.size()
pTime = 0
smoothening = 8
previous_x, previous_y = 0, 0
current_y, current_x = 0, 0
showtheimage = True
eyetracking = False



# Create the screen
screen = pg.display.set_mode((WIDTH, HEIGHT))
pg.display.set_caption("Ace Academia")

CURRENT_SRC = "home"

def xaxis_centering(width): return (WIDTH - width) // 2 
def yaxis_centering(height): return (HEIGHT - height) // 2
def font(size): return pg.font.Font(None, size)
def wrap_text(text, limit):
        if not text or text == "":
            return ""

        words = text.split()
        lines = []
        current_line = words[0]

        for word in words[1:]:
            if len(current_line) + 1 + len(word) <= limit:
                # Add the word to the current line
                current_line += " " + word
            else:
                # Start a new line
                lines.append(current_line)
                current_line = word

        # Add the last line
        lines.append(current_line)

        return lines

def generate_topbar():
    screen.fill(BACKGROUND)
    pg.draw.rect(screen, BACKGROUND, (0, 48, WIDTH, 2))
    [button.draw() for button in navbarbuttons]
    screen.blit(logo, (5,-4))

def home_section():
    global CURRENT_SRC; CURRENT_SRC = "home"
    generate_topbar()
    flashbutton.draw()
    pg.draw.rect(screen, BACKGROUND, (0, 50, WIDTH, HEIGHT - 50))
    
    logo2 = pg.image.load("resources/images/Ace_Academia-removebg-preview.png").convert_alpha()
    logo2 = pg.transform.scale(logo2, (int(logo2.get_width() * 1), int(logo2.get_height() * 1)))
    screen.blit(logo2, (xaxis_centering(100)-93, 275))
            
class Gif:
    def __init__(self, folder_path, x, y):
        self.frames = []
        self.current_frame = 0
        self.frame_delay = 100  # milliseconds
        self.last_frame_time = 0
        self.x = x
        self.y = y

        # Load frames from folder
        for filename in sorted(os.listdir(folder_path)):
            if filename.endswith(".png") or filename.endswith(".jpg") or filename.endswith(".gif"):
                frame_path = os.path.join(folder_path, filename)
                frame = pg.image.load(frame_path).convert_alpha()
                self.frames.append(frame)

    def play(self, screen):
        current_time = pg.time.get_ticks()

        # Check if it's time to switch to the next frame
        if current_time - self.last_frame_time >= self.frame_delay:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.last_frame_time = current_time

        # Display the current frame
        frame = self.frames[self.current_frame]
        screen.blit(frame, (self.x, self.y))

class AudioPlayer:
    def __init__(self, file_path):
        self.file_path = file_path
        self.playing = False

    def play(self):
        if not self.playing:
            # Code to play the audio file in a loop
            pg.mixer.music.load(self.file_path)
            pg.mixer.music.play(-1)  # -1 indicates infinite loop
            self.playing = True

    def stop(self):
        if self.playing:
            # Code to stop playing the audio file
            pg.mixer.music.stop()
            self.playing = False

class Button:
    def __init__(self, x, y, width, height, text, action=None, secondaryAction=None, overrideColour = DARK_BUTTON_COLOUR):
        self.rect = pg.Rect(x, y, width, height)
        self.text = text
        self.action = action
        self.secondaryAction = secondaryAction
        self.shown = True
        self.overrideColour = overrideColour
    def draw(self):
        if not self.shown: return
        pg.draw.rect(screen, self.overrideColour, self.rect,0,5)
        text_surface = FONT.render(self.text, True, BUTTON_TEXT_COLOR)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def handle_event(self, event):
        if not self.shown: return
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.action:
                    self.action()
                if self.secondaryAction:
                    self.secondaryAction()

    def setShown(self, bol):
        self.shown = bol

class TextInputField:
    def __init__(self, x, y, width, height, shiftWrap = True, overrideColour = WHITE):
        self.x = x; self.y = y; self.width = width; self.height = height
        self.rect = pg.Rect(x + 2, y + 2, width - 4, height - 4)
        self.backrect = pg.Rect(x, y, width, height)
        self.text = ""
        self.active = False
        self.shown = False
        self.returnFunc = None
        self.char_limit = 99
        self.shiftWrap = shiftWrap
        self.overrideColour = overrideColour

    def revamp_rect(self, x, y):
        self.x = x
        self.y = y
        self.rect = pg.Rect(x + 2, y + 2, self.width - 4, self.height - 4)
        self.backrect = pg.Rect(x, y, self.width, self.height)

    def handle_event(self, event):
        if not self.shown: return

        if settings.DOdictation:
            with mic as source:
                print("Say something!")
                audio = r.listen(source)
                print("Got it! Now to recognize it...")
                try:
                    dcoded = r.recognize_google(audio)

                    for bw in ['backspace', 'delete', 'erase', 'remove']:
                        if bw in dcoded.split(' '):
                            if len(self.text) > 0:
                                self.text = ' '.join(self.text.split(' ')[:-1])
                                return

                    for sw in ['stop', 'exit', 'done', 'enter']:
                        if sw in dcoded.split(' '):
                            self.returnFunc(self.text)
                            self.returnFunc = None
                            self.char_limit = 99
                            self.setShown(False)
                            return                    

                    self.text += dcoded + " "

                    print("You said: " + dcoded)
                except sr.UnknownValueError:
                    print("Google Speech Recognition could not understand the audio")
                except sr.RequestError as e:
                    print("Could not request results from Google Speech Recognition service; {0}".format(e))

        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            # Check if the mouse click is within the text input field
            if self.rect.collidepoint(event.pos):
                self.active = True
            else:
                self.active = False
        elif event.type == pg.KEYDOWN and self.active:
            if event.key == pg.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pg.K_RETURN:
                if self.returnFunc != None: self.returnFunc(self.text)
                self.returnFunc = None
                self.char_limit = 99
                self.setShown(False)
            else:
                if len(self.text) < self.char_limit:
                    self.text += event.unicode

    def draw(self, surface):
        if not self.shown: return
        pg.draw.rect(surface, BLACK, self.backrect)
        pg.draw.rect(surface, WHITE, self.rect)

        text_surface = FONT.render(self.text, True, BLACK)

        sfce = pg.Surface((self.width, self.height))
        sfce.fill(WHITE)

        y = 0
        if self.shiftWrap:
            sfce.blit(text_surface, (((-text_surface.get_width() + 275) if text_surface.get_width() > 275 else 0), 0))
        else:
            for x in wrap_text(self.text, self.width // 10):
                text_surface = FONT.render(x, True, BLACK)
                sfce.blit(text_surface, (0, y))
                y += 30
                #sfce = pg.transform.scale(sfce, (296, 36 + 20 * len(wrap_text(self.text, TEXT_LIMIT)) - 1))

        surface.blit(sfce, (self.x + 2, self.y + 2))

        if settings.DOdictation:
            listening_text = font(20).render("Listening...", True, BLACK)
            screen.blit(listening_text, (self.x, self.y - 20))

    def setShown(self, bol):
        self.shown = bol

    def initTextInput(self, x, y, returnFunc = None, chrlmt = None):
        self.text = ""
        self.revamp_rect(x, y)
        self.setShown(True)
        self.returnFunc = returnFunc
        if chrlmt != None:
            self.char_limit = chrlmt

class Timer:
    def __init__(self):
        self.start_time = None
        self.time_length = None
        self.running = False
        self.return_action = None

    def initTimer(self, time, ret_act = None): #time in milliseconds
        self.start_time = pg.time.get_ticks()
        self.time_length = time
        self.running = True
        self.return_action = ret_act

    def update(self):
        time_now = pg.time.get_ticks()
        if self.running:
            if time_now - self.start_time > self.time_length:
                self.running = False
                if self.return_action != None: self.return_action()
            else:
                return self.start_time + self.time_length - time_now

class Flashcard:
    def __init__(self, contents):
        self.text = contents

class FlashcardDeck:
    def __init__(self, name):
        self.name = name
        self.flashcards = []
        self.rect = None
        self.revamp_rect(0, 0)

    def revamp_rect(self, x, y):
        self.rect = pg.Rect(x, y, 300, 50)

    def create_flashcard(self, text):
        self.flashcards.append(Flashcard(text))

    def delete_flashcard(self, index):
        self.flashcards.pop(index)

    def draw(self, x, y):
        self.revamp_rect(x, y)
        pg.draw.rect(screen, (150, 150, 150), (x, y, 300, 50))
        text = font(30).render(self.name, True, BLACK)
        screen.blit(text, (x + 2, y + 2))

    def handle_event(self, event):
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                flashcardsection.select_deck(self)

class FlashcardSection:
    def __init__(self):
        self.flashcarddecks = []
        self.json_data = None
        self.load_flash_decks()
        self.update_flash_json()

        self.displaying_cards = False
        self.display_target = None
        self.selected_card_index = None

        self.adddeckbutton = Button(200, 200, 200, 30, "Add Deck", self.add_card_deck)
        self.right_button = Button(WIDTH - 100, yaxis_centering(20), 20, 20, ">", self.right_flash_card)
        self.left_button = Button(100, yaxis_centering(20), 20, 20, "<", self.left_flash_card)
        self.create_card_button = Button(xaxis_centering(200), 140, 200, 30, "Create Card", self.create_flashcard_button)
        self.delete_card_button = Button(xaxis_centering(200), HEIGHT - 150, 200, 30, "Delete Card", self.delete_card)
        self.delete_deck_button = Button(xaxis_centering(200), HEIGHT - 70, 200, 30, "Delete Deck", self.delete_deck)

    def delete_deck(self):
        self.flashcarddecks.remove(self.display_target)

        temp_decks = self.json_data["decks"]

        for x, val in enumerate(temp_decks):
            if val["name"] == self.display_target.name:
                temp_decks.pop(x)
                break

        self.update_flash_json()

        self.open_flashcard_section()

    def open_flashcard_section(self):
        global CURRENT_SRC; CURRENT_SRC = "flashcards"
        self.displaying_cards = False
        self.flashcard_section()

    def delete_card(self):
        self.display_target.flashcards.pop(self.selected_card_index)
        for x in self.json_data["decks"]:
            if x["name"] == self.display_target.name:
                x["cards"].pop(self.selected_card_index)
                break
        self.update_flash_json()

        if len(self.display_target.flashcards) == 0:
            self.flashcard_section()
        else:
            self.selected_card_index += 1
            self.selected_card_index %= len(self.display_target.flashcards)
            self.flashcard_section()

    def create_flashcard_button(self):
        text_input.initTextInput(xaxis_centering(300), HEIGHT - 200, self.apply_create_card_text)

    def apply_create_card_text(self, txt):
        self.display_target.create_flashcard(txt)
        for x in self.json_data["decks"]:
            if x["name"] == self.display_target.name:
                x["cards"].append(txt)
                break
        self.update_flash_json()
        self.flashcard_section()

    def right_flash_card(self):
        if len(self.display_target.flashcards) == 0: return
        self.selected_card_index += 1
        self.selected_card_index %= len(self.display_target.flashcards)
        self.flashcard_section()

    def left_flash_card(self):
        if len(self.display_target.flashcards) == 0: return
        l = len(self.display_target.flashcards)
        self.selected_card_index += l - 1
        self.selected_card_index %= l
        self.flashcard_section()

    def flashcard_section(self):
        self.right_button.setShown(False)
        self.left_button.setShown(False)
        self.create_card_button.setShown(False)
        self.delete_card_button.setShown(False)
        self.delete_deck_button.setShown(False)

        self.adddeckbutton.setShown(True)

        generate_topbar()

        if self.displaying_cards:
            self.adddeckbutton.setShown(False)

            self.create_card_button.setShown(True)
            self.delete_deck_button.setShown(True)
            self.create_card_button.draw()
            self.delete_deck_button.draw()

            pg.draw.rect(screen, (255, 255, 255), (xaxis_centering(500), 200, 500, 200))

            try:
                for x, txt in enumerate(wrap_text(self.display_target.flashcards[self.selected_card_index].text, 47)):
                    text = font(30).render(txt, True, BLACK)
                    screen.blit(text, (xaxis_centering(text.get_width()), 220 + x * 20))
                self.right_button.setShown(True)
                self.left_button.setShown(True)
                self.delete_card_button.setShown(True)
                self.right_button.draw()
                self.left_button.draw()
                self.delete_card_button.draw()
            except IndexError:
                text = font(40).render("No cards in this deck", True, (100, 100, 100))
                screen.blit(text, (xaxis_centering(text.get_width()), yaxis_centering(text.get_height())))

            return

        text = font(50).render("Flashcards", True, BLACK)
        screen.blit(text, (xaxis_centering(text.get_width()), 75))

        x = WIDTH//2 + 125
        y = 150
        for z, fcd in enumerate(self.flashcarddecks):
            fcd.draw(x, y + 75 * z)

        self.adddeckbutton.draw()

    def select_deck(self, flashdeck):
        self.displaying_cards = True
        self.display_target = flashdeck
        self.selected_card_index = 0
        self.flashcard_section()

    def add_card_deck(self):
        if not text_input.shown:
            text_input.initTextInput(150, 100, self.set_new_deck_text, chrlmt = 24)
        else:
            self.set_new_deck_text(text_input.text)
            text_input.setShown(False)

    def load_flash_decks(self):
        with open('resources/flashcards.json', 'r') as json_file:
            data = json.load(json_file)
        json_file.close()

        self.json_data = data

        for d in data["decks"]:
            self.flashcarddecks.append(FlashcardDeck(d["name"]))
            for fc in d["cards"]:
                self.flashcarddecks[-1].create_flashcard(fc)

    def set_new_deck_text(self, txt):
        self.flashcarddecks.append(FlashcardDeck(txt))
        newfcjson = {}
        newfcjson["name"] = txt
        newfcjson["cards"] = []
        self.json_data["decks"].append(newfcjson)
        self.update_flash_json()
        self.flashcard_section()

    def update_flash_json(self):
        with open('resources/flashcards.json', 'w') as f:
            json.dump(self.json_data, f)

class StudyTimerSection:
    def __init__(self):
        self.timer = Timer()
        self.timerRunning = False

        self.currentState = "none"

        self.pomodoroButton = Button(xaxis_centering(200), 200, 200, 30, "Pomodoro", self.pomodoroTechnique)

        self.optionButtons = [self.pomodoroButton]

    def techniqueEnded(self):
        self.currentState = "none"

        self.open_studytimer_section()

    def pomodoroStudyEnded(self):
        self.timer.initTimer(5 * 60 * 1000, self.techniqueEnded)
        self.currentState = "Taking a break"
    def pomodoroTechnique(self):
        self.timer.initTimer(25 * 60 * 1000, self.pomodoroStudyEnded)
        self.timerRunning = True
        self.currentState = "Studying"

    def open_studytimer_section(self):
        global CURRENT_SRC; CURRENT_SRC = "studytimer"
        self.studytimer_section()

    def timerEnded(self):
        self.timerRunning = False

    def studytimer_section(self):
        generate_topbar()

        self.update()

        [but.setShown(True) for but in self.optionButtons]
        [but.draw() for but in self.optionButtons]

    def update(self):
        generate_topbar()

        if self.currentState != "none":
            text = font(60).render(self.currentState, True, (100, 100, 100))
            screen.blit(text, (xaxis_centering(text.get_width()), 200))
            [but.setShown(False) for but in self.optionButtons]

        get_timer = self.timer.update()

        if get_timer != None:
            raw_time = round(get_timer / 1000)

            h = math.floor(raw_time / 3600)
            m = math.floor((raw_time % 3600) / 60)
            s = raw_time - (h * 3600 + m * 60)

            strm = str(m)
            strs = str(s)

            if len(strm) == 1: strm = "0" + strm
            if len(strs) == 1: strs = "0" + strs

            text = font(150).render(strm + ":" + strs, True, WHITE) #omitted {str(h)} for now bc its unneccesary
            screen.blit(text, (xaxis_centering(text.get_width()), 100))

        #self.studytimer_section()

class Settings:
    def __init__(self):
        self.nomousebutton = Button(xaxis_centering(200) - 70, 100, 200, 30, "Eye Tracking", self.no_mouse, self.open_settings)
        self.DOnoMouse = False
        self.dictationbutton = Button(xaxis_centering(200) - 70, 150, 200, 30, "Dictation", self.dictation, self.open_settings)
        self.DOdictation = False
        self.handtrackingbutton = Button(xaxis_centering(200) - 70, 200, 200, 30, "Full Hand Tracking", self.handtracking, self.open_settings)
        self.DOhandtracking = False

        self.optionButtons = [self.nomousebutton, self.dictationbutton, self.handtrackingbutton]

    def draw_toggle(self, x, y, istoggle):
        pg.draw.rect(screen, (169, 169, 169), (x, y, 40, 40))
        if istoggle:
            pg.draw.circle(screen, (0, 0, 0), (x + 20, y + 20), 10)

    def no_mouse(self):
        self.DOnoMouse = not self.DOnoMouse; global eyetracking; eyetracking = self.DOnoMouse
    def dictation(self):
        self.DOdictation = not self.DOdictation
    def handtracking(self):
        self.DOhandtracking = not self.DOhandtracking; global full_hand_tracking; full_hand_tracking = self.DOhandtracking

    def open_settings(self):
        global CURRENT_SRC; CURRENT_SRC = "settings"
        generate_topbar()

        self.update()

    def update(self):
        generate_topbar()

        self.nomousebutton.setShown(True)
        self.nomousebutton.draw()
        self.draw_toggle(xaxis_centering(50) + 70, 100, self.DOnoMouse)

        self.dictationbutton.setShown(True)
        self.dictationbutton.draw()
        self.draw_toggle(xaxis_centering(50) + 70, 150, self.DOdictation)

        self.handtrackingbutton.setShown(True)
        self.handtrackingbutton.draw()
        self.draw_toggle(xaxis_centering(50) + 70, 200, self.DOhandtracking)

class Journal:
    def __init__(self):
        self.journals = []
        self.json_data = None
        self.journal_state = "none"
        
        self.JournalText = TextInputField(150, 100, 600, 40, False)
        self.JournalName = TextInputField(250, 200, 600, 200, False)
        self.blurt_text_input = TextInputField(500, 200, 500, 200, False)

        self.new_journal_name = None
        self.new_journal_text = None
        
        self.selected_journal = None
        self.display_target = None
        self.selectedJournal = None
        self.current_displayed_names = []

        self.showingBlurtNotes = False

        self.addjournalbutton = Button(100, HEIGHT - 70, 200, 30, "Create Journal", self.create_journal_scene, overrideColour=LIGHT_BUTTON_COLOUR)
        self.create_journal_button = Button(350, HEIGHT - 70, 200, 30, "Open Journal", self.load_journal, overrideColour=LIGHT_BUTTON_COLOUR) #THIS IS STILL TO DO
        self.delete_journal_button = Button(600, HEIGHT - 70, 200, 30, "Delete Journal", self.delete_journal, overrideColour=LIGHT_BUTTON_COLOUR)
        self.blurt_button = Button(850, HEIGHT - 70, 200, 30, "Blurt", self.blurt_section, overrideColour=LIGHT_BUTTON_COLOUR)
        self.blurttogglebutton = Button(xaxis_centering(200), HEIGHT - 80, 200, 30, "Toggle Notes", self.toggle_blurt_notes, overrideColour=LIGHT_BUTTON_COLOUR)

        self.save_journal_button = Button(500, HEIGHT - 80, 200, 30, "Save Journal", self.save_journal, overrideColour=LIGHT_BUTTON_COLOUR)
        
    def toggle_blurt_notes(self):
        self.showingBlurtNotes = not self.showingBlurtNotes
        self.update()

    def blurt_section(self):
        self.blurt_text_input.initTextInput(600, 200, returnFunc=None, chrlmt=1000)

        self.journal_state = "blurt"
        self.update()

    def load_journal(self):
        if self.selected_journal == None: return
        for journal in self.journals:
            if journal["name"] == self.selected_journal:
                self.journal_state = "display"
                self.display_target = journal
                self.update()
        
    def update_journal_json(self):
        with open('resources/flashcards.json', 'w') as f:
            json.dump(self.json_data, f)
    
    def create_journal(self, name, content):
        print("Creating journal")
        journal = {
            "name": name,
            "content": content
        }
        self.journals.append(journal)
        self.save_journals()
        
        
    def set_new_journal_name(self, txt):
        self.new_journal_name = txt
    
    def set_new_journal_text(self, txt):
        self.new_journal_text = txt
        
    def create_journal_scene(self):
        self.journal_state = "create"   
        self.update()
        
        
    def delete_journal(self):
        for x, journal in enumerate(self.journals):
            if journal["name"] == self.selected_journal:
                self.journals.pop(x)
                break

        self.save_journals()
        self.open_journal_section()
    
    def save_journals(self):
        data = {
            "journals": self.journals
        }
        with open('resources/journals.json', 'w') as f:
            json.dump(data, f)
    
    def load_journals(self):
        try:
            with open('resources/journals.json', 'r') as f:
                data = json.load(f)
                self.journals = data["journals"]
        except FileNotFoundError:
            self.journals = []
            
    def save_journal(self):
        name = self.new_journal_name
        content = self.new_journal_text
        
        print(name)
        print(content)
        
        if name and content:
            self.create_journal(name, content)
            self.journal_state = "none"
            self.new_journal_name = None
            self.new_journal_text = None
            self.update()
        else:
            print("Please fill in all fields")
    
    def update(self, from_original_button = False):
        self.load_journals()
        generate_topbar()
        # Display the journals
        
        if from_original_button:
            self.journal_state = "none"
            self.selected_journal = None
            self.display_target = None

        if not self.journal_state == "create":
            self.JournalText.setShown(False)
            self.JournalName.setShown(False)
            self.blurt_text_input.setShown(False)

        if self.journal_state == "none":
            self.current_displayed_names = []
            x = 100
            y = 150
            for i, journal in enumerate(self.journals):
                text = font(20).render(journal["name"], True, RED if self.selected_journal == journal["name"] else WHITE)
                screen.blit(text, (x, y))
                self.current_displayed_names.append((pg.rect.Rect(x, y, text.get_width(), text.get_height()), journal['name']))
                x += 100
            self.addjournalbutton.setShown(True)
            self.addjournalbutton.draw()
            
            self.create_journal_button.setShown(True)
            self.create_journal_button.draw()
            
            self.delete_journal_button.setShown(True)
            self.delete_journal_button.draw()

            self.blurt_button.setShown(True)
            self.blurt_button.draw()

            self.blurttogglebutton.setShown(False)
            self.blurttogglebutton.draw()

            self.save_journal_button.setShown(False)
            self.save_journal_button.draw()
        
            self.blurt_text_input.setShown(False)

        elif self.journal_state == "create":
            self.JournalText.initTextInput(250, 100, self.set_new_journal_name, chrlmt=100)
            text = font(30).render("Title", True, WHITE)
            screen.blit(text, (150, 100))
            
            self.JournalName.initTextInput(250, 200, self.set_new_journal_text, chrlmt=1000)
            text = font(30).render("Text", True, WHITE)
            screen.blit(text, (150, 200))
            
            self.save_journal_button.setShown(True)
            self.save_journal_button.draw()

        elif self.journal_state == "display":
            self.addjournalbutton.setShown(False)
            self.addjournalbutton.draw()
            
            self.create_journal_button.setShown(False)
            self.create_journal_button.draw()
            
            self.delete_journal_button.setShown(False)
            self.delete_journal_button.draw()

            self.save_journal_button.setShown(False)
            self.save_journal_button.draw()

            text = font(30).render(self.display_target["name"], True, WHITE)
            screen.blit(text, (150, 100))
            
            for x, txt in enumerate(wrap_text(self.display_target["content"], 47)):
                text = font(30).render(txt, True, WHITE)
                screen.blit(text, (150, 200 + x * 30))

            #text = font(30).render(self.display_target["content"], True, WHITE)
            #screen.blit(text, (150, 200))

        elif self.journal_state == "blurt":
            if self.selected_journal == None: return
            
            self.blurt_text_input.setShown(True)
            self.blurttogglebutton.setShown(True)
            self.blurttogglebutton.draw()
            print("________________________")
            if self.showingBlurtNotes:
                print("Showing notes")
                blurtingTxt = ""
                for journal in self.journals:
                    if journal["name"] == self.selected_journal:
                        blurtingTxt = journal["content"]
                        break

                for x, txt in enumerate(wrap_text(blurtingTxt, 47)):
                    text = font(30).render(txt, True, WHITE)
                    screen.blit(text, (50, 200 + x * 30))

            self.blurt_text_input.draw(screen)
            
    def open_from_button(self):
        self.open_journal_section(True)

    def open_journal_section(self, from_original_button = False):
        global CURRENT_SRC
        CURRENT_SRC = "journal"
        generate_topbar()
        self.update(from_original_button)

    def handle_event(self, event):
        if self.journal_state == "none":
            for rect, name in self.current_displayed_names:
                if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                    if rect.collidepoint(event.pos):
                        self.selected_journal = name
                        self.open_journal_section()
        
class cat_room:
    def __init__(self):
        self.gifs = [
            Gif("resources/gifs/Chinese Dance", 700, 200),
            Gif("resources/gifs/Chipi Chipi", 400, 400),
            Gif("resources/gifs/Computer", 800, 400),
        ]

        #self.audio = AudioPlayer("resources/audio/meowing.mp3")
    
    def play_gifs(self):
        for gif in self.gifs:
            gif.play(screen)

    def open_cats(self):
        global CURRENT_SRC; CURRENT_SRC = "support"

        generate_topbar()
        
        self.play_gifs()

        #self.audio.play()

        image = pg.image.load("resources/images/cat1.png").convert_alpha()
        image = pg.transform.scale(image, (int(image.get_width() * 0.5), int(image.get_height() * 0.5)))
        screen.blit(image, (10, 40))
        
        image2 = pg.image.load("resources/images/cat2.png").convert_alpha()
        image2 = pg.transform.scale(image2, (int(image2.get_width() * 0.5), int(image2.get_height() * 0.5)))
        screen.blit(image2, (1000, 400))

class Schedule:
    def __init__(self):
        self.schedule_file = "resources/schedule.json"
        self.jsonData = self.load_schedule()
        self.start_time = pg.time.get_ticks()
        self.today_time = pg.time.get_ticks() - self.start_time + self.safe_json(today())

    def safe_json(self, v, override = None):
        return (self.jsonData.get(v) if self.jsonData.get(v) else (0 if override == None else override))

    def save_schedule(self):
        self.jsonData[today()] = self.safe_json(today()) + pg.time.get_ticks() - self.start_time
        with open(self.schedule_file, 'w') as f:
            json.dump(self.jsonData, f)
        f.close()

    def load_schedule(self):
        with open(self.schedule_file, 'r') as f:
            data = json.load(f)
        f.close()

        return data

    def open_schedule(self):
        global CURRENT_SRC; CURRENT_SRC = "schedule"
        generate_topbar()
        self.refresh(True)

    def schedule_section(self):
        for i, x in enumerate(['3 Days Ago', '2 Days Ago', 'Yesterday']):
            text = font(20).render(x, True, WHITE)
            screen.blit(text, (50 + i * 150, HEIGHT - 100))
            time_str = str(dt.timedelta(milliseconds=self.safe_json(days_ago(3 - i)))).split('.')[0]
            text = font(17).render(time_str, True, WHITE)
            screen.blit(text, (50 + i * 150, HEIGHT - 70))

    def refresh(self, excl = False):
        if not excl: self.open_schedule()

        self.schedule_section()

        self.today_time = pg.time.get_ticks() - self.start_time + self.safe_json(today())
        font = pg.font.Font('resources/etna.ttf', 50)
        text = font.render("Study Time Today", True, WHITE)
        time_str = str(dt.timedelta(milliseconds=self.today_time))
        screen.blit(text, (xaxis_centering(text.get_width()), 175))
        font = pg.font.Font('resources/etna.ttf', 40)
        text = font.render(time_str.split('.')[0], True, WHITE)
        screen.blit(text, (xaxis_centering(text.get_width()), 250))

#Sections
flashcardsection = FlashcardSection()
studytimersection = StudyTimerSection()
settings = Settings()
journal = Journal()
catroom = cat_room()
schedule = Schedule()

#Top bar buttons
homebutton = Button(40, 10, 150, 30, "Home", home_section, overrideColour=BACKGROUND)
flashbutton = Button(xaxis_centering(150), yaxis_centering(30), 150, 30, "Flashcards", flashcardsection.open_flashcard_section, overrideColour=LIGHT_BUTTON_COLOUR)
studytimerbutton = Button(160, 10, 150, 30, "Study Timer", studytimersection.open_studytimer_section, overrideColour=BACKGROUND)
journalbutton = Button(310, 10, 150, 30, "Journal", journal.open_from_button, overrideColour=BACKGROUND)
supportbutton = Button(460, 10, 150, 30, "Support Room", catroom.open_cats, overrideColour=BACKGROUND)
schedulebutton = Button(610, 10, 150, 30, "Schedule", schedule.open_schedule, overrideColour=BACKGROUND)

settingsbutton = Button(1040, 10, 150, 30, "Settings", settings.open_settings)

logo = pg.image.load("resources/images/Applogo.png").convert_alpha()
logo = pg.transform.scale(logo, (int(logo.get_width() * 0.15), int(logo.get_height() * 0.15)))

navbarbuttons = [homebutton, studytimerbutton, journalbutton, settingsbutton, supportbutton, schedulebutton]

text_input = TextInputField(100, 100, 300, 40)

all_buttons = [navbarbuttons]

extra_event_handling = [
    ("home", [flashbutton]),
    ("flashcards", flashcardsection.flashcarddecks), 
    ("flashcards", [flashcardsection.left_button, flashcardsection.right_button, flashcardsection.create_card_button, flashcardsection.delete_card_button, flashcardsection.delete_deck_button, flashcardsection.adddeckbutton]),
    ("studytimer", studytimersection.optionButtons),
    ("settings", settings.optionButtons),
    ("journal", [journal, journal.addjournalbutton, journal.create_journal_button, journal.delete_journal_button, journal.save_journal_button, journal.blurt_button])
]

home_section()

running = True



programIcon = pg.image.load('resources/images/Applogo.png')
pg.display.set_icon(programIcon)

while running:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            schedule.save_schedule()
            running = False
        for button_ar in all_buttons:
            [button.handle_event(event) for button in button_ar]
        text_input.handle_event(event)
        journal.JournalText.handle_event(event)
        journal.JournalName.handle_event(event)
        journal.blurt_text_input.handle_event(event)
        if CURRENT_SRC == "home":
            flashbutton.draw()
        #if CURRENT_SRC != "support":
            #cat_room.audio.stop()

        for (loci, pack) in extra_event_handling:
            if CURRENT_SRC == loci or loci == "any":
                for obj in pack:
                    obj.handle_event(event)
    if studytimersection.timerRunning: studytimersection.update()
    if CURRENT_SRC == "support":
        catroom.play_gifs()
    elif CURRENT_SRC == "schedule":
        if pg.time.get_ticks() % 1000 == 0:
            schedule.refresh()

    text_input.draw(screen)
    journal.JournalText.draw(screen)
    journal.JournalName.draw(screen)
    journal.blurt_text_input.draw(screen)

    
    if full_hand_tracking:
        
        cap = cv2.VideoCapture(0)
        detector = htl.HandDetector()
        #while True:
        ret, frame = cap.read()
        detector.analyse(frame)
        frame = detector.detection(frame)
        frame_width, frame_height, _ = frame.shape
        
        LmList = detector.position(frame)
        
        if len(LmList) != 0:
            
            x1, y1 = LmList[8][1:] #pointer
            x1, y1 = LmList[12][1:] #middle
            
            fingers = detector.fingers_up()
            
            if fingers[1] == 1 and fingers[2] == 0: #just move
                x3 = np.interp(x1, (0, frame_width), (0, Screen_Width))
                y3 = np.interp(y1, (0, frame_height), (0, Screen_Height))
                
                current_x = previous_x + (x3 - previous_x) / smoothening
                current_y = previous_y + (y3 - previous_y) / smoothening
                
                pyautogui.moveTo(Screen_Width-current_x, current_y)
                
                previous_x, previous_y = current_x, current_y
                
            if fingers[1] == 1 and fingers[2] == 1: #CLICKY CLICKY
                distance = detector.find_distance(8, 12)  #pointer and middle finger
                if distance <= 75:
                    pyautogui.click()
                    cv2.circle(frame, (x1, y1), 15, (0,255,0), cv2.FILLED)
                
        cTime = time.time()
        fps = 1/(cTime-pTime)
        pTime = cTime
        
        frame = cv2.flip(frame, 1)
        cv2.putText(frame, str(int(fps)), (20,50), cv2.FONT_HERSHEY_PLAIN, 3, (255,0,0), 3)
        
        if showtheimage:
            cv2.imshow('Hand Mouse Control', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): #press q to kill 
            cap.release()
            cv2.destroyAllWindows()
            break
        
    if eyetracking:
        cam = cv2.VideoCapture(0)
        face_mesh = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True)
        screen_w, screen_h = pyautogui.size()
        _ , frame = cam.read()
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        output = face_mesh.process(rgb_frame)
        landmarkpoints = output.multi_face_landmarks
        frame_h, frame_w, _ = frame.shape
        
        if landmarkpoints:
            landmarks = landmarkpoints[0].landmark
            for id, landmark in enumerate(landmarks[468:473]):
                x = int(landmark.x * frame_w)
                y = int(landmark.y * frame_h)
                cv2.circle(frame, (x, y), 3, (0, 255, 0))
                if id == 1:
                    screen_x = (screen_w / frame_w) * x
                    screen_y = (screen_h / frame_h) * y
                    pyautogui.moveTo(screen_x, screen_y)
            
            left = [landmarks[145], landmarks[159]]
            right = [landmarks[374], landmarks[386]]
            
            if (left[0].y - left[1].y) <= 0.0127 and (right[0].y - right[1].y) <= 0.0127:
                pyautogui.sleep(1)
                continue
        
            for landmark in left:
                x = int(landmark.x * frame_w)
                y = int(landmark.y * frame_h)
                cv2.circle(frame, (x, y), 3, (0, 255, 255))
            if (left[0].y - left[1].y) <= 0.0127:
                pyautogui.click(button='left')
                pyautogui.sleep(1)
            
            for landmark in right:
                x = int(landmark.x * frame_w)
                y = int(landmark.y * frame_h)
                cv2.circle(frame, (x, y), 3, (0, 255, 255)) 
            if (right[0].y - right[1].y) <= 0.0127:
                pyautogui.click(button='right')
                pyautogui.sleep(1)
                
        cv2.imshow("Eye Cam View", frame)
        cv2.waitKey(1)

    # Update the display
    pg.display.flip()

# Quit pg
pg.quit()
sys.exit()
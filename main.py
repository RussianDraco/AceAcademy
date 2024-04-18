import pygame as pg
import sys, os, json, cv2, pyautogui, time
import math, cv2, pyautogui
import mediapipe as mp
import hand_tracking_landmarks as htl
import numpy as np
import speech_recognition as sr

# Initialize pg
pg.init()

#Init speech recognition
mic = sr.Microphone()
r = sr.Recognizer()

# Constants
WIDTH, HEIGHT = 1200, 600
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BACKGROUND = (23, 4, 25)
TEXT_LIMIT = 19

DARK_BUTTON_COLOUR = (90, 66, 107)
LIGHT_BUTTON_COLOUR = (142, 115, 162)
BUTTON_TEXT_COLOR = (255, 255, 255)
FONT = pg.font.Font(None, 25)
FONT28 = pg.font.Font(None, 25)



# Accessibility
full_hand_tracking = True
camera_width, camera_height = 640, 480
Screen_Width, Screen_Height = pyautogui.size()
pTime = 0
smoothening = 8
previous_x, previous_y = 0, 0
current_y, current_x = 0, 0
showtheimage = False

# Create the screen
screen = pg.display.set_mode((WIDTH, HEIGHT))
pg.display.set_caption("Edupanion")

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

def home_section():
    global CURRENT_SRC; CURRENT_SRC = "home"
    generate_topbar()

    pg.draw.rect(screen, BACKGROUND, (0, 50, WIDTH, HEIGHT - 50))





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
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.action:
                    self.action()
                if self.secondaryAction:
                    self.secondaryAction()

    def setShown(self, bol):
        self.shown = bol

class TextInputField:
    def __init__(self, x, y, width, height):
        self.x = x; self.y = y; self.width = width; self.height = height
        self.rect = pg.Rect(x + 2, y + 2, width - 4, height - 4)
        self.backrect = pg.Rect(x, y, width, height)
        self.text = ""
        self.active = False
        self.shown = False
        self.returnFunc = None
        self.char_limit = 99

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
                self.returnFunc(self.text)
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

        sfce = pg.Surface((296, 36))
        sfce.fill(WHITE)

        sfce.blit(text_surface, (((-text_surface.get_width() + 275) if text_surface.get_width() > 275 else 0), 0))

        surface.blit(sfce, (self.x + 2, self.y + 2))

        if settings.DOdictation:
            listening_text = font(20).render("Listening...", True, BLACK)
            screen.blit(listening_text, (self.x, self.y - 20))

    def setShown(self, bol):
        self.shown = bol

    def initTextInput(self, x, y, returnFunc, chrlmt = None):
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

            text = font(150).render(strm + ":" + strs, True, BLACK) #omitted {str(h)} for now bc its unneccesary
            screen.blit(text, (xaxis_centering(text.get_width()), 100))

        #self.studytimer_section()

class Settings:
    def __init__(self):
        self.nomousebutton = Button(xaxis_centering(200) - 70, 100, 200, 30, "No Mouse", self.no_mouse, self.open_settings)
        self.DOnoMouse = False
        self.dictationbutton = Button(xaxis_centering(200) - 70, 150, 200, 30, "Dictation", self.dictation, self.open_settings)
        self.DOdictation = False

        self.optionButtons = [self.nomousebutton, self.dictationbutton]

    def draw_toggle(self, x, y, istoggle):
        pg.draw.rect(screen, (169, 169, 169), (x, y, 40, 40))
        if istoggle:
            pg.draw.circle(screen, (0, 0, 0), (x + 20, y + 20), 10)

    def no_mouse(self):
        self.DOnoMouse = not self.DOnoMouse
    def dictation(self):
        self.DOdictation = not self.DOdictation

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


#Sections
flashcardsection = FlashcardSection()
studytimersection = StudyTimerSection()
settings = Settings()

#Top bar buttons
homebutton = Button(10, 10, 100, 30, "Home", home_section, overrideColour=BACKGROUND)
flashbutton = Button(120, 10, 100, 30, "Flashcards", flashcardsection.open_flashcard_section, overrideColour=BACKGROUND)
studytimerbutton = Button(230, 10, 100, 30, "Study Timer", studytimersection.open_studytimer_section, overrideColour=BACKGROUND)

settingsbutton = Button(1040, 10, 150, 30, "Settings", settings.open_settings)

navbarbuttons = [homebutton, flashbutton, studytimerbutton, settingsbutton]

text_input = TextInputField(100, 100, 300, 40)

all_buttons = [navbarbuttons]

extra_event_handling = [
    ("flashcards", flashcardsection.flashcarddecks), 
    ("flashcards", [flashcardsection.left_button, flashcardsection.right_button, flashcardsection.create_card_button, flashcardsection.delete_card_button, flashcardsection.delete_deck_button, flashcardsection.adddeckbutton]),
    ("studytimer", studytimersection.optionButtons),
    ("settings", settings.optionButtons)
    ]

home_section()

running = True
while running:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False
        for button_ar in all_buttons:
            [button.handle_event(event) for button in button_ar]
        text_input.handle_event(event)
        for (loci, pack) in extra_event_handling:
            if CURRENT_SRC == loci or loci == "any":
                for obj in pack:
                    obj.handle_event(event)

    if studytimersection.timerRunning: studytimersection.update()

    text_input.draw(screen)
    
    if full_hand_tracking:
<<<<<<< HEAD
        
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
=======
        pass
       #while True:
       #     caption = cv2.VideoCapture(0)
       #     caption.set(3, camera_width)
       #     caption.set(4, camera_height)
       #     success, img = caption.read()
       #     
       #     cv2.imshow("Face_Cam", img)
>>>>>>> 924f206d37a6c7bda24d4d9a102f15e6c3772411
        

    # Update the display
    pg.display.flip()

# Quit pg
pg.quit()
sys.exit()
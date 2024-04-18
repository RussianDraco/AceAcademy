class Game:
    def __init__(self, flashcards):
                self.flashcards = flashcards
                self.cards = []
                self.selected_cards = []
                self.matched_cards = []
                self.create_cards()

    def create_cards(self):
        for flashcard in self.flashcards:
            card1 = Card(flashcard)
            card2 = Card(flashcard)
            self.cards.append(card1)
            self.cards.append(card2)

    def select_card(self, card):
        if card not in self.matched_cards and card not in self.selected_cards:
            self.selected_cards.append(card)
            card.flip()

            if len(self.selected_cards) == 2:
                self.check_match()

    def check_match(self):
        card1, card2 = self.selected_cards
        if card1.content == card2.content:
            self.matched_cards.append(card1)
            self.matched_cards.append(card2)
        else:
            card1.flip()
            card2.flip()

        self.selected_cards = []

    def draw(self):
        for card in self.cards:
            card.draw()

    def handle_event(self, event):
        for card in self.cards:
            card.handle_event(event)

    class Card:
    def __init__(self, content):
        self.content = content
        self.width = 100
        self.height = 150
        self.is_flipped = False

    def flip(self):
        self.is_flipped = not self.is_flipped

    def draw(self):
        # Draw the card based on its state (flipped or not)
        pass

    def handle_event(self, event):
        # Handle mouse click event on the card
        pass
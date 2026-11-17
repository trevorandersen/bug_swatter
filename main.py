"""
Bug Swatter - a pygame demonstration of inheritance, polymorphism and aggregation.

Pick up a swatter, then click on the bugs to swat them before the time runs
out. Leave the ladybirds alone: they are friendly, so swatting one loses points.

Files:
    main.py             the window, buttons and drawing (this file)
    game.py             Player and Game, which are handed the objects they use
    bugs.py             Bug and its subclasses, each with its own way of moving
    swatters.py         Swatter and its subclasses, each with its own way of hitting
    test_bug_swatter.py tests that the bugs, swatters and game work properly

Run the program with:
    pip install -r requirements.txt
    python main.py

Run the tests with:
    python -m unittest
"""

import math
from collections import Counter

import pygame

from bugs import BUG_TYPES, make_random_bug
from game import ROUND_SECONDS, Game, Player
from swatters import SWATTER_TYPES

WIDTH = 1100
HEIGHT = 720
PANEL_WIDTH = 280
MARGIN = 20
SCENE = pygame.Rect(PANEL_WIDTH, 0, WIDTH - PANEL_WIDTH, 440)
INFO = pygame.Rect(PANEL_WIDTH, SCENE.bottom, WIDTH - PANEL_WIDTH, HEIGHT - SCENE.bottom)
# Bugs stay this far inside the scene so that all of each bug can be seen
BUG_MARGIN = 30
BUG_BOUNDS = SCENE.inflate(-2 * BUG_MARGIN, -2 * BUG_MARGIN)
FRAMES_PER_SECOND = 60
MILLISECONDS_PER_SECOND = 1000
LEFT_MOUSE_BUTTON = 1
NUMBER_OF_SWATTER_KEYS = min(9, len(SWATTER_TYPES))  # the keys 1 to 9 choose a swatter
NUMBER_OF_STARTING_BUGS = 5
MAX_NUMBER_OF_BUGS = 14
SECONDS_BETWEEN_BUGS = 0.8
POPUP_SECONDS = 0.8  # how long the points for a swat are shown
POPUP_SPEED = 40  # pixels per second, upwards
POPUP_OFFSET = 34  # how far above the swat the points first appear
POPUP_MARGIN = 20  # the points stay this far below the top of the scene
BUG_METHOD_NAMES = ("move", "take_hit", "draw_body")

# Side panel layout, in pixels
BUTTON_WIDTH = PANEL_WIDTH - 2 * MARGIN
SWATTER_BUTTONS_TOP = 128
MAX_SWATTER_BUTTON_SPACING = 48
SWATTER_BUTTON_GAP = 8
SECTION_GAP = 12
HEADING_OFFSET = 27  # how far a section's heading is above the first thing in it
HEADING_HEIGHT = 26
LINE_HEIGHT = 20
DETAIL_LINE_HEIGHT = 22
NUMBER_OF_DETAIL_LINES = 3  # the lines about the player's swatter, under the buttons
SCORE_TOP = 512
TIME_TOP = SCORE_TOP + 40
TIME_BAR_TOP = TIME_TOP + 24
PROGRESS_BAR_HEIGHT = 8
NEW_GAME_BUTTON_TOP = TIME_BAR_TOP + 20
NEW_GAME_BUTTON_HEIGHT = 36
BEST_SCORE_TOP = NEW_GAME_BUTTON_TOP + NEW_GAME_BUTTON_HEIGHT + 10
KEY_HINTS_TOP = HEIGHT - 46

# Info panel layout, in pixels
INFO_TOP = INFO.top + 10
LEGEND_WIDTH = 400
LEGEND_TOP = INFO_TOP + 24
MAX_LEGEND_ROW_HEIGHT = 36
LEGEND_PICTURE_X = INFO.left + MARGIN + 18
LEGEND_NAME_X = LEGEND_PICTURE_X + 34
LEGEND_POINTS_X = LEGEND_NAME_X + 112
LEGEND_COUNT_X = LEGEND_POINTS_X + 135
LAST_SWAT_LEFT = INFO.left + LEGEND_WIDTH + MARGIN
GAME_OVER_SIZE = (420, 150)

PANEL_COLOUR = (245, 242, 232)
INFO_COLOUR = (252, 250, 244)
TEXT_COLOUR = (40, 40, 40)
MUTED_COLOUR = (120, 115, 105)
ACCENT_COLOUR = (60, 140, 70)
ACCENT_HOVER_COLOUR = (75, 160, 85)
WARNING_COLOUR = (200, 50, 40)
BUTTON_COLOUR = (255, 255, 255)
BUTTON_HOVER_COLOUR = (232, 244, 228)
BUTTON_TEXT_COLOUR = (255, 255, 255)
BORDER_COLOUR = (200, 195, 180)
DISABLED_COLOUR = (215, 212, 205)
RUG_COLOUR = (247, 243, 232)
STRIPE_COLOUR = (218, 230, 240)
CHECK_COLOUR = (186, 208, 228)
CHECK_SIZE = 40


def main():
    """Run Bug Swatter until its window is closed."""
    app = App()
    app.run()


class Button:
    """A rectangle with a label that can be clicked."""

    def __init__(self, rect, label):
        """Initialise a Button, where rect is (left, top, width, height)."""
        self.rect = pygame.Rect(rect)
        self.label = label

    def is_clicked(self, position):
        """Determine if a click at the (x, y) position is on this button."""
        return self.rect.collidepoint(position)

    def draw(self, surface, font, is_selected=False):
        """Draw the button, highlighted if it is selected or the mouse is over it."""
        is_hovered = self.rect.collidepoint(pygame.mouse.get_pos())
        text_colour = TEXT_COLOUR
        if is_selected:
            fill_colour = ACCENT_HOVER_COLOUR if is_hovered else ACCENT_COLOUR
            text_colour = BUTTON_TEXT_COLOUR
        elif is_hovered:
            fill_colour = BUTTON_HOVER_COLOUR
        else:
            fill_colour = BUTTON_COLOUR
        border_colour = ACCENT_COLOUR if is_selected else BORDER_COLOUR
        pygame.draw.rect(surface, fill_colour, self.rect, border_radius=8)
        pygame.draw.rect(surface, border_colour, self.rect, 2, border_radius=8)
        text = font.render(self.label, True, text_colour)
        surface.blit(text, text.get_rect(center=self.rect.center))


class App:
    """The Bug Swatter window, with its buttons, its rack of swatters and the game being played."""

    def __init__(self):
        """Initialise the window, fonts, swatters and buttons, then start the first game."""
        pygame.init()
        pygame.display.set_caption("Bug Swatter")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.title_font = pygame.font.SysFont("helvetica,arial", 30, bold=True)
        self.heading_font = pygame.font.SysFont("helvetica,arial", 18, bold=True)
        self.font = pygame.font.SysFont("helvetica,arial", 17)
        self.small_font = pygame.font.SysFont("helvetica,arial", 14)
        self.code_font = pygame.font.SysFont("menlo,consolas,courier new", 14)
        self.background = make_background()

        # Aggregation: the swatters are made here, once, and every player of every game uses these same ones
        self.swatters = [swatter_type() for swatter_type in SWATTER_TYPES]
        # Shrink the swatter buttons if there are so many kinds of swatter that the side panel would overflow.
        # Every class has object at the end of its __mro__, which the class hierarchy does not show.
        number_of_hierarchy_lines = max(len(swatter_type.__mro__) for swatter_type in SWATTER_TYPES) - 1
        height_below_swatter_buttons = (SECTION_GAP + NUMBER_OF_DETAIL_LINES * DETAIL_LINE_HEIGHT + SECTION_GAP
                                        + HEADING_HEIGHT + LINE_HEIGHT * number_of_hierarchy_lines)
        available_height = SCORE_TOP - HEADING_OFFSET - SWATTER_BUTTONS_TOP - height_below_swatter_buttons
        spacing = min(MAX_SWATTER_BUTTON_SPACING, available_height // len(SWATTER_TYPES))
        self.swatter_buttons = []
        for i, swatter in enumerate(self.swatters):
            rect = (MARGIN, SWATTER_BUTTONS_TOP + i * spacing, BUTTON_WIDTH, spacing - SWATTER_BUTTON_GAP)
            self.swatter_buttons.append(Button(rect, swatter.name))
        new_game_rect = (MARGIN, NEW_GAME_BUTTON_TOP, BUTTON_WIDTH, NEW_GAME_BUTTON_HEIGHT)
        self.new_game_button = Button(new_game_rect, "New game")

        # One bug of each kind, facing right, to be the pictures in the list of bugs.
        # Shrink the rows if there are so many kinds of bug that the list would overflow.
        row_height = min(MAX_LEGEND_ROW_HEIGHT, (INFO.bottom - LEGEND_TOP) // len(BUG_TYPES))
        self.sample_bugs = []
        for i, bug_type in enumerate(BUG_TYPES):
            y = LEGEND_TOP + i * row_height + row_height // 2
            self.sample_bugs.append(bug_type(LEGEND_PICTURE_X, y))

        self.selected_index = 0
        self.best_score = 0
        self.game = None
        self.seconds_until_next_bug = 0
        self.message = ""
        self.last_bug = None
        self.popup_points = 0
        self.popup_position = SCENE.center
        self.popup_seconds_left = 0
        self.start_game()

    def run(self):
        """Handle events, move the game on and redraw the window until it is closed."""
        is_running = True
        while is_running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    is_running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == LEFT_MOUSE_BUTTON:
                    self.handle_click(event.pos)
                elif event.type == pygame.KEYDOWN:
                    self.handle_key(event.key)
            seconds = self.clock.tick(FRAMES_PER_SECOND) / MILLISECONDS_PER_SECOND
            self.update(seconds)
            self.draw()
            pygame.display.flip()
        pygame.quit()

    def start_game(self):
        """Start a new game, with a new player who is holding the selected swatter."""
        # Aggregation: the new player is handed a swatter from the rack, then the game is handed the player
        player = Player(self.swatters[self.selected_index])
        self.game = Game(player, BUG_BOUNDS)
        for _ in range(NUMBER_OF_STARTING_BUGS):
            self.game.add_bug(make_random_bug(BUG_BOUNDS))
        self.seconds_until_next_bug = SECONDS_BETWEEN_BUGS
        self.message = "Click on a bug to swat it"
        self.last_bug = None
        self.popup_seconds_left = 0

    def select(self, index):
        """Hand the player the swatter at index in the rack of swatters."""
        self.selected_index = index
        self.game.player.pick_up(self.swatters[index])

    def update(self, seconds):
        """Move the game on by seconds, and let another bug in when it is time for one."""
        self.popup_seconds_left = max(0, self.popup_seconds_left - seconds)
        # Every swatter in the rack gets ready again, whether or not the player is holding it
        for swatter in self.swatters:
            swatter.update(seconds)
        if self.game.is_over():
            self.best_score = max(self.best_score, self.game.player.score)
        else:
            self.game.update(seconds)
            self.seconds_until_next_bug -= seconds
            if self.seconds_until_next_bug <= 0:
                self.seconds_until_next_bug = SECONDS_BETWEEN_BUGS
                if len(self.game.bugs) < MAX_NUMBER_OF_BUGS:
                    self.game.add_bug(make_random_bug(BUG_BOUNDS))

    def swat(self, position):
        """Swat at the (x, y) position, if the player's swatter is ready, and show what happened."""
        player = self.game.player
        if not self.game.is_over() and player.swatter.is_ready():
            score_before = player.score
            bugs_hit = self.game.swat(position)
            points = player.score - score_before
            if not bugs_hit:
                self.message = "Missed!"
            else:
                # Remember the first bug that was hit, even after the game has cleared it away
                self.last_bug = bugs_hit[0]
                if len(bugs_hit) == 1:
                    self.message = f"Hit {self.last_bug}"
                else:
                    self.message = f"Hit {len(bugs_hit)} bugs"
                if points != 0:
                    self.message += f": {points:+} points"
                    self.popup_points = points
                    self.popup_position = position
                    self.popup_seconds_left = POPUP_SECONDS

    def handle_click(self, position):
        """Respond to a mouse click at the (x, y) position."""
        if SCENE.collidepoint(position):
            self.swat(position)
        for i, button in enumerate(self.swatter_buttons):
            if button.is_clicked(position):
                self.select(i)
        if self.new_game_button.is_clicked(position):
            self.start_game()

    def handle_key(self, key):
        """Respond to a key being pressed."""
        if key == pygame.K_n:
            self.start_game()
        elif pygame.K_1 <= key < pygame.K_1 + NUMBER_OF_SWATTER_KEYS:
            self.select(key - pygame.K_1)

    def draw(self):
        """Draw the scene with the bugs in it, then the two panels."""
        self.screen.blit(self.background, (0, 0))
        self.screen.set_clip(SCENE)
        self.draw_scene()
        self.screen.set_clip(None)
        self.draw_side_panel()
        self.draw_info_panel()

    def draw_text(self, text, position, font, colour=TEXT_COLOUR):
        """Draw text with its top-left corner at position and return the rectangle it covers."""
        text_surface = font.render(text, True, colour)
        self.screen.blit(text_surface, position)
        return text_surface.get_rect(topleft=position)

    def draw_centred_text(self, text, centre, font, colour=TEXT_COLOUR):
        """Draw text with its middle at the (x, y) point centre."""
        text_surface = font.render(text, True, colour)
        self.screen.blit(text_surface, text_surface.get_rect(center=centre))

    def draw_scene(self):
        """Draw the bugs, the player's swatter where the mouse is, and the points for the last swat."""
        # Polymorphism: each bug draws itself, and this line is the same for every kind of bug
        for bug in self.game.bugs:
            bug.draw(self.screen)

        mouse_position = pygame.mouse.get_pos()
        is_swatter_shown = SCENE.collidepoint(mouse_position) and not self.game.is_over()
        if is_swatter_shown:
            # Polymorphism: the swatter draws itself too, whichever kind the player is holding
            self.game.player.swatter.draw(self.screen, mouse_position)
        # The swatter takes the place of the mouse pointer
        pygame.mouse.set_visible(not is_swatter_shown)

        if self.popup_seconds_left > 0:
            x, y = self.popup_position
            rise = POPUP_SPEED * (POPUP_SECONDS - self.popup_seconds_left)
            colour = ACCENT_COLOUR if self.popup_points > 0 else WARNING_COLOUR
            popup_y = max(SCENE.top + POPUP_MARGIN, y - POPUP_OFFSET - rise)
            self.draw_centred_text(f"{self.popup_points:+}", (x, popup_y), self.title_font, colour)

        if self.game.is_over():
            self.draw_game_over()

    def draw_game_over(self):
        """Draw a box in the middle of the scene that shows the final score."""
        box = pygame.Rect((0, 0), GAME_OVER_SIZE)
        box.center = SCENE.center
        pygame.draw.rect(self.screen, PANEL_COLOUR, box, border_radius=12)
        pygame.draw.rect(self.screen, ACCENT_COLOUR, box, 3, border_radius=12)
        player = self.game.player
        self.draw_centred_text("Time's up!", (box.centerx, box.top + 38), self.title_font)
        score_text = f"Score: {player.score}     Bugs squashed: {player.number_of_bugs_squashed}"
        self.draw_centred_text(score_text, (box.centerx, box.top + 82), self.heading_font, ACCENT_COLOUR)
        self.draw_centred_text("Press N for a new game", (box.centerx, box.top + 116), self.font, MUTED_COLOUR)

    def draw_class_hierarchy(self, instance, left, top):
        """Draw every class that instance inherits from, one per line, and return the y below the last line."""
        y = top
        instance_type = type(instance)
        # Show every class except object, which is always last
        for instance_class in instance_type.__mro__[:-1]:
            parent_class = instance_class.__bases__[0]
            if parent_class is object:
                line = f"class {instance_class.__name__}"
            else:
                line = f"class {instance_class.__name__}({parent_class.__name__})"
            colour = ACCENT_COLOUR if instance_class is instance_type else TEXT_COLOUR
            self.draw_text(line, (left, y), self.code_font, colour)
            y += LINE_HEIGHT
        return y

    def draw_side_panel(self):
        """Draw the panel with the swatter buttons, the player's swatter, the score and the key hints."""
        player = self.game.player
        swatter = player.swatter
        pygame.draw.rect(self.screen, PANEL_COLOUR, (0, 0, PANEL_WIDTH, HEIGHT))
        pygame.draw.line(self.screen, BORDER_COLOUR, (PANEL_WIDTH - 1, 0), (PANEL_WIDTH - 1, HEIGHT), 2)
        self.draw_text("Bug Swatter", (MARGIN, 18), self.title_font)
        self.draw_text("A demonstration of inheritance,", (MARGIN, 54), self.small_font, MUTED_COLOUR)
        self.draw_text("polymorphism and aggregation", (MARGIN, 71), self.small_font, MUTED_COLOUR)

        heading_top = SWATTER_BUTTONS_TOP - HEADING_OFFSET
        self.draw_text("1. Pick up a swatter", (MARGIN, heading_top), self.heading_font)
        for i, button in enumerate(self.swatter_buttons):
            # Aggregation: the player's swatter is one of the swatters in the rack, not a copy of it
            button.draw(self.screen, self.font, is_selected=swatter is self.swatters[i])

        y = self.swatter_buttons[-1].rect.bottom + SECTION_GAP
        self.draw_text(swatter.description, (MARGIN, y), self.font)
        y += DETAIL_LINE_HEIGHT
        details = f"Power {swatter.power}, ready again in {swatter.seconds_between_swings} s"
        self.draw_text(details, (MARGIN, y), self.small_font, MUTED_COLOUR)
        y += DETAIL_LINE_HEIGHT
        self.draw_text(f"player.swatter is swatters[{self.selected_index}]", (MARGIN, y), self.code_font, ACCENT_COLOUR)

        y += DETAIL_LINE_HEIGHT + SECTION_GAP
        self.draw_text("Class hierarchy", (MARGIN, y), self.heading_font)
        self.draw_class_hierarchy(swatter, MARGIN, y + HEADING_HEIGHT)

        self.draw_text("2. Swat the bugs", (MARGIN, SCORE_TOP - HEADING_OFFSET), self.heading_font)
        self.draw_text(f"Score: {player.score}", (MARGIN, SCORE_TOP), self.title_font, ACCENT_COLOUR)
        self.draw_text(f"Time left: {math.ceil(self.game.seconds_left)} s", (MARGIN, TIME_TOP), self.font)
        time_bar = pygame.Rect(MARGIN, TIME_BAR_TOP, BUTTON_WIDTH, PROGRESS_BAR_HEIGHT)
        pygame.draw.rect(self.screen, DISABLED_COLOUR, time_bar, border_radius=4)
        filled_width = round(time_bar.width * self.game.seconds_left / ROUND_SECONDS)
        if filled_width > 0:
            filled_bar = pygame.Rect(time_bar.left, time_bar.top, filled_width, PROGRESS_BAR_HEIGHT)
            pygame.draw.rect(self.screen, ACCENT_COLOUR, filled_bar, border_radius=4)
        self.new_game_button.draw(self.screen, self.small_font)
        self.draw_text(f"Best score: {self.best_score}", (MARGIN, BEST_SCORE_TOP), self.small_font, MUTED_COLOUR)

        key_hint = f"Keys: 1-{NUMBER_OF_SWATTER_KEYS} = pick up a swatter,"
        self.draw_text(key_hint, (MARGIN, KEY_HINTS_TOP), self.small_font, MUTED_COLOUR)
        self.draw_text("N = new game", (MARGIN, KEY_HINTS_TOP + 18), self.small_font, MUTED_COLOUR)

    def draw_info_panel(self):
        """Draw the panel that lists the kinds of bug and describes the last bug that was hit."""
        pygame.draw.rect(self.screen, INFO_COLOUR, INFO)
        pygame.draw.line(self.screen, BORDER_COLOUR, INFO.topleft, INFO.topright, 2)
        self.draw_bug_list()
        self.draw_last_swat()

    def draw_bug_list(self):
        """Draw a row for each kind of bug: a picture, its class, its points and how many are in the game."""
        self.draw_text("Bugs", (INFO.left + MARGIN, INFO_TOP), self.heading_font)
        class_names = [type(bug).__name__ for bug in self.game.bugs if not bug.is_squashed()]
        class_name_to_count = Counter(class_names)
        for sample_bug in self.sample_bugs:
            # Polymorphism: every kind of bug draws itself and knows its own points
            sample_bug.draw(self.screen)
            class_name = type(sample_bug).__name__
            text_top = sample_bug.y - LINE_HEIGHT / 2
            self.draw_text(class_name, (LEGEND_NAME_X, text_top + 1), self.code_font, MUTED_COLOUR)
            points_colour = TEXT_COLOUR if sample_bug.points > 0 else WARNING_COLOUR
            self.draw_text(sample_bug.describe_points(), (LEGEND_POINTS_X, text_top), self.font, points_colour)
            count = class_name_to_count[class_name]
            if count > 0:
                self.draw_text(f"{count} in play", (LEGEND_COUNT_X, text_top), self.font, MUTED_COLOUR)

    def draw_last_swat(self):
        """Draw what the last swat did, then the classes and methods of the bug that it hit."""
        left = LAST_SWAT_LEFT
        self.draw_text("Last swat", (left, INFO_TOP), self.heading_font)
        self.draw_text(self.message, (left, INFO_TOP + HEADING_HEIGHT + 2), self.font, ACCENT_COLOUR)
        if self.last_bug is not None:
            y = self.draw_class_hierarchy(self.last_bug, left, INFO_TOP + HEADING_HEIGHT + 30)
            y += SECTION_GAP
            for method_name in BUG_METHOD_NAMES:
                # The first class in the list is the one whose method Python runs
                class_name = list_classes_with_method(self.last_bug, method_name)[0]
                line = f"bug.{method_name}() runs {class_name}.{method_name}"
                self.draw_text(line, (left, y), self.code_font, MUTED_COLOUR)
                y += LINE_HEIGHT


def make_background():
    """Make a picture of a checked picnic rug, to be copied to the screen every frame."""
    background = pygame.Surface((WIDTH, HEIGHT))
    background.fill(RUG_COLOUR)
    stripe_spacing = 2 * CHECK_SIZE
    for x in range(SCENE.left, SCENE.right, stripe_spacing):
        pygame.draw.rect(background, STRIPE_COLOUR, (x, SCENE.top, CHECK_SIZE, SCENE.height))
    for y in range(SCENE.top, SCENE.bottom, stripe_spacing):
        pygame.draw.rect(background, STRIPE_COLOUR, (SCENE.left, y, SCENE.width, CHECK_SIZE))
    # The rug is darker where two stripes cross
    for x in range(SCENE.left, SCENE.right, stripe_spacing):
        for y in range(SCENE.top, SCENE.bottom, stripe_spacing):
            pygame.draw.rect(background, CHECK_COLOUR, (x, y, CHECK_SIZE, CHECK_SIZE))
    return background


def list_classes_with_method(instance, method_name):
    """List the names of the classes that have their own version of a method, starting from instance's own class.

    For a FruitFly and "move", that is ["Fly", "Bug"]. FruitFly is not in the
    list because it has no move() of its own. Python runs the first one it
    finds, so fruit_fly.move() runs Fly.move(), which FruitFly inherits.
    """
    class_names = []
    for instance_class in type(instance).__mro__:
        if method_name in vars(instance_class):
            class_names.append(instance_class.__name__)
    return class_names


if __name__ == "__main__":
    main()

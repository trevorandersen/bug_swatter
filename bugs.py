"""
Kinds of bug for the Bug Swatter game.

Inheritance:
    Bug                     the base class
    ├── Ant                 marches in a straight line
    ├── Fly                 buzzes about, changing direction all the time
    │   └── FruitFly        inherits from Fly, which inherits from Bug
    ├── Beetle              has a shell, so it takes two hits
    ├── Grasshopper         sits still, then leaps
    └── Ladybird            friendly: swatting one loses points

Polymorphism:
    Every kind of bug has update(), take_hit() and draw() methods, but each
    kind moves and looks different, and a Beetle takes a hit differently.
    A program never needs to know which kind of bug it has. It just calls

        for bug in bugs:
            bug.update(seconds, bounds)
            bug.draw(surface)

    and Python runs the right methods for whatever class each bug is.

Directions are in radians: 0 is right and math.pi / 2 is down the screen.
"""

import math
import random

import pygame

DARK_COLOUR = (30, 30, 30)
LEG_COLOUR = (40, 35, 35)
EYE_COLOUR = (205, 40, 40)
CRACK_COLOUR = (235, 235, 215)
NUMBER_OF_OVAL_POINTS = 16
SIDES = (-1, 1)  # left and right
# How far forwards each pair of legs is, as fractions of the bug's size
LEG_POSITIONS = (0.25, 0.0, -0.25)
LEG_SWING = 0.1  # how far a foot swings, as a fraction of the bug's size
STRIDE = 0.3  # a bigger stride makes the legs swing more slowly
SPLAT_SECONDS = 1.5  # how long a squashed bug stays where it was
# Each blob of a splat is (forwards, sideways, radius), as fractions of the bug's size
SPLAT_BLOBS = ((0, 0, 0.4), (0.45, 0.2, 0.18), (-0.4, 0.3, 0.2), (0.1, -0.5, 0.16), (-0.45, -0.25, 0.13))
# Each point of a crack and each spot is (forwards, sideways), as fractions of the bug's size
CRACK_POINTS = ((0.2, -0.2), (0.05, 0.05), (-0.1, -0.1), (-0.3, 0.15))
LADYBIRD_SPOTS = ((0.12, 0.2), (-0.12, 0.24), (-0.32, 0.13))
FLY_MAX_TURN = 1.2  # radians
HOP_MAX_TURN = 1.0  # radians
LADYBIRD_TURN_SPEED = 1.5  # radians per second
LADYBIRD_BEND_LENGTH = 30  # pixels
EDGES = ("left", "right", "top", "bottom")
MAX_START_TURN = 0.6  # radians


def calculate_oval(centre, angle, length, width):
    """Calculate the points around an oval that is length long in the direction angle (radians) and width wide."""
    along_x, along_y = math.cos(angle), math.sin(angle)
    outline = []
    for i in range(NUMBER_OF_OVAL_POINTS):
        angle_around = 2 * math.pi * i / NUMBER_OF_OVAL_POINTS
        along = math.cos(angle_around) * length / 2
        across = math.sin(angle_around) * width / 2
        outline.append((centre[0] + along_x * along - along_y * across, centre[1] + along_y * along + along_x * across))
    return outline


def make_random_bug(bounds):
    """Make a bug of a random kind on a random edge of bounds (a pygame.Rect), facing inwards."""
    bug_type = random.choice(BUG_TYPES)
    x = random.uniform(bounds.left, bounds.right)
    y = random.uniform(bounds.top, bounds.bottom)
    edge = random.choice(EDGES)
    if edge == "left":
        x = bounds.left
    elif edge == "right":
        x = bounds.right
    elif edge == "top":
        y = bounds.top
    else:
        y = bounds.bottom
    # Face the middle, give or take a bit
    direction = math.atan2(bounds.centery - y, bounds.centerx - x) + random.uniform(-MAX_START_TURN, MAX_START_TURN)
    # The exact class of the bug is only known when the program is running
    return bug_type(x, y, direction)


class Bug:
    """Base class for every kind of bug.

    Subclasses change the class variables, and override move() to move in
    their own way and draw_body() to look like themselves.
    """

    name = "Bug"
    points = 10  # scored for squashing this bug
    max_health = 1  # how much swatter power it takes to squash this bug
    speed = 60  # pixels per second
    size = 20  # pixels from head to tail
    colour = (95, 75, 55)
    # How far the feet are from the middle of the bug, as a fraction of its size
    leg_reach = 0.5
    splat_colour = (160, 180, 70)

    def __init__(self, x, y, direction=0.0):
        """Initialise a healthy Bug at (x, y) that faces direction (radians)."""
        self.x = x
        self.y = y
        self.direction = direction
        self.health = self.max_health
        self.distance_walked = 0  # pixels
        self.seconds_squashed = 0

    def __str__(self):
        """Return the bug's name and how healthy it is."""
        if self.is_squashed():
            return f"{self.name} (squashed)"
        return f"{self.name} ({self.health} of {self.max_health} health)"

    def is_squashed(self):
        """Determine if the bug has been squashed."""
        return self.health <= 0

    def is_gone(self):
        """Determine if the bug was squashed so long ago that it can be cleared away."""
        return self.seconds_squashed >= SPLAT_SECONDS

    def take_hit(self, power):
        """Lose power health, which squashes the bug if it has none left."""
        self.health = max(0, self.health - power)

    def update(self, seconds, bounds):
        """Move for seconds inside bounds (a pygame.Rect), or stay squashed for that long."""
        # This method is not overridden. It works for every subclass because
        # it calls move(), which is overridden.
        if self.is_squashed():
            self.seconds_squashed += seconds
        else:
            self.move(seconds, bounds)

    def move(self, seconds, bounds):
        """Walk forwards for seconds, turning back at the edges of bounds.

        The moving that every bug does is here. Subclasses override move()
        to choose when and where to go, and call super().move(seconds, bounds)
        to do the walking.
        """
        distance = self.speed * seconds
        self.x += math.cos(self.direction) * distance
        self.y += math.sin(self.direction) * distance
        self.distance_walked += distance
        if self.x < bounds.left or self.x > bounds.right:
            # Bounce off the left or right edge
            self.direction = math.pi - self.direction
            self.x = max(bounds.left, min(self.x, bounds.right))
        if self.y < bounds.top or self.y > bounds.bottom:
            # Bounce off the top or bottom edge
            self.direction = -self.direction
            self.y = max(bounds.top, min(self.y, bounds.bottom))

    def calculate_position(self, forwards, sideways=0.0):
        """Calculate the (x, y) position on the screen of a point on the bug.

        forwards is how far the point is towards the bug's head from its
        middle and sideways is how far it is to the bug's right. Both are
        fractions of the bug's size, so the position turns and scales with the bug.
        """
        forwards_x = math.cos(self.direction)
        forwards_y = math.sin(self.direction)
        distance_forwards = forwards * self.size
        distance_sideways = sideways * self.size
        return (self.x + forwards_x * distance_forwards - forwards_y * distance_sideways,
                self.y + forwards_y * distance_forwards + forwards_x * distance_sideways)

    def draw(self, surface):
        """Draw the bug, or a splat if it has been squashed."""
        # This method is not overridden either: it calls draw_body(), which is
        if self.is_squashed():
            self.draw_splat(surface)
        else:
            self.draw_legs(surface)
            self.draw_body(surface)

    def draw_body(self, surface):
        """Draw a plain oval body with a round head. Subclasses override this to look like themselves."""
        self.draw_oval(surface, self.colour, -0.1, 0.8, 0.45)
        self.draw_circle(surface, self.colour, 0.35, 0.15)

    def draw_legs(self, surface):
        """Draw three pairs of legs, which swing backwards and forwards as the bug walks."""
        swing = LEG_SWING * math.sin(self.distance_walked / (self.size * STRIDE))
        width = max(1, round(self.size / 15))
        for i, forwards in enumerate(LEG_POSITIONS):
            for side in SIDES:
                # Legs that are next to each other swing in opposite directions
                foot_swing = swing * side if i % 2 == 0 else -swing * side
                self.draw_line(surface, LEG_COLOUR, (forwards, 0), (forwards + foot_swing, side * self.leg_reach),
                               width)

    def draw_splat(self, surface):
        """Draw the blobs of goo that are left when the bug is squashed."""
        for forwards, sideways, radius in SPLAT_BLOBS:
            self.draw_circle(surface, self.splat_colour, forwards, radius, sideways)

    def draw_oval(self, surface, colour, forwards, length, width, sideways=0.0, turn=0.0):
        """Draw an oval on the bug, with its middle at the (forwards, sideways) point.

        length and width are fractions of the bug's size.
        turn is how far the oval is turned from the way the bug is facing, in radians.
        """
        centre = self.calculate_position(forwards, sideways)
        outline = calculate_oval(centre, self.direction + turn, length * self.size, width * self.size)
        pygame.draw.polygon(surface, colour, outline)

    def draw_circle(self, surface, colour, forwards, radius, sideways=0.0):
        """Draw a circle on the bug at the (forwards, sideways) point, where radius is a fraction of the bug's size."""
        pygame.draw.circle(surface, colour, self.calculate_position(forwards, sideways), max(1, radius * self.size))

    def draw_line(self, surface, colour, start, end, width=1):
        """Draw a line on the bug from start to end, which are (forwards, sideways) points."""
        start_point = self.calculate_position(start[0], start[1])
        end_point = self.calculate_position(end[0], end[1])
        pygame.draw.line(surface, colour, start_point, end_point, width)


class Ant(Bug):
    """A small bug that marches in a straight line. It has no move() of its own, so it inherits Bug's."""

    name = "Ant"
    points = 5
    speed = 75
    colour = (45, 30, 30)

    def draw_body(self, surface):
        """Draw a body in three parts, with two antennae."""
        self.draw_oval(surface, self.colour, -0.28, 0.44, 0.3)
        self.draw_circle(surface, self.colour, 0.05, 0.11)
        self.draw_circle(surface, self.colour, 0.33, 0.15)
        for side in SIDES:
            self.draw_line(surface, self.colour, (0.42, side * 0.06), (0.62, side * 0.22))


class Fly(Bug):
    """A fast bug that keeps changing direction."""

    name = "Fly"
    speed = 170
    size = 16
    colour = (55, 60, 70)
    leg_reach = 0.4
    wing_colour = (165, 190, 215)
    turns_per_second = 4  # how often it changes direction, on average

    def move(self, seconds, bounds):
        """Buzz forwards, changing direction at random every so often."""
        if random.random() < self.turns_per_second * seconds:
            self.direction += random.uniform(-FLY_MAX_TURN, FLY_MAX_TURN)
        super().move(seconds, bounds)

    def draw_body(self, surface):
        """Draw a body with two wings folded back over it."""
        self.draw_oval(surface, self.colour, -0.08, 0.8, 0.4)
        for side in SIDES:
            self.draw_oval(surface, self.wing_colour, -0.2, 0.75, 0.3, sideways=side * 0.28, turn=-side * 0.5)
        self.draw_circle(surface, self.colour, 0.38, 0.17)


class FruitFly(Fly):
    """A Fly that is smaller, faster and worth more points.

    Only the differences are written here; everything else is inherited from Fly.
    """

    name = "Fruit fly"
    points = 25
    speed = 215
    size = 11
    colour = (180, 125, 50)
    turns_per_second = 6

    def draw_body(self, surface):
        """Draw the body the way a Fly does, then add two red eyes."""
        super().draw_body(surface)
        for side in SIDES:
            self.draw_circle(surface, EYE_COLOUR, 0.45, 0.09, sideways=side * 0.12)


class Beetle(Bug):
    """A big, slow bug with a hard shell, which takes two hits to squash."""

    name = "Beetle"
    points = 20
    max_health = 2
    speed = 35
    size = 30
    colour = (40, 100, 85)
    seam_colour = (25, 60, 50)
    shine_colour = (120, 180, 160)

    def is_cracked(self):
        """Determine if the shell has been hit."""
        return self.health < self.max_health

    def take_hit(self, power):
        """Take a hit like any bug, then turn around if the shell held."""
        super().take_hit(power)
        if not self.is_squashed():
            self.direction += math.pi

    def draw_body(self, surface):
        """Draw a shiny shell, with a crack across it once it has been hit."""
        self.draw_circle(surface, DARK_COLOUR, 0.33, 0.17)
        self.draw_oval(surface, self.colour, -0.1, 0.8, 0.62)
        self.draw_line(surface, self.seam_colour, (0.28, 0), (-0.48, 0))
        self.draw_oval(surface, self.shine_colour, 0.05, 0.3, 0.07, sideways=-0.17)
        if self.is_cracked():
            crack = [self.calculate_position(forwards, sideways) for forwards, sideways in CRACK_POINTS]
            pygame.draw.lines(surface, CRACK_COLOUR, False, crack, 2)


class Grasshopper(Bug):
    """A long bug that sits still, then leaps a long way."""

    name = "Grasshopper"
    points = 15
    speed = 420  # while it is in the air
    size = 32
    colour = (105, 165, 60)
    leg_reach = 0.35
    back_leg_colour = (70, 120, 40)
    rest_seconds = 1.2  # how long it sits still between hops
    hop_seconds = 0.3  # how long each hop lasts

    def __init__(self, x, y, direction=0.0):
        """Initialise a Grasshopper that is resting before its first hop."""
        super().__init__(x, y, direction)
        self.seconds_until_hop = self.rest_seconds
        self.hop_seconds_left = 0

    def move(self, seconds, bounds):
        """Sit still until it is time to hop, then turn and leap."""
        if self.hop_seconds_left > 0:
            self.hop_seconds_left -= seconds
            super().move(seconds, bounds)
        else:
            self.seconds_until_hop -= seconds
            if self.seconds_until_hop <= 0:
                self.direction += random.uniform(-HOP_MAX_TURN, HOP_MAX_TURN)
                self.seconds_until_hop = self.rest_seconds
                self.hop_seconds_left = self.hop_seconds

    def draw_body(self, surface):
        """Draw a long thin body with big bent back legs and long antennae."""
        for side in SIDES:
            hip = (-0.1, side * 0.1)
            knee = (-0.42, side * 0.42)
            foot = (-0.12, side * 0.55)
            self.draw_line(surface, self.back_leg_colour, hip, knee, 3)
            self.draw_line(surface, self.back_leg_colour, knee, foot, 2)
        self.draw_oval(surface, self.colour, -0.05, 0.9, 0.24)
        self.draw_circle(surface, self.colour, 0.38, 0.13)
        for side in SIDES:
            self.draw_circle(surface, DARK_COLOUR, 0.42, 0.04, sideways=side * 0.09)
            self.draw_line(surface, self.back_leg_colour, (0.48, side * 0.05), (0.8, side * 0.28))


class Ladybird(Bug):
    """A friendly bug that wanders about slowly. Swatting one loses points."""

    name = "Ladybird"
    points = -20
    speed = 45
    size = 22
    colour = (215, 40, 35)
    splat_colour = (200, 90, 70)

    def move(self, seconds, bounds):
        """Wander forwards in gentle S-bends."""
        # Turn one way for a while, then the other way, depending on how far it has walked
        bend = math.cos(self.distance_walked / LADYBIRD_BEND_LENGTH)
        self.direction += LADYBIRD_TURN_SPEED * bend * seconds
        super().move(seconds, bounds)

    def draw_body(self, surface):
        """Draw a round red shell with black spots."""
        self.draw_circle(surface, DARK_COLOUR, 0.36, 0.16)
        self.draw_oval(surface, self.colour, -0.08, 0.84, 0.76)
        self.draw_line(surface, DARK_COLOUR, (0.32, 0), (-0.5, 0))
        for forwards, sideways in LADYBIRD_SPOTS:
            for side in SIDES:
                self.draw_circle(surface, DARK_COLOUR, forwards, 0.07, sideways=side * sideways)


# The kinds of bug that can turn up (this must come after the classes it lists)
BUG_TYPES = [Ant, Fly, FruitFly, Beetle, Grasshopper, Ladybird]

"""
Swatters for the Bug Swatter game.

Inheritance:
    Swatter                 the base class
    ├── FlySwatter          a good all-rounder
    ├── Newspaper           big and strong, but slow
    ├── Chopsticks          tiny and quick, for triple points
    └── BugSpray            hits a round cloud instead of a rectangle

Polymorphism:
    Every swatter has covers(), calculate_points() and draw() methods.
    A program never needs to know which kind of swatter it has. It just calls

        bugs_hit = swatter.swing(position, bugs)
        swatter.draw(surface, position)

    and Python runs the right methods for whatever class the swatter is.
    The bugs are polymorphic too: swing() calls bug.take_hit(power) on each
    bug it hits without knowing what kind of bug it is.
"""

import math

import pygame

NOT_READY_COLOUR = (175, 175, 175)
OUTLINE_WIDTH = 3
HANDLE_LENGTH = 130  # pixels
HANDLE_LEAN = 45  # how far the end of the handle is to the right of the head
HANDLE_WIDTH = 6
MESH_SPACING = 12
NEWSPAPER_MARGIN = 14
NUMBER_OF_PRINT_LINES = 3
CHOPSTICKS_BONUS = 3
CHOPSTICK_WIDTH = 4
# Each chopstick is ((x, y) of its tip, (x, y) of its other end), measured from where the swatter is
CHOPSTICK_LINES = (((-3, 2), (70, 150)), ((3, -2), (100, 135)))
SPRAY_CAN_SIZE = (26, 60)
SPRAY_NOZZLE_SIZE = (10, 8)


class Swatter:
    """Base class for every kind of swatter.

    Subclasses change the class variables, and can override covers() to hit
    a different shape, calculate_points() to score differently, and
    draw_head() and draw_handle() to look like themselves.
    """

    name = "Swatter"
    description = "Squashes bugs"
    width = 50  # pixels, the size of the head that hits the bugs
    height = 50
    power = 1  # how much health each hit takes off a bug
    seconds_between_swings = 0.5
    colour = (90, 90, 90)

    def __init__(self):
        """Initialise a Swatter that is ready to swing."""
        self.seconds_until_ready = 0

    def __str__(self):
        """Return the swatter's name, its power and how often it can swing."""
        return f"{self.name}: power {self.power}, ready again in {self.seconds_between_swings} s"

    def is_ready(self):
        """Determine if the swatter can be swung now."""
        return self.seconds_until_ready <= 0

    def update(self, seconds):
        """Get seconds closer to being ready to swing again."""
        self.seconds_until_ready = max(0, self.seconds_until_ready - seconds)

    def calculate_head(self, position):
        """Calculate the rectangle that the head covers when its middle is at the (x, y) position."""
        head = pygame.Rect(0, 0, self.width, self.height)
        head.center = position
        return head

    def covers(self, position, bug):
        """Determine if a swing at the (x, y) position would hit bug."""
        return self.calculate_head(position).collidepoint(bug.x, bug.y)

    def calculate_points(self, bug):
        """Calculate the points scored for squashing bug with this swatter."""
        return bug.points

    def swing(self, position, bugs):
        """Swing at the (x, y) position and return a list of the bugs that were hit.

        A swatter that is not ready hits nothing.
        """
        bugs_hit = []
        if self.is_ready():
            self.seconds_until_ready = self.seconds_between_swings
            for bug in bugs:
                # Polymorphism: covers() depends on the kind of swatter, take_hit() on the kind of bug
                if not bug.is_squashed() and self.covers(position, bug):
                    bug.take_hit(self.power)
                    bugs_hit.append(bug)
        return bugs_hit

    def draw(self, surface, position):
        """Draw the swatter with the middle of its head at the (x, y) position, grey if it is not ready."""
        # This method is not overridden. It works for every subclass because
        # it calls draw_handle() and draw_head(), which are overridden.
        colour = self.colour if self.is_ready() else NOT_READY_COLOUR
        self.draw_handle(surface, position, colour)
        self.draw_head(surface, position, colour)

    def draw_handle(self, surface, position, colour):
        """Draw a straight handle from the bottom of the head."""
        x, y = position
        top = y + self.height / 2
        pygame.draw.line(surface, colour, (x, top), (x + HANDLE_LEAN, top + HANDLE_LENGTH), HANDLE_WIDTH)

    def draw_head(self, surface, position, colour):
        """Draw the outline of the head, so the bugs under it can still be seen."""
        pygame.draw.rect(surface, colour, self.calculate_head(position), OUTLINE_WIDTH, border_radius=6)


class FlySwatter(Swatter):
    """A square of plastic mesh on a handle."""

    name = "Fly swatter"
    description = "A good all-rounder"
    width = 60
    height = 60
    seconds_between_swings = 0.4
    colour = (40, 110, 200)

    def draw_head(self, surface, position, colour):
        """Draw the outline of the head like any swatter, then fill it with mesh."""
        super().draw_head(surface, position, colour)
        head = self.calculate_head(position)
        for x in range(head.left + MESH_SPACING, head.right, MESH_SPACING):
            pygame.draw.line(surface, colour, (x, head.top), (x, head.bottom))
        for y in range(head.top + MESH_SPACING, head.bottom, MESH_SPACING):
            pygame.draw.line(surface, colour, (head.left, y), (head.right, y))


class Newspaper(Swatter):
    """A rolled-up newspaper, which is wide and heavy enough to squash a beetle in one hit."""

    name = "Newspaper"
    description = "Big and strong, but slow"
    width = 130
    height = 46
    power = 2
    seconds_between_swings = 1.0
    colour = (95, 95, 105)

    def draw_handle(self, surface, position, colour):
        """Draw nothing, because a rolled-up newspaper has no handle."""

    def draw_head(self, surface, position, colour):
        """Draw the outline of the head like any swatter, then add lines of print."""
        super().draw_head(surface, position, colour)
        head = self.calculate_head(position)
        for i in range(1, NUMBER_OF_PRINT_LINES + 1):
            y = head.top + head.height * i / (NUMBER_OF_PRINT_LINES + 1)
            pygame.draw.line(surface, colour, (head.left + NEWSPAPER_MARGIN, y), (head.right - NEWSPAPER_MARGIN, y))


class Chopsticks(Swatter):
    """A pair of chopsticks, which are hard to catch a bug with but score triple points."""

    name = "Chopsticks"
    description = "Tiny, but triple points"
    width = 22
    height = 22
    seconds_between_swings = 0.15
    colour = (150, 95, 45)

    def calculate_points(self, bug):
        """Calculate three times the points that any other swatter would score."""
        return CHOPSTICKS_BONUS * super().calculate_points(bug)

    def draw_handle(self, surface, position, colour):
        """Draw two sticks that meet where the swatter is."""
        x, y = position
        for (tip_x, tip_y), (end_x, end_y) in CHOPSTICK_LINES:
            pygame.draw.line(surface, colour, (x + tip_x, y + tip_y), (x + end_x, y + end_y), CHOPSTICK_WIDTH)


class BugSpray(Swatter):
    """A can of spray, which hits every bug in a big round cloud but takes a long time to be ready again."""

    name = "Bug spray"
    description = "A wide cloud, slow to refill"
    width = 170  # the cloud is a circle, so this is how far across it is
    height = 170
    seconds_between_swings = 2.0
    colour = (50, 150, 90)

    def calculate_radius(self):
        """Calculate the radius of the cloud of spray."""
        return self.width / 2

    def covers(self, position, bug):
        """Determine if bug is inside the round cloud of a spray at the (x, y) position."""
        # This replaces Swatter.covers() completely, so it does not call super()
        return math.dist(position, (bug.x, bug.y)) <= self.calculate_radius()

    def draw_handle(self, surface, position, colour):
        """Draw a spray can beside the cloud."""
        can = pygame.Rect((0, 0), SPRAY_CAN_SIZE)
        can.topleft = (position[0] + self.calculate_radius() * 0.75, position[1] + self.calculate_radius() * 0.75)
        nozzle = pygame.Rect((0, 0), SPRAY_NOZZLE_SIZE)
        nozzle.midbottom = can.midtop
        pygame.draw.rect(surface, colour, can, border_radius=4)
        pygame.draw.rect(surface, colour, nozzle)

    def draw_head(self, surface, position, colour):
        """Draw the outline of the round cloud."""
        pygame.draw.circle(surface, colour, position, self.calculate_radius(), OUTLINE_WIDTH)


# The kinds of swatter a player can choose from (this must come after the classes it lists)
SWATTER_TYPES = [FlySwatter, Newspaper, Chopsticks, BugSpray]

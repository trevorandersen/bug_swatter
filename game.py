"""
The player and the game for Bug Swatter.

Aggregation:
    A Game has a Player and a list of Bugs, and a Player has a Swatter.
    None of them makes the things it has. They are made somewhere else and
    handed over:

        swatter = FlySwatter()
        player = Player(swatter)        the player is handed a swatter
        game = Game(player, bounds)     the game is handed a player
        game.add_bug(Fly(300, 200))     ...and its bugs, one at a time

    So an object can be used in more than one place, and it can outlive
    whatever was using it. When the player picks up a different swatter, the
    old one still exists and can be picked up again. When a new game starts,
    its new Player can use the very same swatters.

    (Composition is the other kind of "has a". There, an object makes its own
    parts and nothing else uses them, like a plant that grows its own stem.)

Polymorphism:
    Player and Game work with any kind of Swatter and any kind of Bug,
    because they only call methods that every Swatter or every Bug has.
"""

ROUND_SECONDS = 60


class Player:
    """Someone who swats bugs with whichever swatter they are holding."""

    def __init__(self, swatter):
        """Initialise a Player with no points who is holding swatter."""
        # Aggregation: the swatter was made somewhere else, and the player just uses it
        self.swatter = swatter
        self.score = 0
        self.number_of_bugs_squashed = 0

    def __str__(self):
        """Return what the player is holding and how well they are doing."""
        return f"Player with {self.swatter.name}: score {self.score}, bugs squashed {self.number_of_bugs_squashed}"

    def pick_up(self, swatter):
        """Swap the swatter the player is holding for a different one."""
        # The old swatter is not destroyed. Whoever made it still has it.
        self.swatter = swatter

    def swat(self, position, bugs):
        """Swing the swatter at the (x, y) position and return a list of the bugs it hit.

        The player scores points for each bug that the swing squashes.
        """
        # Polymorphism: this works the same whichever kind of swatter the player is holding
        bugs_hit = self.swatter.swing(position, bugs)
        for bug in bugs_hit:
            if bug.is_squashed():
                self.number_of_bugs_squashed += 1
                self.score += self.swatter.calculate_points(bug)
        return bugs_hit


class Game:
    """One round of Bug Swatter: a player swats the bugs inside bounds until the time runs out."""

    def __init__(self, player, bounds, seconds=ROUND_SECONDS):
        """Initialise a Game for player that lasts for seconds and has no bugs yet.

        bounds is the pygame.Rect that the bugs stay inside.
        """
        # Aggregation: the player was made somewhere else, and so is every bug that is added
        self.player = player
        self.bounds = bounds
        self.seconds_left = seconds
        self.bugs = []

    def __str__(self):
        """Return how many bugs there are and how long is left."""
        return f"Game: bugs {len(self.bugs)}, seconds left {self.seconds_left:.0f}"

    def add_bug(self, bug):
        """Add a bug that was made somewhere else to the game."""
        self.bugs.append(bug)

    def is_over(self):
        """Determine if the time has run out."""
        return self.seconds_left <= 0

    def update(self, seconds):
        """Move the game on by seconds, unless it is over."""
        if not self.is_over():
            self.seconds_left = max(0, self.seconds_left - seconds)
            self.player.swatter.update(seconds)
            # Polymorphism: each bug moves in its own way
            for bug in self.bugs:
                bug.update(seconds, self.bounds)
            # Clear away the bugs that were squashed a while ago
            self.bugs = [bug for bug in self.bugs if not bug.is_gone()]

    def swat(self, position):
        """Let the player swat at the (x, y) position, unless the game is over, and return the bugs that were hit."""
        if self.is_over():
            return []
        return self.player.swat(position, self.bugs)

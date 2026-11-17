"""
Tests for Bug Swatter.

Run the tests with:
    python -m unittest

Many of the tests loop over every kind of bug or every kind of swatter. That
only works because of polymorphism: a test does not care which class it has,
it just calls update(), take_hit(), covers(), draw() and so on.
"""

import math
import unittest

import pygame

from bugs import BUG_TYPES, SPLAT_SECONDS, Ant, Beetle, Bug, Fly, FruitFly, Grasshopper, Ladybird, make_random_bug
from game import ROUND_SECONDS, Game, Player
from main import BUG_BOUNDS, FRAMES_PER_SECOND, HEIGHT, SCENE, WIDTH, list_classes_with_method
from swatters import SWATTER_TYPES, BugSpray, Chopsticks, FlySwatter, Newspaper, Swatter

BOUNDS = pygame.Rect(100, 100, 400, 300)
MIDDLE = BOUNDS.center
FRAME_SECONDS = 1 / FRAMES_PER_SECOND
NUMBER_OF_DIRECTIONS = 8


def make_bugs(position=MIDDLE):
    """Make one bug of every kind at the (x, y) position."""
    x, y = position
    return [bug_type(x, y) for bug_type in BUG_TYPES]


def make_swatters():
    """Make one swatter of every kind."""
    return [swatter_type() for swatter_type in SWATTER_TYPES]


def update_for(bug, seconds):
    """Update bug one frame at a time for seconds, the way the game does."""
    number_of_frames = round(seconds / FRAME_SECONDS)
    for _ in range(number_of_frames):
        bug.update(FRAME_SECONDS, BOUNDS)


def draw_picture(bug):
    """Draw bug on a see-through surface the size of the window and return the surface."""
    surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    bug.draw(surface)
    return surface


class BugTests(unittest.TestCase):
    """Tests of how bugs move and take hits."""

    def test_new_bug_is_healthy(self):
        """Test that a new bug has all of its health and has not walked anywhere."""
        for bug in make_bugs():
            with self.subTest(bug.name):
                self.assertEqual(bug.health, bug.max_health)
                self.assertFalse(bug.is_squashed())
                self.assertFalse(bug.is_gone())
                self.assertEqual(bug.distance_walked, 0)

    def test_every_bug_moves(self):
        """Test that every kind of bug goes somewhere when it is updated."""
        for bug in make_bugs():
            with self.subTest(bug.name):
                update_for(bug, 5)
                self.assertGreater(bug.distance_walked, 0)
                self.assertNotEqual((bug.x, bug.y), MIDDLE)

    def test_bugs_stay_in_bounds(self):
        """Test that no bug ever leaves the bounds, whichever way it starts off."""
        for bug in make_bugs():
            for i in range(NUMBER_OF_DIRECTIONS):
                with self.subTest(bug.name, i=i):
                    bug.direction = 2 * math.pi * i / NUMBER_OF_DIRECTIONS
                    number_of_frames = 600
                    for _ in range(number_of_frames):
                        bug.update(FRAME_SECONDS, BOUNDS)
                        self.assertTrue(BOUNDS.left <= bug.x <= BOUNDS.right, f"x is {bug.x}")
                        self.assertTrue(BOUNDS.top <= bug.y <= BOUNDS.bottom, f"y is {bug.y}")

    def test_ant_walks_straight(self):
        """Test that an ant walks at its speed in the direction it is facing."""
        ant = Ant(200, 200, direction=0)
        ant.update(1, BOUNDS)
        self.assertAlmostEqual(ant.x, 200 + Ant.speed)
        self.assertAlmostEqual(ant.y, 200)
        ant = Ant(200, 200, direction=math.pi / 2)
        ant.update(1, BOUNDS)
        self.assertAlmostEqual(ant.x, 200)
        self.assertAlmostEqual(ant.y, 200 + Ant.speed)

    def test_only_ant_and_beetle_walk_straight(self):
        """Test that an ant and a beetle keep to a straight line, but the other kinds of bug turn as they go."""
        for bug in (Ant(MIDDLE[0], MIDDLE[1]), Beetle(MIDDLE[0], MIDDLE[1])):
            with self.subTest(bug.name):
                update_for(bug, 10)
                self.assertAlmostEqual(bug.y, MIDDLE[1])
        for bug_type in (Fly, FruitFly, Grasshopper, Ladybird):
            with self.subTest(bug_type.__name__):
                bug = bug_type(MIDDLE[0], MIDDLE[1])
                update_for(bug, 10)
                self.assertNotAlmostEqual(bug.y, MIDDLE[1])

    def test_bug_bounces_off_edge(self):
        """Test that a bug that reaches an edge turns back."""
        ant = Ant(BOUNDS.right - 1, 200, direction=0)
        ant.update(1, BOUNDS)
        ant.update(1, BOUNDS)
        self.assertAlmostEqual(ant.x, BOUNDS.right - Ant.speed)
        ant = Ant(200, BOUNDS.bottom - 1, direction=math.pi / 2)
        ant.update(1, BOUNDS)
        ant.update(1, BOUNDS)
        self.assertAlmostEqual(ant.y, BOUNDS.bottom - Ant.speed)

    def test_fruit_fly_is_a_fly(self):
        """Test that a fruit fly is a small, fast fly that inherits the way a fly moves."""
        fruit_fly = FruitFly(200, 200)
        self.assertIsInstance(fruit_fly, Fly)
        self.assertIsInstance(fruit_fly, Bug)
        self.assertLess(FruitFly.size, Fly.size)
        self.assertGreater(FruitFly.speed, Fly.speed)
        self.assertGreater(FruitFly.points, Fly.points)
        self.assertEqual(list_classes_with_method(fruit_fly, "move"), ["Fly", "Bug"])

    def test_grasshopper_rests_then_hops(self):
        """Test that a grasshopper sits still for its rest, then makes one hop."""
        grasshopper = Grasshopper(MIDDLE[0], MIDDLE[1])
        update_for(grasshopper, Grasshopper.rest_seconds / 2)
        self.assertEqual((grasshopper.x, grasshopper.y), MIDDLE)
        update_for(grasshopper, Grasshopper.rest_seconds / 2 + Grasshopper.hop_seconds + 0.2)
        hop_length = Grasshopper.speed * Grasshopper.hop_seconds
        self.assertAlmostEqual(grasshopper.distance_walked, hop_length, delta=Grasshopper.speed * FRAME_SECONDS * 2)

    def test_hit_squashes_bug(self):
        """Test that one hit squashes every kind of bug that has only 1 health."""
        for bug in make_bugs():
            with self.subTest(bug.name):
                bug.take_hit(1)
                self.assertEqual(bug.is_squashed(), bug.max_health == 1)

    def test_squashed_bug_stays_still_then_goes(self):
        """Test that a squashed bug does not move, and is gone after SPLAT_SECONDS."""
        for bug in make_bugs():
            with self.subTest(bug.name):
                bug.take_hit(bug.max_health)
                update_for(bug, SPLAT_SECONDS / 2)
                self.assertEqual((bug.x, bug.y), MIDDLE)
                self.assertFalse(bug.is_gone())
                update_for(bug, SPLAT_SECONDS / 2 + FRAME_SECONDS)
                self.assertTrue(bug.is_gone())

    def test_beetle_takes_two_hits(self):
        """Test that the first hit only cracks a beetle's shell and turns it around."""
        beetle = Beetle(200, 200, direction=0)
        self.assertFalse(beetle.is_cracked())
        beetle.take_hit(1)
        self.assertTrue(beetle.is_cracked())
        self.assertFalse(beetle.is_squashed())
        self.assertAlmostEqual(beetle.direction, math.pi)
        beetle.take_hit(1)
        self.assertTrue(beetle.is_squashed())
        self.assertAlmostEqual(beetle.direction, math.pi)

    def test_str(self):
        """Test that a bug's string shows its name and its health."""
        beetle = Beetle(200, 200)
        self.assertEqual(str(beetle), "Beetle (2 of 2 health)")
        beetle.take_hit(1)
        self.assertEqual(str(beetle), "Beetle (1 of 2 health)")
        beetle.take_hit(1)
        self.assertEqual(str(beetle), "Beetle (squashed)")
        self.assertEqual(str(FruitFly(200, 200)), "Fruit fly (1 of 1 health)")

    def test_make_random_bug(self):
        """Test that random bugs are of every kind and each starts on an edge of the bounds."""
        bugs = [make_random_bug(BOUNDS) for _ in range(300)]
        self.assertEqual({type(bug) for bug in bugs}, set(BUG_TYPES))
        for bug in bugs:
            is_on_side = bug.x in (BOUNDS.left, BOUNDS.right) and BOUNDS.top <= bug.y <= BOUNDS.bottom
            is_on_end = bug.y in (BOUNDS.top, BOUNDS.bottom) and BOUNDS.left <= bug.x <= BOUNDS.right
            self.assertTrue(is_on_side or is_on_end, f"({bug.x}, {bug.y}) is not on an edge")


class SwatterTests(unittest.TestCase):
    """Tests of how swatters hit bugs."""

    def test_new_swatter_is_ready(self):
        """Test that every kind of swatter can be swung straight away."""
        for swatter in make_swatters():
            with self.subTest(swatter.name):
                self.assertTrue(swatter.is_ready())

    def test_covers_bug_under_head(self):
        """Test that every swatter covers a bug under it or just inside its edge, but not one below it or far away."""
        bug = Ant(MIDDLE[0], MIDDLE[1])
        far_away = (MIDDLE[0] + 150, MIDDLE[1])
        for swatter in make_swatters():
            with self.subTest(swatter.name):
                self.assertTrue(swatter.covers(MIDDLE, bug))
                self.assertFalse(swatter.covers(far_away, bug))
                # The head is centred on the position, so its edges are half its size away
                left_bug = Ant(MIDDLE[0] - swatter.width / 2 + 1, MIDDLE[1])
                below_bug = Ant(MIDDLE[0], MIDDLE[1] + swatter.height / 2 + 1)
                self.assertTrue(swatter.covers(MIDDLE, left_bug))
                self.assertFalse(swatter.covers(MIDDLE, below_bug))

    def test_fly_swatter_is_square_but_spray_is_round(self):
        """Test that a fly swatter covers a bug in its corner, but bug spray does not."""
        fly_swatter = FlySwatter()
        corner_bug = Ant(MIDDLE[0] + FlySwatter.width * 0.45, MIDDLE[1] + FlySwatter.height * 0.45)
        self.assertTrue(fly_swatter.covers(MIDDLE, corner_bug))

        bug_spray = BugSpray()
        corner_bug = Ant(MIDDLE[0] + BugSpray.width * 0.45, MIDDLE[1] + BugSpray.height * 0.45)
        side_bug = Ant(MIDDLE[0] + BugSpray.width * 0.45, MIDDLE[1])
        self.assertFalse(bug_spray.covers(MIDDLE, corner_bug))
        self.assertTrue(bug_spray.covers(MIDDLE, side_bug))

    def test_swing_hits_every_bug_under_head(self):
        """Test that one swing hits all of the bugs under the swatter and none of the others."""
        for swatter in make_swatters():
            with self.subTest(swatter.name):
                near_bugs = make_bugs()
                far_bug = Fly(BOUNDS.left, BOUNDS.top)
                bugs_hit = swatter.swing(MIDDLE, near_bugs + [far_bug])
                self.assertEqual(bugs_hit, near_bugs)
                self.assertEqual(far_bug.health, far_bug.max_health)
                for bug in near_bugs:
                    self.assertLess(bug.health, bug.max_health)

    def test_swatter_is_not_ready_straight_after_swing(self):
        """Test that a swatter hits nothing until seconds_between_swings have passed."""
        for swatter in make_swatters():
            with self.subTest(swatter.name):
                swatter.swing(MIDDLE, [])
                self.assertFalse(swatter.is_ready())
                bug = Ant(MIDDLE[0], MIDDLE[1])
                self.assertEqual(swatter.swing(MIDDLE, [bug]), [])
                self.assertFalse(bug.is_squashed())
                swatter.update(swatter.seconds_between_swings / 2)
                self.assertFalse(swatter.is_ready())
                swatter.update(swatter.seconds_between_swings / 2)
                self.assertTrue(swatter.is_ready())
                self.assertEqual(swatter.swing(MIDDLE, [bug]), [bug])

    def test_squashed_bug_is_not_hit_again(self):
        """Test that a swing does not hit a bug that is already squashed."""
        swatter = FlySwatter()
        bug = Ant(MIDDLE[0], MIDDLE[1])
        bug.take_hit(1)
        self.assertEqual(swatter.swing(MIDDLE, [bug]), [])

    def test_newspaper_squashes_beetle_in_one_hit(self):
        """Test that a newspaper has enough power for a beetle, but a fly swatter needs two swings."""
        beetle = Beetle(MIDDLE[0], MIDDLE[1])
        Newspaper().swing(MIDDLE, [beetle])
        self.assertTrue(beetle.is_squashed())
        beetle = Beetle(MIDDLE[0], MIDDLE[1])
        FlySwatter().swing(MIDDLE, [beetle])
        self.assertFalse(beetle.is_squashed())

    def test_chopsticks_score_triple_points(self):
        """Test that chopsticks score three times what the other swatters do, for good and for bad."""
        for bug in make_bugs():
            with self.subTest(bug.name):
                self.assertEqual(FlySwatter().calculate_points(bug), bug.points)
                self.assertEqual(Chopsticks().calculate_points(bug), 3 * bug.points)

    def test_str(self):
        """Test that a swatter's string shows its name, its power and how often it can swing."""
        self.assertEqual(str(Newspaper()), "Newspaper: power 2, ready again in 1.0 s")


class AggregationTests(unittest.TestCase):
    """Tests that players and games use the objects they are handed, instead of making their own."""

    def test_player_holds_swatter_it_is_handed(self):
        """Test that a player's swatter is the very same object that it was given."""
        fly_swatter = FlySwatter()
        player = Player(fly_swatter)
        self.assertIs(player.swatter, fly_swatter)

    def test_swatter_outlives_being_put_down(self):
        """Test that a swatter the player swaps for another one still exists and still works."""
        fly_swatter = FlySwatter()
        newspaper = Newspaper()
        player = Player(fly_swatter)
        player.pick_up(newspaper)
        self.assertIs(player.swatter, newspaper)
        bug = Ant(MIDDLE[0], MIDDLE[1])
        self.assertEqual(fly_swatter.swing(MIDDLE, [bug]), [bug])

    def test_players_can_share_swatter(self):
        """Test that two players can hold the same swatter, so a swing by one makes the other wait."""
        swatter = BugSpray()
        first_player = Player(swatter)
        second_player = Player(swatter)
        first_player.swat(MIDDLE, [])
        self.assertFalse(second_player.swatter.is_ready())

    def test_swatter_outlives_game(self):
        """Test that a new player in a new game can use the swatter from the game before."""
        swatter = FlySwatter()
        first_game = Game(Player(swatter), BOUNDS)
        first_game.update(ROUND_SECONDS)
        self.assertTrue(first_game.is_over())
        second_game = Game(Player(swatter), BOUNDS)
        self.assertIs(second_game.player.swatter, first_game.player.swatter)

    def test_game_holds_bug_it_is_handed(self):
        """Test that a game's bug is the very same object that was added to it."""
        game = Game(Player(FlySwatter()), BOUNDS)
        fly = Fly(MIDDLE[0], MIDDLE[1])
        game.add_bug(fly)
        self.assertIs(game.bugs[0], fly)

    def test_bug_outlives_being_cleared_away(self):
        """Test that a squashed bug the game has cleared away still exists for anything else that has it."""
        game = Game(Player(FlySwatter()), BOUNDS)
        ant = Ant(MIDDLE[0], MIDDLE[1])
        game.add_bug(ant)
        game.swat(MIDDLE)
        game.update(SPLAT_SECONDS)
        game.update(FRAME_SECONDS)
        self.assertEqual(game.bugs, [])
        self.assertEqual(str(ant), "Ant (squashed)")


class GameTests(unittest.TestCase):
    """Tests of scoring and of how a game runs."""

    def test_swat_scores_points_for_squashed_bugs(self):
        """Test that squashing bugs scores their points."""
        game = Game(Player(FlySwatter()), BOUNDS)
        game.add_bug(Ant(MIDDLE[0], MIDDLE[1]))
        game.add_bug(Fly(MIDDLE[0] + 5, MIDDLE[1] + 5))
        bugs_hit = game.swat(MIDDLE)
        self.assertEqual(len(bugs_hit), 2)
        self.assertEqual(game.player.score, Ant.points + Fly.points)
        self.assertEqual(game.player.number_of_bugs_squashed, 2)

    def test_miss_scores_nothing(self):
        """Test that a swat with no bug under it scores no points."""
        game = Game(Player(FlySwatter()), BOUNDS)
        game.add_bug(Ant(BOUNDS.left, BOUNDS.top))
        self.assertEqual(game.swat(MIDDLE), [])
        self.assertEqual(game.player.score, 0)

    def test_ladybird_loses_points(self):
        """Test that squashing a ladybird takes points away."""
        game = Game(Player(FlySwatter()), BOUNDS)
        game.add_bug(Ladybird(MIDDLE[0], MIDDLE[1]))
        game.swat(MIDDLE)
        self.assertEqual(game.player.score, -20)

    def test_beetle_scores_only_when_squashed(self):
        """Test that cracking a beetle's shell scores nothing, and squashing it scores its points."""
        game = Game(Player(FlySwatter()), BOUNDS)
        beetle = Beetle(MIDDLE[0], MIDDLE[1])
        game.add_bug(beetle)
        self.assertEqual(game.swat(MIDDLE), [beetle])
        self.assertEqual(game.player.score, 0)
        game.player.swatter.update(FlySwatter.seconds_between_swings)
        game.swat((beetle.x, beetle.y))
        self.assertEqual(game.player.score, Beetle.points)

    def test_update_moves_bugs(self):
        """Test that updating the game moves its bugs and counts down the time."""
        game = Game(Player(FlySwatter()), BOUNDS)
        ant = Ant(MIDDLE[0], MIDDLE[1])
        game.add_bug(ant)
        game.update(1)
        self.assertAlmostEqual(ant.x, MIDDLE[0] + Ant.speed)
        self.assertAlmostEqual(game.seconds_left, ROUND_SECONDS - 1)

    def test_game_ends_when_time_runs_out(self):
        """Test that nothing moves and nothing can be swatted once the time is up."""
        game = Game(Player(FlySwatter()), BOUNDS, seconds=2)
        ant = Ant(MIDDLE[0], MIDDLE[1])
        game.add_bug(ant)
        self.assertFalse(game.is_over())
        game.update(2)
        self.assertTrue(game.is_over())
        position = (ant.x, ant.y)
        game.update(1)
        self.assertEqual((ant.x, ant.y), position)
        self.assertEqual(game.swat(position), [])
        self.assertEqual(game.player.score, 0)

    def test_str(self):
        """Test that the strings of a player and a game show how the game is going."""
        game = Game(Player(Chopsticks()), BOUNDS)
        game.add_bug(Ant(MIDDLE[0], MIDDLE[1]))
        game.swat(MIDDLE)
        self.assertEqual(str(game.player), "Player with Chopsticks: score 15, bugs squashed 1")
        self.assertEqual(str(game), "Game: bugs 1, seconds left 60")


class DrawingTests(unittest.TestCase):
    """Tests of how bugs and swatters are drawn."""

    def test_bug_fits_in_scene(self):
        """Test that every bug is drawn completely inside the scene, even in its corners and when squashed."""
        corners = (BUG_BOUNDS.topleft, BUG_BOUNDS.topright, BUG_BOUNDS.bottomleft, BUG_BOUNDS.bottomright)
        for corner in corners:
            for bug in make_bugs(corner):
                for i in range(NUMBER_OF_DIRECTIONS):
                    with self.subTest(bug.name, corner=corner, i=i):
                        bug.direction = 2 * math.pi * i / NUMBER_OF_DIRECTIONS
                        drawn_area = draw_picture(bug).get_bounding_rect()
                        self.assertGreater(drawn_area.width, 0)
                        self.assertTrue(SCENE.contains(drawn_area), f"{drawn_area} is outside {SCENE}")
                with self.subTest(bug.name, corner=corner, squashed=True):
                    bug.take_hit(bug.max_health)
                    drawn_area = draw_picture(bug).get_bounding_rect()
                    self.assertGreater(drawn_area.width, 0)
                    self.assertTrue(SCENE.contains(drawn_area), f"{drawn_area} is outside {SCENE}")

    def test_cracked_beetle_looks_different(self):
        """Test that a beetle is drawn differently once its shell has been hit."""
        beetle = Beetle(SCENE.centerx, SCENE.centery)
        picture_before = pygame.image.tobytes(draw_picture(beetle), "RGBA")
        beetle.take_hit(1)
        beetle.direction = 0
        self.assertNotEqual(pygame.image.tobytes(draw_picture(beetle), "RGBA"), picture_before)

    def test_swatter_is_drawn_around_position(self):
        """Test that every swatter draws a head that surrounds the position it is drawn at."""
        for swatter in make_swatters():
            with self.subTest(swatter.name):
                surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                swatter.draw(surface, SCENE.center)
                drawn_area = surface.get_bounding_rect()
                self.assertTrue(drawn_area.collidepoint(SCENE.center))
                self.assertGreaterEqual(drawn_area.width, swatter.width)


class MethodTests(unittest.TestCase):
    """Tests of which class's method runs for a bug or a swatter."""

    def test_lists_classes_with_method(self):
        """Test that the classes with their own version of a method are listed from the instance's class upwards."""
        self.assertEqual(list_classes_with_method(Ant(0, 0), "move"), ["Bug"])
        self.assertEqual(list_classes_with_method(Fly(0, 0), "move"), ["Fly", "Bug"])
        self.assertEqual(list_classes_with_method(Beetle(0, 0), "take_hit"), ["Beetle", "Bug"])
        self.assertEqual(list_classes_with_method(FruitFly(0, 0), "draw_body"), ["FruitFly", "Fly", "Bug"])
        self.assertEqual(list_classes_with_method(BugSpray(), "covers"), ["BugSpray", "Swatter"])
        self.assertEqual(list_classes_with_method(Chopsticks(), "covers"), ["Swatter"])

    def test_every_kind_inherits_from_base_class(self):
        """Test that every kind of swatter and bug inherits from its base class."""
        for swatter in make_swatters():
            self.assertIsInstance(swatter, Swatter)
        for bug in make_bugs():
            self.assertIsInstance(bug, Bug)


if __name__ == "__main__":
    unittest.main()

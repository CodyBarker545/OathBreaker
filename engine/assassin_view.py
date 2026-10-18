"""Selectable, animated assassin. Grid legality lives in core.movement."""
from collections import deque
from pathlib import Path
import math

import gltf
from direct.actor.Actor import Actor
from panda3d.core import NodePath
from ursina import BoxCollider, Entity, Vec3, color, time

from core.movement import find_path


MODEL_PATH = (Path(__file__).resolve().parents[1] / 'assets' / 'characters' /
              'hooded_assassin' / 'blendswap_assassin' / 'assassin_refined.glb')


class AssassinView(Entity):
    def __init__(self, battlefield, grid_position, on_selected, on_arrived,
                 model_path=MODEL_PATH, display_name='Assassin', marker_color=None):
        super().__init__(position=battlefield.tiles[grid_position].position + Vec3(0, .08, 0))
        self.battlefield = battlefield
        self.grid_position = grid_position
        self.on_selected = on_selected
        self.on_arrived = on_arrived
        self.display_name = display_name
        self.path = deque()
        self.move_speed = 3.5
        self.selected = False
        self.collider = BoxCollider(self, center=(0, .8, 0), size=(.7, 1.7, .7))

        self.actor = Actor(NodePath(gltf.load_model(str(model_path))))
        self.actor.reparentTo(self)
        # glTF's loader honours Ursina's Y-up coordinate system automatically.
        # The authored character faces -Z after import; turn it toward +Z.
        self.actor.setH(180)
        self.actor.setScale(.8)
        self.animation = None
        self.play_animation('Idle')
        self.selection_marker = Entity(
            parent=self, model='circle', rotation_x=90, y=.015,
            scale=.92, color=marker_color or color.rgba(.15, .8, .85, .45), enabled=False,
            unlit=True,
        )

    @property
    def moving(self):
        return bool(self.path)

    def set_selected(self, selected):
        self.selected = selected
        self.selection_marker.enabled = selected

    def play_animation(self, name):
        if name != self.animation:
            self.actor.loop(name)
            self.animation = name

    def input(self, key):
        if key == 'left mouse down' and self.hovered:
            self.on_selected(self)

    def move_to(self, destination, blocked=()):
        if self.moving:
            return False
        route = find_path(self.grid_position, destination, self.battlefield.tiles.keys() - set(blocked))
        if not route:
            return False
        self.path = deque(route)
        self.battlefield.show_path(route)
        self.play_animation('Walk')
        return True

    def advance(self, dt):
        """Advance along grid centres without overshoot, including long frames."""
        distance_left = self.move_speed * max(0, dt)
        while self.path and distance_left > 0:
            cell = self.path[0]
            target = self.battlefield.tiles[cell].position + Vec3(0, .08, 0)
            direction = target - self.position
            distance = direction.length()
            if distance > .00001:
                self.rotation_y = math.degrees(math.atan2(direction.x, direction.z))
            if distance <= distance_left:
                self.position = target
                self.grid_position = self.path.popleft()
                self.battlefield.tiles[cell].set_path_state(None)
                distance_left -= distance
            else:
                self.position += direction.normalized() * distance_left
                distance_left = 0
            if not self.path:
                self.play_animation('Idle')
                self.on_arrived(self, self.grid_position)

    def update(self):
        self.advance(time.dt)

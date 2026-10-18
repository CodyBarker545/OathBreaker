from ursina import Entity, Vec3, camera, held_keys, time


class BattlefieldCamera(Entity):
    def __init__(self, move_speed=10):
        super().__init__()

        self.move_speed = move_speed

        camera.orthographic = True
        camera.fov = 12
        camera.position = (18, 22, -18)
        camera.look_at((0, 0, 0))

    def input(self, key):
        if key == 'scroll up':
            camera.fov = max(6, camera.fov - 1.5)
        elif key == 'scroll down':
            camera.fov = min(40, camera.fov + 1.5)

    def update(self):
        # Read keyboard input.
        horizontal = held_keys["d"] - held_keys["a"]
        vertical = held_keys["w"] - held_keys["s"]

        # Project the camera's directions onto the ground.
        forward = Vec3(
            camera.forward.x, 0, camera.forward.z
        ).normalized()

        right = Vec3(
            camera.right.x, 0, camera.right.z
        ).normalized()

        direction = right * horizontal + forward * vertical

        if direction.length() > 0:
            # Normalizing prevents faster diagonal movement.
            direction = direction.normalized()

            camera.position += (
                direction * self.move_speed * time.dt
            )


def setup_battlefield_camera():
    return BattlefieldCamera()


# space sim game
__author__ = "Max Bartolo"
__version__ = "05/22/2025"

import pygame
import random
import math

# Initialize Pygame
pygame.init()
game_over = False

# Set up the game window
WINDOW_WIDTH = 1620
WINDOW_HEIGHT = 1100
window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Space Simulator")

# Camera and world settings
WORLD_SCALE = 100000  # Scale factor for world coordinates
G = 6.67430e-11 * 10  # Increased gravitational constant
TIME_STEP = 100  # Simulation time step in seconds
CAMERA_ZOOM = 1.0  # Initial zoom level

# Pre-compute values
HALF_WIDTH = WINDOW_WIDTH // 2
HALF_HEIGHT = WINDOW_HEIGHT // 2

# Generate stars once at startup
star_count = 1000
stars = [(random.randint(0, WINDOW_WIDTH),
          random.randint(0, WINDOW_HEIGHT),
          random.randint(100, 255)) for _ in range(star_count)]

class ResourceManager:
    def __init__(self):
        self.images = {}

    def load_image(self, name, path, size=None):
        image = pygame.image.load(path)
        if size:
            image = pygame.transform.scale(image, size)
        self.images[name] = image
        return image

    def get_image(self, name):
        return self.images.get(name)

# Create resource manager
resource_manager = ResourceManager()

class SoundManager:
    def __init__(self):
        # Initialize the mixer
        pygame.mixer.init()

        # Dictionary to store loaded sounds
        self.sounds = {}

        # Volume settings
        self.music_volume = 0.5
        self.sfx_volume = 0.7

    def load_sound(self, name, filepath):

        try:
            sound = pygame.mixer.Sound(filepath)
            self.sounds[name] = sound
        except pygame.error as e:
            print(f"Could not load sound {name}: {e}")


    def play_sound(self, name, loops=0):
        if name in self.sounds:
            self.sounds[name].set_volume(self.sfx_volume)
            self.sounds[name].play(loops)

    def set_sfx_volume(self, volume):

        self.sfx_volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            sound.set_volume(self.sfx_volume)

sound_manager = SoundManager()

class CelestialBody:
    def __init__(self, x, y, mass, radius, color):
        self.x = x
        self.y = y
        self.mass = mass
        self.radius = radius
        self.color = color

        # Render surface cache
        self.render_surfaces = {}

    def get_render_surface(self, zoom):
        # Use a more precise rounding to reduce surface regeneration
        zoom_key = round(zoom, 3)

        # Check if surface for this zoom level exists
        if zoom_key in self.render_surfaces:
            return self.render_surfaces[zoom_key]

        # Calculate screen radius
        screen_radius = max(int(self.radius / WORLD_SCALE * zoom), 1)

        # Create surface with alpha
        surface = pygame.Surface((screen_radius * 2, screen_radius * 2), pygame.SRCALPHA)

        # Draw planet with slight transparency
        pygame.draw.circle(surface, self.color + (200,),
                           (screen_radius, screen_radius),
                           screen_radius)

        # Cache surface
        self.render_surfaces[zoom_key] = surface

        # Limit cache size
        if len(self.render_surfaces) > 20:
            # Remove the least recently used surface
            self.render_surfaces.pop(next(iter(self.render_surfaces)))

        return surface

    def draw(self, surface, camera_pos):
        # Calculate precise screen position with zoom
        screen_x = ((self.x / WORLD_SCALE - camera_pos[0]) * CAMERA_ZOOM) + HALF_WIDTH
        screen_y = ((self.y / WORLD_SCALE - camera_pos[1]) * CAMERA_ZOOM) + HALF_HEIGHT

        # Get render surface
        planet_surface = self.get_render_surface(CAMERA_ZOOM)

        # Calculate precise blit position
        blit_x = int(screen_x - planet_surface.get_width() / 2)
        blit_y = int(screen_y - planet_surface.get_height() / 2)

        # Blit planet with precise positioning
        surface.blit(planet_surface, (blit_x, blit_y))

    def apply_gravity(self, obj):
        # Calculate distance and direction in real coordinates
        dx = self.x - obj.position[0] * WORLD_SCALE
        dy = self.y - obj.position[1] * WORLD_SCALE
        distance_squared = dx * dx + dy * dy
        distance = math.sqrt(distance_squared)

        # Don't apply gravity if inside the body
        if distance < self.radius:
            return

        # Calculate gravitational force
        force = G * self.mass * obj.mass / distance_squared

        # Convert to acceleration
        acc = force / obj.mass

        # Break into components
        acc_x = acc * dx / distance
        acc_y = acc * dy / distance

        # Apply acceleration over time step
        obj.velocity[0] += (acc_x * TIME_STEP) / WORLD_SCALE
        obj.velocity[1] += (acc_y * TIME_STEP) / WORLD_SCALE


class Ship:
    def __init__(self):
        # Ship image (simple triangle)
        self.base_image = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.polygon(self.base_image, (255, 0, 0),
                            [(10, 0), (20, 20), (10, 15), (0, 20)])

        # Load Nixon image (optional: add error handling)
        try:
            self.nixon_image = resource_manager.load_image('nixon', 'nixon.png', (40, 40))
        except:
            print("Could not load nixon.png. Using default ship image.")
            self.nixon_image = self.base_image

        # Current image
        self.current_image = self.base_image

        # Rotated image cache
        self.rotated_image = self.current_image

        # Zoom-related attributes
        self.scaled_images = {}

        # Low Earth Orbit (LEO) parameters
        EARTH_RADIUS = 6371e3  # meters
        LEO_ALTITUDE = 40000e3  # 400 km above Earth's surface
        orbit_radius = EARTH_RADIUS + LEO_ALTITUDE

        # Calculate orbital velocity for circular orbit
        # v = sqrt(G * M / r)
        # Increase the velocity multiplier to make the orbit faster
        velocity_multiplier = 1.5  # Adjust this value to change orbital speed
        orbital_velocity = velocity_multiplier * math.sqrt(G * EARTH.mass / orbit_radius)

        # Initial position: circular orbit in the x-y plane
        # Start at an angle of 45 degrees from x-axis
        orbit_angle = math.pi / 4  # 45 degrees

        # Position calculation
        self.position = [
            (orbit_radius / WORLD_SCALE) * math.cos(orbit_angle),
            (orbit_radius / WORLD_SCALE) * math.sin(orbit_angle)
        ]

        # Velocity calculation for circular orbit
        # Velocity is perpendicular to the position vector
        # Ensure tangential velocity for circular orbit
        self.velocity = [
            -orbital_velocity * math.sin(orbit_angle) / WORLD_SCALE,
            orbital_velocity * math.cos(orbit_angle) / WORLD_SCALE
        ]

        # Movement properties
        self.angle = math.degrees(orbit_angle)
        self.main_thrust = 0.1
        self.rcs_thrust = 0.05
        self.mass = 1000  # kg

    def check_planet_collision(self):
        for body in celestial_bodies:
            # Convert object's position to world coordinates
            obj_x = self.position[0] * WORLD_SCALE
            obj_y = self.position[1] * WORLD_SCALE

            # Calculate distance between object and body center
            dx = body.x - obj_x
            dy = body.y - obj_y
            distance = math.sqrt(dx * dx + dy * dy)

            # Check if distance is less than the body's radius
            if distance < body.radius:
                return body
        return None

    def toggle_nixon_mode(self):
        # Toggle between base image and Nixon image
        if self.current_image == self.base_image:
            self.current_image = self.nixon_image
        else:
            self.current_image = self.base_image

        # Reset rotated image when changing image
        self.rotated_image = pygame.transform.rotate(self.current_image, -self.angle)
        # Clear scaled images cache
        self.scaled_images.clear()

    def rotate(self, angle_change):
        self.angle = (self.angle + angle_change) % 360
        self.rotated_image = pygame.transform.rotate(self.current_image, -self.angle)
        # Clear scaled images cache when rotation changes
        self.scaled_images.clear()

    def move_forward(self):
        angle_rad = math.radians(self.angle)
        self.velocity[0] += self.main_thrust * math.sin(angle_rad)
        self.velocity[1] -= self.main_thrust * math.cos(angle_rad)

    def apply_rcs(self, dx, dy):
        angle_rad = math.radians(self.angle)
        rotated_dx = dx * math.cos(angle_rad) - dy * math.sin(angle_rad)
        rotated_dy = dx * math.sin(angle_rad) + dy * math.cos(angle_rad)
        self.velocity[0] += rotated_dx * self.rcs_thrust
        self.velocity[1] += rotated_dy * self.rcs_thrust

    def update(self):
        # Apply gravity from celestial bodies
        for body in celestial_bodies:
            body.apply_gravity(self)

        # Update position based on velocity
        self.position[0] += self.velocity[0]
        self.position[1] += self.velocity[1]

    def draw(self, surface, camera_pos):
        # Calculate screen position with zoom
        screen_x = ((self.position[0] - camera_pos[0]) * CAMERA_ZOOM) + HALF_WIDTH
        screen_y = ((self.position[1] - camera_pos[1]) * CAMERA_ZOOM) + HALF_HEIGHT

        # Always use the current image size, just rotate
        rotated_image = pygame.transform.rotate(self.current_image, -self.angle)

        # Scale the rotated image
        scaled_image = pygame.transform.scale(
            rotated_image,
            (int(rotated_image.get_width() * CAMERA_ZOOM),
             int(rotated_image.get_height() * CAMERA_ZOOM))
        )

        # Calculate precise blit position
        blit_x = int(screen_x - scaled_image.get_width() / 2)
        blit_y = int(screen_y - scaled_image.get_height() / 2)

        # Blit ship with precise positioning
        surface.blit(scaled_image, (blit_x, blit_y))


def draw_minimap(surface, player_pos, zoom=0.01):
    # Create a small surface for the minimap
    minimap_size = 200
    minimap = pygame.Surface((minimap_size, minimap_size))
    minimap.fill((0, 0, 0))

    # Draw a border
    pygame.draw.rect(minimap, (100, 100, 100), (0, 0, minimap_size, minimap_size), 2)

    minimap_center = minimap_size // 2

    # Draw celestial bodies on minimap
    for body in celestial_bodies:
        mini_x = int(minimap_center + (body.x / WORLD_SCALE - player_pos[0]) * zoom)
        mini_y = int(minimap_center + (body.y / WORLD_SCALE - player_pos[1]) * zoom)

        # Only draw if within minimap bounds
        if 0 <= mini_x < minimap_size and 0 <= mini_y < minimap_size:
            # Size based on mass
            size = max(3, int(math.log10(body.mass) - 20))
            pygame.draw.circle(minimap, body.color, (mini_x, mini_y), size)

    # Draw player position (white dot)
    pygame.draw.circle(minimap, (255, 255, 255), (minimap_center, minimap_center), 2)

    # Blit minimap to corner of screen
    surface.blit(minimap, (WINDOW_WIDTH - minimap_size - 10, 10))


# Create celestial bodies
EARTH = CelestialBody(
    x=0, y=0,
    mass=5.972e24,  # kg
    radius=6371e3,  # meters
    color=(100, 149, 237)  # Cornflower blue
)

MOON = CelestialBody(
    x=384400e3,  # meters
    y=0,
    mass=7.34767309e22,  # kg
    radius=1737.1e3,  # meters
    color=(200, 200, 200)  # Light gray
)

SUN = CelestialBody(
    x=-149.6e9,  # 1 AU distance from Earth
    y=0,
    mass=1.989e30,  # kg
    radius=696340e3,  # meters
    color=(255, 215, 0)  # Gold color
)

MARS = CelestialBody(
    x=225.0e9,  # Approximate distance from Earth
    y=0,
    mass=6.39e23,  # kg
    radius=3389.5e3,  # meters
    color=(194, 107, 72)  # Reddish color
)

celestial_bodies = [EARTH, MOON, SUN, MARS]

# Create the ship
player_ship = Ship()

#load sounds
sound_manager.load_sound('nixon mode', 'blip1.wav')

# Precompute font
font = pygame.font.Font(None, 24)

# Game loop
running = True
clock = pygame.time.Clock()

while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Nixon mode toggle
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_n:
                player_ship.toggle_nixon_mode()
                sound_manager.play_sound('nixon mode')

            # Restart game if ship is destroyed and R is pressed
            if game_over and event.key == pygame.K_r:
                # Reset game state
                player_ship = Ship()
                game_over = False
                CAMERA_ZOOM = 1.0

    # Only process game logic if not game over
    if not game_over:
        # Handle continuous keyboard input
        keys = pygame.key.get_pressed()

        # Ship controls
        if keys[pygame.K_LEFT]:
            player_ship.rotate(-5)
        if keys[pygame.K_RIGHT]:
            player_ship.rotate(5)
        if keys[pygame.K_UP]:
            player_ship.move_forward()

        # RCS controls
        dx = 0
        dy = 0
        if keys[pygame.K_a]: dx = -1
        if keys[pygame.K_d]: dx = 1
        if keys[pygame.K_w]: dy = -1
        if keys[pygame.K_s]: dy = 1
        if dx != 0 or dy != 0:
            player_ship.apply_rcs(dx, dy)

        # Zoom controls
        zoom_speed = 0.2  # Adjust for desired zoom smoothness
        if keys[pygame.K_EQUALS] or keys[pygame.K_PLUS]:  # Zoom in
            CAMERA_ZOOM *= 1 + zoom_speed
        if keys[pygame.K_MINUS]:  # Zoom out
            CAMERA_ZOOM /= 1 + zoom_speed

        # Optional: Add zoom limits
        CAMERA_ZOOM = max(0.1, min(CAMERA_ZOOM, 10))  # Limit zoom between 0.1 and 10

        # Update ship
        player_ship.update()

        # Check for planet collision
        collided_body = player_ship.check_planet_collision()
        if collided_body:
            game_over = True
            print(f"Ship crashed into {collided_body.color} planet!")

    # Clear the window
    window.fill((0, 0, 0))

    # Draw starfield with parallax
    for x, y, brightness in stars:
        parallax = brightness / 255.0
        star_x = int((x - player_ship.position[0] * parallax * 0.1) % WINDOW_WIDTH)
        star_y = int((y - player_ship.position[1] * parallax * 0.1) % WINDOW_HEIGHT)
        color = (brightness, brightness, brightness)
        size = 1 if brightness < 230 else 2
        pygame.draw.circle(window, color, (star_x, star_y), size)

    # Draw celestial bodies
    for body in celestial_bodies:
        body.draw(window, player_ship.position)

    # Draw ship
    player_ship.draw(window, player_ship.position)

    # Draw minimap
    draw_minimap(window, player_ship.position)

    # Draw debug info
    speed = math.sqrt(player_ship.velocity[0] ** 2 + player_ship.velocity[1] ** 2) * WORLD_SCALE / 1000
    speed_text = font.render(f"Speed: {speed:.1f} km/s Zoom: {CAMERA_ZOOM:.2f}", True, (255, 255, 255))
    window.blit(speed_text, (10, 10))

    # Draw game over text if game is over
    if game_over:
        game_over_font = pygame.font.Font(None, 74)
        game_over_text = game_over_font.render("GAME OVER", True, (255, 0, 0))
        game_over_rect = game_over_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        window.blit(game_over_text, game_over_rect)

        restart_font = pygame.font.Font(None, 36)
        restart_text = restart_font.render("Press R to Restart", True, (255, 255, 255))
        restart_rect = restart_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 100))
        window.blit(restart_text, restart_rect)

    # Update the display
    pygame.display.flip()
    clock.tick(60)

pygame.quit()

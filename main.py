import pygame
import sys
import random
from utils.room_generator import generate_rooms, connect_rooms
from entities.player import Player
from entities.wall import Wall
from entities.enemy import Enemy
from entities.bullet import Bullet
from utils.camera import Camera
from scenes.hole_room import HoleRoom

# Initialize Pygame
pygame.init()

# Global Settings
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 900
WORLD_WIDTH = 6400  # Increased map size (160 tiles) for better room placement
WORLD_HEIGHT = 5200  # Increased map size (130 tiles) for better room placement  
FPS = 60
TILE_SIZE = 40
GRID_WIDTH = WORLD_WIDTH // TILE_SIZE
GRID_HEIGHT = WORLD_HEIGHT // TILE_SIZE
ROOM_AMT = 16  # Increased for better connectivity options with larger map

# Colors
BLACK = (0, 0, 0)
FLOOR_COLOR = (30, 30, 120)
WALL_COLOR = (100, 100, 100)
DOOR_COLOR = (255, 215, 0)  # Gold color
CHEST_COLOR = (160, 82, 45)  # Saddle brown for unlocked chest
LOCKED_CHEST_COLOR = (34, 139, 34)  # Forest green for locked chest
SHOP_COLOR = (138, 43, 226)  # Blue violet for shop floors
BOSS_COLOR = (220, 20, 20)  # Red for boss room floors
HOLE_COLOR = (20, 20, 20)  # Dark gray for hole tiles
# Set up screen and clock
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SCALED | pygame.FULLSCREEN)
pygame.display.set_caption("Procedural Roguelike TD Puzzle Game")
clock = pygame.time.Clock()

# Set up camera
camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)

tilemap = [[1 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
fogmap = [[False for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
exploredmap = [[False for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
room_discovered = {}  # Track which rooms have been discovered
hallway_networks = {}  # Cache revealed hallway networks to avoid repeated flood-fills

fog_tile = pygame.Surface((TILE_SIZE, TILE_SIZE))
fog_tile.set_alpha(180)
fog_tile.fill((0, 0, 0))

def spawn_enemies_in_rooms(rooms, walls, tile_size):
    """Spawn enemies randomly in rooms (excluding spawn room, chest rooms, and shop rooms)"""
    enemies = pygame.sprite.Group()
    enemy_types = ["basic", "fast", "tank"]
    
    # Skip spawn room, chest rooms, and shop rooms
    eligible_rooms = []
    for room in rooms:
        if room.room_type == "normal":  # Only normal rooms get enemies
            eligible_rooms.append(room)
    
    for room in eligible_rooms:
        # Number of enemies per room (1-3)
        num_enemies = random.randint(1, 3)
        
        for _ in range(num_enemies):
            # Random position within room bounds (with some padding)
            padding = tile_size
            x = random.randint(room.rect.left + padding, room.rect.right - padding)
            y = random.randint(room.rect.top + padding, room.rect.bottom - padding)
            
            # Random enemy type with weighted probability
            enemy_type = random.choices(
                enemy_types, 
                weights=[60, 30, 10],  # Basic: 60%, Fast: 30%, Tank: 10%
                k=1
            )[0]
            
            enemy = Enemy(x, y, walls, enemy_type)
            enemies.add(enemy)
    
    return enemies

def play_hole_room_scene(player_stats):
    """Play the hole room scene"""
    # Create hole room
    hole_room = HoleRoom(TILE_SIZE)
    
    # Create new camera for hole room
    hole_camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
    
    # Create walls for hole room
    hole_walls = pygame.sprite.Group()
    for y, row in enumerate(hole_room.tilemap):
        for x, tile in enumerate(row):
            if tile == 1:  # Wall tiles
                wall = Wall(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE)
                hole_walls.add(wall)
    
    # Create player at spawn position
    hole_player = Player(hole_room.spawn_x, hole_room.spawn_y, hole_walls)
    # Restore player stats
    hole_player.health = player_stats['health']
    hole_player.max_health = player_stats['max_health']
    
    # Create bullet group
    hole_bullets = pygame.sprite.Group()
    
    # Hole room game loop
    hole_running = True
    while hole_running:
        clock.tick(FPS)
        hole_camera.move_to(hole_player.rect)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    bullet = hole_player.shoot(mouse_x, mouse_y, hole_camera)
                    if bullet:
                        hole_bullets.add(bullet)
        
        # Update player and bullets
        hole_player.update()
        
        # Update hole room bullets - remove bullets that are far off-screen
        hole_bullets_to_update = []
        hole_camera_center_x = hole_camera.rect.centerx
        hole_camera_center_y = hole_camera.rect.centery
        max_update_distance = SCREEN_WIDTH + SCREEN_HEIGHT
        
        for bullet in hole_bullets:
            # Calculate distance from camera center
            bullet_center_x = bullet.rect.centerx
            bullet_center_y = bullet.rect.centery
            distance = abs(hole_camera_center_x - bullet_center_x) + abs(hole_camera_center_y - bullet_center_y)
            
            if distance <= max_update_distance:
                hole_bullets_to_update.append(bullet)
            else:
                bullet.kill()
        
        for bullet in hole_bullets_to_update:
            bullet.update()
        
        # No exit functionality - player is stuck in this room
        
        # Draw hole room
        screen.fill(WALL_COLOR)  # Use wall color for consistency
        
        # Viewport bounds for hole room
        x_start = max(hole_camera.rect.left // TILE_SIZE, 0)
        x_end = min(hole_camera.rect.right // TILE_SIZE + 1, hole_room.room_width)
        y_start = max(hole_camera.rect.top // TILE_SIZE, 0)
        y_end = min(hole_camera.rect.bottom // TILE_SIZE + 1, hole_room.room_height)
        
        # Draw hole room tiles
        for y in range(y_start, y_end):
            for x in range(x_start, x_end):
                if y < len(hole_room.tilemap) and x < len(hole_room.tilemap[y]):
                    screen_x = x * TILE_SIZE - hole_camera.rect.x
                    screen_y = y * TILE_SIZE - hole_camera.rect.y
                    
                    if hole_room.tilemap[y][x] == 1:
                        color = WALL_COLOR
                    else:
                        color = FLOOR_COLOR
                    
                    pygame.draw.rect(screen, color, (screen_x, screen_y, TILE_SIZE, TILE_SIZE))
        
        # Draw player and bullets (only if on screen)
        hole_player_screen_rect = hole_camera.apply(hole_player)
        if (hole_player_screen_rect.right >= 0 and hole_player_screen_rect.left < SCREEN_WIDTH and
            hole_player_screen_rect.bottom >= 0 and hole_player_screen_rect.top < SCREEN_HEIGHT):
            screen.blit(hole_player.image, hole_player_screen_rect)
        
        for bullet in hole_bullets:
            bullet_screen_rect = hole_camera.apply(bullet)
            if (bullet_screen_rect.right >= 0 and bullet_screen_rect.left < SCREEN_WIDTH and
                bullet_screen_rect.bottom >= 0 and bullet_screen_rect.top < SCREEN_HEIGHT):
                screen.blit(bullet.image, bullet_screen_rect)
        
        # Draw player health bar
        hole_player.draw_health_bar(screen, hole_camera)
        
        pygame.display.flip()

def validate_world(rooms, tilemap):
    """Validate that a generated world meets all requirements for a playable game"""
    if not rooms:
        return False, "No rooms generated"
    
    if len(rooms) < ROOM_AMT:
        return False, f"Only {len(rooms)} rooms generated, need {ROOM_AMT}"
    
    # Check for spawn room
    spawn_rooms = [r for r in rooms if r.room_type == "spawn"]
    if len(spawn_rooms) != 1:
        return False, f"Found {len(spawn_rooms)} spawn rooms, need exactly 1"
    
    # Check for all required special rooms
    boss_rooms = [r for r in rooms if r.room_type == "boss"]
    shop_rooms = [r for r in rooms if r.room_type == "shop"]
    chest_unlocked_rooms = [r for r in rooms if r.room_type == "chest_unlocked"]
    chest_locked_rooms = [r for r in rooms if r.room_type == "chest_locked"]
    
    if len(boss_rooms) != 1:
        return False, f"Found {len(boss_rooms)} boss rooms, need exactly 1"
    if len(shop_rooms) != 1:
        return False, f"Found {len(shop_rooms)} shop rooms, need exactly 1"
    if len(chest_unlocked_rooms) != 1:
        return False, f"Found {len(chest_unlocked_rooms)} unlocked chest rooms, need exactly 1"
    if len(chest_locked_rooms) != 2:
        return False, f"Found {len(chest_locked_rooms)} locked chest rooms, need exactly 2"
    
    # STRICT: All special rooms (except spawn) must have exactly 1 connection (dead ends)
    connection_violations = []
    for room in rooms:
        connection_count = len(room.connections) if hasattr(room, 'connections') else 0
        
        # Special rooms (boss, shop, chests) must have exactly 1 connection
        if room.room_type in ["boss", "shop", "chest_unlocked", "chest_locked"]:
            if connection_count != 1:
                connection_violations.append(f"{room.room_type} has {connection_count} connections, must have exactly 1 (dead end)")
        
        # Spawn room can have multiple connections
        elif room.room_type == "spawn":
            if connection_count == 0:
                connection_violations.append(f"spawn has {connection_count} connections, must have at least 1")
    
    if connection_violations:
        return False, f"Dead end violations: {'; '.join(connection_violations)}"
    
    # Check spawn connections (only unlocked chests should connect directly to spawn)
    spawn_room = spawn_rooms[0]
    invalid_spawn_connections = []
    if hasattr(spawn_room, 'connections'):
        for connected_room in spawn_room.connections:
            if connected_room.room_type != "chest_unlocked" and connected_room.room_type != "normal":
                invalid_spawn_connections.append(connected_room.room_type)
    
    if invalid_spawn_connections:
        return False, f"Invalid direct connections to spawn: {invalid_spawn_connections}"
    
    # CRITICAL: Check actual tilemap connectivity using BFS
    spawn_center_x = (spawn_room.rect.x // TILE_SIZE) + 6  # Center of 14x14 room (offset 6)
    spawn_center_y = (spawn_room.rect.y // TILE_SIZE) + 6
    
    # BFS to find all reachable tiles
    visited = set()
    queue = [(spawn_center_x, spawn_center_y)]
    visited.add((spawn_center_x, spawn_center_y))
    
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    
    while queue:
        current_x, current_y = queue.pop(0)
        
        for dx, dy in directions:
            next_x = current_x + dx
            next_y = current_y + dy
            
            if (0 <= next_x < GRID_WIDTH and 0 <= next_y < GRID_HEIGHT and
                (next_x, next_y) not in visited and
                tilemap[next_y][next_x] in [0, 2]):  # Floor or door
                
                visited.add((next_x, next_y))
                queue.append((next_x, next_y))
    
    # Check if all rooms are reachable via tilemap
    unreachable_rooms = []
    unreachable_types = []
    
    for room in rooms:
        if room.room_type == "spawn":
            continue  # Skip spawn room
        
        # Check if ANY floor tile in the room is reachable (not just center, which may have items)
        room_floor_x = room.rect.x // TILE_SIZE
        room_floor_y = room.rect.y // TILE_SIZE
        
        room_reachable = False
        for dy in range(14):  # 14x14 room floor
            for dx in range(14):
                check_x = room_floor_x + dx
                check_y = room_floor_y + dy
                if (check_x, check_y) in visited and tilemap[check_y][check_x] == 0:  # Floor tile that's reachable
                    room_reachable = True
                    break
            if room_reachable:
                break
        
        if not room_reachable:
            unreachable_rooms.append(room)
            unreachable_types.append(room.room_type)
    
    if unreachable_rooms:
        return False, f"Map connectivity failed: {len(unreachable_rooms)} rooms unreachable from spawn via floor tiles. Unreachable types: {unreachable_types}"
    
    print(f"✅ Tilemap connectivity validated: All {len(rooms)} rooms reachable from spawn")
    return True, "World is valid"

def generate_valid_world():
    """Generate worlds until we find a valid one - keep trying until success"""
    attempt = 0
    
    while True:
        attempt += 1
        print(f"🌍 Generating world attempt {attempt}...")
        
        # Create fresh tilemap for this attempt
        fresh_tilemap = [[1 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        
        try:
            # Generate rooms
            rooms = generate_rooms(ROOM_AMT, WORLD_WIDTH, WORLD_HEIGHT, TILE_SIZE, fresh_tilemap)
            
            if not rooms:
                print(f"❌ Attempt {attempt}: Room generation failed")
                continue
            
            # Connect rooms
            hallways = connect_rooms(rooms, TILE_SIZE, fresh_tilemap)
            
            # Validate the world
            is_valid, message = validate_world(rooms, fresh_tilemap)
            
            if is_valid:
                print(f"✅ Attempt {attempt}: Valid world generated! {message}")
                # Copy the successful tilemap to the global tilemap
                for y in range(len(tilemap)):
                    for x in range(len(tilemap[0])):
                        tilemap[y][x] = fresh_tilemap[y][x]
                return rooms, hallways
            else:
                print(f"❌ Attempt {attempt}: Invalid world - {message}")
                
        except Exception as e:
            print(f"❌ Attempt {attempt}: Generation failed with error - {e}")
        
        # Add a reasonable safety check to prevent infinite loops
        if attempt >= 100:
            print(f"🚫 Stopping after {attempt} attempts to prevent infinite loop")
            return None, None

def main():
    global room_discovered
    
    # Generate a valid world - keep trying until we get one
    rooms, hallways = generate_valid_world()
    
    if not rooms:
        print("🚫 CRITICAL ERROR: Failed to generate a valid world after many attempts!")
        print("This should be extremely rare. Please try running again.")
        return

    print(f"🎉 Final result: {len(rooms)} rooms, {len(hallways) if hallways else 0} hallway segments")
    
    # Debug: Print all room positions
    print("DEBUG: All room positions:")
    for i, room in enumerate(rooms):
        print(f"  Room {i}: {room.room_type} at pixel ({room.rect.x}, {room.rect.y}) = grid ({room.rect.x//TILE_SIZE}, {room.rect.y//TILE_SIZE})")
    
    # Count room types for verification
    normal_rooms = [r for r in rooms if r.room_type == "normal"]
    chest_rooms = [r for r in rooms if r.room_type.startswith("chest")]
    shop_rooms = [r for r in rooms if r.room_type == "shop"]
    boss_rooms = [r for r in rooms if r.room_type == "boss"]
    spawn_rooms = [r for r in rooms if r.room_type == "spawn"]
    print(f"✅ Room breakdown: {len(spawn_rooms)} spawn, {len(normal_rooms)} normal, {len(chest_rooms)} chest, {len(shop_rooms)} shop, {len(boss_rooms)} boss")

    # Initialize room discovery tracking
    room_discovered = {}
    for i, room in enumerate(rooms):
        room_discovered[i] = False
    
    # Discover spawn room immediately
    for i, room in enumerate(rooms):
        if room.room_type == "spawn":
            room_discovered[i] = True
            break

    # Create Wall sprites based on wall tiles and chest tiles (both block movement)
    walls = pygame.sprite.Group()
    for y, row in enumerate(tilemap):
        for x, tile in enumerate(row):
            if tile == 1:  # Walls (type 1)
                wall = Wall(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE)
                walls.add(wall)
            elif tile == 3 or tile == 4:  # Both unlocked (3) and locked (4) chests block movement
                wall = Wall(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE)
                walls.add(wall)

    # Create Player - spawn in spawn room
    spawn_room = None
    for room in rooms:
        if room.room_type == "spawn":
            spawn_room = room
            break
    
    if not spawn_room:
        print("Error: No spawn room found!")
        return
    
    spawn_x, spawn_y = spawn_room.center
    spawn_x -= TILE_SIZE // 2
    spawn_y -= TILE_SIZE // 2
    player = Player(spawn_x, spawn_y, walls)

    # Spawn enemies in rooms (excluding spawn room and chest rooms)
    enemies = spawn_enemies_in_rooms(rooms, walls, TILE_SIZE)
    
    # Create bullet group
    bullets = pygame.sprite.Group()

    running = True
    while running:
        clock.tick(FPS)
        camera.move_to(player.rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    bullet = player.shoot(mouse_x, mouse_y, camera)
                    if bullet:
                        bullets.add(bullet)

        # Update sprites individually to handle different update signatures
        player.update()
        
        # Update bullets - remove bullets that are far off-screen to improve performance
        bullets_to_update = []
        for bullet in bullets:
            # Calculate distance from camera center
            camera_center_x = camera.rect.centerx
            camera_center_y = camera.rect.centery
            bullet_center_x = bullet.rect.centerx
            bullet_center_y = bullet.rect.centery
            
            # Only update bullets within a reasonable distance from camera
            # Use Manhattan distance for speed (no sqrt needed)
            distance = abs(camera_center_x - bullet_center_x) + abs(camera_center_y - bullet_center_y)
            max_update_distance = SCREEN_WIDTH + SCREEN_HEIGHT  # Bullets within 2 screen distances
            
            if distance <= max_update_distance:
                bullets_to_update.append(bullet)
            else:
                # Remove bullets that are too far away
                bullet.kill()
        
        # Update remaining bullets
        for bullet in bullets_to_update:
            bullet.update()
        
        # Check bullet-enemy collisions
        for bullet in bullets:
            hit_enemy = bullet.check_enemy_collision(enemies)
            if hit_enemy:
                if hit_enemy.take_damage(bullet.damage):
                    enemies.remove(hit_enemy)
        
        # Update enemies with player reference for AI - only update enemies near the camera
        camera_center_x = camera.rect.centerx
        camera_center_y = camera.rect.centery
        max_enemy_update_distance = SCREEN_WIDTH + SCREEN_HEIGHT  # Update enemies within 2 screen distances
        
        for enemy in enemies:
            # Calculate distance from camera center
            enemy_center_x = enemy.rect.centerx
            enemy_center_y = enemy.rect.centery
            distance = abs(camera_center_x - enemy_center_x) + abs(camera_center_y - enemy_center_y)
            
            # Only update enemies that are reasonably close to the camera
            if distance <= max_enemy_update_distance:
                enemy.update(player)

        # Check if player stepped on a hole tile
        player_grid_x = player.rect.centerx // TILE_SIZE
        player_grid_y = player.rect.centery // TILE_SIZE
        
        if (0 <= player_grid_x < GRID_WIDTH and 0 <= player_grid_y < GRID_HEIGHT and 
            tilemap[player_grid_y][player_grid_x] == 5):  # Hole tile
            # Save player stats
            player_stats = {
                'health': player.health,
                'max_health': player.max_health
            }
            
            # Enter hole room scene (no return)
            play_hole_room_scene(player_stats)

        # Determine current room or if in hallway
        current_room = None
        player_grid_x = player.rect.centerx // TILE_SIZE
        player_grid_y = player.rect.centery // TILE_SIZE
        in_hallway = False
        
        # Check if player is in a room and discover it
        for i, room in enumerate(rooms):
            if room.rect.collidepoint(player.rect.center):
                current_room = room
                if not room_discovered[i]:  # Only print when first discovered
                    room_discovered[i] = True  # Discover the room when entering
                    if room.room_type != "normal":  # Only print special rooms
                        print(f"🎉 DISCOVERED {room.room_type.upper()} ROOM at grid ({room.rect.x//TILE_SIZE}, {room.rect.y//TILE_SIZE})!")
                    else:
                        print(f"Discovered normal room {i}")
                else:
                    room_discovered[i] = True
                break
        
        # If not in a room, check if in a hallway (floor tile that's not in any room)
        if not current_room:
            if (0 <= player_grid_x < GRID_WIDTH and 0 <= player_grid_y < GRID_HEIGHT and 
                tilemap[player_grid_y][player_grid_x] in [0, 3, 4, 5]):  # On floor, unlocked chest, locked chest, or hole
                in_hallway = True

        # Reset fogmap (for current visibility)
        fogmap = [[False for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]

        # Light up current area (only if room is discovered)
        if current_room:
            # Find the room index to check if it's discovered
            current_room_index = None
            for i, room in enumerate(rooms):
                if room == current_room:
                    current_room_index = i
                    break
            
            # Only light up if the room is discovered
            if current_room_index is not None and room_discovered[current_room_index]:
                # Light up the entire current room
                for y in range(current_room.rect.top // TILE_SIZE, current_room.rect.bottom // TILE_SIZE):
                    for x in range(current_room.rect.left // TILE_SIZE, current_room.rect.right // TILE_SIZE):
                        if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
                            fogmap[y][x] = True
                            exploredmap[y][x] = True
                
                # Also light up doors connected to this room
                room_left = current_room.rect.left // TILE_SIZE - 1
                room_right = current_room.rect.right // TILE_SIZE
                room_top = current_room.rect.top // TILE_SIZE - 1
                room_bottom = current_room.rect.bottom // TILE_SIZE
                
                # Check all potential door positions around the room
                for y in range(room_top, room_bottom + 1):
                    for x in range(room_left, room_right + 1):
                        if (0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT and 
                            tilemap[y][x] == 2):  # Door tile
                            # Check if this door is on the room's perimeter
                            on_left_wall = (x == room_left and room_top <= y <= room_bottom)
                            on_right_wall = (x == room_right and room_top <= y <= room_bottom)
                            on_top_wall = (y == room_top and room_left <= x <= room_right)
                            on_bottom_wall = (y == room_bottom and room_left <= x <= room_right)
                            
                            if on_left_wall or on_right_wall or on_top_wall or on_bottom_wall:
                                fogmap[y][x] = True
                                exploredmap[y][x] = True
        elif in_hallway:
            # Reveal entire connected hallway system when entering, like rooms
            # Check if this hallway network is already cached
            hallway_key = (player_grid_x, player_grid_y)
            
            # Check if we already know which network this position belongs to
            network_tiles = None
            for cached_tiles in hallway_networks.values():
                if (player_grid_x, player_grid_y) in cached_tiles:
                    network_tiles = cached_tiles
                    break
            
            if network_tiles is None:
                # Discover new hallway network using flood-fill
                def discover_hallway_network(start_x, start_y):
                    """Flood-fill to discover all connected hallway tiles"""
                    stack = [(start_x, start_y)]
                    visited = set()
                    network = set()
                    
                    while stack:
                        x, y = stack.pop()
                        
                        if (x, y) in visited:
                            continue
                        if not (0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT):
                            continue
                        if tilemap[y][x] == 1:  # Wall - stop here
                            continue
                        
                        # Check if this tile is inside any room
                        in_any_room = False
                        for room in rooms:
                            if (room.rect.left // TILE_SIZE <= x < room.rect.right // TILE_SIZE and
                                room.rect.top // TILE_SIZE <= y < room.rect.bottom // TILE_SIZE):
                                in_any_room = True
                                break
                        
                        # Only include if it's a hallway tile (floor/door not in any room)
                        if not in_any_room and tilemap[y][x] in [0, 2]:  # Floor or door
                            visited.add((x, y))
                            network.add((x, y))
                            
                            # Add adjacent tiles to stack
                            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                                stack.append((x + dx, y + dy))
                    
                    return network
                
                # Discover and cache the network
                network_tiles = discover_hallway_network(player_grid_x, player_grid_y)
                hallway_networks[hallway_key] = network_tiles
            
            # Reveal all tiles in the network
            for x, y in network_tiles:
                fogmap[y][x] = True
                exploredmap[y][x] = True

        # Draw
        screen.fill(WALL_COLOR)  # Use wall color so walls appear to extend infinitely

        # Viewport bounds
        x_start = max(camera.rect.left // TILE_SIZE, 0)
        x_end = min(camera.rect.right // TILE_SIZE + 1, GRID_WIDTH)
        y_start = max(camera.rect.top // TILE_SIZE, 0)
        y_end = min(camera.rect.bottom // TILE_SIZE + 1, GRID_HEIGHT)

        # Draw visible tiles
        for y in range(y_start, y_end):
            for x in range(x_start, x_end):
                # Check if this tile is inside an undiscovered room
                in_undiscovered_room = False
                for i, room in enumerate(rooms):
                    if not room_discovered[i]:
                        room_grid_left = room.rect.left // TILE_SIZE
                        room_grid_right = room.rect.right // TILE_SIZE
                        room_grid_top = room.rect.top // TILE_SIZE
                        room_grid_bottom = room.rect.bottom // TILE_SIZE
                        
                        if (room_grid_left <= x < room_grid_right and 
                            room_grid_top <= y < room_grid_bottom):
                            in_undiscovered_room = True
                            break
                
                # If in undiscovered room, draw black (complete fog)
                if in_undiscovered_room:
                    screen_x = x * TILE_SIZE - camera.rect.x
                    screen_y = y * TILE_SIZE - camera.rect.y
                    pygame.draw.rect(screen, BLACK, (screen_x, screen_y, TILE_SIZE, TILE_SIZE))
                    continue
                
                # Normal tile rendering for discovered areas
                if tilemap[y][x] == 1:
                    # Only render walls that are adjacent to non-wall tiles (visible edges)
                    is_visible_wall = False
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            if dx == 0 and dy == 0:
                                continue
                            check_x, check_y = x + dx, y + dy
                            if (0 <= check_x < GRID_WIDTH and 0 <= check_y < GRID_HEIGHT and
                                tilemap[check_y][check_x] != 1):  # Adjacent to non-wall
                                is_visible_wall = True
                                break
                        if is_visible_wall:
                            break
                    
                    if is_visible_wall:
                        color = WALL_COLOR
                        screen_x = x * TILE_SIZE - camera.rect.x
                        screen_y = y * TILE_SIZE - camera.rect.y
                        pygame.draw.rect(screen, color, (screen_x, screen_y, TILE_SIZE, TILE_SIZE))
                elif tilemap[y][x] == 2:
                    color = DOOR_COLOR
                    screen_x = x * TILE_SIZE - camera.rect.x
                    screen_y = y * TILE_SIZE - camera.rect.y
                    pygame.draw.rect(screen, color, (screen_x, screen_y, TILE_SIZE, TILE_SIZE))
                elif tilemap[y][x] == 3:
                    color = CHEST_COLOR  # Unlocked chest
                    screen_x = x * TILE_SIZE - camera.rect.x
                    screen_y = y * TILE_SIZE - camera.rect.y
                    pygame.draw.rect(screen, color, (screen_x, screen_y, TILE_SIZE, TILE_SIZE))
                elif tilemap[y][x] == 4:
                    color = LOCKED_CHEST_COLOR  # Locked chest
                    screen_x = x * TILE_SIZE - camera.rect.x
                    screen_y = y * TILE_SIZE - camera.rect.y
                    pygame.draw.rect(screen, color, (screen_x, screen_y, TILE_SIZE, TILE_SIZE))
                elif tilemap[y][x] == 5:
                    color = HOLE_COLOR  # Hole tile
                    screen_x = x * TILE_SIZE - camera.rect.x
                    screen_y = y * TILE_SIZE - camera.rect.y
                    pygame.draw.rect(screen, color, (screen_x, screen_y, TILE_SIZE, TILE_SIZE))
                else:
                    # Check if this floor tile is in a shop room or boss room
                    in_shop_room = False
                    in_boss_room = False
                    for room in rooms:
                        if (room.rect.left // TILE_SIZE <= x < room.rect.right // TILE_SIZE and
                            room.rect.top // TILE_SIZE <= y < room.rect.bottom // TILE_SIZE):
                            if room.room_type == "shop":
                                in_shop_room = True
                                break
                            elif room.room_type == "boss":
                                in_boss_room = True
                                break
                    
                    if in_boss_room:
                        color = BOSS_COLOR
                    elif in_shop_room:
                        color = SHOP_COLOR
                    else:
                        color = FLOOR_COLOR
                    screen_x = x * TILE_SIZE - camera.rect.x
                    screen_y = y * TILE_SIZE - camera.rect.y
                    pygame.draw.rect(screen, color, (screen_x, screen_y, TILE_SIZE, TILE_SIZE))

                # Fog overlay - hide floors, doors, chests, and holes that haven't been explored or aren't currently visible
                # Walls are always visible once explored (no fog on walls) and only visible walls are drawn
                if tilemap[y][x] in [0, 2, 3, 4, 5]:  # Floors, doors, unlocked chests, locked chests, and holes get fog overlay
                    screen_x = x * TILE_SIZE - camera.rect.x
                    screen_y = y * TILE_SIZE - camera.rect.y
                    
                    if not exploredmap[y][x]:
                        # Completely black if never explored
                        pygame.draw.rect(screen, BLACK, (screen_x, screen_y, TILE_SIZE, TILE_SIZE))
                    elif not fogmap[y][x]:
                        # Special handling for doors - show them if connected to any discovered room
                        if tilemap[y][x] == 2:  # Door tile
                            door_should_be_visible = False
                            
                            # Check if this door is connected to any discovered room
                            for i, room in enumerate(rooms):
                                if room_discovered[i]:
                                    # Get room boundaries including walls
                                    room_left = room.rect.left // TILE_SIZE - 1
                                    room_right = room.rect.right // TILE_SIZE
                                    room_top = room.rect.top // TILE_SIZE - 1
                                    room_bottom = room.rect.bottom // TILE_SIZE
                                    
                                    # Check if door is on any wall of this discovered room
                                    on_left_wall = (x == room_left and room_top <= y <= room_bottom)
                                    on_right_wall = (x == room_right and room_top <= y <= room_bottom)
                                    on_top_wall = (y == room_top and room_left <= x <= room_right)
                                    on_bottom_wall = (y == room_bottom and room_left <= x <= room_right)
                                    
                                    if on_left_wall or on_right_wall or on_top_wall or on_bottom_wall:
                                        door_should_be_visible = True
                                        break
                            
                            # Only apply fog if door is not connected to any discovered room
                            if not door_should_be_visible:
                                screen.blit(fog_tile, (screen_x, screen_y))
                        else:
                            # Apply fog overlay for non-door tiles
                            screen.blit(fog_tile, (screen_x, screen_y))

        # Debug: Draw room boundaries and door locations
        if True:  # Enabled for debugging
            for room in rooms:
                # Only draw rooms that are at least partially visible on screen
                room_screen_x = room.rect.x - camera.rect.x
                room_screen_y = room.rect.y - camera.rect.y
                
                # Check if room is visible on screen
                if (room_screen_x + room.rect.width >= 0 and room_screen_x < SCREEN_WIDTH and
                    room_screen_y + room.rect.height >= 0 and room_screen_y < SCREEN_HEIGHT):
                    
                    # Draw room outline - different colors for different room types
                    room_screen_rect = pygame.Rect(room_screen_x, room_screen_y, room.rect.width, room.rect.height)
                    
                    if room.room_type.startswith("chest"):
                        color = (255, 165, 0)  # Orange for chest rooms
                    elif room.room_type == "spawn":
                        color = (0, 255, 255)  # Cyan for spawn room
                    elif room.room_type == "shop":
                        color = (255, 0, 255)  # Magenta for shop room
                    elif room.room_type == "boss":
                        color = (255, 0, 0)    # Red for boss room
                    else:
                        color = (0, 255, 0)    # Green for normal rooms
                        
                    pygame.draw.rect(screen, color, room_screen_rect, 2)
                    
                    # Draw room center
                    center_x = room_screen_rect.centerx - 2
                    center_y = room_screen_rect.centery - 2
                    pygame.draw.rect(screen, color, (center_x, center_y, 4, 4))
            
            # Highlight door tiles with a border
            for y in range(y_start, y_end):
                for x in range(x_start, x_end):
                    if tilemap[y][x] == 2:  # Door tile
                        screen_x = x * TILE_SIZE - camera.rect.x
                        screen_y = y * TILE_SIZE - camera.rect.y
                        pygame.draw.rect(screen, (255, 255, 255), (screen_x-1, screen_y-1, TILE_SIZE+2, TILE_SIZE+2), 2)

        # Draw player (only if on screen)
        player_screen_rect = camera.apply(player)
        if (player_screen_rect.right >= 0 and player_screen_rect.left < SCREEN_WIDTH and
            player_screen_rect.bottom >= 0 and player_screen_rect.top < SCREEN_HEIGHT):
            screen.blit(player.image, player_screen_rect)
        
        # Draw bullets (only if on screen)
        for bullet in bullets:
            bullet_screen_rect = camera.apply(bullet)
            if (bullet_screen_rect.right >= 0 and bullet_screen_rect.left < SCREEN_WIDTH and
                bullet_screen_rect.bottom >= 0 and bullet_screen_rect.top < SCREEN_HEIGHT):
                screen.blit(bullet.image, bullet_screen_rect)
        
        # Draw enemies (only if visible in fog, in discovered rooms, AND on screen)
        for enemy in enemies:
            # First check if enemy is on screen to avoid unnecessary calculations
            enemy_screen_rect = camera.apply(enemy)
            if not (enemy_screen_rect.right >= 0 and enemy_screen_rect.left < SCREEN_WIDTH and
                    enemy_screen_rect.bottom >= 0 and enemy_screen_rect.top < SCREEN_HEIGHT):
                continue  # Skip enemies that are off-screen
            
            enemy_grid_x = enemy.rect.centerx // TILE_SIZE
            enemy_grid_y = enemy.rect.centery // TILE_SIZE
            
            # Check bounds and fog visibility before doing room discovery
            if not (0 <= enemy_grid_x < GRID_WIDTH and 
                    0 <= enemy_grid_y < GRID_HEIGHT and 
                    fogmap[enemy_grid_y][enemy_grid_x]):
                continue  # Skip enemies that are out of bounds or in fog
            
            # Check if enemy is in a discovered room
            enemy_in_discovered_room = True  # Assume true for hallways
            for i, room in enumerate(rooms):
                if room.rect.collidepoint(enemy.rect.center):
                    enemy_in_discovered_room = room_discovered[i]
                    break
            
            # Only draw if enemy is in discovered room
            if enemy_in_discovered_room:
                screen.blit(enemy.image, enemy_screen_rect)
                enemy.draw_health_bar(screen, camera)
            
        # Draw UI
        player.draw_health_bar(screen, camera)
        
        # Draw crosshair at mouse position
        mouse_x, mouse_y = pygame.mouse.get_pos()
        crosshair_size = 10
        pygame.draw.line(screen, (255, 255, 255), 
                        (mouse_x - crosshair_size, mouse_y), 
                        (mouse_x + crosshair_size, mouse_y), 2)
        pygame.draw.line(screen, (255, 255, 255), 
                        (mouse_x, mouse_y - crosshair_size), 
                        (mouse_x, mouse_y + crosshair_size), 2)

        pygame.display.flip()


    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
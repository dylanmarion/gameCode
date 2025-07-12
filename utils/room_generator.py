import random
import pygame
from data.room import Room

def generate_rooms(max_rooms, map_width, map_height, tile_size, tilemap):
    """Generate rooms using a simple grid-based system"""
    return generate_grid_rooms(max_rooms, map_width, map_height, tile_size, tilemap)

def generate_grid_rooms(max_rooms, map_width, map_height, tile_size, tilemap):
    """Generate rooms in a grid pattern with 14x14 floor rooms connected by 2-wide hallways"""
    """Improved algorithm with smarter placement for guaranteed connectivity"""
    
    max_attempts = 20
    
    for attempt in range(max_attempts):
        print(f"DEBUG: Layout attempt {attempt + 1}/{max_attempts}")
        
        # Reset tilemap for this attempt
        for y in range(len(tilemap)):
            for x in range(len(tilemap[0])):
                tilemap[y][x] = 1  # Reset to walls
        
        # Calculate grid dimensions
        grid_width = len(tilemap[0])  # Should be 120 tiles (4800/40)
        grid_height = len(tilemap)    # Should be 90 tiles (3600/40)
        
        # Room settings - one tile larger in each direction again
        room_floor_size = 14  # 14x14 floor tiles (increased from 12x12)
        room_wall_thickness = 1  # 1 tile walls
        room_total_size = room_floor_size + 2 * room_wall_thickness  # 16x16 total
        hallway_length = 4  # Reduced from 5 to 4 tiles long
        
        # Calculate spacing: room + hallway
        spacing = room_total_size + hallway_length  # 16 + 4 = 20 tiles between room centers
        
        # Calculate how many rooms fit
        rooms_per_row = grid_width // spacing
        rooms_per_col = grid_height // spacing
        
        # Generate room positions
        room_positions = []
        
        # Calculate how many rooms we want
        num_rooms = min(max_rooms, rooms_per_row * rooms_per_col)
        
        # Start with one room in the center and build outward to ensure connectivity
        center_col = rooms_per_row // 2
        center_row = rooms_per_col // 2
        
        # Place first room (spawn) in center
        center_x = center_col * spacing + spacing // 2
        center_y = center_row * spacing + spacing // 2
        room_left = center_x - room_total_size // 2
        room_top = center_y - room_total_size // 2
        
        if (room_left >= 0 and room_top >= 0 and 
            room_left + room_total_size < grid_width and 
            room_top + room_total_size < grid_height):
            room_positions.append((room_left, room_top, center_row, center_col))
        
        # Build connected layout by adding adjacent rooms
        placed_grid_positions = {(center_col, center_row)}
        
        # Generate candidate adjacent positions
        candidates = []
        for row in range(rooms_per_col):
            for col in range(rooms_per_row):
                if (col, row) not in placed_grid_positions:
                    center_x = col * spacing + spacing // 2
                    center_y = row * spacing + spacing // 2
                    room_left = center_x - room_total_size // 2
                    room_top = center_y - room_total_size // 2
                    
                    if (room_left >= 0 and room_top >= 0 and 
                        room_left + room_total_size < grid_width and 
                        room_top + room_total_size < grid_height):
                        candidates.append((room_left, room_top, row, col))
        
        # IMPROVED: Use BFS-like expansion to guarantee connectivity and ensure enough edge positions for special rooms
        # Priority queue: rooms closer to center get priority, but ensure we create enough dead-end positions
        
        # Add all valid adjacent positions to the queue with their connectivity count
        def get_adjacency_count(col, row, placed_positions):
            """Count how many adjacent positions are already placed"""
            count = 0
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                if (col + dx, row + dy) in placed_positions:
                    count += 1
            return count
        
        # Build room network systematically to ensure both connectivity and special room positions
        while len(room_positions) < num_rooms:
            # Find all valid adjacent positions
            adjacent_candidates = []
            
            for row in range(rooms_per_col):
                for col in range(rooms_per_row):
                    if (col, row) in placed_grid_positions:
                        continue
                    
                    # Check if position is valid
                    center_x = col * spacing + spacing // 2
                    center_y = row * spacing + spacing // 2
                    room_left = center_x - room_total_size // 2
                    room_top = center_y - room_total_size // 2
                    
                    if not (room_left >= 0 and room_top >= 0 and 
                            room_left + room_total_size < grid_width and 
                            room_top + room_total_size < grid_height):
                        continue
                    
                    # Check if adjacent to existing rooms
                    adjacency_count = get_adjacency_count(col, row, placed_grid_positions)
                    if adjacency_count > 0:
                        adjacent_candidates.append((room_left, room_top, row, col, adjacency_count))
            
            if not adjacent_candidates:
                print(f"DEBUG: No more adjacent positions available at {len(room_positions)} rooms")
                break
            
            # Smart selection strategy:
            # - Early in placement: prefer positions with exactly 1 connection (creates dead ends for special rooms)
            # - Later in placement: prefer positions with more connections (ensures connectivity)
            rooms_needed = num_rooms - len(room_positions)
            special_rooms_needed = 5  # boss, shop, 3 chests
            
            if rooms_needed > special_rooms_needed + 2:  # Early phase: create dead ends
                # Prefer positions with exactly 1 connection
                single_connection_candidates = [c for c in adjacent_candidates if c[4] == 1]
                if single_connection_candidates:
                    # Randomize among single-connection positions
                    chosen = random.choice(single_connection_candidates)
                else:
                    # If no single connections available, take lowest connection count
                    chosen = min(adjacent_candidates, key=lambda x: x[4])
            else:  # Late phase: ensure strong connectivity
                # Prefer positions with more connections
                chosen = max(adjacent_candidates, key=lambda x: x[4])
            
            room_left, room_top, row, col, _ = chosen
            room_positions.append((room_left, room_top, row, col))
            placed_grid_positions.add((col, row))
            
            print(f"DEBUG: Placed room {len(room_positions)}/{num_rooms} at grid ({col}, {row}) with {chosen[4]} connections")
        
        print(f"DEBUG: Successfully placed {len(room_positions)} connected rooms")
        
        # Use room_positions as selected_positions for consistency with the rest of the code
        selected_positions = room_positions
        
        # Test if this layout can achieve full connectivity
        test_rooms = create_test_rooms(selected_positions, tile_size, room_floor_size, room_wall_thickness)
        if test_connectivity(test_rooms):
            print(f"DEBUG: Found valid layout on attempt {attempt + 1}")
            # Use this layout
            break
        else:
            print(f"DEBUG: Layout {attempt + 1} failed connectivity test")
            if attempt == max_attempts - 1:
                print("WARNING: Could not find fully connected layout, using last attempt")
    
    # Generate the actual rooms using the selected positions
    grid_width = len(tilemap[0])
    grid_height = len(tilemap)
    room_floor_size = 14
    room_wall_thickness = 1
    
    rooms = []
    
    # Create rooms with simplified room type system
    for i, (room_x, room_y, _, _) in enumerate(selected_positions):
        # First room is always spawn, rest start as normal
        if i == 0:
            room_type = "spawn"
        else:
            room_type = "normal"
        
        # Create Room object (position of the floor area)
        floor_x = room_x + room_wall_thickness
        floor_y = room_y + room_wall_thickness
        
        room = Room(floor_x * tile_size, floor_y * tile_size,
                   room_floor_size * tile_size, room_floor_size * tile_size, room_type)
        
        # Store grid info for hallway connections
        room.grid_x = room_x
        room.grid_y = room_y
        rooms.append(room)
    
    # IMPROVED: Smart assignment of special rooms to positions that will have exactly 1 connection
    # Need: 1 spawn (already assigned), 1 boss, 1 shop, 3 chests (1 unlocked + 2 locked)
    available_rooms = list(range(1, len(rooms)))  # Skip spawn room (index 0)
    
    if len(available_rooms) < 5:  # Need at least 5 non-spawn rooms
        print(f"ERROR: Not enough rooms for special assignments: {len(available_rooms)} available, need 5")
        return rooms
    
    # Calculate which rooms will have exactly 1 connection (ideal for special rooms)
    def count_potential_connections(room_idx):
        """Count how many adjacent rooms this room will have when connected"""
        room = rooms[room_idx]
        grid_col = room.grid_x // 20  # Convert to grid coordinates
        grid_row = room.grid_y // 20
        
        adjacent_count = 0
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            neighbor_col = grid_col + dx
            neighbor_row = grid_row + dy
            
            # Check if there's a room at this position
            for other_room in rooms:
                other_col = other_room.grid_x // 20
                other_row = other_room.grid_y // 20
                if other_col == neighbor_col and other_row == neighbor_row:
                    adjacent_count += 1
                    break
        
        return adjacent_count
    
    # Categorize available rooms by their connection potential
    single_connection_candidates = []
    multi_connection_candidates = []
    
    for room_idx in available_rooms:
        connection_count = count_potential_connections(room_idx)
        if connection_count == 1:
            single_connection_candidates.append(room_idx)
        else:
            multi_connection_candidates.append(room_idx)
    
    print(f"DEBUG: Found {len(single_connection_candidates)} single-connection positions, {len(multi_connection_candidates)} multi-connection positions")
    
    # Ensure we have enough single-connection positions for special rooms
    if len(single_connection_candidates) < 5:
        print(f"WARNING: Only {len(single_connection_candidates)} single-connection positions, need 5 for special rooms")
        print("         Will use some multi-connection positions, which may affect game balance")
        # Add some multi-connection rooms to make up the difference
        needed = 5 - len(single_connection_candidates)
        single_connection_candidates.extend(multi_connection_candidates[:needed])
    
    # Randomly assign special rooms to single-connection positions
    random.shuffle(single_connection_candidates)
    
    # Assign boss room (furthest from spawn if possible)
    boss_idx = single_connection_candidates[0]
    rooms[boss_idx].room_type = "boss"
    rooms[boss_idx].single_connection = True
    
    # Assign shop room
    shop_idx = single_connection_candidates[1]
    rooms[shop_idx].room_type = "shop"
    rooms[shop_idx].single_connection = True
    
    # Assign 3 chest rooms (1 unlocked, 2 locked)
    chest_indices = single_connection_candidates[2:5]
    for i, chest_idx in enumerate(chest_indices):
        if i == 0:
            rooms[chest_idx].room_type = "chest_unlocked"
        else:
            rooms[chest_idx].room_type = "chest_locked"
        rooms[chest_idx].single_connection = True
    
    print(f"DEBUG: Assigned special rooms to single-connection positions - Boss: {boss_idx}, Shop: {shop_idx}, Chests: {chest_indices}")
    
    # Verify assignments
    type_counts = {"spawn": 0, "normal": 0, "boss": 0, "shop": 0, "chest_unlocked": 0, "chest_locked": 0}
    for room in rooms:
        type_counts[room.room_type] += 1
    
    print(f"✅ Room type assignments: {type_counts}")
    
    if type_counts["boss"] != 1 or type_counts["shop"] != 1 or type_counts["chest_unlocked"] != 1 or type_counts["chest_locked"] != 2:
        print(f"WARNING: Incorrect special room counts!")
    
    # Carve out room floors
    for room in rooms:
        floor_x = room.rect.x // tile_size
        floor_y = room.rect.y // tile_size
        
        for dy in range(room_floor_size):
            for dx in range(room_floor_size):
                grid_x = floor_x + dx
                grid_y = floor_y + dy
                if 0 <= grid_x < grid_width and 0 <= grid_y < grid_height:
                    tilemap[grid_y][grid_x] = 0  # Floor
    
    # Place special items in rooms based on their types
    place_special_room_items(rooms, tilemap, tile_size)
    
    return rooms

def create_straight_hallway(room1, room2, tilemap):
    """Create a direct 4-tile hallway between adjacent rooms only"""
    
    # Get room centers in grid coordinates - FIXED: Use consistent calculation with validation
    # Room floor is 14x14, so center is at offset 6 from floor start
    r1_center_x = (room1.rect.x // 40) + 6  # Convert pixel to grid, then add offset
    r1_center_y = (room1.rect.y // 40) + 6
    r2_center_x = (room2.rect.x // 40) + 6
    r2_center_y = (room2.rect.y // 40) + 6
    
    # Calculate direction between rooms
    dx = r2_center_x - r1_center_x
    dy = r2_center_y - r1_center_y
    
    print(f"    DEBUG: Creating hallway between rooms:")
    print(f"      Room1 grid_pos ({room1.grid_x}, {room1.grid_y}) center ({r1_center_x}, {r1_center_y})")
    print(f"      Room2 grid_pos ({room2.grid_x}, {room2.grid_y}) center ({r2_center_x}, {r2_center_y})")
    print(f"      Delta: dx={dx}, dy={dy}")
    
    # Calculate grid distance to determine hallway type
    grid_dx = abs(dx) // 20  # Distance in room grid units (rooms are 20 tiles apart)
    grid_dy = abs(dy) // 20
    grid_distance = grid_dx + grid_dy
    
    # Allow both adjacent (distance=1) and short distant (distance=2-3) connections
    # Only reject very long connections (distance > 3)
    if grid_distance > 3:
        print(f"      REJECTED: Rooms too far apart (distance: {grid_distance} grid units), maximum allowed is 3")
        return []  # Cannot create hallway - too far apart
    elif grid_distance == 1:
        print(f"      Creating direct hallway (distance: {grid_distance} grid units) - ADJACENT")
        create_direct_hallway(room1, room2, tilemap)
    else:
        print(f"      Creating L-shaped hallway (distance: {grid_distance} grid units) - SHORT DISTANCE")
        create_l_shaped_hallway(room1, room2, tilemap)
    
    # Return single hallway rectangle for the connection
    return [pygame.Rect(0, 0, 40, 40)]  # Placeholder - just need one segment for counting

def create_l_shaped_hallway(room1, room2, tilemap):
    """Create an L-shaped hallway between rooms that are not adjacent"""
    
    # Get room centers in grid coordinates
    r1_center_x = (room1.rect.x // 40) + 6
    r1_center_y = (room1.rect.y // 40) + 6
    r2_center_x = (room2.rect.x // 40) + 6
    r2_center_y = (room2.rect.y // 40) + 6
    
    # Calculate direction
    dx = r2_center_x - r1_center_x
    dy = r2_center_y - r1_center_y
    
    print(f"      Creating L-shaped hallway:")
    print(f"        From ({r1_center_x}, {r1_center_y}) to ({r2_center_x}, {r2_center_y})")
    
    # Get room floor coordinates
    room1_floor_x = room1.rect.x // 40
    room1_floor_y = room1.rect.y // 40
    room2_floor_x = room2.rect.x // 40
    room2_floor_y = room2.rect.y // 40
    
    # Always place doors at both rooms, regardless of L-shape direction
    door1_x, door1_y = None, None
    door2_x, door2_y = None, None
    
    # Create horizontal segment first, then vertical (L-shape)
    if dx != 0:
        # Horizontal segment - make it 2 tiles wide like direct hallways
        start_x = min(r1_center_x, r2_center_x)
        end_x = max(r1_center_x, r2_center_x)
        y = r1_center_y
        
        print(f"        Horizontal segment from x={start_x} to x={end_x} at y={y} (2 tiles wide)")
        for x in range(start_x, end_x + 1):
            if 0 <= x < len(tilemap[0]) and 0 <= y < len(tilemap) and 0 <= y + 1 < len(tilemap):
                tilemap[y][x] = 0      # Floor
                tilemap[y + 1][x] = 0  # Floor (2 tiles wide)
        
        # Calculate door1 position at room1 edge
        if dx > 0:  # Moving right from room1
            door1_x = room1_floor_x + 14  # Right edge of room1 floor + 1 (the wall)
            door1_y = room1_floor_y + 6   # Center the 2-wide door
        else:  # Moving left from room1
            door1_x = room1_floor_x - 1   # Left edge of room1 floor - 1 (the wall)
            door1_y = room1_floor_y + 6   # Center the 2-wide door
        
        # If this is purely horizontal (dy=0), also place door at room2
        if dy == 0:
            if dx > 0:  # Moving right to room2
                door2_x = room2_floor_x - 1   # Left edge of room2 floor - 1 (the wall)
                door2_y = room2_floor_y + 6   # Center the 2-wide door
            else:  # Moving left to room2
                door2_x = room2_floor_x + 14  # Right edge of room2 floor + 1 (the wall)
                door2_y = room2_floor_y + 6   # Center the 2-wide door
    
    if dy != 0:
        # Vertical segment - make it 2 tiles wide like direct hallways
        start_y = min(r1_center_y, r2_center_y)
        end_y = max(r1_center_y, r2_center_y)
        x = r2_center_x
        
        print(f"        Vertical segment from y={start_y} to y={end_y} at x={x} (2 tiles wide)")
        for y in range(start_y, end_y + 1):
            if 0 <= x < len(tilemap[0]) and 0 <= x + 1 < len(tilemap[0]) and 0 <= y < len(tilemap):
                tilemap[y][x] = 0      # Floor
                tilemap[y][x + 1] = 0  # Floor (2 tiles wide)
        
        # Calculate door2 position at room2 edge
        if dy > 0:  # Moving down to room2
            door2_x = room2_floor_x + 6   # Center the 2-wide door
            door2_y = room2_floor_y - 1   # Top edge of room2 floor - 1 (the wall)
        else:  # Moving up to room2
            door2_x = room2_floor_x + 6   # Center the 2-wide door
            door2_y = room2_floor_y + 14  # Bottom edge of room2 floor + 1 (the wall)
        
        # If this is purely vertical (dx=0), also place door at room1
        if dx == 0:
            if dy > 0:  # Moving down from room1
                door1_x = room1_floor_x + 6   # Center the 2-wide door
                door1_y = room1_floor_y + 14  # Bottom edge of room1 floor + 1 (the wall)
            else:  # Moving up from room1
                door1_x = room1_floor_x + 6   # Center the 2-wide door
                door1_y = room1_floor_y - 1   # Top edge of room1 floor - 1 (the wall)
    
    # Place door1 if calculated
    if door1_x is not None and door1_y is not None:
        if 0 <= door1_x < len(tilemap[0]) and 0 <= door1_y < len(tilemap) and 0 <= door1_y + 1 < len(tilemap):
            tilemap[door1_y][door1_x] = 2      # Door
            tilemap[door1_y + 1][door1_x] = 2  # Door (2nd door tile)
            print(f"        Door1 at ({door1_x}, {door1_y})")
    
    # Place door2 if calculated
    if door2_x is not None and door2_y is not None:
        if 0 <= door2_x < len(tilemap[0]) and 0 <= door2_y < len(tilemap):
            # For horizontal doors, place 2 tiles vertically; for vertical doors, place 2 tiles horizontally
            if dy == 0:  # Horizontal connection
                if 0 <= door2_y + 1 < len(tilemap):
                    tilemap[door2_y][door2_x] = 2      # Door
                    tilemap[door2_y + 1][door2_x] = 2  # Door (2nd door tile)
                    print(f"        Door2 at ({door2_x}, {door2_y})")
            else:  # Vertical connection
                if 0 <= door2_x + 1 < len(tilemap[0]):
                    tilemap[door2_y][door2_x] = 2      # Door
                    tilemap[door2_y][door2_x + 1] = 2  # Door (2nd door tile)
                    print(f"        Door2 at ({door2_x}, {door2_y})")

def get_room_grid_pos(room, tile_size):
    """Get the grid position of a room based on its pixel coordinates"""
    spacing = 20  # room_total_size + hallway_length = 16 + 4 = 20
    grid_col = room.rect.x // (spacing * tile_size)
    grid_row = room.rect.y // (spacing * tile_size)
    return grid_col, grid_row

def connect_rooms(rooms, tile_size, tilemap):
    """Connect rooms ensuring 100% connectivity using only adjacent connections"""
    """Special rooms (shop, boss, chest) will only have one connection"""
    
    if len(rooms) < 2:
        return []

    hallways = []
    
    # Initialize connections list for all rooms
    for room in rooms:
        room.connections = []
    
    # Create a grid lookup for faster room finding
    room_grid = {}
    for room in rooms:
        grid_col, grid_row = get_room_grid_pos(room, tile_size)
        room_grid[(grid_col, grid_row)] = room
    
    print(f"DEBUG: Room grid layout:")
    for (col, row), room in room_grid.items():
        print(f"  Grid ({col}, {row}): {room.room_type} at pixel ({room.rect.x}, {room.rect.y})")
    
    # Find spawn room
    spawn_room = next((room for room in rooms if room.room_type == "spawn"), None)
    if not spawn_room:
        return hallways
    
    spawn_grid_col, spawn_grid_row = get_room_grid_pos(spawn_room, tile_size)
    print(f"DEBUG: Spawn room at grid ({spawn_grid_col}, {spawn_grid_row})")
    
    # PHASE 1: Connect all normal rooms to each other and spawn
    normal_rooms = [room for room in rooms if room.room_type == "normal"]
    connected_rooms = {spawn_room}
    unconnected_rooms = set(normal_rooms)
    
    print(f"DEBUG: Phase 1 - Connecting {len(normal_rooms)} normal rooms to spawn")
    
    # Connect normal rooms using BFS-like approach
    max_attempts = 100
    attempts = 0
    
    while unconnected_rooms and attempts < max_attempts:
        attempts += 1
        connection_made = False
        
        for unconnected_room in list(unconnected_rooms):
            unconnected_grid = (unconnected_room.grid_x // 20, unconnected_room.grid_y // 20)
            
            # Check if adjacent to any connected room
            for connected_room in connected_rooms:
                connected_grid = (connected_room.grid_x // 20, connected_room.grid_y // 20)
                
                # Check if adjacent (Manhattan distance = 1)
                if abs(unconnected_grid[0] - connected_grid[0]) + abs(unconnected_grid[1] - connected_grid[1]) == 1:
                    segments = create_straight_hallway(unconnected_room, connected_room, tilemap)
                    if segments:
                        hallways.extend(segments)
                        unconnected_room.connections.append(connected_room)
                        connected_room.connections.append(unconnected_room)
                        connected_rooms.add(unconnected_room)
                        unconnected_rooms.remove(unconnected_room)
                        print(f"  Connected {unconnected_room.room_type} to {connected_room.room_type}")
                        connection_made = True
                        break
            if connection_made:
                break
        
        if not connection_made:
            print(f"  No more adjacent connections possible at attempt {attempts}")
            break
    
    print(f"DEBUG: Phase 1 complete. Connected {len(connected_rooms)} rooms")
    
    # PHASE 2: Connect special rooms (each gets exactly one connection)
    special_rooms = [room for room in rooms if room.room_type in ["boss", "shop", "chest_unlocked", "chest_locked"]]
    print(f"DEBUG: Phase 2 - Connecting {len(special_rooms)} special rooms (one connection each)")
    
    for special_room in special_rooms:
        special_grid = (special_room.grid_x // 20, special_room.grid_y // 20)
        connected = False
        
        # Find an adjacent connected room to connect to
        for connected_room in connected_rooms:
            # Skip other special rooms for connections
            if connected_room.room_type in ["boss", "shop", "chest_unlocked", "chest_locked"]:
                continue
                
            connected_grid = (connected_room.grid_x // 20, connected_room.grid_y // 20)
            
            # Check if adjacent
            if abs(special_grid[0] - connected_grid[0]) + abs(special_grid[1] - connected_grid[1]) == 1:
                segments = create_straight_hallway(special_room, connected_room, tilemap)
                if segments:
                    hallways.extend(segments)
                    special_room.connections.append(connected_room)
                    connected_room.connections.append(special_room)
                    connected_rooms.add(special_room)
                    print(f"  Connected {special_room.room_type} to {connected_room.room_type} (single connection)")
                    connected = True
                    break
        
        if not connected:
            print(f"  WARNING: Could not connect {special_room.room_type} room!")
    
    # Verify all special rooms have exactly one connection
    for room in rooms:
        if room.room_type in ["boss", "shop", "chest_unlocked", "chest_locked"]:
            connection_count = len(room.connections)
            if connection_count != 1:
                print(f"  WARNING: {room.room_type} room has {connection_count} connections, should have 1")
    
    return hallways

def place_special_room_items(rooms, tilemap, tile_size):
    """Place items in special rooms after all room type assignments are finalized"""
    print(f"DEBUG: Placing special items based on final room types...")
    
    grid_width = len(tilemap[0])
    grid_height = len(tilemap)
    room_wall_thickness = 1
    
    for i, room in enumerate(rooms):
        # Calculate actual room boundaries in tile coordinates
        room_tile_x = room.rect.x // tile_size
        room_tile_y = room.rect.y // tile_size
        room_tile_width = room.rect.width // tile_size
        room_tile_height = room.rect.height // tile_size
        
        # Calculate floor area coordinates (inside the walls)
        floor_x = room_tile_x + room_wall_thickness
        floor_y = room_tile_y + room_wall_thickness
        floor_width = room_tile_width - 2 * room_wall_thickness
        floor_height = room_tile_height - 2 * room_wall_thickness
        
        print(f"  Room {i}: {room.room_type} at grid ({room.grid_x//20}, {room.grid_y//20})")
        
        # Place chest in center of chest rooms (2x2 chest)
        if room.room_type in ["chest_unlocked", "chest_locked"]:
            chest_center_x = floor_x + floor_width // 2
            chest_center_y = floor_y + floor_height // 2
            
            # Use room_type to determine if unlocked or locked
            chest_tile = 3 if room.room_type == "chest_unlocked" else 4
            chest_type = "unlocked" if room.room_type == "chest_unlocked" else "locked"
            
            print(f"    Placing {chest_type} chest (tile {chest_tile}) at center ({chest_center_x}, {chest_center_y})")
            
            # Place 2x2 chest centered in room
            for dy in range(2):
                for dx in range(2):
                    chest_x = chest_center_x - 1 + dx  # Center the 2x2 chest
                    chest_y = chest_center_y - 1 + dy
                    if 0 <= chest_x < grid_width and 0 <= chest_y < grid_height:
                        tilemap[chest_y][chest_x] = chest_tile
        
        # Place hole tiles in center of boss rooms (2x2 hole)
        elif room.room_type == "boss":
            hole_center_x = floor_x + floor_width // 2
            hole_center_y = floor_y + floor_height // 2
            
            print(f"    Placing boss hole at center ({hole_center_x}, {hole_center_y})")
            
            # Place 2x2 hole centered in room
            for dy in range(2):
                for dx in range(2):
                    hole_x = hole_center_x - 1 + dx  # Center the 2x2 hole
                    hole_y = hole_center_y - 1 + dy
                    if 0 <= hole_x < grid_width and 0 <= hole_y < grid_height:
                        tilemap[hole_y][hole_x] = 5  # Hole tile type

def ensure_all_special_rooms_connected(rooms, room_grid, tilemap):
    """Ensure all special rooms are connected to spawn by relocating them if necessary"""
    print(f"DEBUG: Validating special room connectivity to spawn...")
    
    # Find spawn room first
    spawn_room = None
    spawn_idx = None
    for i, room in enumerate(rooms):
        if room.room_type == "spawn":
            spawn_room = room
            spawn_idx = i
            break
    
    if not spawn_room:
        print("ERROR: No spawn room found for connectivity validation!")
        return
    
    def can_reach_spawn(start_room_idx):
        """Check if a room can reach spawn using BFS through tilemap connectivity"""
        if start_room_idx == spawn_idx:
            return True
        
        start_room = rooms[start_room_idx]
        
        # Start BFS from spawn room center
        spawn_floor_x = spawn_room.rect.x // 40
        spawn_floor_y = spawn_room.rect.y // 40
        spawn_center_x = spawn_floor_x + 6  # Center of spawn room
        spawn_center_y = spawn_floor_y + 6
        
        visited = set()
        queue = [(spawn_center_x, spawn_center_y)]
        visited.add((spawn_center_x, spawn_center_y))
        
        # Directions for BFS (4-directional)
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        
        while queue:
            current_x, current_y = queue.pop(0)
            
            # Check if we've reached the target room
            target_floor_x = start_room.rect.x // 40
            target_floor_y = start_room.rect.y // 40
            
            # Check if current position is inside the target room's floor area
            if (target_floor_x <= current_x < target_floor_x + 14 and
                target_floor_y <= current_y < target_floor_y + 14 and
                tilemap[current_y][current_x] == 0):  # Floor tile
                return True  # Found path to target room!
            
            # Explore adjacent tiles
            for dx, dy in directions:
                next_x = current_x + dx
                next_y = current_y + dy
                
                if (0 <= next_x < len(tilemap[0]) and 0 <= next_y < len(tilemap) and
                    (next_x, next_y) not in visited and
                    tilemap[next_y][next_x] in [0, 2]):  # Floor or door
                    
                    visited.add((next_x, next_y))
                    queue.append((next_x, next_y))
        
        return False  # No path to target room found
    
    # Find all special rooms and check their connectivity TO SPAWN
    special_rooms = []
    disconnected_special_rooms = []
    
    for i, room in enumerate(rooms):
        if hasattr(room, 'single_connection') and room.single_connection:
            special_rooms.append((i, room))
            
            # Check if this special room can reach spawn
            if not can_reach_spawn(i):
                disconnected_special_rooms.append((i, room))
                grid_col = room.grid_x // 20
                grid_row = room.grid_y // 20
                print(f"  Found {room.room_type} at grid ({grid_col}, {grid_row}) CANNOT reach spawn!")
    
    # If we have disconnected special rooms, we MUST relocate them to ensure 100% connectivity
    if disconnected_special_rooms:
        print(f"DEBUG: CRITICAL: Relocating {len(disconnected_special_rooms)} special rooms that cannot reach spawn...")
        
        # Find normal rooms that CAN reach spawn and will have exactly 1 connection when converted to special
        available_normal_rooms = []
        
        for i, room in enumerate(rooms):
            if room.room_type == "normal" and can_reach_spawn(i):
                grid_col = room.grid_x // 20
                grid_row = room.grid_y // 20
                
                # Count how many adjacent normal/spawn rooms this position has
                adjacent_count = 0
                adjacent_spawn_count = 0
                for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    neighbor_key = (grid_col + dx, grid_row + dy)
                    if neighbor_key in room_grid:
                        neighbor_room = room_grid[neighbor_key]
                        # Handle both tuple format (i, room) and room-only format
                        if isinstance(neighbor_room, tuple):
                            neighbor_idx, neighbor_room = neighbor_room
                        
                        if neighbor_room.room_type == "normal":
                            adjacent_count += 1
                        elif neighbor_room.room_type == "spawn":
                            adjacent_spawn_count += 1
                
                # Special rooms should have exactly 1 connection
                # Only unlocked chest rooms can connect to spawn directly
                total_connections = adjacent_count + adjacent_spawn_count
                
                # For this position to be suitable for a special room, it should have exactly 1 total connection
                if total_connections == 1:
                    # Additional check: if it's adjacent to spawn, only allow unlocked chest
                    if adjacent_spawn_count > 0:
                        # This position is adjacent to spawn - only suitable for unlocked chest
                        available_normal_rooms.append((i, room, "chest_unlocked_only"))
                    else:
                        # This position is not adjacent to spawn - suitable for any special room
                        available_normal_rooms.append((i, room, "any_special"))
                elif total_connections > 1:
                    # Position has multiple connections - not suitable for special rooms that need exactly 1
                    continue
        
        print(f"  Found {len(available_normal_rooms)} normal rooms that can reach spawn and will have exactly 1 connection")
        
        # Relocate special rooms to available normal rooms - THIS IS MANDATORY
        relocated_count = 0
        for special_idx, special_room in disconnected_special_rooms:
            relocated = False
            
            # Try to find a suitable position for this special room type
            for i, (normal_idx, normal_room, position_type) in enumerate(available_normal_rooms):
                if relocated_count >= len(available_normal_rooms):
                    break
                    
                # Check if this position is suitable for this special room type
                suitable = False
                if position_type == "any_special":
                    suitable = True
                elif position_type == "chest_unlocked_only" and special_room.room_type == "chest_unlocked":
                    suitable = True
                
                if suitable:
                    print(f"  MANDATORY RELOCATION: {special_room.room_type} from grid ({special_room.grid_x//20}, {special_room.grid_y//20}) to ({normal_room.grid_x//20}, {normal_room.grid_y//20})")
                    
                    # Swap the room types and properties
                    old_special_type = special_room.room_type
                    old_special_single = special_room.single_connection
                    
                    # CRITICAL: Clear connections before swap to prevent inheritance
                    # Save normal room's connections (it will keep them as a normal room)
                    normal_room_connections = normal_room.connections[:]
                    special_room_connections = special_room.connections[:]
                    
                    # Move special room properties to normal room
                    normal_room.room_type = old_special_type
                    normal_room.single_connection = old_special_single
                    normal_room.connections = []  # Special room starts with no connections for Phase 2
                    
                    # Convert old special room to normal and give it the normal room's connections
                    special_room.room_type = "normal"
                    if hasattr(special_room, 'single_connection'):
                        delattr(special_room, 'single_connection')
                    special_room.connections = normal_room_connections  # Keep normal room's connections
                    
                    # Update all connection references to point to the correct rooms after swap
                    for connected_room in normal_room_connections:
                        # Remove reference to normal_room and add reference to special_room
                        if normal_room in connected_room.connections:
                            connected_room.connections.remove(normal_room)
                        if special_room not in connected_room.connections:
                            connected_room.connections.append(special_room)
                    
                    for connected_room in special_room_connections:
                        # Remove reference to special_room
                        if special_room in connected_room.connections:
                            connected_room.connections.remove(special_room)
                    
                    print(f"    SUCCESS: {old_special_type} relocated successfully")
                    
                    # Remove this position from available list
                    available_normal_rooms.pop(i)
                    relocated_count += 1
                    relocated = True
                    break
            
            if not relocated:
                print(f"    ERROR: No more normal rooms available for {special_room.room_type}!")
        
        # Update room_grid after relocations
        for i, room in enumerate(rooms):
            grid_col = room.grid_x // 20
            grid_row = room.grid_y // 20
            room_grid[(grid_col, grid_row)] = room
    
    # Final validation - ALL special rooms MUST be connected TO SPAWN
    final_disconnected = []
    for i, room in enumerate(rooms):
        if hasattr(room, 'single_connection') and room.single_connection:
            if not can_reach_spawn(i):
                final_disconnected.append(room.room_type)
    
    if final_disconnected:
        print(f"CRITICAL ERROR: These special rooms still cannot reach spawn: {final_disconnected}")
    else:
        print(f"SUCCESS: All special rooms can now reach spawn!")


def ensure_boss_is_furthest_room(rooms, room_grid):
    """Ensure boss room is the furthest from spawn after all relocations"""
    boss_room = None
    boss_idx = None
    spawn_room = None
    
    for i, room in enumerate(rooms):
        if room.room_type == "boss":
            boss_room = room
            boss_idx = i
        elif room.room_type == "spawn":
            spawn_room = room
    
    if boss_room and spawn_room:
        # Calculate hallway distances for all special rooms to ensure boss is furthest
        special_room_distances = []
        for i, room in enumerate(rooms):
            if hasattr(room, 'single_connection') and room.single_connection:
                distance = calculate_hallway_distance_from_spawn_after_connections(i, rooms, room_grid)
                special_room_distances.append((i, room, distance))
                print(f"    {room.room_type} at distance {distance} from spawn")
        
        # Find the furthest special room
        if special_room_distances:
            furthest_room = max(special_room_distances, key=lambda x: x[2])
            furthest_idx, furthest_room_obj, furthest_distance = furthest_room
            
            # If boss is not the furthest, swap it with the furthest
            if furthest_room_obj.room_type != "boss":
                print(f"  Boss is not furthest (distance {calculate_hallway_distance_from_spawn_after_connections(boss_idx, rooms, room_grid)}), swapping with {furthest_room_obj.room_type} (distance {furthest_distance})")
                
                # Swap room types
                old_boss_type = boss_room.room_type
                old_boss_single = boss_room.single_connection
                old_furthest_type = furthest_room_obj.room_type
                old_furthest_single = furthest_room_obj.single_connection
                
                boss_room.room_type = old_furthest_type
                boss_room.single_connection = old_furthest_single
                
                furthest_room_obj.room_type = "boss"
                furthest_room_obj.single_connection = True
                
                print(f"    FINAL SWAP: Room {boss_idx} changed from {old_boss_type} to {boss_room.room_type}")
                print(f"    FINAL SWAP: Room {furthest_idx} changed from {old_furthest_type} to {furthest_room_obj.room_type}")
                print(f"    SUCCESS: Boss is now at distance {furthest_distance} from spawn")

def calculate_hallway_distance_from_spawn_after_connections(room_idx, rooms, room_grid):
    """Calculate hallway distance after rooms are connected - uses actual connectivity"""
    # Find spawn room
    spawn_idx = None
    for i, room in enumerate(rooms):
        if room.room_type == "spawn":
            spawn_idx = i
            break
    
    if spawn_idx is None or room_idx == spawn_idx:
        return 0
    
    # BFS to find shortest path using grid adjacency
    visited = set()
    queue = [(spawn_idx, 0)]  # (room_index, distance)
    visited.add(spawn_idx)
    
    while queue:
        current_room_idx, distance = queue.pop(0)
        
        if current_room_idx == room_idx:
            return distance
        
        current_room = rooms[current_room_idx]
        current_grid_col = current_room.grid_x // 20
        current_grid_row = current_room.grid_y // 20
        
        # Check all adjacent grid positions
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            neighbor_key = (current_grid_col + dx, current_grid_row + dy)
            if neighbor_key in room_grid:
                neighbor_data = room_grid[neighbor_key]
                
                # Handle both tuple format (i, room) and room-only format
                if isinstance(neighbor_data, tuple):
                    neighbor_idx, neighbor_room = neighbor_data
                else:
                    # Find the index by searching through rooms
                    neighbor_room = neighbor_data
                    neighbor_idx = None
                    for i, room in enumerate(rooms):
                        if room == neighbor_room:
                            neighbor_idx = i
                            break
                
                if neighbor_idx is not None and neighbor_idx not in visited:
                    visited.add(neighbor_idx)
                    queue.append((neighbor_idx, distance + 1))
    
    return float('inf')  # Unreachable

def is_room_connected_to_spawn(room, spawn_room):
    """Check if a room is connected to spawn room using BFS"""
    if not spawn_room or room == spawn_room:
        return True
    
    visited = set()
    queue = [spawn_room]
    visited.add(spawn_room)
    
    while queue:
        current = queue.pop(0)
        if current == room:
            return True
        
        for connected_room in current.connections:
            if connected_room not in visited:
                visited.add(connected_room)
                queue.append(connected_room)
    
    return False

def find_reachable_rooms_from_spawn(rooms):
    """Find all rooms reachable from spawn room using BFS"""
    spawn_room = next((room for room in rooms if room.room_type == "spawn"), None)
    if not spawn_room:
        return set()
    
    visited = set()
    queue = [spawn_room]
    visited.add(spawn_room)
    
    while queue:
        current = queue.pop(0)
        for connected_room in current.connections:
            if connected_room not in visited:
                visited.add(connected_room)
                queue.append(connected_room)
    
    return visited

def find_closest_connected_room(target_room, connected_rooms, all_rooms):
    """Find the closest room that's already connected to the main network"""
    if not connected_rooms:
        return None
    
    # Create grid lookup for distance calculation
    room_grid = {}
    for room in all_rooms:
        grid_col = room.grid_x // 20
        grid_row = room.grid_y // 20
        room_grid[(grid_col, grid_row)] = room
    
    target_grid_col = target_room.grid_x // 20
    target_grid_row = target_room.grid_y // 20
    
    min_distance = float('inf')
    closest_room = None
    
    for room in connected_rooms:
        room_grid_col = room.grid_x // 20
        room_grid_row = room.grid_y // 20
        
        # Calculate Manhattan distance
        distance = abs(target_grid_col - room_grid_col) + abs(target_grid_row - room_grid_row)
        
        # Prefer adjacent rooms (distance 1)
        if distance == 1:
            return room
        elif distance < min_distance:
            min_distance = distance
            closest_room = room
    
    return closest_room

def create_test_rooms(selected_positions, tile_size, room_floor_size, room_wall_thickness):
    """Create test room objects to check connectivity without assigning types"""
    test_rooms = []
    
    for i, (room_x, room_y, _, _) in enumerate(selected_positions):
        # Create Room object (position of the floor area)
        floor_x = room_x + room_wall_thickness
        floor_y = room_y + room_wall_thickness
        
        room = Room(floor_x * tile_size, floor_y * tile_size,
                   room_floor_size * tile_size, room_floor_size * tile_size, "normal")
        
        # Store grid info for hallway connections
        room.grid_x = room_x
        room.grid_y = room_y
        room.connections = []
        test_rooms.append(room)
    
    return test_rooms

def test_connectivity(test_rooms):
    """Test if all rooms can be connected using only adjacent connections"""
    """This must match exactly with the connect_rooms algorithm"""
    if len(test_rooms) < 2:
        return True
    
    # Create a grid lookup for faster room finding
    room_grid = {}
    for room in test_rooms:
        grid_col = room.grid_x // 20  # 20 = room size + hallway spacing
        grid_row = room.grid_y // 20
        room_grid[(grid_col, grid_row)] = room
    
    # Simulate the exact same spanning tree algorithm as connect_rooms
    spawn_room = test_rooms[0]  # Use first room as spawn for testing
    connected_rooms = {spawn_room}
    unconnected_rooms = set(test_rooms) - connected_rooms
    
    # Try the same multi-pass approach as the real algorithm
    max_attempts = len(test_rooms) * 2
    attempts = 0
    
    while unconnected_rooms and attempts < max_attempts:
        found_connection = False
        attempts += 1
        
        # Look for any unconnected room that's adjacent to a connected room
        for connected_room in list(connected_rooms):  # Create copy to avoid modification during iteration
            grid_col = connected_room.grid_x // 20
            grid_row = connected_room.grid_y // 20
            
            # Check all four directions for adjacent unconnected rooms
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                neighbor = room_grid.get((grid_col + dx, grid_row + dy))
                if neighbor and neighbor in unconnected_rooms:
                    # Found an adjacent connection
                    connected_rooms.add(neighbor)
                    unconnected_rooms.remove(neighbor)
                    found_connection = True
                    break
            
            if found_connection:
                break
        
        # If no connection found in this pass, continue trying
        if not found_connection:
            # No progress made in this pass
            pass
    
    # If we still have unconnected rooms after all attempts, layout is invalid
    if unconnected_rooms:
        print(f"DEBUG: Connectivity test failed - {len(unconnected_rooms)} rooms unreachable after {attempts} attempts")
        return False
    
    # Verify connectivity and special room placement requirements
    isolated_rooms = 0
    single_connection_rooms = 0  # Suitable for special rooms
    multi_connection_rooms = 0
    
    for room in test_rooms:
        grid_col = room.grid_x // 20
        grid_row = room.grid_y // 20
        
        # Count adjacent rooms
        adjacent_count = 0
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            neighbor = room_grid.get((grid_col + dx, grid_row + dy))
            if neighbor:
                adjacent_count += 1
        
        if adjacent_count == 0:
            isolated_rooms += 1
        elif adjacent_count == 1:
            single_connection_rooms += 1
        else:
            multi_connection_rooms += 1
    
    # No isolated rooms allowed
    if isolated_rooms > 0:
        print(f"DEBUG: Connectivity test failed - {isolated_rooms} isolated rooms")
        return False
    
    # We need at least 5 single-connection positions for special rooms (1 boss + 1 shop + 3 chests)
    # The spawn room (multi-connection) doesn't count toward this requirement
    if single_connection_rooms < 5:
        print(f"DEBUG: Connectivity test failed - only {single_connection_rooms} single-connection rooms, need 5 for special rooms")
        return False
    
    # Should have at least some multi-connection rooms for backbone connectivity
    if multi_connection_rooms < 2:
        print(f"DEBUG: Connectivity test failed - only {multi_connection_rooms} multi-connection rooms, need at least 2 for backbone")
        return False
    
    print(f"DEBUG: Connectivity test passed - all {len(test_rooms)} rooms connected")
    print(f"       {single_connection_rooms} single-connection (good for special rooms)")
    print(f"       {multi_connection_rooms} multi-connection (good for backbone)")
    return True  # All rooms can be connected


def count_room_connections(target_room, all_rooms):
    """Count how many connections a room has using the connections list"""
    if hasattr(target_room, 'connections'):
        return len(target_room.connections)
    return 0

def create_direct_hallway(room1, room2, tilemap):
    """Create a direct straight hallway between adjacent rooms"""
    
    # Get room centers in grid coordinates
    r1_center_x = (room1.rect.x // 40) + 6
    r1_center_y = (room1.rect.y // 40) + 6
    r2_center_x = (room2.rect.x // 40) + 6
    r2_center_y = (room2.rect.y // 40) + 6
    
    dx = r2_center_x - r1_center_x
    dy = r2_center_y - r1_center_y
    
    # Handle horizontal connections (rooms aligned horizontally)
    if dy == 0 and abs(dx) > 0:  # Horizontal connection - rooms are horizontally aligned
        print(f"      Creating horizontal hallway")
        if dx > 0:  # room2 is to the right of room1
            # Calculate door positions at room walls - FIXED: Use floor coordinates
            room1_floor_x = room1.rect.x // 40
            room1_floor_y = room1.rect.y // 40
            room2_floor_x = room2.rect.x // 40
            room2_floor_y = room2.rect.y // 40
            
            door1_x = room1_floor_x + 14  # Right edge of room1 floor + 1 (the wall)
            door1_y = room1_floor_y + 6   # Center the 2-wide door on 14-tile wall (positions 6,7)
            door2_x = room2_floor_x - 1   # Left edge of room2 floor - 1 (the wall)
            door2_y = room2_floor_y + 6   # Center the 2-wide door on 14-tile wall (positions 6,7)
            
            # Create hallway that connects the doors properly
            hallway_start_x = door1_x + 1  # Start just outside room1
            hallway_end_x = door2_x - 1    # End just before room2
            hallway_y = door1_y
            
            print(f"        Horizontal hallway from x={hallway_start_x} to x={hallway_end_x} at y={hallway_y}")
            print(f"        Door1 at ({door1_x}, {door1_y}), Door2 at ({door2_x}, {door2_y})")
            
            # Carve 2-wide horizontal hallway that connects the doors
            for x in range(hallway_start_x, hallway_end_x + 1):
                if 0 <= x < len(tilemap[0]) and 0 <= hallway_y < len(tilemap) and 0 <= hallway_y + 1 < len(tilemap):
                    tilemap[hallway_y][x] = 0      # Floor
                    tilemap[hallway_y + 1][x] = 0  # Floor (2 tiles wide)
        else:  # room2 is to the left of room1
            # Calculate door positions at room walls - FIXED: Use floor coordinates
            room1_floor_x = room1.rect.x // 40
            room1_floor_y = room1.rect.y // 40
            room2_floor_x = room2.rect.x // 40
            room2_floor_y = room2.rect.y // 40
            
            door1_x = room1_floor_x - 1   # Left edge of room1 floor - 1 (the wall)
            door1_y = room1_floor_y + 6   # Center the 2-wide door on 14-tile wall (positions 6,7)
            door2_x = room2_floor_x + 14  # Right edge of room2 floor + 1 (the wall)
            door2_y = room2_floor_y + 6   # Center the 2-wide door on 14-tile wall (positions 6,7)
            
            # Create hallway that connects the doors properly
            hallway_start_x = door2_x + 1  # Start just outside room2
            hallway_end_x = door1_x - 1    # End just before room1
            hallway_y = door1_y
            
            print(f"        Horizontal hallway from x={hallway_start_x} to x={hallway_end_x} at y={hallway_y}")
            print(f"        Door1 at ({door1_x}, {door1_y}), Door2 at ({door2_x}, {door2_y})")
            
            # Carve 2-wide horizontal hallway that connects the doors
            for x in range(hallway_start_x, hallway_end_x + 1):
                if 0 <= x < len(tilemap[0]) and 0 <= hallway_y < len(tilemap) and 0 <= hallway_y + 1 < len(tilemap):
                    tilemap[hallway_y][x] = 0      # Floor
                    tilemap[hallway_y + 1][x] = 0  # Floor (2 tiles wide)
        
        # Place doors at both rooms - doors must be ON the room walls
        if 0 <= door1_x < len(tilemap[0]) and 0 <= door1_y < len(tilemap):
            tilemap[door1_y][door1_x] = 2      # Door
            tilemap[door1_y + 1][door1_x] = 2  # Door (2nd door)
        if 0 <= door2_x < len(tilemap[0]) and 0 <= door2_y < len(tilemap):
            tilemap[door2_y][door2_x] = 2      # Door  
            tilemap[door2_y + 1][door2_x] = 2  # Door (2nd door)
    # Handle vertical connections (rooms aligned vertically)
    elif dx == 0 and abs(dy) > 0:  # Vertical connection - rooms are vertically aligned
        print(f"      Creating vertical hallway")
        if dy > 0:  # room2 is below room1
            # Calculate door positions at room walls - FIXED: Use floor coordinates
            room1_floor_x = room1.rect.x // 40
            room1_floor_y = room1.rect.y // 40
            room2_floor_x = room2.rect.x // 40
            room2_floor_y = room2.rect.y // 40
            
            door1_x = room1_floor_x + 6   # Center the 2-wide door on 14-tile wall (positions 6,7)
            door1_y = room1_floor_y + 14  # Bottom edge of room1 floor + 1 (the wall)
            door2_x = room2_floor_x + 6   # Center the 2-wide door on 14-tile wall (positions 6,7)
            door2_y = room2_floor_y - 1   # Top edge of room2 floor - 1 (the wall)
            
            # Create hallway that connects the doors properly
            hallway_start_y = door1_y + 1  # Start just outside room1
            hallway_end_y = door2_y - 1    # End just before room2
            hallway_x = door1_x
            
            print(f"        Vertical hallway from y={hallway_start_y} to y={hallway_end_y} at x={hallway_x}")
            print(f"        Door1 at ({door1_x}, {door1_y}), Door2 at ({door2_x}, {door2_y})")
            
            # Carve 2-wide vertical hallway that connects the doors
            for y in range(hallway_start_y, hallway_end_y + 1):
                if 0 <= hallway_x < len(tilemap[0]) and 0 <= hallway_x + 1 < len(tilemap[0]) and 0 <= y < len(tilemap):
                    tilemap[y][hallway_x] = 0      # Floor
                    tilemap[y][hallway_x + 1] = 0  # Floor (2 tiles wide)
        else:  # room2 is above room1
            # Calculate door positions at room walls - FIXED: Use floor coordinates
            room1_floor_x = room1.rect.x // 40
            room1_floor_y = room1.rect.y // 40
            room2_floor_x = room2.rect.x // 40
            room2_floor_y = room2.rect.y // 40
            
            door1_x = room1_floor_x + 6   # Center the 2-wide door on 14-tile wall (positions 6,7)
            door1_y = room1_floor_y - 1   # Top edge of room1 floor - 1 (the wall)
            door2_x = room2_floor_x + 6   # Center the 2-wide door on 14-tile wall (positions 6,7)
            door2_y = room2_floor_y + 14  # Bottom edge of room2 floor + 1 (the wall)
            
            # Create hallway that connects the doors properly
            hallway_start_y = door2_y + 1  # Start just outside room2
            hallway_end_y = door1_y - 1    # End just before room1
            hallway_x = door1_x
            
            print(f"        Vertical hallway from y={hallway_start_y} to y={hallway_end_y} at x={hallway_x}")
            print(f"        Door1 at ({door1_x}, {door1_y}), Door2 at ({door2_x}, {door2_y})")
            
            # Carve 2-wide vertical hallway that connects the doors
            for y in range(hallway_start_y, hallway_end_y + 1):
                if 0 <= hallway_x < len(tilemap[0]) and 0 <= hallway_x + 1 < len(tilemap[0]) and 0 <= y < len(tilemap):
                    tilemap[y][hallway_x] = 0      # Floor
                    tilemap[y][hallway_x + 1] = 0  # Floor (2 tiles wide)
        
        # Place doors at both rooms - doors must be ON the room walls
        if 0 <= door1_x < len(tilemap[0]) and 0 <= door1_y < len(tilemap):
            tilemap[door1_y][door1_x] = 2      # Door
            tilemap[door1_y][door1_x + 1] = 2  # Door (2nd door)
        if 0 <= door2_x < len(tilemap[0]) and 0 <= door2_y < len(tilemap):
            tilemap[door2_y][door2_x] = 2      # Door
            tilemap[door2_y][door2_x + 1] = 2  # Door (2nd door)
    else:
        # REJECT any connection that isn't purely horizontal or vertical
        print(f"      REJECTED: Only horizontal/vertical connections allowed (dx={dx}, dy={dy})")
        return []  # Cannot create hallway - only straight connections allowed
    
    # Return single hallway rectangle for the connection
    return [pygame.Rect(0, 0, 40, 40)]  # Placeholder - just need one segment for counting

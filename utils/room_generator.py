import random
import pygame
from data.room import Room

def calculate_position_distance(room1, room2):
    """Calculate Manhattan distance (faster than Euclidean) between room centers"""
    center1_x = room1.grid_x + 8  # Center of 16x16 room
    center1_y = room1.grid_y + 8
    center2_x = room2.grid_x + 8
    center2_y = room2.grid_y + 8
    
    dx = abs(center2_x - center1_x)
    dy = abs(center2_y - center1_y)
    return dx + dy  # Manhattan distance is much faster than Euclidean

def generate_rooms(max_rooms, map_width, map_height, tile_size, tilemap):
    """Generate rooms using a simple grid-based system"""
    return generate_grid_rooms(max_rooms, map_width, map_height, tile_size, tilemap)

def generate_grid_rooms(max_rooms, map_width, map_height, tile_size, tilemap):
    """Generate rooms in a grid pattern with 14x14 floor rooms connected by 2-wide hallways"""
    """Try multiple layouts until we find one with 100% connectivity"""
    
    max_attempts = 50  # Try up to 50 different layouts
    
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
        
        # Generate room positions using connected placement strategy
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
        
        # Add rooms one at a time, ensuring each new room is adjacent to an existing room
        random.shuffle(candidates)
        
        for room_left, room_top, row, col in candidates:
            if len(room_positions) >= num_rooms:
                break
            
            # Check if this position is adjacent to any existing room
            is_adjacent = False
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                neighbor_pos = (col + dx, row + dy)
                if neighbor_pos in placed_grid_positions:
                    is_adjacent = True
                    break
            
            if is_adjacent:
                room_positions.append((room_left, room_top, row, col))
                placed_grid_positions.add((col, row))
        
        # If we don't have enough connected rooms, try a different approach
        if len(room_positions) < num_rooms:
            print(f"DEBUG: Only got {len(room_positions)} connected rooms, need {num_rooms}")
            # Fall back to the old random selection method for this attempt
            room_positions = []
            all_positions = []
            for row in range(rooms_per_col):
                for col in range(rooms_per_row):
                    center_x = col * spacing + spacing // 2
                    center_y = row * spacing + spacing // 2
                    room_left = center_x - room_total_size // 2
                    room_top = center_y - room_total_size // 2
                    
                    if (room_left >= 0 and room_top >= 0 and 
                        room_left + room_total_size < grid_width and 
                        room_top + room_total_size < grid_height):
                        all_positions.append((room_left, room_top, row, col))
            
            if len(all_positions) >= num_rooms:
                room_positions = random.sample(all_positions, num_rooms)
        
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
    # Re-define variables for actual room creation
    grid_width = len(tilemap[0])
    grid_height = len(tilemap)
    room_floor_size = 14
    room_wall_thickness = 1
    
    rooms = []
    
    # Create rooms with better chest room distribution
    chest_positions = []
    for i, (room_x, room_y, _, _) in enumerate(selected_positions):  # grid_row, grid_col not used
        # Determine room type with better chest separation
        if i == 0:
            room_type = "spawn"
        else:
            room_type = "normal"  # Default to normal, we'll assign chests later
        
        # Create Room object (position of the floor area)
        floor_x = room_x + room_wall_thickness
        floor_y = room_y + room_wall_thickness
        
        # Create room with default size first (will be adjusted later for shop)
        room = Room(floor_x * tile_size, floor_y * tile_size,
                   room_floor_size * tile_size, room_floor_size * tile_size, room_type)
        
        # Store grid info for hallway connections
        room.grid_x = room_x
        room.grid_y = room_y
        rooms.append(room)
        
        # Track potential chest positions (skip spawn room)
        if i > 0:
            chest_positions.append((i, room))
    
    # Create a grid lookup for checking adjacent rooms - must happen before assignments
    room_grid = {}
    for i, room in enumerate(rooms):
        grid_col = room.grid_x // 20  # 20 = room size + hallway spacing
        grid_row = room.grid_y // 20
        room_grid[(grid_col, grid_row)] = (i, room)
    
    def can_connect_to_normal_or_spawn(room_idx, intended_room_type=None):
        """Check if a room can connect to at least one normal or spawn room, considering connection restrictions"""
        room = rooms[room_idx]
        grid_col = room.grid_x // 20
        grid_row = room.grid_y // 20
        
        has_normal_neighbor = False
        has_spawn_neighbor = False
        
        # Check all four directions for normal or spawn rooms
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            neighbor_key = (grid_col + dx, grid_row + dy)
            if neighbor_key in room_grid:
                neighbor_idx, neighbor_room = room_grid[neighbor_key]
                if neighbor_room.room_type == "normal":
                    has_normal_neighbor = True
                elif neighbor_room.room_type == "spawn":
                    has_spawn_neighbor = True
        
        # Connection rules:
        # - If there's a spawn neighbor and the intended room type is NOT unlocked chest, reject placement
        # - Only unlocked chest rooms can be placed adjacent to spawn
        if has_spawn_neighbor and intended_room_type != "chest_unlocked":
            return False
        
        # Check if there's any valid neighbor (normal or spawn if allowed)
        if has_normal_neighbor:
            return True
        elif has_spawn_neighbor:
            # Only unlocked chest can connect to spawn
            return intended_room_type == "chest_unlocked"
        
        return False
    
    def is_corner_room(room_idx):
        """Check if a room is in a corner or edge position that could cause connectivity issues"""
        room = rooms[room_idx]
        grid_col = room.grid_x // 20
        grid_row = room.grid_y // 20
        
        # Count how many adjacent positions have rooms
        adjacent_count = 0
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            neighbor_key = (grid_col + dx, grid_row + dy)
            if neighbor_key in room_grid:
                adjacent_count += 1
        
        # Corner/edge rooms have 2 or fewer adjacent rooms
        # We want to avoid placing special rooms in positions with only 1-2 neighbors
        return adjacent_count <= 2
    
    def calculate_hallway_distance_from_spawn(room_idx):
        """Calculate the minimum number of hallways needed to reach this room from spawn using BFS"""
        if room_idx == 0:  # spawn room
            return 0
        
        # BFS to find shortest path in terms of room hops
        visited = set()
        queue = [(0, 0)]  # (room_index, distance)
        visited.add(0)
        
        while queue:
            current_room_idx, distance = queue.pop(0)
            current_room = rooms[current_room_idx]
            current_grid_col = current_room.grid_x // 20
            current_grid_row = current_room.grid_y // 20
            
            # Check all adjacent rooms
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                neighbor_key = (current_grid_col + dx, current_grid_row + dy)
                if neighbor_key in room_grid:
                    neighbor_idx, neighbor_room = room_grid[neighbor_key]
                    
                    if neighbor_idx == room_idx:
                        return distance + 1
                    
                    if neighbor_idx not in visited:
                        visited.add(neighbor_idx)
                        queue.append((neighbor_idx, distance + 1))
        
        return float('inf')  # Unreachable
    
    # Ensure we have minimum required special rooms
    required_special_rooms = 5  # 1 boss + 1 shop + 3 chest rooms
    
    if len(chest_positions) < required_special_rooms:
        print(f"ERROR: Not enough non-spawn rooms ({len(chest_positions)}) for required special rooms ({required_special_rooms})")
        # Try increasing the room count by expanding the map or adjusting the algorithm
        return rooms  # Return what we have
    
    # Assign special rooms with guaranteed connectivity
    spawn_room = rooms[0]
    
    # Pre-calculate all distances from spawn
    spawn_distances = {}
    for pos_idx, room in chest_positions:
        spawn_distances[pos_idx] = calculate_position_distance(spawn_room, room)
    
    # Strategy: Assign rooms in order of importance, ensuring connectivity each time
    boss_room_index = None
    selected_chest_indices = []
    shop_room_index = None
    
    # Step 1: Find boss room - FURTHEST valid room from spawn by hallway distance
    valid_boss_candidates = [(pos_idx, room) for pos_idx, room in chest_positions 
                            if can_connect_to_normal_or_spawn(pos_idx, "boss") and not is_corner_room(pos_idx)]
    
    print(f"DEBUG: Valid boss candidates: {len(valid_boss_candidates)} out of {len(chest_positions)} (excluding corners)")
    
    if valid_boss_candidates:
        # Sort by hallway distance from spawn and pick the furthest
        boss_candidate = max(valid_boss_candidates, key=lambda x: calculate_hallway_distance_from_spawn(x[0]))
        boss_room_index = boss_candidate[0]
        boss_hallway_distance = calculate_hallway_distance_from_spawn(boss_room_index)
        rooms[boss_room_index].room_type = "boss"
        rooms[boss_room_index].single_connection = True
        print(f"DEBUG: Selected boss room index: {boss_room_index}, hallway distance: {boss_hallway_distance}")
    else:
        print("WARNING: No valid boss room positions found! Will force assignment later...")
        # Don't return early - continue with chest/shop assignment and force assignment later
    
    # Remove boss room from available positions
    remaining_positions = [(pos_idx, room) for pos_idx, room in chest_positions if pos_idx != boss_room_index]
    
    # Step 2: Assign chest rooms - need 1 unlocked (can connect to spawn) and 2 locked (cannot connect to spawn)
    # First, find positions that can connect to spawn (for unlocked chest)
    unlocked_chest_candidates = [(pos_idx, room) for pos_idx, room in remaining_positions 
                                if can_connect_to_normal_or_spawn(pos_idx, "chest_unlocked") and not is_corner_room(pos_idx)]
    
    # Find positions that can connect to normal rooms but NOT spawn (for locked chests)
    locked_chest_candidates = [(pos_idx, room) for pos_idx, room in remaining_positions 
                              if can_connect_to_normal_or_spawn(pos_idx, "chest_locked") and not is_corner_room(pos_idx)]
    
    if len(unlocked_chest_candidates) >= 1 and len(locked_chest_candidates) >= 2:
        # Select 1 unlocked chest (closest to spawn for easier access)
        unlocked_chest_candidates.sort(key=lambda x: calculate_hallway_distance_from_spawn(x[0]))
        selected_chest_indices.append(unlocked_chest_candidates[0][0])
        
        # Remove the selected unlocked chest from locked candidates (if it was there)
        locked_chest_candidates = [candidate for candidate in locked_chest_candidates 
                                  if candidate[0] != unlocked_chest_candidates[0][0]]
        
        # Select 2 locked chests (furthest from spawn)
        locked_chest_candidates.sort(key=lambda x: calculate_hallway_distance_from_spawn(x[0]), reverse=True)
        for i in range(min(2, len(locked_chest_candidates))):
            selected_chest_indices.append(locked_chest_candidates[i][0])
        
        print(f"DEBUG: Selected chest rooms: {selected_chest_indices}")
    else:
        print(f"WARNING: Not enough valid chest positions! Unlocked: {len(unlocked_chest_candidates)}, Locked: {len(locked_chest_candidates)}")
        # Fallback: just assign the first available positions
        available_positions = list(set(unlocked_chest_candidates + locked_chest_candidates))
        for i, (pos_idx, room) in enumerate(available_positions[:3]):
            selected_chest_indices.append(pos_idx)
    
    # Remove selected chest rooms from available positions
    remaining_positions = [(pos_idx, room) for pos_idx, room in remaining_positions 
                          if pos_idx not in selected_chest_indices]
    
    # Step 3: Assign shop room from remaining positions, avoid corners
    valid_shop_candidates = [(pos_idx, room) for pos_idx, room in remaining_positions 
                            if can_connect_to_normal_or_spawn(pos_idx, "shop") and not is_corner_room(pos_idx)]
    
    if valid_shop_candidates:
        # Pick shop room with good balance of distances from spawn and boss
        boss_room = rooms[boss_room_index]
        best_shop_score = 0
        
        for pos_idx, room in valid_shop_candidates:
            hallway_dist_spawn = calculate_hallway_distance_from_spawn(pos_idx)
            hallway_dist_boss = calculate_hallway_distance_from_spawn(boss_room_index) - calculate_hallway_distance_from_spawn(pos_idx)
            # Balanced score favoring distance from spawn
            combined_score = hallway_dist_spawn * 2 + abs(hallway_dist_boss)
            if combined_score > best_shop_score:
                best_shop_score = combined_score
                shop_room_index = pos_idx
        
        print(f"DEBUG: Selected shop room index: {shop_room_index}")
    else:
        print("WARNING: No valid shop room positions found!")
    
    # Assign room types based on selections
    if len(selected_chest_indices) >= 1:
        rooms[selected_chest_indices[0]].room_type = "chest_unlocked"
        rooms[selected_chest_indices[0]].single_connection = True
    if len(selected_chest_indices) >= 2:
        rooms[selected_chest_indices[1]].room_type = "chest_locked"
        rooms[selected_chest_indices[1]].single_connection = True
    if len(selected_chest_indices) >= 3:
        rooms[selected_chest_indices[2]].room_type = "chest_locked"
        rooms[selected_chest_indices[2]].single_connection = True
    
    if shop_room_index is not None:
        rooms[shop_room_index].room_type = "shop"
        rooms[shop_room_index].single_connection = True
    
    # Verify all required special rooms were assigned
    assigned_types = set()
    for room in rooms:
        if hasattr(room, 'single_connection') and room.single_connection:
            assigned_types.add(room.room_type)
    
    required_types = {"boss", "shop", "chest_unlocked", "chest_locked"}
    missing_types = required_types - assigned_types
    
    if missing_types:
        print(f"CRITICAL: Missing required room types: {missing_types}")
        # MUST assign all missing types - try best candidates first, force if needed
        for missing_type in missing_types:
            assigned = False
            
            # First, try to find a normal room that can connect and convert it
            for i, room in enumerate(rooms):
                if (room.room_type == "normal" and 
                    can_connect_to_normal_or_spawn(i)):
                    room.room_type = missing_type
                    room.single_connection = True
                    print(f"SMART assignment: {missing_type} to room {i} (can connect)")
                    assigned = True
                    break
            
            # If no connectable room found, force assignment to ANY normal room
            if not assigned:
                for i, room in enumerate(rooms):
                    if room.room_type == "normal":
                        room.room_type = missing_type
                        room.single_connection = True
                        print(f"FORCED assignment: {missing_type} to room {i} (will be relocated later)")
                        assigned = True
                        break
            
            if not assigned:
                print(f"ERROR: Could not assign {missing_type} - no normal rooms available!")
    
    # NOW validate boss room placement after all room types are assigned
    if boss_room_index is not None:
        boss_room = rooms[boss_room_index]
        boss_grid_col = boss_room.grid_x // 20
        boss_grid_row = boss_room.grid_y // 20
        
        print(f"DEBUG: Final validation of boss room at grid ({boss_grid_col}, {boss_grid_row})")
        
        # Check if boss has adjacent normal/spawn rooms (after all assignments)
        has_adjacent_normal = False
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            neighbor_key = (boss_grid_col + dx, boss_grid_row + dy)
            if neighbor_key in room_grid:
                neighbor_idx, neighbor_room = room_grid[neighbor_key]
                print(f"DEBUG: Boss neighbor at {neighbor_key}: {neighbor_room.room_type}")
                if neighbor_room.room_type in ["normal", "spawn"]:
                    has_adjacent_normal = True
                    break
        
        if not has_adjacent_normal:
            print(f"WARNING: Boss room has no adjacent normal/spawn rooms after assignments!")
            # Find a normal room adjacent to the boss and swap their types
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                neighbor_key = (boss_grid_col + dx, boss_grid_row + dy)
                if neighbor_key in room_grid:
                    neighbor_idx, neighbor_room = room_grid[neighbor_key]
                    # If it's a chest room, we can swap
                    if neighbor_room.room_type.startswith("chest") or neighbor_room.room_type == "shop":
                        print(f"SWAPPING: Boss and {neighbor_room.room_type} room types")
                        # Swap room types
                        old_neighbor_type = neighbor_room.room_type
                        old_neighbor_single = getattr(neighbor_room, 'single_connection', False)
                        
                        neighbor_room.room_type = "boss"
                        neighbor_room.single_connection = True
                        
                        boss_room.room_type = old_neighbor_type
                        boss_room.single_connection = old_neighbor_single
                        
                        # Update boss_room_index
                        boss_room_index = neighbor_idx
                        print(f"Boss is now room {boss_room_index}")
                        break
    
    # FINAL connectivity validation - check ALL special rooms after assignment
    special_rooms_to_check = [room for room in rooms if hasattr(room, 'single_connection') and room.single_connection]
    
    for special_room in special_rooms_to_check:
        special_grid_col = special_room.grid_x // 20
        special_grid_row = special_room.grid_y // 20
        
        # Check if this special room has adjacent normal/spawn rooms
        has_adjacent_normal = False
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            neighbor_key = (special_grid_col + dx, special_grid_row + dy)
            if neighbor_key in room_grid:
                neighbor_idx, neighbor_room = room_grid[neighbor_key]
                if neighbor_room.room_type in ["normal", "spawn"]:
                    has_adjacent_normal = True
                    break
        
        if not has_adjacent_normal:
            print(f"WARNING: {special_room.room_type} room at ({special_grid_col}, {special_grid_row}) has no adjacent normal/spawn rooms!")
            # Try to find a way to fix this by looking for swappable adjacent rooms
            swapped = False
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                neighbor_key = (special_grid_col + dx, special_grid_row + dy)
                if neighbor_key in room_grid:
                    neighbor_idx, neighbor_room = room_grid[neighbor_key]
                    # If it's another special room adjacent to a normal room, we can swap
                    if (neighbor_room.room_type.startswith("chest") or 
                        neighbor_room.room_type in ["shop", "boss"]) and neighbor_room != special_room:
                        
                        # Check if the neighbor has adjacent normal rooms
                        neighbor_grid_col = neighbor_room.grid_x // 20
                        neighbor_grid_row = neighbor_room.grid_y // 20
                        neighbor_has_normal = False
                        
                        for ndx, ndy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                            nn_key = (neighbor_grid_col + ndx, neighbor_grid_row + ndy)
                            if nn_key in room_grid:
                                nn_room = room_grid[nn_key][1]
                                if nn_room.room_type in ["normal", "spawn"]:
                                    neighbor_has_normal = True
                                    break
                        
                        if neighbor_has_normal:
                            print(f"SWAPPING: {special_room.room_type} and {neighbor_room.room_type} room types for connectivity")
                            # Swap room types
                            old_neighbor_type = neighbor_room.room_type
                            old_neighbor_single = getattr(neighbor_room, 'single_connection', False)
                            old_special_type = special_room.room_type
                            old_special_single = special_room.single_connection
                            
                            neighbor_room.room_type = old_special_type
                            neighbor_room.single_connection = old_special_single
                            
                            special_room.room_type = old_neighbor_type
                            special_room.single_connection = old_neighbor_single
                            
                            swapped = True
                            break
            
            if not swapped:
                print(f"Could not fix connectivity for {special_room.room_type} room")
    
    # Carve out room floors FIRST (before placing special items)
    for room in rooms:
        # Get floor position for this room
        floor_x = (room.rect.x // tile_size)  # Convert back to grid coordinates
        floor_y = (room.rect.y // tile_size)
        
        # All rooms use the same 14x14 size for consistency
        room_width = room_floor_size
        room_height = room_floor_size
        
        # Carve out room floor in one operation
        for dy in range(room_height):
            for dx in range(room_width):
                floor_grid_x = floor_x + dx
                floor_grid_y = floor_y + dy
                if 0 <= floor_grid_x < grid_width and 0 <= floor_grid_y < grid_height:
                    tilemap[floor_grid_y][floor_grid_x] = 0  # Floor
    
    # Place special items AFTER all room type assignments are finalized
    print("DEBUG: Placing special items based on final room types...")
    for i, room in enumerate(rooms):
        floor_x = (room.rect.x // tile_size)  # Convert back to grid coordinates
        floor_y = (room.rect.y // tile_size)
        room_width = room_floor_size
        room_height = room_floor_size
        
        print(f"  Room {i}: {room.room_type} at grid ({room.grid_x//20}, {room.grid_y//20})")
    
    # Count room types for summary
    room_type_counts = {"spawn": 0, "normal": 0, "chest": 0, "shop": 0, "boss": 0}
    for room in rooms:
        if room.room_type.startswith('chest'):
            room_type_counts["chest"] += 1
        else:
            room_type_counts[room.room_type] += 1
    
    # VERIFICATION: Confirm all required special rooms are present
    final_types = set()
    chest_counts = {"chest_unlocked": 0, "chest_locked": 0}
    
    for room in rooms:
        if hasattr(room, 'single_connection') and room.single_connection:
            final_types.add(room.room_type)
            if room.room_type in chest_counts:
                chest_counts[room.room_type] += 1
    
    required_types = {"boss", "shop", "chest_unlocked", "chest_locked"}
    still_missing = required_types - final_types
    
    # Check chest requirements specifically
    chest_issues = []
    if chest_counts["chest_unlocked"] != 1:
        chest_issues.append(f"Need exactly 1 unlocked chest, got {chest_counts['chest_unlocked']}")
    if chest_counts["chest_locked"] != 2:
        chest_issues.append(f"Need exactly 2 locked chests, got {chest_counts['chest_locked']}")
    
    if still_missing:
        print(f"CRITICAL ERROR: Still missing required room types after all fixes: {still_missing}")
    elif chest_issues:
        print(f"CRITICAL ERROR: Chest room count issues: {'; '.join(chest_issues)}")
    else:
        print(f"SUCCESS: All required special rooms are now present: {final_types}")
        print(f"         Chest breakdown: {chest_counts['chest_unlocked']} unlocked, {chest_counts['chest_locked']} locked")
    
    return rooms

def calculate_room_distance(room1, room2, tile_size):
    """Calculate Manhattan distance between room centers"""
    center1 = room1.rect.center
    center2 = room2.rect.center
    dx = abs(center1[0] - center2[0]) // tile_size
    dy = abs(center1[1] - center2[1]) // tile_size
    return dx + dy

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
    
    # PHASE 1: Create spanning tree for normal rooms using only adjacent connections
    # Explicitly exclude special rooms from Phase 1 connectivity
    normal_rooms = [room for room in rooms if (not hasattr(room, 'single_connection') or not room.single_connection) and room.room_type != 'spawn']
    connected_normal_rooms = {spawn_room}
    unconnected_normal_rooms = set(normal_rooms)  # Only normal rooms should be in this set
    
    print(f"DEBUG: Phase 1 - Connecting {len(normal_rooms)} normal rooms")
    print(f"  Starting with spawn room, {len(unconnected_normal_rooms)} rooms to connect")
    
    # IMPROVED ALGORITHM: Multi-phase connection strategy
    max_connection_attempts = 200  # Increased safety limit for better coverage
    connection_attempts = 0
    
    while unconnected_normal_rooms and connection_attempts < max_connection_attempts:
        connection_made = False
        connection_attempts += 1
        
        # Strategy 1: Connect adjacent rooms to the main connected component
        for unconnected_room in list(unconnected_normal_rooms):
            # Skip if this room has already become a special room
            if hasattr(unconnected_room, 'single_connection') and unconnected_room.single_connection:
                unconnected_normal_rooms.remove(unconnected_room)
                continue
                
            unconnected_grid = (unconnected_room.grid_x // 20, unconnected_room.grid_y // 20)
            
            # Check if this unconnected room is adjacent to any connected room
            for connected_room in connected_normal_rooms:
                # GUARD: Skip connecting to special rooms that already have a connection (enforce dead end)
                if (hasattr(connected_room, 'single_connection') and connected_room.single_connection and 
                    hasattr(connected_room, 'connections') and len(connected_room.connections) >= 1):
                    continue  # This special room already has its one allowed connection
                
                connected_grid = (connected_room.grid_x // 20, connected_room.grid_y // 20)
                
                # Check if they're adjacent (Manhattan distance = 1)
                if abs(unconnected_grid[0] - connected_grid[0]) + abs(unconnected_grid[1] - connected_grid[1]) == 1:
                    segments = create_straight_hallway(unconnected_room, connected_room, tilemap)
                    if segments:
                        hallways.extend(segments)
                        unconnected_room.connections.append(connected_room)
                        connected_room.connections.append(unconnected_room)
                        connected_normal_rooms.add(unconnected_room)
                        unconnected_normal_rooms.remove(unconnected_room)
                        print(f"  Connecting {unconnected_room.room_type} at ({unconnected_grid[0]}, {unconnected_grid[1]}) to {connected_room.room_type} at ({connected_grid[0]}, {connected_grid[1]})")
                        print(f"    SUCCESS: Created hallway")
                        connection_made = True
                        break
            if connection_made:
                break
        
        # Strategy 2: Bridge to unconnected rooms with forced connections every 10 attempts
        if not connection_made and connection_attempts % 10 == 0:
            print(f"  Pass {connection_attempts}: No adjacent connections found, {len(unconnected_normal_rooms)} rooms still unconnected")
            print("  Trying to force bridge connections...")
            
            # Find closest unconnected room to any connected room and force connect it
            closest_pair = None
            min_distance = float('inf')
            
            for unconnected_room in unconnected_normal_rooms:
                # Skip if this room has already become a special room
                if hasattr(unconnected_room, 'single_connection') and unconnected_room.single_connection:
                    continue
                    
                unconnected_grid = (unconnected_room.grid_x // 20, unconnected_room.grid_y // 20)
                
                for connected_room in connected_normal_rooms:
                    # GUARD: Skip connecting to special rooms that already have a connection (enforce dead end)
                    if (hasattr(connected_room, 'single_connection') and connected_room.single_connection and 
                        hasattr(connected_room, 'connections') and len(connected_room.connections) >= 1):
                        continue  # This special room already has its one allowed connection
                    
                    connected_grid = (connected_room.grid_x // 20, connected_room.grid_y // 20)
                    
                    # Calculate Manhattan distance
                    distance = abs(unconnected_grid[0] - connected_grid[0]) + abs(unconnected_grid[1] - connected_grid[1])
                    
                    # Only connect ADJACENT rooms (distance = 1) that are horizontally or vertically aligned
                    if ((unconnected_grid[0] == connected_grid[0] or unconnected_grid[1] == connected_grid[1]) 
                        and distance == 1 and distance < min_distance):
                        min_distance = distance
                        closest_pair = (unconnected_room, connected_room)
            
            if closest_pair:
                unconnected_room, connected_room = closest_pair
                unconnected_grid = (unconnected_room.grid_x // 20, unconnected_room.grid_y // 20)
                connected_grid = (connected_room.grid_x // 20, connected_room.grid_y // 20)
                
                print(f"    Force-bridging {unconnected_room.room_type} at {unconnected_grid} to {connected_room.room_type} at {connected_grid}, distance={min_distance}")
                segments = create_straight_hallway(unconnected_room, connected_room, tilemap)
                if segments:
                    hallways.extend(segments)
                    unconnected_room.connections.append(connected_room)
                    connected_room.connections.append(unconnected_room)
                    connected_normal_rooms.add(unconnected_room)
                    unconnected_normal_rooms.remove(unconnected_room)
                    print(f"    SUCCESS: Force-bridged connection")
                    connection_made = True
    print(f"DEBUG: Phase 1 complete. Connected {len(connected_normal_rooms)} normal rooms after {connection_attempts} attempts")
    
    # PHASE 1.5: Handle disconnected normal rooms - be more conservative about removal
    target_normal_rooms = 15  # Increased target for better gameplay (was 10)
    
    if len(unconnected_normal_rooms) > 0:
        current_connected_count = len(connected_normal_rooms) - 1  # Subtract spawn room
        
        print(f"DEBUG: Have {current_connected_count} connected normal rooms (target: {target_normal_rooms})")
        print(f"DEBUG: Attempting to connect remaining {len(unconnected_normal_rooms)} disconnected rooms")
        
        # CRITICAL: Try much harder to connect disconnected rooms before removing them
        for disconnected_room in list(unconnected_normal_rooms):
            # GUARD: Skip force-connecting special rooms - they will be connected in Phase 2
            if hasattr(disconnected_room, 'single_connection') and disconnected_room.single_connection:
                print(f"  Skipping special room {disconnected_room.room_type} - will be connected in Phase 2")
                continue
                
            closest_connected = None
            min_distance = float('inf')
            
            # Find closest connected room
            for connected_room in connected_normal_rooms:
                # GUARD: Skip connecting to special rooms that already have a connection (enforce dead end)
                if (hasattr(connected_room, 'single_connection') and connected_room.single_connection and 
                    hasattr(connected_room, 'connections') and len(connected_room.connections) >= 1):
                    continue  # This special room already has its one allowed connection
                
                distance = abs(disconnected_room.grid_x - connected_room.grid_x) + abs(disconnected_room.grid_y - connected_room.grid_y)
                if distance < min_distance:
                    min_distance = distance
                    closest_connected = connected_room
            
            # Try to connect with more relaxed distance constraints
            if closest_connected and min_distance <= 120:  # Allow up to 6 grid spaces (very flexible)
                print(f"  Force-connecting disconnected room at ({disconnected_room.grid_x//20}, {disconnected_room.grid_y//20}) to ({closest_connected.grid_x//20}, {closest_connected.grid_y//20}) distance={min_distance//20}")
                segments = create_straight_hallway(disconnected_room, closest_connected, tilemap)
                if segments:
                    hallways.extend(segments)
                    disconnected_room.connections.append(closest_connected)
                    closest_connected.connections.append(disconnected_room)
                    connected_normal_rooms.add(disconnected_room)
                    unconnected_normal_rooms.remove(disconnected_room)
                    print(f"    SUCCESS: Force-connected room")
                else:
                    print(f"    FAILED: Could not force-connect room even with relaxed constraints")
            else:
                print(f"  SKIPPED: Room is too far away (distance={min_distance//20} grid spaces, max allowed=6)")
        
        # Final count after aggressive connection attempts
        current_connected_count = len(connected_normal_rooms) - 1  # Subtract spawn
        
        # Only remove rooms if we MUST, and only if we have a reasonable buffer
        if current_connected_count >= target_normal_rooms and len(unconnected_normal_rooms) > 0:
            # Filter to only remove normal rooms, not special rooms
            normal_rooms_to_remove = [room for room in unconnected_normal_rooms 
                                    if not (hasattr(room, 'single_connection') and room.single_connection)]
            
            if normal_rooms_to_remove:
                print(f"DEBUG: Removing {len(normal_rooms_to_remove)} disconnected normal rooms to ensure 100% connectivity")
                
                rooms_to_remove = []
                for disconnected_room in normal_rooms_to_remove:
                    for i, room in enumerate(rooms):
                        if room == disconnected_room:
                            rooms_to_remove.append(i)
                            print(f"  Removing disconnected normal room {i} at grid ({room.grid_x//20}, {room.grid_y//20})")
                            break
                
                # Remove rooms in reverse order to maintain correct indices
                for room_index in sorted(rooms_to_remove, reverse=True):
                    del rooms[room_index]
                    
                # Update unconnected_normal_rooms to remove the deleted rooms
                for removed_room in normal_rooms_to_remove:
                    if removed_room in unconnected_normal_rooms:
                        unconnected_normal_rooms.remove(removed_room)
            else:
                print(f"DEBUG: No normal rooms to remove (only special rooms are disconnected)")
        else:
            print(f"WARNING: Only have {current_connected_count} connected normal rooms, keeping all rooms")
            print(f"DEBUG: System will attempt to work with {len(rooms)} total rooms including disconnected ones")
        
        # Rebuild room_grid and chest_positions after removal
        room_grid = {}
        chest_positions = []
        for i, room in enumerate(rooms):
            grid_col = room.grid_x // 20
            grid_row = room.grid_y // 20
            room_grid[(grid_col, grid_row)] = room  # Store room directly, not tuple
            
            # Rebuild chest positions (skip spawn room)
            if i > 0 and room.room_type == "normal":
                chest_positions.append((i, room))
        
        print(f"DEBUG: After cleanup: {len(rooms)} total rooms, {len(chest_positions)} potential special room positions")
    
    # CRITICAL: Ensure 100% connectivity by relocating any disconnected special rooms BEFORE Phase 2
    ensure_all_special_rooms_connected(rooms, room_grid, tilemap)
    
    # PHASE 2: Connect each special room to exactly one adjacent normal/spawn room
    special_rooms = [room for room in rooms if hasattr(room, 'single_connection') and room.single_connection]
    print(f"DEBUG: Phase 2 - Connecting {len(special_rooms)} special rooms")
    
    for special_room in special_rooms:
        # CRITICAL: Skip if this special room already has a connection (from Phase 1 or relocations)
        if len(special_room.connections) > 0:
            print(f"  Skipping {special_room.room_type} - already has {len(special_room.connections)} connection(s)")
            continue
            
        grid_col = special_room.grid_x // 20
        grid_row = special_room.grid_y // 20
        print(f"  Processing {special_room.room_type} at grid ({grid_col}, {grid_row})")
        
        # Find all adjacent normal/spawn rooms based on room type restrictions
        adjacent_normal_rooms = []
        adjacent_spawn_rooms = []
        
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            neighbor_pos = (grid_col + dx, grid_row + dy)
            neighbor = room_grid.get(neighbor_pos)  # Get room directly
            if neighbor and (not hasattr(neighbor, 'single_connection') or not neighbor.single_connection):
                if neighbor.room_type == "spawn":
                    # Only unlocked chest rooms can connect to spawn
                    if special_room.room_type == "chest_unlocked":
                        adjacent_spawn_rooms.append(neighbor)
                        print(f"    Found adjacent {neighbor.room_type} at grid {neighbor_pos}")
                    else:
                        print(f"    Found adjacent {neighbor.room_type} at grid {neighbor_pos} (RESTRICTED - only unlocked chests can connect to spawn)")
                else:
                    adjacent_normal_rooms.append(neighbor)
                    print(f"    Found adjacent {neighbor.room_type} at grid {neighbor_pos}")
        
        # Connection priority based on room type
        if special_room.room_type == "chest_unlocked":
            # Unlocked chest rooms prefer spawn room, then normal rooms with minimal connections
            if adjacent_spawn_rooms:
                chosen_neighbor = adjacent_spawn_rooms[0]
            elif adjacent_normal_rooms:
                # Prefer normal rooms with fewer connections to minimize overall connections
                chosen_neighbor = min(adjacent_normal_rooms, key=lambda r: len(r.connections))
            else:
                chosen_neighbor = None
        else:
            # All other special rooms (boss, shop, locked chests) must connect to normal rooms only
            if adjacent_normal_rooms:
                # Prefer normal rooms with fewer connections to minimize overall connections
                chosen_neighbor = min(adjacent_normal_rooms, key=lambda r: len(r.connections))
            else:
                chosen_neighbor = None
                
        # Connect to chosen neighbor (ONLY if we don't already have a connection)
        if chosen_neighbor and len(special_room.connections) == 0:
            print(f"    Connecting to {chosen_neighbor.room_type}")
            segments = create_straight_hallway(special_room, chosen_neighbor, tilemap)
            if segments:
                hallways.extend(segments)
                special_room.connections.append(chosen_neighbor)
                chosen_neighbor.connections.append(special_room)
                print(f"    SUCCESS: Connected {special_room.room_type} to {chosen_neighbor.room_type}")
            else:
                print(f"    FAILED: Could not create hallway to {chosen_neighbor.room_type}")
        elif len(special_room.connections) > 0:
            print(f"    SKIP: {special_room.room_type} already has {len(special_room.connections)} connection(s)")
        else:
            print(f"    ERROR: No adjacent normal/spawn rooms found for {special_room.room_type}")
    
    # Place special room items AFTER all relocations are complete
    place_special_room_items(rooms, tilemap, tile_size)
    
    return hallways

def place_special_room_items(rooms, tilemap, tile_size):
    """Place items in special rooms after all room type assignments are finalized"""
    print(f"DEBUG: Placing special items based on final room types...")
    
    grid_width = len(tilemap[0])
    grid_height = len(tilemap)
    room_floor_size = 14
    room_wall_thickness = 1
    
    for i, room in enumerate(rooms):
        # Correct grid position calculation
        grid_x = room.rect.x // tile_size // 20
        grid_y = room.rect.y // tile_size // 20
        print(f"  Room {i}: {room.room_type} at grid ({grid_x}, {grid_y})")
        
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
        
        # Place chest in center of chest rooms (2x2 chest)
        if room.room_type.startswith("chest"):
            chest_center_x = floor_x + floor_width // 2
            chest_center_y = floor_y + floor_height // 2
            chest_tile = 3 if room.room_type == "chest_unlocked" else 4
            
            print(f"    Placing {room.room_type} (tile {chest_tile}) at center ({chest_center_x}, {chest_center_y})")
            
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
    
    # Verify that every room has at least one neighbor (for special room placement)
    isolated_rooms = 0
    corner_rooms = 0
    
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
        elif adjacent_count <= 2:
            corner_rooms += 1
    
    # No isolated rooms allowed
    if isolated_rooms > 0:
        print(f"DEBUG: Connectivity test failed - {isolated_rooms} isolated rooms")
        return False
    
    # We need at least 5 non-corner rooms for special rooms (1 boss + 1 shop + 3 chest)
    non_corner_rooms = len(test_rooms) - corner_rooms
    if non_corner_rooms < 5:
        print(f"DEBUG: Connectivity test failed - only {non_corner_rooms} non-corner rooms, need 5 for special rooms")
        return False
    
    # With more rooms (24), we should be more lenient about corner rooms to allow more valid layouts
    # As long as we have enough non-corner rooms for special placement, it should be fine
    print(f"DEBUG: Connectivity test passed - all {len(test_rooms)} rooms connected, {non_corner_rooms} non-corner rooms available")
    return True  # All rooms can be connected

def can_reach_room_through_connections(start_room, target_room, all_rooms):
    """Check if start_room can reach target_room through existing connections using BFS"""
    if start_room == target_room:
        return True
    
    visited = set()
    queue = [start_room]
    visited.add(start_room)
    
    while queue:
        current_room = queue.pop(0)
        
        # Check all connected rooms
        for connected_room in current_room.connections:
            if connected_room == target_room:
                return True
            
            if connected_room not in visited:
                visited.add(connected_room)
                queue.append(connected_room)
    
    return False

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

def enforce_dead_end_requirement(rooms):
    """Ensure all special rooms (except spawn) have exactly 1 connection"""
    print(f"DEBUG: Enforcing dead end requirement for special rooms...")
    
    violations_fixed = 0
    
    for room in rooms:
        # Skip spawn room - it can have multiple connections
        if room.room_type == "spawn":
            continue
            
        # Special rooms must have exactly 1 connection
        if room.room_type in ["boss", "shop", "chest_unlocked", "chest_locked"]:
            connection_count = len(room.connections) if hasattr(room, 'connections') else 0
            
            if connection_count == 0:
                print(f"  WARNING: {room.room_type} has NO connections! This should be fixed by relocation.")
            elif connection_count > 1:
                print(f"  VIOLATION: {room.room_type} has {connection_count} connections, but this should have been prevented during connection phase!")
                print(f"    WARNING: Cannot safely remove excess connections after hallways are created.")
                print(f"    The system should prevent multiple connections during connection creation.")
                
                # Mark as violation but don't try to fix it here since it would break hallways
                violations_fixed += 1
    
    if violations_fixed > 0:
        print(f"DEBUG: Found {violations_fixed} dead end violations - these should be prevented during connection phase")
    else:
        print(f"DEBUG: Fixed 0 dead end violations")
        
    return violations_fixed > 0

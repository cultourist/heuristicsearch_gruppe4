import random
import statistics
import heapq

# Globale Variable zum Zählen der Vergleiche (Zeitkomplexitäts-Ersatz)
comparison_counter = 0

# --- 1. Klasse für den Zustand des Puzzles ---
class PuzzleState:
    def __init__(self, board_tuple, g_cost=0, parent=None):
        self.board = board_tuple          # Das Puzzle als Tupel (z.B. (1, 2, 3, 4, 5, 6, 7, 8, 0))
        self.empty_index = self.board.index(0) # Position der Leerstelle (0)
        self.g_cost = g_cost              # Bisherige Schrittkosten vom Start
        self.h_cost = 0                   # Geschätzte Kosten zum Ziel (Heuristik)
        self.f_cost = 0                   # Gesamtkosten (g + h)
        self.parent = parent              # Eltern-Zustand für den Weg zurück

    # Methode, um alle möglichen Nachbar-Zustände zu erzeugen
    def get_neighbor_states(self):
        neighbors = []
        row, col = divmod(self.empty_index, 3)
        
        # Mögliche Bewegungen der Leerstelle: Oben, Unten, Links, Rechts
        possible_directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        for row_change, column_change in possible_directions:
            new_row, new_col = row + row_change, col + column_change
            
            # Prüfen, ob die Bewegung innerhalb des 3x3 Feldes liegt
            if 0 <= new_row < 3 and 0 <= new_col < 3:
                new_empty_index = new_row * 3 + new_col
                
                # Leerstelle mit dem Nachbarn vertauschen
                board_list = list(self.board)
                board_list[self.empty_index], board_list[new_empty_index] = board_list[new_empty_index], board_list[self.empty_index]
                
                # Neuen Nachbar-Zustand erstellen
                neighbor_state = PuzzleState(tuple(board_list), self.g_cost + 1, parent=self)
                neighbors.append(neighbor_state)
                
        return neighbors

    # Wird vom A*-Algorithmus (heapq) benötigt, um Zustände nach f_cost zu sortieren
    def __lt__(self, other):
        global comparison_counter
        comparison_counter += 1
        return self.f_cost < other.f_cost


# --- 2. Heuristiken (als einfache Funktionen, keine eigenen Klassen) ---

# Heuristik 1: Manhattan-Distanz (Summe der Wege, die jeder Stein zum Ziel braucht)
def calculate_manhattan_distance(state_board, goal_board):
    distance = 0
    for index, value in enumerate(state_board):
        if value != 0:
            current_row, current_col = divmod(index, 3)
            goal_index = goal_board.index(value)
            goal_row, goal_col = divmod(goal_index, 3)
            distance += abs(current_row - goal_row) + abs(current_col - goal_col)
    return distance

# Heuristik 2: Hamming-Distanz (Falsch positionierte Steine)
def calculate_misplaced_tiles(state_board, goal_board):
    misplaced_count = 0
    for index, value in enumerate(state_board):
        if value != 0 and value != goal_board[index]:
            misplaced_count += 1
    return misplaced_count


# --- 3. Der A*-Suchalgorithmus (Solver) ---
def solve_puzzle(start_state, goal_state, heuristic_function):
    global comparison_counter
    comparison_counter = 0

    # Start-Heuristik berechnen
    start_state.h_cost = heuristic_function(start_state.board, goal_state.board)
    start_state.f_cost = start_state.g_cost + start_state.h_cost

    open_priority_queue = []
    heapq.heappush(open_priority_queue, start_state)
    
    visited_boards = set()
    expanded_nodes_count = 0
    max_stored_nodes = 1

    while open_priority_queue:
        current_state = heapq.heappop(open_priority_queue)

        # Ziel erreicht?
        if current_state.board == goal_state.board:
            return {
                "success": True,
                "comparisons": comparison_counter,
                "expanded_nodes": expanded_nodes_count,
                "stored_nodes": max_stored_nodes
            }

        if current_state.board in visited_boards:
            continue
            
        visited_boards.add(current_state.board)
        expanded_nodes_count += 1

        # Nachbarn untersuchen
        for neighbor in current_state.get_neighbor_states():
            if neighbor.board in visited_boards:
                continue
            
            neighbor.h_cost = heuristic_function(neighbor.board, goal_state.board)
            neighbor.f_cost = neighbor.g_cost + neighbor.h_cost
            
            heapq.heappush(open_priority_queue, neighbor)
            max_stored_nodes = max(max_stored_nodes, len(open_priority_queue) + len(visited_boards))

    return {"success": False, "comparisons": comparison_counter, "expanded_nodes": expanded_nodes_count, "stored_nodes": max_stored_nodes}

# --- Hilfsfunktion: Pfad vom Start zum Ziel ausgeben ---
def print_solution_path(final_state):
    path = []
    current = final_state
    
    # Vom Zielknoten rückwärts über die Eltern hangeln bis zum Start
    while current is not None:
        path.append(current)
        current = current.parent
    
    # Da wir rückwärts gesammelt haben, drehen wir den Pfad um (vom Start zum Ziel)
    path.reverse()
    
    print(f"\n--- Lösungspfad (Anzahl Schritte: {len(path) - 1}) ---")
    for step_index, state in enumerate(path):
        print(f"Schritt {step_index}:")
        # Drucke das 3x3 Raster hübsch aus (0 wird als Leerzeichen dargestellt)
        for r in range(3):
            row_vals = [str(val) if val != 0 else " " for val in state.board[r*3 : (r+1)*3]]
            print(" | ".join(row_vals))
        print("-" * 9)

# --- 4. Hilfsfunktionen für Lösbarkeit & Generierung ---
def is_board_solvable(board):
    # Zählt Inversionen (ohne die 0). Ist die Anzahl gerade, ist das Puzzle lösbar.
    flat_board = [val for val in board if val != 0]
    inversion_count = 0
    for i in range(len(flat_board)):
        for j in range(i + 1, len(flat_board)):
            if flat_board[i] > flat_board[j]:
                inversion_count += 1
    return inversion_count % 2 == 0

def generate_random_solvable_state():
    while True:
        board_list = list(range(9))
        random.shuffle(board_list)
        if is_board_solvable(board_list):
            return PuzzleState(tuple(board_list))


# --- 5. Hauptprogramm & Experimente (100 Läufe) ---
if __name__ == "__main__":
    goal_state = PuzzleState((1, 2, 3, 4, 5, 6, 7, 8, 0))
    number_of_runs = 100

    print(f"Generiere {number_of_runs} lösbare Startzustände...")
    start_states = [generate_random_solvable_state() for _ in range(number_of_runs)]
    
    # hier weise ich dem Dictionary heuristics die 2 Heuristischen Funktionen zu. 
    heuristics = {
        "Manhattan-Distanz": calculate_manhattan_distance,
        "Hamming-Distanz (Falsch positionierte Steine)": calculate_misplaced_tiles
    }

    # Ergebnisse speichern
    results = {name: {"comparisons": [], "expanded": [], "stored": []} for name in heuristics}

    print("Führe Experimente durch...")
    for heuristic_name, heuristic_func in heuristics.items():
        for start_state in start_states:
            # Frische Kopie des Startzustands für jeden Testlauf
            fresh_start = PuzzleState(start_state.board)
            outcome = solve_puzzle(fresh_start, goal_state, heuristic_func)
            
            if outcome["success"]:
                results[heuristic_name]["comparisons"].append(outcome["comparisons"])
                results[heuristic_name]["expanded"].append(outcome["expanded_nodes"])
                results[heuristic_name]["stored"].append(outcome["stored_nodes"])

    # --- 6. Auswertung (Mittelwert und Standardabweichung) ---
    print("\n" + "="*40)
    print(f" ERGEBNISSE DER EXPERIMENTE ({number_of_runs} Läufe)")
    print("="*40)
    
    for heuristic_name, measurements in results.items():
        print(f"\nHeuristik: {heuristic_name}")
        for measurement_name, values in measurements.items():
            mean_value = statistics.mean(values)
            std_deviation = statistics.stdev(values) if len(values) > 1 else 0.0
            print(f"  - {measurement_name.capitalize()}: Mittelwert = {mean_value:.2f} | Standardabweichung = {std_deviation:.2f}")
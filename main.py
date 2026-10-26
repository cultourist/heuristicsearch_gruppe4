"""8-Puzzle mit A*-Suche, Manhattan- und Hamming-Heuristik.

Die 100 Startzustaende sind bei jedem Programmstart neu zufaellig erzeugt.
Jedes Startpuzzle wird auf Loesbarkeit geprueft, und Duplikate werden entfernt.
Beide Heuristiken erhalten die gleichen 100 Startzustaende.
"""

import random  # Mischt die Zahlen fuer zufaellige Startzustaende.
import statistics  # Berechnet Mittelwert und Standardabweichung.
import heapq  # Stellt eine Priority Queue bereit.
import time  # Misst die tatsaechliche Programmlaufzeit.
import csv  # Schreibt die Messwerte in eine CSV-Datei.
import os  # Ermittelt den Speicherordner dieses Python-Skripts.

comparison_counter = 0  # Zaehlt die Objektvergleiche der Priority Queue.


# ============================================================
# 1. KLASSE FUER EINEN ZUSTAND DES PUZZLES
# ============================================================

class PuzzleState:  # Definiert die Eigenschaften und Methoden eines Spielzustands.

    def __init__(self, board_tuple, g_cost=0, parent=None):  # Erstellt einen neuen Spielzustand.
        self.board = board_tuple  # Speichert die neun Felder als Tuple.
        self.empty_index = self.board.index(0)  # Sucht die Position der Leerstelle.
        self.g_cost = g_cost  # Speichert die bisherigen Kosten vom Start.
        self.h_cost = 0  # Speichert spaeter den Heuristikwert.
        self.f_cost = 0  # Speichert spaeter die Summe aus g und h.
        self.parent = parent  # Verweist auf den vorherigen Zustand.

    def get_neighbor_states(self):  # Erzeugt alle Nachfolger durch genau einen Zug.
        neighbors = []  # Erstellt eine leere Liste fuer die Nachfolger.
        empty_row = self.empty_index // 3  # Berechnet die Zeile der Leerstelle.
        empty_column = self.empty_index % 3  # Berechnet die Spalte der Leerstelle.
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Oben, unten, links, rechts.

        for direction in directions:  # Prueft die vier Bewegungsrichtungen.
            row_change = direction[0]  # Liest die Aenderung der Zeile.
            column_change = direction[1]  # Liest die Aenderung der Spalte.
            new_row = empty_row + row_change  # Berechnet die neue Zeile.
            new_column = empty_column + column_change  # Berechnet die neue Spalte.

            if 0 <= new_row < 3 and 0 <= new_column < 3:  # Prueft die Grenzen des Feldes.
                new_empty_index = new_row * 3 + new_column  # Berechnet den neuen Index.
                board_list = list(self.board)  # Erstellt eine veraenderbare Kopie.
                moved_tile = board_list[new_empty_index]  # Liest den zu verschiebenden Stein.
                board_list[self.empty_index] = moved_tile  # Setzt diesen Stein auf die alte Leerstelle.
                board_list[new_empty_index] = 0  # Setzt die Leerstelle auf den neuen Platz.
                new_board = tuple(board_list)  # Wandelt das neue Spielfeld zurueck in ein Tuple.
                new_g_cost = self.g_cost + 1  # Erhoeht die Wegkosten um einen Zug.
                neighbor = PuzzleState(new_board, new_g_cost, self)  # Erstellt ein neues Objekt mit Vorgaenger.
                neighbors.append(neighbor)  # Speichert den Nachfolger in der Liste.

        return neighbors  # Gibt alle gueltigen Nachfolger zurueck.

    def __lt__(self, other):  # Vergleicht zwei Objekte fuer die Priority Queue.
        global comparison_counter  # Erlaubt das Aendern des globalen Vergleichszaehlers.
        comparison_counter = comparison_counter + 1  # Zaehlt einen weiteren Vergleich.

        if self.f_cost == other.f_cost:  # Prueft, ob beide Zustaende dieselben f-Kosten haben.
            return self.g_cost > other.g_cost  # Bevorzugt bei Gleichstand groessere g-Kosten.

        return self.f_cost < other.f_cost  # Sonst hat der kleinere f-Wert Vorrang.


# ============================================================
# 2. MANHATTAN-HEURISTIK
# ============================================================

def calculate_manhattan_distance(state_board, goal_board):  # Berechnet die Schaetzung der Restkosten.
    total_distance = 0  # Startet die Summe bei null.

    for index in range(9):  # Untersucht die neun Felder nacheinander.
        tile = state_board[index]  # Liest die Zahl am aktuellen Feld.

        if tile != 0:  # Ueberspringt die Leerstelle.
            current_row = index // 3  # Berechnet die aktuelle Zeile.
            current_column = index % 3  # Berechnet die aktuelle Spalte.
            goal_index = goal_board.index(tile)  # Sucht die richtige Position dieser Zahl.
            goal_row = goal_index // 3  # Berechnet die Zielzeile.
            goal_column = goal_index % 3  # Berechnet die Zielspalte.
            row_distance = abs(current_row - goal_row)  # Berechnet den Abstand der Zeilen.
            column_distance = abs(current_column - goal_column)  # Berechnet den Abstand der Spalten.
            tile_distance = row_distance + column_distance  # Berechnet den Abstand dieses Steins.
            total_distance = total_distance + tile_distance  # Addiert diesen Abstand zur Gesamtsumme.

    return total_distance  # Gibt die Manhattan-Distanz zurueck.


# ============================================================
# 3. HAMMING-HEURISTIK
# ============================================================

def calculate_misplaced_tiles(state_board, goal_board):  # Zaehlt falsch platzierte Steine.
    misplaced_count = 0  # Startet den Zaehler bei null.

    for index in range(9):  # Prueft jede Position des Spielfelds.
        tile = state_board[index]  # Liest den Stein an dieser Position.

        if tile != 0:  # Ueberspringt die Leerstelle.
            goal_tile = goal_board[index]  # Liest den Stein an der richtigen Zielposition.

            if tile != goal_tile:  # Prueft, ob die beiden Steine unterschiedlich sind.
                misplaced_count = misplaced_count + 1  # Zaehlt einen falsch platzierten Stein.

    return misplaced_count  # Gibt die Anzahl falsch platzierter Steine zurueck.


# ============================================================
# 4. LOESBARKEIT DURCH INVERSIONEN PRUEFEN
# ============================================================

def is_board_solvable(board):  # Gilt fuer das 3x3-Ziel (0,1,2,3,4,5,6,7,8).
    numbers = []  # Speichert alle Zahlen ohne die Leerstelle.

    for tile in board:  # Geht die neun Werte durch.
        if tile != 0:  # Ignoriert den Wert null.
            numbers.append(tile)  # Fuegt eine Zahl zur Liste hinzu.

    inversion_count = 0  # Beginnt die Zahl der Inversionen bei null.

    for left_index in range(len(numbers)):  # Waehlt eine linke Zahl aus.
        for right_index in range(left_index + 1, len(numbers)):  # Waehlt jede rechts davon stehende Zahl aus.
            if numbers[left_index] > numbers[right_index]:  # Prueft, ob die linke Zahl groesser ist als die rechte (= Inversion)
                inversion_count = inversion_count + 1  # Zaehlt die Inversion.

    is_even = (inversion_count % 2 == 0)  # Prueft, ob die Zahl der Inversionen gerade ist.
    return is_even  # Gibt True fuer ein loesbares Puzzle zurueck.


# ============================================================
# 5. ZUFAELLIGEN, LOESBAREN STARTZUSTAND ERZEUGEN
# ============================================================

def generate_random_solvable_state():  # Liefert ein neues PuzzleState-Objekt.
    while True:  # Wiederholt den Versuch, bis das Puzzle loesbar ist.
        board_list = list(range(9))  # Erzeugt eine Liste mit den Zahlen 0 bis 8.
        random.shuffle(board_list)  # Mischt die Zahlen neu.

        if is_board_solvable(board_list):  # Laesst nur loesbare Anordnungen zu.
            new_board = tuple(board_list)  # Wandelt die Liste in ein Tuple um.
            new_state = PuzzleState(new_board)  # Erstellt einen neuen Puzzle-Zustand.
            return new_state  # Gibt den loesbaren Zustand zurueck.


# ============================================================
# 6. A*-SUCHALGORITHMUS
# ============================================================

def solve_puzzle(start_state, goal_state, heuristic_function):  # Findet den kuerzesten Weg zum Ziel.
    global comparison_counter  # Greift auf den globalen Vergleichszaehler zu.
    comparison_counter = 0  # Setzt den Vergleichszaehler fuer diesen Lauf zurueck.
    start_state.h_cost = heuristic_function(start_state.board, goal_state.board)  # Bewertet den Startzustand.
    start_state.f_cost = start_state.g_cost + start_state.h_cost  # Berechnet f = g + h.
    open_priority_queue = []  # Erstellt die Liste offener Suchknoten.
    heapq.heappush(open_priority_queue, start_state)  # Fuegt den Startknoten in den Heap ein.
    visited_boards = set()  # Merkt sich bereits vollstaendig bearbeitete Spielfelder.
    best_g_cost = {}  # Merkt sich die besten bekannten Wegkosten je Spielfeld.
    best_g_cost[start_state.board] = start_state.g_cost  # Speichert die Wegkosten des Starts.
    expanded_nodes_count = 0  # Zaehlt die expandierten Knoten.
    max_stored_entries = 1  # Speichert die groesste Summe aus Queue und besuchten Boards.

    while len(open_priority_queue) > 0:  # Laeuft, solange noch offene Knoten existieren.
        current_state = heapq.heappop(open_priority_queue)  # Holt den Knoten mit dem kleinsten f-Wert.

        if current_state.board in visited_boards:  # Prueft, ob der Knoten bereits bearbeitet wurde.
            continue  # Ueberspringt diesen doppelten Heap-Eintrag.

        known_g_cost = best_g_cost[current_state.board]  # Liest die aktuell besten Wegkosten.

        if current_state.g_cost != known_g_cost:  # Prueft, ob dieser Heap-Eintrag veraltet ist.
            continue  # Ignoriert den veralteten Eintrag.

        if current_state.board == goal_state.board:  # Prueft, ob das Ziel erreicht wurde.
            result = {}  # Erstellt das Ergebnis-Dictionary.
            result["success"] = True  # Meldet eine erfolgreiche Suche.
            result["comparisons"] = comparison_counter  # Speichert die Heap-Vergleiche.
            result["expanded_nodes"] = expanded_nodes_count  # Speichert expandierte Knoten.
            result["stored_entries"] = max_stored_entries  # Speichert die grobe Speicherkennzahl.
            result["final_state"] = current_state  # Speichert das Zielobjekt mit seiner parent-Kette.
            return result  # Gibt das Ergebnis zurueck.

        visited_boards.add(current_state.board)  # Markiert den Zustand als abschliessend bearbeitet.
        expanded_nodes_count = expanded_nodes_count + 1  # Erhoeht den Expansionszaehler.
        neighbors = current_state.get_neighbor_states()  # Erzeugt alle gueltigen Nachfolger.

        for neighbor in neighbors:  # Untersucht die neuen Nachfolger nacheinander.
            if neighbor.board in visited_boards:  # Prueft, ob dieser Nachfolger bereits erledigt ist.
                continue  # Ueberspringt ihn dann.

            if neighbor.board in best_g_cost:  # Prueft, ob die Anordnung bereits bekannt ist.
                previous_g_cost = best_g_cost[neighbor.board]  # Liest die bisher besten Wegkosten.

                if neighbor.g_cost >= previous_g_cost:  # Prueft, ob der neue Weg nicht besser ist.
                    continue  # Ueberspringt schlechtere oder gleich gute Wege.

            best_g_cost[neighbor.board] = neighbor.g_cost  # Speichert die neuen besten Wegkosten.
            neighbor.h_cost = heuristic_function(neighbor.board, goal_state.board)  # Berechnet die Heuristik.
            neighbor.f_cost = neighbor.g_cost + neighbor.h_cost  # Berechnet den f-Wert.
            heapq.heappush(open_priority_queue, neighbor)  # Fuegt den Nachfolger in den Heap ein.
            stored_entries = len(open_priority_queue) + len(visited_boards)  # Berechnet die Anzahl Eintraege.

            if stored_entries > max_stored_entries:  # Prueft, ob ein neuer Hoechstwert erreicht ist.
                max_stored_entries = stored_entries  # Speichert das neue Maximum.

    result = {}  # Erstellt das Ergebnis bei einer erfolglosen Suche.
    result["success"] = False  # Meldet, dass kein Ziel gefunden wurde.
    result["comparisons"] = comparison_counter  # Speichert die Zahl der Vergleiche.
    result["expanded_nodes"] = expanded_nodes_count  # Speichert die Zahl der Expansionen.
    result["stored_entries"] = max_stored_entries  # Speichert die grobe Speicherkennzahl.
    result["final_state"] = None  # Ohne Ziel existiert kein Loesungspfad.
    return result  # Gibt das erfolglose Ergebnis zurueck.


# ============================================================
# 7. LOESUNGSWEG REKONSTRUIEREN UND AUSGEBEN
# ============================================================

def reconstruct_solution_path(final_state):  # Erstellt eine Liste vom Start bis zum Ziel.
    path = []  # Erstellt eine leere Liste fuer den Pfad.
    current_state = final_state  # Beginnt beim gefundenen Zielzustand.

    while current_state is not None:  # Geht bis zum Startknoten zurueck.
        path.append(current_state)  # Speichert das aktuelle Objekt.
        current_state = current_state.parent  # Folgt dem Verweis auf den Vorgaenger.

    path.reverse()  # Dreht die Reihenfolge auf Start bis Ziel um.
    return path  # Gibt alle Zustaende des Loesungswegs zurueck.


def print_solution_path(final_state):  # Zeigt den Pfad als 3x3-Spielbretter an.
    path = reconstruct_solution_path(final_state)  # Holt den vollstaendigen Loesungsweg.
    number_of_moves = len(path) - 1  # Ermittelt die Anzahl der Bewegungen.
    print("\nLoesungspfad:", number_of_moves, "Bewegungen")  # Gibt die Pfadlaenge aus.

    for step_number in range(len(path)):  # Geht den Loesungsweg Schritt fuer Schritt durch.
        current_state = path[step_number]  # Holt den aktuellen Spielzustand.
        print("Schritt", step_number)  # Gibt die Nummer des Schritts aus.

        for row in range(3):  # Geht die drei Zeilen durch.
            line = ""  # Beginnt mit einer leeren Ausgabezeile.

            for column in range(3):  # Geht die drei Spalten durch.
                index = row * 3 + column  # Berechnet die Position im Tuple.
                tile = current_state.board[index]  # Liest den Stein an der Position.

                if tile == 0:  # Prueft, ob diese Position leer ist.
                    tile_text = " "  # Zeigt die Leerstelle als Leerzeichen.
                else:  # Fuer alle nummerierten Steine.
                    tile_text = str(tile)  # Wandelt die Zahl in Text um.

                if column == 0:  # Bei der ersten Spalte ist kein Trenner notwendig.
                    line = tile_text  # Beginnt den Text der Zeile.
                else:  # Fuer die zweite und dritte Spalte.
                    line = line + " | " + tile_text  # Fuegt den Stein mit Trenner hinzu.

            print(line)  # Gibt die aktuelle Zeile aus.

        print("---------")  # Trennt die Puzzle-Schritte voneinander.


# ============================================================
# 8. MESSWERTE VORBEREITEN, AUSWERTEN UND SPEICHERN
# ============================================================

def create_result_lists():  # Erzeugt leere Listen fuer die Messgroessen.
    measurements = {}  # Erstellt ein leeres Dictionary.
    measurements["runtime_seconds"] = []  # Hier speichern wir Laufzeiten in Sekunden.
    measurements["expanded_nodes"] = []  # Hier speichern wir expandierte Knoten.
    measurements["stored_entries"] = []  # Hier speichern wir die grobe Speicherkennzahl.
    measurements["comparisons"] = []  # Hier speichern wir Heap-Vergleiche.
    measurements["moves"] = []  # Hier speichern wir die Anzahl der Loesungsschritte.
    return measurements  # Gibt das Dictionary zurueck.


def print_statistics(results):  # Berechnet Mittelwert und Standardabweichung.
    print("\nERGEBNISSE: 100 Startzustaende je Heuristik")  # Gibt die Tabellenueberschrift aus.

    for heuristic_name in results:  # Geht alle Heuristiken durch.
        print("\nHeuristik:", heuristic_name)  # Gibt den Namen der Heuristik aus.
        measurements = results[heuristic_name]  # Holt die zugehoerigen Messwerte.

        for metric_name in measurements:  # Untersucht jede Messgroesse.
            values = measurements[metric_name]  # Holt die Liste der Messwerte.

            if len(values) == 0:  # Prueft, ob Messwerte vorhanden sind.
                print(metric_name, ": keine Messwerte")  # Meldet eine leere Liste.
                continue  # Geht zur naechsten Messgroesse.

            mean_value = statistics.mean(values)  # Berechnet den Mittelwert.

            if len(values) > 1:  # Prueft, ob genug Werte fuer eine Standardabweichung existieren.
                standard_deviation = statistics.stdev(values)  # Berechnet die Stichproben-Standardabweichung.
            else:  # Sonderfall mit nur einem Messwert.
                standard_deviation = 0.0  # Nutzt dann null als Anzeige.

            print(metric_name, "Mittelwert:", round(mean_value, 6), "Std:", round(standard_deviation, 6))  # Gibt die Werte aus.


def save_measurements_csv(rows, filename):  # Speichert die einzelnen Suchlaeufe als CSV.
    with open(filename, "w", newline="", encoding="utf-8") as file:  # Oeffnet die CSV-Datei zum Schreiben.
        writer = csv.writer(file, delimiter=";")  # Erstellt den CSV-Schreiber mit Semikolon.
        writer.writerow(["heuristic", "run", "start_board", "runtime_seconds", "expanded_nodes", "stored_entries", "comparisons", "moves", "success"])  # Schreibt die Ueberschriften.

        for row in rows:  # Geht alle Messdatensaetze durch.
            writer.writerow(row)  # Schreibt einen Datensatz pro Zeile.


# ============================================================
# 9. HAUPTPROGRAMM
# ============================================================

def main():  # Steuert die Erzeugung, die Suche und die statistische Auswertung.

    # Kein fester Seed: Bei jedem Programmstart entstehen neue zufaellige Startzustaende.

    goal_board = (0, 1, 2, 3, 4, 5, 6, 7, 8)  # Legt die Zielanordnung fest.
    goal_state = PuzzleState(goal_board)  # Erstellt das Zielobjekt.
    number_of_runs = 100  # Legt die Anzahl der Testpuzzles pro Heuristik fest.
    start_states = []  # Hier sammeln wir alle 100 zufaelligen Startzustaende.
    known_boards = set()  # Diese Menge verhindert doppelte Startanordnungen.

    # --------------------------------------------------------
    # 9.1 ZUFAELLIGE STARTZUSTAENDE ERZEUGEN
    # --------------------------------------------------------

    while len(start_states) < number_of_runs:  # Laeuft bis 100 verschiedene Puzzles vorhanden sind.
        random_state = generate_random_solvable_state()  # Erzeugt ein zufaelliges, loesbares Puzzle.

        if random_state.board not in known_boards:  # Prueft, ob die Anordnung neu ist.
            known_boards.add(random_state.board)  # Merkt sich die Anordnung als bereits verwendet.
            start_states.append(random_state)  # Fuegt sie zu den 100 Startzustaenden hinzu.

    print("Erzeugte unterschiedliche, loesbare Startzustaende:", len(start_states))  # Kontrolliert die Anzahl.
    print("Erstes zufaelliges Puzzle:", start_states[0].board)  # Zeigt die erste Startanordnung.

    # --------------------------------------------------------
    # 9.2 HEURISTIKEN UND ERGEBNISSE VORBEREITEN
    # --------------------------------------------------------

    heuristics = {}  # Erstellt die Zuordnung von Namen zu Funktionen.
    heuristics["Manhattan"] = calculate_manhattan_distance  # Verwendet die Manhattan-Funktion.
    heuristics["Hamming"] = calculate_misplaced_tiles  # Verwendet die Hamming-Funktion.
    results = {}  # Speichert die Statistikwerte fuer beide Heuristiken.
    csv_rows = []  # Sammelt alle 200 Einzelmessungen fuer die CSV-Datei.
    solution_lengths = {}  # Speichert die Loesungslaengen zum Vergleich beider Heuristiken.

    # --------------------------------------------------------
    # 9.3 DIE 100 TESTS PRO HEURISTIK AUSFUEHREN
    # --------------------------------------------------------

    for heuristic_name in heuristics:  # Testet nacheinander Manhattan und Hamming.
        heuristic_function = heuristics[heuristic_name]  # Holt die aktuelle Bewertungsfunktion.
        results[heuristic_name] = create_result_lists()  # Erstellt leere Listen fuer die Ergebnisse.
        run_number = 0  # Setzt die Nummer des Versuchs zurueck.
        print("\nStarte Heuristik:", heuristic_name)  # Meldet die aktuelle Heuristik.

        for original_start in start_states:  # Testet bei beiden Heuristiken dieselben 100 Puzzles.
            run_number = run_number + 1  # Zaehlt den aktuellen Versuch.
            fresh_start = PuzzleState(original_start.board)  # Erstellt ein neues Objekt fuer die Suche.
            start_time = time.perf_counter()  # Beginnt die Laufzeitmessung.
            outcome = solve_puzzle(fresh_start, goal_state, heuristic_function)  # Fuehrt A* aus.
            end_time = time.perf_counter()  # Beendet die Laufzeitmessung.
            runtime_seconds = end_time - start_time  # Berechnet die verstrichene Zeit.

            if not outcome["success"]:  # Ein loesbares Puzzle muss gefunden werden.
                raise RuntimeError("Ein loesbares Puzzle wurde nicht geloest.")  # Meldet einen Suchfehler.

            final_state = outcome["final_state"]  # Holt das gefundene Zielobjekt.
            number_of_moves = final_state.g_cost  # Liest die Anzahl der Loesungsschritte.

            if heuristic_name == "Manhattan":  # Speichert die Loesungslaenge aus dem ersten Testblock.
                solution_lengths[original_start.board] = number_of_moves  # Merkt sich die optimale Zugzahl.
            else:  # Prueft die Loesungslaenge des zweiten Testblocks.
                expected_moves = solution_lengths[original_start.board]  # Holt die gespeicherte Manhattan-Zugzahl.

                if number_of_moves != expected_moves:  # Vergleicht die beiden Loesungslaengen.
                    raise RuntimeError("Die Heuristiken liefern unterschiedliche Loesungslaengen.")  # Meldet einen Fehler.

            measurements = results[heuristic_name]  # Holt die Listen fuer die aktuelle Heuristik.
            measurements["runtime_seconds"].append(runtime_seconds)  # Speichert die Laufzeit.
            measurements["expanded_nodes"].append(outcome["expanded_nodes"])  # Speichert Expansionen.
            measurements["stored_entries"].append(outcome["stored_entries"])  # Speichert die Eintragszahl.
            measurements["comparisons"].append(outcome["comparisons"])  # Speichert Heap-Vergleiche.
            measurements["moves"].append(number_of_moves)  # Speichert die Loesungslaenge.

            csv_row = [heuristic_name, run_number, str(original_start.board), runtime_seconds, outcome["expanded_nodes"], outcome["stored_entries"], outcome["comparisons"], number_of_moves, True]  # Erstellt einen CSV-Datensatz.
            csv_rows.append(csv_row)  # Fuegt den Datensatz zur Exportliste hinzu.

            if run_number % 10 == 0:  # Prueft, ob zehn weitere Versuche fertig sind.
                print("Fertig:", run_number, "von", number_of_runs, "mit", heuristic_name)  # Zeigt den Fortschritt.

    # --------------------------------------------------------
    # 9.4 STATISTIK BERECHNEN UND CSV SPEICHERN
    # --------------------------------------------------------

    print_statistics(results)  # Berechnet und zeigt die statistischen Ergebnisse.

    script_folder = os.path.dirname(os.path.abspath(__file__))  # Findet den Ordner der Python-Datei.
    csv_filename = os.path.join(script_folder, "8puzzle_messwerte.csv")  # Legt die CSV neben dem Skript ab.
    save_measurements_csv(csv_rows, csv_filename)  # Erstellt die CSV-Datei mit den 200 Messungen.
    print("\nEinzelmessungen:", csv_filename)  # Zeigt den vollstaendigen Speicherpfad an.

    # --------------------------------------------------------
    # 9.5 EINEN ZUFAELLIGEN LOESUNGSWEG ANZEIGEN
    # --------------------------------------------------------

    example_board = start_states[0].board  # Zeigt den Loesungsweg exemplarisch am ersten der zufaelligen Startzustaende.
    example_start = PuzzleState(example_board)  # Erstellt ein frisches Objekt fuer die Ausgabe.
    print("\nZufaelliger Startzustand fuer den angezeigten Loesungsweg:", example_board)  # Zeigt das Start-Tuple.
    example_result = solve_puzzle(example_start, goal_state, calculate_manhattan_distance)  # Loest dieses Puzzle mit A*.

    if example_result["success"]:  # Prueft, ob die Beispielsuche erfolgreich war.
        print_solution_path(example_result["final_state"])  # Zeigt alle Schritte von Start bis Ziel.


# ============================================================
# 10. PROGRAMMSTART
# ============================================================

if __name__ == "__main__":  # Prueft, ob das Skript direkt gestartet wird.
    main()  # Startet das komplette 8-Puzzle-Experiment.
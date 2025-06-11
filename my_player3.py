import random
import sys
import time
from copy import deepcopy

from host import GO
from read import readInput
from write import writeOutput


class ABPruning:
    def __init__(self, max_dep=3):
        self.type = "ABPruning"
        self.max_dep = max_dep
        self.first_move = False
        self.max_time = 9

    def saver(self, go, i, j, piece_type):
        value = 0
        temp = go.copy_board()
        temp.place_chess(i, j, piece_type)
        visit = set()
        for x in range(5):
            for y in range(5):
                if temp.board[x][y] == piece_type and (x, y) not in visit:
                    visit.update(temp.ally_dfs(x, y))
                    lib = self.count_lib(temp, temp.ally_dfs(x, y))
                    if lib == 1:
                        value = value + 15
                    elif lib == 2:
                        value = value + 8
        return value

    def score_list(self, go, placement, piece_type):
        p_value = []
        for place in placement:
            value = 0
            temp = go.copy_board()
            temp.place_chess(place[0], place[1], piece_type)
            died_pieces = temp.find_died_pieces(3 - piece_type)
            num_died = len(died_pieces)
            value = value + num_died * 5

            if place[0] == 2 and place[1] == 2:
                value = value + 20
            elif (
                (place[0] == 2 and place[1] == 1)
                or (place[0] == 1 and place[1] == 2)
                or (place[0] == 2 and place[1] == 3)
                or (place[0] == 3 and place[1] == 2)
            ):
                value = value + 8
            elif (place[0] == 1 or place[0] == go.size - 2) and (
                place[1] == 1 or place[1] == go.size - 2
            ):
                value = value + 3

            lib_kill = self.total_lib(go, (3 - piece_type)) - self.total_lib(
                temp, (3 - piece_type)
            )
            if lib_kill > 0:
                value = value + lib_kill * 5

            ngh = go.detect_neighbor(place[0], place[1])
            adj_opp = 0
            for neighbot in ngh:
                if go.board[neighbot[0]][neighbot[1]] == (3 - piece_type):
                    adj_opp = adj_opp + 1
            value = value + adj_opp * 3

            connection = temp.ally_dfs(place[0], place[1])
            connection_v = len(connection) - 1
            value = value + connection_v * 5

            eye = self.eye_eval(go, place[0], place[1], piece_type)
            value = value + eye * 7

            d = self.def_eval(go, place[0], place[1], piece_type)
            value = value + d * 6
            save = self.saver(go, place[0], place[1], piece_type)
            value = value + save
            cut = self.cutting(go, place[0], place[1], piece_type)
            value = value + cut

            temp.remove_died_pieces(3 - piece_type)
            ally_members = temp.ally_dfs(place[0], place[1])
            lib = self.count_lib(go, ally_members)
            value = value + lib
            p_value.append((place, value))
        p_value.sort(key=lambda x: x[1], reverse=True)
        result = []
        for p in p_value:
            result.append(p[0])
        return result

    def cutting(self, go, i, j, piece_type):
        value = 0
        bb = go.copy_board()
        opp = 0
        visit = set()
        for x in range(5):
            for y in range(5):
                if bb.board[x][y] == (3 - piece_type) and (x, y) not in visit:
                    visit.update(bb.ally_dfs(x, y))
                    opp = opp + 1
        ab = go.copy_board()
        ab.place_chess(i, j, piece_type)
        opp_a = 0
        visit = set()
        for x in range(5):
            for y in range(5):
                if ab.board[x][y] == (3 - piece_type) and (x, y) not in visit:
                    visit.update(ab.ally_dfs(x, y))
                    opp_a = opp_a + 1
        if opp_a > opp:
            value = value + 10 * (opp_a - opp)
        return value

    def terminal_state(self, go):
        if go.game_end(1) or go.game_end(2):
            return True
        if go.previous_board:
            is_same = True
            for i in range(go.size):
                for j in range(go.size):
                    if go.previous_board[i][j] != go.board[i][j]:
                        is_same = False
                        break
                if not is_same:
                    break
            if is_same:
                return True
        return False

    def max_value(self, go, alpha, beta, piece_type, depth, start):
        if (
            self.terminal_state(go)
            or depth >= self.max_dep
            or ((time.time() - start) > self.max_time)
        ):
            return self.util(go, piece_type)
        v = float("-inf")
        placement = []
        for i in range(5):
            for j in range(5):
                if go.valid_place_check(i, j, piece_type, test_check=True):
                    placement.append((i, j))
        if not placement:
            temp = go.copy_board()
            temp.previous_board = deepcopy(temp.board)
            return self.min_value(temp, alpha, beta, piece_type, depth + 1, start)
        for p in placement:
            temp = go.copy_board()
            temp.place_chess(p[0], p[1], piece_type)
            temp.remove_died_pieces(3 - piece_type)
            v = max(v, self.min_value(temp, alpha, beta, piece_type, depth + 1, start))
            if v >= beta:
                return v
            alpha = max(alpha, v)
        return v

    def min_value(self, go, alpha, beta, piece_type, depth, start):
        if self.terminal_state(go) or ((time.time() - start) > self.max_time):
            return self.util(go, piece_type)
        v = float("inf")
        placement = []
        for i in range(5):
            for j in range(5):
                if go.valid_place_check(i, j, 3 - piece_type, test_check=True):
                    placement.append((i, j))
        if not placement:
            temp = go.copy_board()
            temp.previous_board = deepcopy(temp.board)
            return self.max_value(temp, alpha, beta, piece_type, depth + 1, start)
        for p in placement:
            temp = go.copy_board()
            temp.place_chess(p[0], p[1], 3 - piece_type)
            temp.remove_died_pieces(piece_type)
            v = min(v, self.max_value(temp, alpha, beta, piece_type, depth + 1, start))
            if v <= alpha:
                return v
            beta = min(beta, v)
        return v

    def fill_terr(self, go, i, j, piece_type, visit):
        q = [(i, j)]
        area = []
        a_border = set()
        while q:
            x, y = q.pop(0)
            if (x, y) in visit:
                continue
            visit.add((x, y))
            if go.board[x][y] == 0:
                area.append((x, y))
                neighbor = go.detect_neighbor(x, y)
                for a, b in neighbor:
                    if go.board[a][b] == 0 and (a, b) not in visit:
                        q.append((a, b))
                    elif go.board[a][b] != 0:
                        a_border.add((a, b))
        is_terr = True
        for x, y in a_border:
            if go.board[x][y] != piece_type:
                is_terr = False
                break
        result = (len(area), is_terr)
        return result

    def est_terr(self, go, piece_type):
        terr = 0
        visit = set()
        for i in range(5):
            for j in range(5):
                if go.board[i][j] == 0 and (i, j) not in visit:
                    a, is_terr = self.fill_terr(go, i, j, piece_type, visit)
                    if is_terr:
                        terr = terr + a
        return terr

    def util(self, go, piece_type):
        m = go.score(piece_type)
        o = go.score(3 - piece_type)

        m_terr = self.est_terr(go, piece_type)
        o_terr = self.est_terr(go, 3 - piece_type)

        m_lib = self.total_lib(go, piece_type)
        o_lib = self.total_lib(go, 3 - piece_type)

        m_connection = self.connect_stone(go, piece_type)

        value = (m - o) * 10
        value = value + (m_terr - o_terr) * 5
        value = value + (m_lib - o_lib) * 2

        value = value - m_connection[0] * 3
        value = value + m_connection[1] * 4
        return value

    def count_lib(self, go, ally):
        count = 0
        for a in ally:
            neighbor = go.detect_neighbor(a[0], a[1])
            for n in neighbor:
                if go.board[n[0]][n[1]] == 0:
                    count = count + 1
        return count

    def eval_center(self, go, piece_type):
        b = go.board
        center = [
            (1, 1),
            (1, 2),
            (1, 3),
            (2, 1),
            (2, 2),
            (2, 3),
            (3, 1),
            (3, 2),
            (3, 3),
        ]
        adj_pos = [(1, 2), (3, 2), (2, 1), (2, 3)]
        my = 0
        op = 0
        for pos in center:
            if b[pos[0]][pos[1]] == piece_type:
                if pos == (2, 2):
                    my = my + 3
                else:
                    my = my + 1
            elif b[pos[0]][pos[1]] == (3 - piece_type):
                if pos == (2, 2):
                    op = op + 3
                else:
                    op = op + 1
        if b[2][2] == piece_type:
            adj = 0
            for pos in adj_pos:
                if b[pos[0]][pos[1]] == piece_type:
                    adj = adj + 1
            if adj >= 2:
                my = my + 3
            elif adj == 1:
                my = my + 1
        if b[2][2] == (3 - piece_type):
            adj = 0
            for pos in adj_pos:
                if b[pos[0]][pos[1]] == (3 - piece_type):
                    adj = adj + 1
            if adj >= 2:
                op = op + 3
            elif adj == 1:
                op = op + 1
        diff = my - op
        return diff

    def connect_stone(self, go, piece_type):
        visit = set()
        connecting = []
        for i in range(5):
            for j in range(5):
                if go.board[i][j] == piece_type and (i, j) not in visit:
                    connect = go.ally_dfs(i, j)
                    visit.update(connect)
                    connecting.append(connect)
        if not connecting:
            return (0, 0)
        total = 0
        num_connect = len(connecting)

        for c in connecting:
            c_size = len(c)
            total = total + c_size

        if num_connect > 0:
            avg_size = total / num_connect
        else:
            avg_size = 0
        result = (num_connect, avg_size)
        return result

    def total_lib(self, go, piece_type):
        visit = set()
        total = 0
        for i in range(5):
            for j in range(5):
                if go.board[i][j] == piece_type and (i, j) not in visit:
                    ally = go.ally_dfs(i, j)
                    visit.update(ally)
                    lib = self.count_lib(go, ally)
                    total = total + lib
        return total

    def eye_eval(self, go, i, j, piece_type):
        value = 0
        if (
            (i == 2 and j == 1)
            or (i == 1 and j == 2)
            or (i == 2 and j == 3)
            or (i == 3 and j == 2)
        ):
            value = value + 3
        elif (i == 1 or i == 3) and (j == 1 or j == 3):
            value = value + 2
        elif i == 0 or i == 4 or j == 0 or j == 4:
            value = value + 1
        if (i == 0 or i == 4) and (j == 0 or j == 4):
            value = value - 1
        temp = go.copy_board()
        temp.place_chess(i, j, piece_type)

        eye = self.eye_pattern(temp.board, piece_type)

        for pattern in eye:
            if pattern[0] == "mouth":
                value = value + 10
            elif pattern[0] == "t_space":
                value = value + 7.0
            elif pattern[0] == "diagonal":
                value = value + 3.5
            elif pattern[0] == "l_space":
                value = value + 5.0
        connected = temp.ally_dfs(i, j)
        potential = set()

        for a, b in connected:
            neighbor = temp.detect_neighbor(a, b)
            for x, y in neighbor:
                if temp.board[x][y] == 0:
                    potential.add((x, y))
        for pos in potential:
            eye_neighbor = temp.detect_neighbor(pos[0], pos[1])
            ally_ngh = 0
            opp_ngh = 0
            for x, y in eye_neighbor:
                if temp.board[x][y] == piece_type:
                    ally_ngh = ally_ngh + 1
                elif temp.board[x][y] == 3 - piece_type:
                    opp_ngh = opp_ngh + 1
            if ally_ngh == len(potential):
                value = value + 3
            elif ally_ngh >= len(potential) - 1 and opp_ngh == 0:
                value = value + 2
            elif ally_ngh > opp_ngh:
                value = value + (ally_ngh - opp_ngh) / 2
        return value

    def on(self, i, j):
        return 0 <= i < 5 and 0 <= j < 5

    def eye_pattern(self, board, piece_type):
        result = []
        emp = 0
        for y in range(5):
            for x in range(5):
                if (
                    self.on(x - 1, y)
                    and self.on(x + 1, y)
                    and self.on(x, y - 1)
                    and self.on(x, y + 1)
                ):
                    if (
                        board[y][x] == emp
                        and board[y - 1][x] == piece_type
                        and board[y + 1][x] == piece_type
                        and board[y][x - 1] == piece_type
                        and board[y][x + 1] == piece_type
                    ):
                        result.append(("mouth", (x, y)))
                l_shape = [
                    [(0, 0), (1, 0), (0, 1)],
                    [(0, 0), (-1, 0), (0, 1)],
                    [(0, 0), (0, -1), (1, 0)],
                    [(0, 0), (0, -1), (-1, 0)],
                ]
                for s in l_shape:
                    valid = True
                    emp_count = 0
                    p_count = 0
                    for pos in s:
                        a, b = x + pos[0], y + pos[1]
                        if not self.on(a, b):
                            valid = False
                            break
                        if board[a][b] == emp:
                            emp_count = emp_count + 1
                        elif (board[a][b]) == piece_type:
                            p_count = p_count + 1

                    if valid and emp_count == 2 and p_count == 1:
                        result.append(("l_shape", (x, y)))

                diag = [
                    [(0, 0), (1, 1)],
                    [(0, 0), (-1, 1)],
                    [(0, 0), (1, -1)],
                    [(0, 0), (-1, -1)],
                ]

                for d in diag:
                    pos1, pos2 = d
                    x1, y1 = x + pos1[0], y + pos1[1]
                    x2, y2 = x + pos2[0], y + pos2[1]
                    if self.on(x1, y1) and self.on(x2, y2):
                        if board[y1][x1] == emp and board[y2][x2] == emp:
                            surrounding = 0
                            for a, b in [(x1, y2), (x2, y1)]:
                                if self.on(a, b) and board[a][b] == piece_type:
                                    surrounding = surrounding + 1
                            if surrounding > 0:
                                result.append(("diagonal", (x, y)))
                if self.on(x + 1, y) and board[y][x] == emp and board[y][x + 1] == emp:
                    surrounding = []
                    surrounding_pos = [
                        (x - 1, y),
                        (x + 2, y),
                        (x, y - 1),
                        (x, y + 1),
                        (x + 1, y - 1),
                        (x + 1, y + 1),
                    ]
                    for pos in surrounding_pos:
                        a, b = pos
                        if self.on(a, b):
                            surrounding.append(board[a][b])
                    if surrounding.count(piece_type) >= 3:
                        result.append(("t_space", (x, y)))
                if self.on(x, y + 1) and board[y][x] == emp and board[y + 1][x] == emp:
                    surrounding = []
                    surrounding_pos = [
                        (x, y - 1),
                        (x, y + 2),
                        (x - 1, y),
                        (x + 1, y),
                        (x - 1, y + 1),
                        (x + 1, y + 1),
                    ]
                    for pos in surrounding_pos:
                        a, b = pos
                        if self.on(a, b):
                            surrounding.append(board[a][b])
                    if surrounding.count(piece_type) >= 3:
                        result.append(("t_space", (x, y)))
        return result

    def def_eval(self, go, i, j, piece_type):
        value = 0
        temp = go.copy_board()
        opp_eye = self.eye_pattern(temp.board, 3 - piece_type)
        opp_eye_pos = {}
        for pattern, pos in opp_eye:
            opp_eye_pos[pos] = pattern
        after = go.copy_board()
        after.place_chess(i, j, piece_type)
        a_eye = self.eye_pattern(after.board, 3 - piece_type)
        a_eye_pos = {}
        for pattern, pos in a_eye:
            a_eye_pos[pos] = pattern
        for pos, pattern in opp_eye_pos.items():
            if pos not in a_eye_pos:
                if pattern == "t_shape":
                    value = value + 4
                elif pattern == "diagonal":
                    value = value + 2
                elif pattern == "l_space":
                    value = value + 7
        go_cut = go.copy_board()
        b_opp = 0
        visit = set()
        for a in range(5):
            for b in range(5):
                if go_cut.board[a][b] == (3 - piece_type) and (a, b) not in visit:
                    our = go_cut.ally_dfs(a, b)
                    visit.update(our)
                    b_opp = b_opp + 1
        go_cut.place_chess(i, j, piece_type)

        a_opp = 0
        visit = set()
        for a in range(5):
            for b in range(5):
                if go_cut.board[a][b] == (3 - piece_type) and (a, b) not in visit:
                    our = go_cut.ally_dfs(a, b)
                    visit.update(our)
                    a_opp = a_opp + 1
        if a_opp > b_opp:
            value = value + 3 * (a_opp - b_opp)
        return value

    def get_input(self, go, piece_type):
        """
        Get one input.

        :param go: Go instance.
        :param piece_type: 1('X') or 2('O').
        :return: (row, column) coordinate of input.
        """
        start = time.time()
        if not self.first_move:
            if piece_type == 1:
                if go.valid_place_check(2, 2, piece_type, test_check=True):
                    self.first_move = True
                    return (2, 2)
            else:
                if go.board[2][2] != 0:
                    adj = [(1, 2), (3, 2), (2, 1), (2, 3)]
                    for pos in adj:
                        if go.valid_place_check(
                            pos[0], pos[1], piece_type, test_check=True
                        ):
                            self.first_move = True
                            return pos
                else:
                    if go.valid_place_check(2, 2, piece_type, test_check=True):
                        self.first_move = True
                        return (2, 2)

        possible_placements = []
        for i in range(go.size):
            for j in range(go.size):
                if go.valid_place_check(i, j, piece_type, test_check=True):
                    possible_placements.append((i, j))

        if not possible_placements:
            return "PASS"
        if len(possible_placements) == 1:
            return possible_placements[0]
        best_m = None
        best_v = float("-inf")
        alpha = float("-inf")
        beta = float("inf")
        possible_placements = self.score_list(go, possible_placements, piece_type)
        for p in possible_placements:
            if (time.time() - start) > self.max_time:
                break
            temp = go.copy_board()
            temp.place_chess(p[0], p[1], piece_type)
            temp.remove_died_pieces(3 - piece_type)
            v = self.min_value(temp, alpha, beta, piece_type, 1, start)
            if v > best_v:
                best_v = v
                best_m = p
            alpha = max(alpha, best_v)
        if best_m:
            return best_m
        else:
            return random.choice(possible_placements)


if __name__ == "__main__":
    N = 5
    piece_type, previous_board, board = readInput(N)
    go = GO(N)
    go.set_board(piece_type, previous_board, board)
    player = ABPruning()
    action = player.get_input(go, piece_type)
    writeOutput(action)

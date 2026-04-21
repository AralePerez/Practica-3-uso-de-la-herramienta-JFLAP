from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Iterable, Optional
from collections import defaultdict, deque
import itertools
import math

EPSILON = "λ"


@dataclass
class StateVisual:
    x: float = 0.0
    y: float = 0.0


@dataclass
class Automaton:
    alphabet: Set[str] = field(default_factory=set)
    states: Set[str] = field(default_factory=set)
    initial_state: Optional[str] = None
    accept_states: Set[str] = field(default_factory=set)
    transitions: Dict[str, Dict[str, Set[str]]] = field(default_factory=lambda: defaultdict(lambda: defaultdict(set)))
    visuals: Dict[str, StateVisual] = field(default_factory=dict)
    automaton_type: str = "dfa"  # dfa, nfa, nfae

    def add_state(self, name: str, initial: bool = False, accept: bool = False, x: float = 0.0, y: float = 0.0) -> None:
        self.states.add(name)
        self.visuals.setdefault(name, StateVisual(x=x, y=y))
        if initial:
            self.initial_state = name
        if accept:
            self.accept_states.add(name)

    def add_transition(self, source: str, symbol: str, target: str) -> None:
        self.states.update({source, target})
        if symbol != EPSILON and symbol != "":
            self.alphabet.add(symbol)
        self.transitions[source][symbol].add(target)
        self._update_type()

    def set_transition(self, source: str, symbol: str, target: str) -> None:
        self.transitions[source][symbol] = {target}
        if symbol != EPSILON and symbol != "":
            self.alphabet.add(symbol)
        self.states.update({source, target})
        self._update_type()

    def _update_type(self) -> None:
        has_epsilon = False
        deterministic = True
        for src, by_symbol in self.transitions.items():
            for symbol, targets in by_symbol.items():
                if symbol in (EPSILON, ""):
                    has_epsilon = True
                if len(targets) > 1:
                    deterministic = False
        if has_epsilon:
            self.automaton_type = "nfae"
        elif deterministic:
            self.automaton_type = "dfa"
        else:
            self.automaton_type = "nfa"

    def clone(self) -> "Automaton":
        a = Automaton(alphabet=set(self.alphabet), automaton_type=self.automaton_type)
        for st in self.states:
            vis = self.visuals.get(st, StateVisual())
            a.add_state(st, initial=(st == self.initial_state), accept=(st in self.accept_states), x=vis.x, y=vis.y)
        for src in self.states:
            for sym, targets in self.transitions.get(src, {}).items():
                for dst in targets:
                    a.add_transition(src, sym, dst)
        return a

    def validate_basic(self) -> List[str]:
        errors = []
        if not self.states:
            errors.append("No hay estados definidos.")
        if not self.initial_state:
            errors.append("No hay estado inicial definido.")
        elif self.initial_state not in self.states:
            errors.append("El estado inicial no pertenece al conjunto de estados.")
        for st in self.accept_states:
            if st not in self.states:
                errors.append(f"El estado de aceptación {st} no existe.")
        return errors

    def validate_nfa_structure(self) -> List[str]:
        errors = self.validate_basic()
        for src in self.states:
            for sym, targets in self.transitions.get(src, {}).items():
                if sym not in self.alphabet and sym not in (EPSILON, ""):
                    errors.append(f"La transición {src} --{sym}--> usa un símbolo fuera del alfabeto.")
                for dst in targets:
                    if dst not in self.states:
                        errors.append(f"La transición {src} --{sym}--> {dst} apunta a un estado inexistente.")
        return errors

    def is_dfa(self) -> bool:
        if self.validate_basic():
            return False
        for st in self.states:
            for symbol in self.alphabet:
                targets = self.transitions.get(st, {}).get(symbol, set())
                if len(targets) != 1:
                    return False
        for by_symbol in self.transitions.values():
            if EPSILON in by_symbol or "" in by_symbol:
                return False
        return True

    def simulate_dfa(self, string: str) -> Tuple[bool, List[dict]]:
        if not self.is_dfa():
            raise ValueError("El autómata actual no es un AFD completo.")
        current = self.initial_state
        trace = [{"step": 0, "symbol": "ε", "from": None, "to": current}]
        for idx, ch in enumerate(string, start=1):
            if ch not in self.alphabet:
                trace.append({"step": idx, "symbol": ch, "from": current, "to": None, "error": "Símbolo fuera del alfabeto"})
                return False, trace
            nxt = next(iter(self.transitions[current][ch]))
            trace.append({"step": idx, "symbol": ch, "from": current, "to": nxt})
            current = nxt
        return current in self.accept_states, trace

    def epsilon_closure(self, states: Iterable[str]) -> Set[str]:
        closure = set(states)
        stack = list(states)
        while stack:
            state = stack.pop()
            for nxt in self.transitions.get(state, {}).get(EPSILON, set()) | self.transitions.get(state, {}).get("", set()):
                if nxt not in closure:
                    closure.add(nxt)
                    stack.append(nxt)
        return closure

    def epsilon_closure_map(self) -> Dict[str, Set[str]]:
        return {st: self.epsilon_closure({st}) for st in sorted(self.states)}

    def move(self, states: Iterable[str], symbol: str) -> Set[str]:
        result = set()
        for st in states:
            result |= self.transitions.get(st, {}).get(symbol, set())
        return result

    def simulate_nfa(self, string: str) -> Tuple[bool, List[dict]]:
        errors = self.validate_nfa_structure()
        if errors:
            raise ValueError("; ".join(errors))
        use_epsilon = self.automaton_type == "nfae" or any(EPSILON in by_symbol or "" in by_symbol for by_symbol in self.transitions.values())
        current_states = {self.initial_state}
        initial_closure = self.epsilon_closure(current_states) if use_epsilon else set(current_states)
        trace = [{
            "step": 0,
            "symbol": "ε",
            "active_before": sorted(current_states),
            "closure": sorted(initial_closure),
            "active_after": sorted(initial_closure),
            "branches": [],
            "lambda_used": sorted(initial_closure - current_states),
        }]
        current_states = initial_closure
        for idx, ch in enumerate(string, start=1):
            if ch not in self.alphabet:
                trace.append({
                    "step": idx,
                    "symbol": ch,
                    "active_before": sorted(current_states),
                    "closure": sorted(current_states),
                    "active_after": [],
                    "branches": [],
                    "error": "Símbolo fuera del alfabeto",
                })
                return False, trace
            branches = []
            moved = set()
            for st in sorted(current_states):
                targets = sorted(self.transitions.get(st, {}).get(ch, set()))
                branches.append({"from": st, "symbol": ch, "to": targets})
                moved.update(targets)
            closure_after = self.epsilon_closure(moved) if use_epsilon else moved
            trace.append({
                "step": idx,
                "symbol": ch,
                "active_before": sorted(current_states),
                "raw_move": sorted(moved),
                "closure": sorted(closure_after),
                "active_after": sorted(closure_after),
                "branches": branches,
                "lambda_used": sorted(closure_after - moved) if use_epsilon else [],
            })
            current_states = closure_after
        accepted = bool(current_states & self.accept_states)
        return accepted, trace

    def determinize(self) -> "Automaton":
        errors = self.validate_basic()
        if errors:
            raise ValueError("; ".join(errors))
        start_set = frozenset(self.epsilon_closure({self.initial_state}))
        dfa = Automaton(alphabet=set(self.alphabet), automaton_type="dfa")

        def name_of(state_set: frozenset[str]) -> str:
            if not state_set:
                return "∅"
            return "{" + ",".join(sorted(state_set)) + "}"

        queue = deque([start_set])
        visited = {start_set}
        dfa.add_state(name_of(start_set), initial=True, accept=bool(set(start_set) & self.accept_states))

        while queue:
            current_set = queue.popleft()
            current_name = name_of(current_set)
            for symbol in sorted(self.alphabet):
                moved = self.move(current_set, symbol)
                closed = frozenset(self.epsilon_closure(moved))
                next_name = name_of(closed)
                if closed not in visited:
                    visited.add(closed)
                    queue.append(closed)
                    dfa.add_state(next_name, accept=bool(set(closed) & self.accept_states))
                dfa.set_transition(current_name, symbol, next_name)

        dfa.complete_with_sink()
        dfa.layout_states()
        return dfa

    def determinize_with_steps(self) -> Tuple["Automaton", List[dict]]:
        errors = self.validate_basic()
        if errors:
            raise ValueError("; ".join(errors))

        def name_of(state_set: frozenset[str]) -> str:
            if not state_set:
                return "∅"
            return "{" + ",".join(sorted(state_set)) + "}"

        start_set = frozenset(self.epsilon_closure({self.initial_state}))
        dfa = Automaton(alphabet=set(self.alphabet), automaton_type="dfa")
        dfa.add_state(name_of(start_set), initial=True, accept=bool(set(start_set) & self.accept_states))

        queue = deque([start_set])
        visited = {start_set}
        steps = []
        while queue:
            current_set = queue.popleft()
            current_name = name_of(current_set)
            step_info = {"subset": sorted(current_set), "name": current_name, "transitions": []}
            for symbol in sorted(self.alphabet):
                moved = self.move(current_set, symbol)
                closed = frozenset(self.epsilon_closure(moved))
                next_name = name_of(closed)
                step_info["transitions"].append({
                    "symbol": symbol,
                    "move": sorted(moved),
                    "closure": sorted(closed),
                    "target_name": next_name,
                    "accepting": bool(set(closed) & self.accept_states),
                })
                if closed not in visited:
                    visited.add(closed)
                    queue.append(closed)
                    dfa.add_state(next_name, accept=bool(set(closed) & self.accept_states))
                dfa.set_transition(current_name, symbol, next_name)
            steps.append(step_info)
        dfa.complete_with_sink()
        dfa.layout_states()
        return dfa, steps

    def remove_epsilon_transitions(self) -> Tuple["Automaton", List[dict]]:
        errors = self.validate_basic()
        if errors:
            raise ValueError("; ".join(errors))
        closure_map = self.epsilon_closure_map()
        nfa = Automaton(alphabet=set(self.alphabet), automaton_type="nfa")
        steps = []
        for st in sorted(self.states):
            accept = bool(closure_map[st] & self.accept_states)
            vis = self.visuals.get(st, StateVisual())
            nfa.add_state(st, initial=(st == self.initial_state), accept=accept, x=vis.x, y=vis.y)
        for st in sorted(self.states):
            state_step = {"state": st, "closure": sorted(closure_map[st]), "transitions": []}
            for sym in sorted(self.alphabet):
                moved = self.move(closure_map[st], sym)
                expanded = self.epsilon_closure(moved)
                for dst in sorted(expanded):
                    nfa.add_transition(st, sym, dst)
                state_step["transitions"].append({
                    "symbol": sym,
                    "move_from_closure": sorted(moved),
                    "expanded": sorted(expanded),
                })
            steps.append(state_step)
        nfa.layout_states()
        return nfa, steps

    def reachable_states(self) -> Set[str]:
        if not self.initial_state:
            return set()
        seen = set()
        queue = deque([self.initial_state])
        while queue:
            st = queue.popleft()
            if st in seen:
                continue
            seen.add(st)
            for sym, targets in self.transitions.get(st, {}).items():
                for dst in targets:
                    if dst not in seen:
                        queue.append(dst)
        return seen

    def prune_unreachable(self) -> Tuple["Automaton", Set[str]]:
        reachable = self.reachable_states()
        pruned = Automaton(alphabet=set(self.alphabet), automaton_type=self.automaton_type)
        for st in sorted(reachable):
            vis = self.visuals.get(st, StateVisual())
            pruned.add_state(st, initial=(st == self.initial_state), accept=(st in self.accept_states), x=vis.x, y=vis.y)
        for src in sorted(reachable):
            for sym, targets in self.transitions.get(src, {}).items():
                if sym in (EPSILON, "") and self.is_dfa():
                    continue
                for dst in sorted(targets & reachable):
                    pruned.add_transition(src, sym, dst)
        pruned.layout_states()
        return pruned, self.states - reachable

    def minimize_dfa(self) -> Tuple["Automaton", dict]:
        if not self.is_dfa():
            raise ValueError("La minimización solo aplica a AFD completos.")
        base, unreachable = self.prune_unreachable()
        states = sorted(base.states)
        marked = set()
        mark_reasons = {}
        pairs = []
        for i in range(len(states)):
            for j in range(i + 1, len(states)):
                a, b = states[i], states[j]
                pair = (a, b)
                pairs.append(pair)
                if (a in base.accept_states) != (b in base.accept_states):
                    marked.add(pair)
                    mark_reasons[pair] = "Uno es de aceptación y el otro no."
        changed = True
        while changed:
            changed = False
            for a, b in pairs:
                if (a, b) in marked:
                    continue
                for sym in sorted(base.alphabet):
                    ta = next(iter(base.transitions[a][sym]))
                    tb = next(iter(base.transitions[b][sym]))
                    if ta == tb:
                        continue
                    dep = tuple(sorted((ta, tb)))
                    if dep in marked:
                        marked.add((a, b))
                        mark_reasons[(a, b)] = f"Con símbolo '{sym}' llegan a {dep}, que ya es distinguible."
                        changed = True
                        break
        parent = {st: st for st in states}

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a, b):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[rb] = ra

        for a, b in pairs:
            if (a, b) not in marked:
                union(a, b)

        groups_dict = defaultdict(set)
        for st in states:
            groups_dict[find(st)].add(st)
        groups = [set(v) for v in groups_dict.values()]
        groups_sorted = sorted(groups, key=lambda g: (len(g), sorted(g)))

        minimized = Automaton(alphabet=set(base.alphabet), automaton_type="dfa")
        group_names = {}
        for group in groups_sorted:
            name = "{" + ",".join(sorted(group)) + "}"
            for st in group:
                group_names[st] = name
            minimized.add_state(
                name,
                initial=base.initial_state in group,
                accept=bool(group & base.accept_states),
            )
        for group in groups_sorted:
            rep = sorted(group)[0]
            src_name = group_names[rep]
            for sym in sorted(base.alphabet):
                dst = next(iter(base.transitions[rep][sym]))
                minimized.set_transition(src_name, sym, group_names[dst])
        minimized.layout_states()
        info = {
            "original_states": sorted(self.states),
            "reachable_states": sorted(base.states),
            "unreachable_states": sorted(unreachable),
            "distinguishable_pairs": [
                {"pair": [a, b], "reason": mark_reasons[(a, b)]}
                for (a, b) in sorted(marked)
            ],
            "equivalent_groups": [sorted(g) for g in groups_sorted],
            "before_count": len(self.states),
            "after_reachable_count": len(base.states),
            "after_count": len(minimized.states),
            "removed_total": len(self.states) - len(minimized.states),
        }
        return minimized, info

    def representative_test_strings(self, limit: int = 5, max_len: int = 3) -> List[str]:
        strings = [""]
        for length in range(1, max_len + 1):
            for prod in itertools.product(sorted(self.alphabet), repeat=length):
                strings.append("".join(prod))
                if len(strings) >= limit:
                    return strings
        return strings[:limit]

    def complete_with_sink(self, sink_name: str = "q_sink") -> None:
        if not self.states:
            return
        need_sink = False
        for st in list(self.states):
            for symbol in self.alphabet:
                if len(self.transitions.get(st, {}).get(symbol, set())) != 1:
                    need_sink = True
        if not need_sink:
            return
        self.add_state(sink_name)
        for symbol in self.alphabet:
            self.set_transition(sink_name, symbol, sink_name)
        for st in list(self.states):
            for symbol in self.alphabet:
                targets = self.transitions.get(st, {}).get(symbol, set())
                if len(targets) != 1:
                    self.set_transition(st, symbol, sink_name)
        self.automaton_type = "dfa"

    def layout_states(self, width: int = 700, height: int = 320) -> None:
        if not self.states:
            return
        cx, cy = width / 2, height / 2
        radius = min(width, height) * 0.35
        ordered = sorted(self.states)
        n = len(ordered)
        for i, st in enumerate(ordered):
            angle = 2 * math.pi * i / max(n, 1)
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            self.visuals[st] = StateVisual(x=x, y=y)

    def transition_table(self, include_epsilon: bool = True) -> List[List[str]]:
        symbols = sorted(self.alphabet)
        if include_epsilon:
            has_epsilon = any(EPSILON in by_symbol or "" in by_symbol for by_symbol in self.transitions.values())
            if has_epsilon:
                symbols += [EPSILON]
        header = ["Estado"] + symbols
        rows = [header]
        for st in sorted(self.states):
            name = st
            if st == self.initial_state:
                name = "→" + name
            if st in self.accept_states:
                name = "*" + name
            row = [name]
            for symbol in symbols:
                key = "" if symbol == EPSILON and symbol not in self.transitions.get(st, {}) and "" in self.transitions.get(st, {}) else symbol
                targets = sorted(self.transitions.get(st, {}).get(key, set()) or self.transitions.get(st, {}).get(symbol, set()))
                row.append(", ".join(targets) if targets else "—")
            rows.append(row)
        return rows

    def batch_validate_strings(self, strings: List[str]) -> List[dict]:
        results = []
        for s in strings:
            accepted, trace = self.simulate_dfa(s) if self.is_dfa() else self.simulate_nfa(s)
            results.append({
                "string": s,
                "accepted": accepted,
                "final_active": trace[-1].get("active_after") if trace else [],
                "steps": len(trace) - 1,
            })
        return results

    def to_serializable(self) -> dict:
        return {
            "type": self.automaton_type,
            "alphabet": sorted(self.alphabet),
            "states": [
                {
                    "name": st,
                    "initial": st == self.initial_state,
                    "accept": st in self.accept_states,
                    "x": self.visuals.get(st, StateVisual()).x,
                    "y": self.visuals.get(st, StateVisual()).y,
                }
                for st in sorted(self.states)
            ],
            "transitions": [
                {"from": src, "symbol": sym, "to": dst}
                for src in sorted(self.states)
                for sym in sorted(self.transitions.get(src, {}).keys(), key=lambda s: (s != EPSILON, s))
                for dst in sorted(self.transitions[src][sym])
            ],
        }


def prefixes(s: str) -> List[str]:
    return [s[:i] for i in range(len(s) + 1)]


def suffixes(s: str) -> List[str]:
    return [s[i:] for i in range(len(s) + 1)]


def substrings(s: str) -> List[str]:
    seen = []
    found = set()
    for i in range(len(s) + 1):
        for j in range(i, len(s) + 1):
            piece = s[i:j]
            if piece not in found:
                found.add(piece)
                seen.append(piece)
    return seen


def kleene_closure(alphabet: List[str], max_len: int, positive: bool = False) -> List[str]:
    results = []
    start = 1 if positive else 0
    if not alphabet:
        return [""] if not positive else []
    for length in range(start, max_len + 1):
        for prod in itertools.product(alphabet, repeat=length):
            results.append("".join(prod))
    if not positive:
        results.insert(0, "ε")
    return results

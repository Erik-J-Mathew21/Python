"""
Neurosystems Explorer v3 - learning, sleep and memory in a 3D spiking network.
pip install pygame numpy

BUTTONS (bottom left)
  Learn      repeatedly fire a chain of neurons (A->B->C): their pathways grow thicker
  Sleep      slow-wave sleep with memory replay; pick Synaptic or Systems consolidation
  No sleep   sleep deprivation: fatigue, erratic firing, forgetting, poor learning
  Wake       return to normal
CLICK any neuron, pathway (line) or part of a neuron for an explanation card.
Double-click a neuron to go inside it.

CAMERA   Arrows move | A/D turn | Q/E tilt | W/S or wheel zoom | drag orbit | H home | O spin
OTHER    Right click lesion | L unlesion | 1-4 firing type | -/= noise | ,/. gain
         T plasticity on/off | [ ] speed | SPACE pause | N new network | ESC back/quit
"""
import math
import random
import time
from collections import deque

import numpy as np
import pygame

W, H = 1240, 760
PANEL_X = 880
N = 140
HIST = 300
CX, CY = PANEL_X // 2, H // 2
D_CAM = 900.0
CENTER = np.array([PANEL_X / 2, H / 2, 0.0])
HOME = (0.4, 0.25, 0.95, 0.0, 0.0)  # yaw, pitch, zoom, panx, pany
SMAX = 4.0

TYPES = {
    "1": ("Regular spiking", 0.02, 0.2, -65.0, 8.0),
    "2": ("Intrinsic bursting", 0.02, 0.2, -55.0, 4.0),
    "3": ("Chattering", 0.02, 0.2, -50.0, 2.0),
    "4": ("Fast spiking", 0.10, 0.2, -65.0, 2.0),
}
BG = (10, 12, 20)
EXC_C = (80, 170, 255)
INH_C = (255, 100, 85)
GOLD = (255, 205, 90)
GREEN = (110, 230, 150)
PURPLE = (150, 110, 230)
BTN_COL = {"learn": GOLD, "sleep": (120, 130, 255), "nosleep": (255, 110, 90), "wake": (150, 160, 180),
           "synaptic": (120, 220, 200), "systems": (190, 130, 255)}

INFO = {
    "soma": ("Soma (cell body)", "The control centre of the neuron. It adds up every excitatory and inhibitory signal arriving from the dendrites. If the total pushes the voltage past threshold, the neuron fires a spike. It also houses the organelles that keep the cell alive."),
    "nucleus": ("Nucleus", "Stores the cell's DNA. During learning and deep sleep it switches on genes that build proteins, which synapses use to grow bigger and last longer. This is how a short-lived change becomes a long-term memory."),
    "mito": ("Mitochondria", "The cell's power plants. Spikes and re-balancing ions cost a lot of ATP, so they glow brighter the more the neuron fires. Fatigued, sleep-deprived neurons cannot keep up with this energy demand."),
    "membrane": ("Cell membrane", "A thin fatty skin separating inside from outside. Pumps keep the inside about -65 mV relative to outside (the resting potential). The ring's colour shows the live voltage; a spike is a rapid swing of it."),
    "channel": ("Ion channels", "Protein gates in the membrane. When the cell depolarises, sodium (Na+) channels open and Na+ floods in, driving the spike upward. Then potassium (K+) channels open and K+ flows out, resetting the voltage."),
    "dendrite": ("Dendrite", "Branches that receive signals. Each input is a synapse from another neuron: excitatory ones nudge the voltage up, inhibitory ones push it down. Big dendritic trees let one neuron listen to thousands of others."),
    "spine": ("Dendritic spine", "A tiny bump where a synapse sits. Spines physically enlarge when a connection is used a lot (long-term potentiation): bigger spine, stronger connection. Sleep helps stabilise those enlarged spines."),
    "bouton": ("Input synapse from {pid}", "Where neuron {pid} contacts this dendrite. Neurotransmitter arriving here opens ion channels and nudges this cell's voltage. Strength: {sz:.1f}x baseline. It grows when the two cells fire together and shrinks if unused."),
    "hillock": ("Axon hillock", "The trigger zone where soma meets axon. It has the densest sodium channels, so this is where the decision to fire is made. If voltage here crosses threshold, an action potential starts down the axon."),
    "axon": ("Axon", "The long cable that carries the spike away from the cell body to the neurons it talks to, without the signal fading."),
    "myelin": ("Myelin sheath", "Fatty insulation wrapped around the axon. It stops current leaking out, so spikes travel much faster. Damaged myelin (as in multiple sclerosis) slows or blocks signals."),
    "node": ("Node of Ranvier", "A gap in the myelin packed with ion channels. The spike is regenerated at each node and effectively jumps from node to node (saltatory conduction), which is fast and energy efficient."),
    "terminal": ("Axon terminal -> {pid}", "Where this neuron talks to {pid}. When a spike arrives, calcium enters and vesicles release neurotransmitter (glutamate if excitatory, GABA if inhibitory) across the synaptic cleft. Strength: {sz:.1f}x. A bigger terminal means a stronger, more reliable connection."),
    "terminal_branch": ("Axon branch", "The axon splits so a single spike can reach several target neurons at once."),
}


def lerp3(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def vcolor(v, base, fog=1.0):
    t = max(0.0, min(1.0, (v + 80) / 110))
    return tuple(int((25 + (c - 25) * (0.25 + 0.75 * t)) * fog) for c in base)


def seg_dist(px, py, x0, y0, x1, y1):
    dx, dy = x1 - x0, y1 - y0
    t = max(0.0, min(1.0, ((px - x0) * dx + (py - y0) * dy) / (dx * dx + dy * dy or 1)))
    return math.hypot(px - x0 - t * dx, py - y0 - t * dy)


def wrap(text, font, width):
    lines, cur = [], ""
    for word in text.split():
        t = (cur + " " + word).strip()
        if font.size(t)[0] <= width:
            cur = t
        else:
            lines.append(cur)
            cur = word
    lines.append(cur)
    return lines


class Net:
    def __init__(self, n=N):
        self.n = n
        self.type_key = "1"
        self.build()

    def build(self):
        n = self.n
        pts = []
        while len(pts) < n:
            p = (random.uniform(40, PANEL_X - 40), random.uniform(70, H - 40), random.uniform(-220, 220))
            if all(math.dist(p, q) > 44 for q in pts):
                pts.append(p)
        self.pos = np.array(pts)
        D = np.linalg.norm(self.pos[:, None] - self.pos[None], axis=2)
        self.exc = np.random.rand(n) < 0.8
        self.mask = (np.random.rand(n, n) < 0.5 * np.exp(-D / 100)) & ~np.eye(n, dtype=bool)  # [post, pre]
        w = np.where(self.exc[None, :], np.random.rand(n, n) * 5.0, -np.random.rand(n, n) * 8.0)
        self.W = w * self.mask
        self.out = [np.nonzero(self.mask[:, i])[0] for i in range(n)]
        self.lp, self.lq = np.nonzero(self.mask)  # post, pre of each link
        self.lidx = {(int(p), int(q)): k for k, (p, q) in enumerate(zip(self.lp, self.lq))}
        self.lcol = np.where(self.exc[self.lq][:, None], np.array([70, 120, 180.0]), np.array([190, 80, 70.0]))
        self.size = np.ones((n, n))  # pathway size (1 = baseline)
        self.rate = np.full((n, n), 4e-4)  # forgetting rate per link
        self.hip = (self.pos[:, 0] < 330) & (self.pos[:, 1] > 430)  # "hippocampus" region
        self.v = np.full(n, -65.0)
        self.syn = np.zeros(n)
        self.tr = np.zeros(n)
        self.stim = np.zeros(n)
        self.lapse = np.zeros(n)
        self.dead = np.zeros(n, dtype=bool)
        self.flash = np.zeros(n)
        self.t = 0
        self.apply_type()
        self.u = self.b * self.v

    def apply_type(self):
        _, a, b, c, d = TYPES[self.type_key]
        self.a = np.where(self.exc, a, 0.1)
        self.b = np.where(self.exc, b, 0.2)
        self.c = np.where(self.exc, c, -65.0)
        self.d = np.where(self.exc, d, 2.0)

    def step(self, drive, gain, plast, lr=1.0, forget=1.0, fatigue=0.0):
        n = self.n
        noise = np.random.randn(n) * drive * (1 + 1.2 * fatigue) * np.where(self.exc, 1.0, 0.6)
        I = noise + gain * (1 - 0.3 * fatigue) * self.syn
        I[self.stim > 0] += 15
        self.stim = np.maximum(self.stim - 1, 0)
        if fatigue > 0:  # microsleep-like lapses
            new = (np.random.rand(n) < 0.003 * fatigue) & (self.lapse <= 0)
            self.lapse[new] = 60
        I[self.lapse > 0] -= 14
        self.lapse = np.maximum(self.lapse - 1, 0)
        v, u = self.v, self.u
        for _ in range(2):
            v = np.minimum(v + 0.5 * (0.04 * v * v + 5 * v + 140 - u + I), 30.0)
        u = u + self.a * (self.b * v - u)
        fired = (v >= 30) & ~self.dead
        v = np.where(fired, self.c, v)
        u = np.where(fired, u + self.d, u)
        v[self.dead] = -65.0
        self.v, self.u = v, u
        f = fired.astype(float)
        self.syn = self.syn * 0.8 + (self.W * (0.4 + 0.6 * self.size)) @ f
        self.tr *= 0.95
        if plast and fired.any():  # Hebbian: post fires after recently-active pre -> pathway grows
            inc = lr * 0.05 * (SMAX - self.size[fired, :]) * self.tr[None, :] * self.mask[fired, :] * self.exc[None, :]
            self.size[fired, :] += inc
        self.tr += f
        self.t += 1
        if self.t % 4 == 0:  # unused pathways shrink back
            self.size -= 4 * self.rate * forget * (self.size - 1)
        self.flash = np.maximum(self.flash * 0.9, f)
        return fired


def project(pos, yaw, pitch, zoom, panx, pany):
    c = pos - CENTER
    cy_, sy_ = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)
    x = c[:, 0] * cy_ + c[:, 2] * sy_
    z = -c[:, 0] * sy_ + c[:, 2] * cy_
    y = c[:, 1] * cp - z * sp
    z = c[:, 1] * sp + z * cp
    k = D_CAM / np.maximum(D_CAM + z, 60.0) * zoom
    return CX + (x - panx) * k, CY + (y - pany) * k, k, z


class Sim:
    """Owns the network plus learning / sleep / sleep-deprivation behaviour."""

    def __init__(self):
        self.net = Net()
        self.reset()

    def reset(self):
        self.mems, self.sched = [], {}
        self.state, self.sub, self.t, self.lt = "awake", None, 0, 0
        self.fatigue, self.cur, self.note = 0.0, None, ""
        self.update_masks()

    @property
    def up(self):
        return self.t % 1100 < 550

    @property
    def speedmul(self):
        return 1 if self.state == "awake" else 4

    @staticmethod
    def links(ch):
        return [(ch[1], ch[0]), (ch[2], ch[1])]  # (post, pre)

    def update_masks(self):
        mm = np.zeros((self.net.n, self.net.n), bool)
        self.ring, self.memset, idx = {}, set(), []
        for m in self.mems:
            for key, col in (("h", GOLD), ("k", GREEN)):
                if m[key]:
                    for l in self.links(m[key]):
                        mm[l] = True
                        self.memset.add(l)
                        idx.append(self.net.lidx[l])
                    for c in m[key]:
                        self.ring[c] = col
        self.nonmem = (self.net.mask & ~mm).astype(float)
        self.memidx = np.array(idx, dtype=int)

    def find_chain(self, region):
        net = self.net
        pool = np.nonzero(region & net.exc)[0].tolist()
        for _ in range(300 if pool else 0):
            a = random.choice(pool)
            o1 = [int(x) for x in net.out[a] if region[x] and net.exc[x]]
            if not o1:
                continue
            b = random.choice(o1)
            o2 = [int(x) for x in net.out[b] if region[x] and net.exc[x] and x != a]
            if o2:
                return [int(a), b, random.choice(o2)]
        return None

    def learn(self):
        if len(self.mems) >= 4:
            self.note = "Memory slots full (4). Press N for a fresh network."
            return
        ch = self.find_chain(self.net.hip) or self.find_chain(np.ones(self.net.n, bool))
        if not ch:
            self.note = "Could not find a connected chain; press N."
            return
        self.mems.append(dict(name=f"M{len(self.mems) + 1}", h=ch, k=None, prog=0.0, kprog=0.0))
        self.cur = self.mems[-1]
        self.state, self.sub, self.lt, self.note = "learn", None, 0, ""
        self.update_masks()

    def start(self, state):
        self.state, self.sub, self.note = state, None, ""

    def wake(self):
        self.state, self.sub, self.note = "awake", None, ""

    def bump(self, links, target, k):
        s = self.net.size
        for l in links:
            s[l] += k * (target - s[l])

    def replay(self):
        net, t = self.net, self.t
        for m in self.mems:
            for off, n in zip((0, 6, 12), m["h"]):
                self.sched.setdefault(t + off, []).append(n)
            hl = self.links(m["h"])
            if self.sub == "synaptic":  # strengthen + lock in this memory's own synapses
                m["prog"] = min(1.0, m["prog"] + 0.05)
                self.bump(hl, 3.4, 0.15)
                for l in hl:
                    net.rate[l] = 4e-4 * (1 - m["prog"]) + 2e-5 * m["prog"]
            elif self.sub == "systems":  # hippocampus trains neocortex
                if m["k"] is None:
                    m["k"] = self.find_chain(~net.hip) or []
                    self.update_masks()
                if m["k"]:
                    for off, n in zip((18, 24, 30), m["k"]):
                        self.sched.setdefault(t + off, []).append(n)
                    m["kprog"] = min(1.0, m["kprog"] + 0.03)
                    kp, kl = m["kprog"], self.links(m["k"])
                    self.bump(kl, 3.4, 0.12)
                    for l in kl:
                        net.rate[l] = 4e-4 * (1 - kp) + 2e-5 * kp
                    self.bump(hl, 3.4 - 2.0 * kp, 0.05)
            else:
                self.bump(hl, 3.0, 0.04)

    def tick(self, drive, gain, plast):
        net = self.net
        for n in self.sched.pop(self.t, []):
            net.stim[n] = 3
        d, lr, forget, st = drive, 1.0, 1.0, self.state
        if st == "learn":
            ph = self.lt % 70
            a, b, c = self.cur["h"]
            if ph == 0:
                net.stim[a] = 3
            elif ph == 12:
                net.stim[b] = 3
            elif ph == 24:
                net.stim[c] = 3
            lr = 3.0
            self.lt += 1
            if self.lt >= 70 * 24:
                self.state = "awake"
        elif st == "sleep":
            ph = self.t % 1100
            d = drive * (1.0 if ph < 550 else 0.12)
            forget, lr = 0.3, 1.5
            if ph < 550 and ph % 110 == 50:
                self.replay()
            self.fatigue = max(0.0, self.fatigue - 0.0008)
            if self.sub == "synaptic" and self.t % 4 == 0:
                net.size -= 0.01 * (net.size - 1) * self.nonmem  # scale back unused synapses
        elif st == "nosleep":
            self.fatigue = min(1.0, self.fatigue + 0.0004)
        fat = self.fatigue
        fired = net.step(d, gain, plast, lr * (1 - 0.85 * fat), forget * (1 + 8 * fat), fat)
        self.t += 1
        return fired

    def banner(self):
        s, sub = self.state, self.sub
        if s == "learn":
            return "LEARNING", GOLD, "Neurons A, B, C are activated in sequence again and again. Each time B fires just after A, the A-B pathway strengthens and grows thicker (Hebbian plasticity)."
        if s == "sleep" and sub == "synaptic":
            return "SLEEP: SYNAPTIC CONSOLIDATION", BTN_COL["synaptic"], "Replay strengthens the memory's own synapses and locks them in with new proteins (permanent, gold). Unused synapses are scaled back so the memory stands out."
        if s == "sleep" and sub == "systems":
            return "SLEEP: SYSTEMS CONSOLIDATION", BTN_COL["systems"], "Hippocampal replay trains the neocortex. A new cortical pathway (green) grows and becomes permanent while the hippocampal one fades: the memory moves to long-term storage."
        if s == "sleep":
            return "SLEEP", BTN_COL["sleep"], "Slow waves alternate active and silent periods while the brain replays recent memories, thickening their pathways. Choose a consolidation type below."
        if s == "nosleep":
            return "NO SLEEP", BTN_COL["nosleep"], "Adenosine builds up. Neurons fire erratically and drop out in microsleeps, replay never happens, pathways fade faster and new learning barely takes hold."
        return "AWAKE", (190, 200, 220), "Neurons that fire together wire together: repeated co-activity thickens a pathway, and unused pathways slowly shrink back."


class Inside:
    """Cutaway of one neuron: dendrites, soma, axon, terminals, ion flow, vesicles."""
    SOMA = (290, H // 2)

    def __init__(self, net, idx):
        rng = random.Random(idx)
        self.i = idx
        self.pre = [int(p) for p in np.nonzero(net.mask[idx])[0]]
        self.post = [int(p) for p in net.out[idx]]
        sx, sy = self.SOMA
        shown = self.pre[:12] or [None] * 3
        m = len(shown)
        self.dend = []
        for k, pid in enumerate(shown):
            a = math.radians(125 + 110 * (k + 0.5) / m)
            L = rng.uniform(110, 150)
            x0, y0 = sx + math.cos(a) * 62, sy + math.sin(a) * 62
            ex, ey = sx + math.cos(a) * (70 + L), sy + math.sin(a) * (70 + L)
            bend = rng.uniform(-40, 40)
            qx, qy = (x0 + ex) / 2 - math.sin(a) * bend, (y0 + ey) / 2 + math.cos(a) * bend
            pts = []
            for j in range(15):
                t = j / 14
                pts.append(((1 - t) ** 2 * x0 + 2 * (1 - t) * t * qx + t * t * ex,
                            (1 - t) ** 2 * y0 + 2 * (1 - t) * t * qy + t * t * ey))
            a2 = a + rng.choice([-1, 1]) * rng.uniform(0.5, 0.9)
            tip = (pts[9][0] + math.cos(a2) * 55, pts[9][1] + math.sin(a2) * 55)
            spines = []
            for t in range(2, 14, 2):
                (px0, py0), (px1, py1) = pts[t], pts[t + 1]
                ln = math.hypot(px1 - px0, py1 - py0) or 1
                s = rng.choice([-1, 1]) * 7
                spines.append(((px0, py0), (px0 - (py1 - py0) / ln * s, py0 + (px1 - px0) / ln * s)))
            self.dend.append(dict(pts=pts, br=[pts[9], tip], tip=pts[-1], pid=pid, spines=spines))
        self.ax0 = 410
        self.sheaths, self.nodes = [], []
        x = self.ax0
        for _ in range(5):
            self.nodes.append(x + 5)
            x += 11
            self.sheaths.append((x, 50))
            x += 50
        self.nodes.append(x + 5)
        self.ax1 = x + 11
        sp = self.post[:5] or [None] * 2
        self.terms = [dict(x=805, y=sy + (k - (len(sp) - 1) / 2) * 80, pid=pid, fl=0.0) for k, pid in enumerate(sp)]
        self.mito = [(sx + math.cos(a) * r, sy + math.sin(a) * r)
                     for a, r in ((rng.uniform(0, 6.28), rng.uniform(42, 54)) for _ in range(6))]
        self.aps, self.parts = [], []

    def fire(self):
        self.aps.append(0.0)

    def step(self, net):
        i = self.i
        v, u, fl = net.v[i], net.u[i], net.flash[i]
        sx, sy = self.SOMA
        for kind, rate in (("na", 0.3 + 5 * fl + max(0.0, (v + 68) / 25)),
                           ("k", 4 * min(1.0, max(0.0, (u + 14) / 14)))):
            for _ in range(int(rate + random.random())):
                if len(self.parts) > 450:
                    break
                a = random.uniform(0, 6.283)
                ca, sa = math.cos(a), math.sin(a)
                r0, spd = (88, -3.0) if kind == "na" else (54, 3.0)
                self.parts.append([sx + ca * r0, sy + sa * r0, ca * spd, sa * spd, 14, kind])
        done = []
        for k, ap in enumerate(self.aps):
            self.aps[k] = ap + 0.03
            if self.aps[k] >= 1.0:
                done.append(k)
                for tm in self.terms:
                    tm["fl"] = 1.0
                    for _ in range(5):
                        self.parts.append([tm["x"] + 6, tm["y"] + random.uniform(-8, 8), random.uniform(0.8, 1.8),
                                           random.uniform(-0.6, 0.6), 45, "ve" if net.exc[i] else "vi"])
        self.aps = [a for k, a in enumerate(self.aps) if k not in done]
        for tm in self.terms:
            tm["fl"] *= 0.93
        for p in self.parts:
            p[0] += p[2]
            p[1] += p[3]
            p[4] -= 1
        self.parts = [p for p in self.parts if p[4] > 0]

    def part_at(self, x, y):
        sx, sy = self.SOMA
        for d in self.dend:
            if d["pid"] is not None and math.hypot(x - d["tip"][0], y - d["tip"][1]) < 15:
                return ("bouton", d["pid"])
        for tm in self.terms:
            if math.hypot(x - tm["x"], y - tm["y"]) < 18:
                return ("terminal", tm["pid"])
        for nx in self.nodes:
            if math.hypot(x - nx, y - sy) < 9:
                return ("node", None)
        for x0, w in self.sheaths:
            if x0 <= x <= x0 + w and abs(y - sy) <= 12:
                return ("myelin", None)
        r = math.hypot(x - sx, y - sy)
        if math.hypot(x - (sx - 4), y - (sy + 2)) < 28:
            return ("nucleus", None)
        for mx, my in self.mito:
            if math.hypot(x - mx, y - my) < 13:
                return ("mito", None)
        if 62 <= r <= 80:
            step = math.tau / 24
            off = abs(((math.atan2(y - sy, x - sx) % math.tau) + step / 2) % step - step / 2)
            if off * r < 5:
                return ("channel", None)
            if 66 <= r <= 74:
                return ("membrane", None)
        if r < 68:
            return ("soma", None)
        if sx + 60 <= x <= self.ax0:
            half = 26 - (x - (sx + 60)) / (self.ax0 - (sx + 60)) * 22
            if abs(y - sy) <= half:
                return ("hillock", None)
        if self.ax0 <= x <= self.ax1 and abs(y - sy) <= 8:
            return ("axon", None)
        for d in self.dend:
            for _, b in d["spines"]:
                if math.hypot(x - b[0], y - b[1]) < 7:
                    return ("spine", None)
        for d in self.dend:
            for pts in (d["pts"], d["br"]):
                for k in range(len(pts) - 1):
                    if seg_dist(x, y, *pts[k], *pts[k + 1]) < 7:
                        return ("dendrite", None)
        for tm in self.terms:
            if seg_dist(x, y, self.ax1, sy, tm["x"], tm["y"]) < 6:
                return ("terminal_branch", None)
        return None

    def draw(self, s, net, font, big, fat, memset):
        i = self.i
        s.fill(BG)
        exc = bool(net.exc[i])
        base = EXC_C if exc else INH_C
        sx, sy = self.SOMA
        v, fl = float(net.v[i]), float(net.flash[i])

        def lab(txt, x, y, c=(135, 145, 175)):
            s.blit(font.render(txt, True, c), (x, y))

        anygold = False
        for d in self.dend:
            pid = d["pid"]
            f = float(net.flash[pid]) if pid is not None else 0.0
            sz = float(net.size[i, pid]) if pid is not None else 1.0
            gold = pid is not None and (i, pid) in memset
            anygold = anygold or gold
            pb = (EXC_C if net.exc[pid] else INH_C) if pid is not None else (110, 115, 140)
            col = lerp3((70, 80, 115), pb, f * 1.2)
            if gold:
                col = lerp3(col, GOLD, 0.4)
            pygame.draw.lines(s, col, False, d["pts"], 4 + int(1.3 * (sz - 1)))
            pygame.draw.lines(s, col, False, d["br"], 3)
            for a, b in d["spines"]:
                pygame.draw.line(s, col, a, b, 2 + int(sz - 1))
                pygame.draw.circle(s, col, b, int(2 + 2.2 * (sz - 1)))
            if pid is not None:
                bx, by = d["tip"]
                r = int(8 + 5 * f + 2 * (sz - 1))
                pygame.draw.circle(s, lerp3((40, 45, 70), pb, 0.35 + 0.65 * f), (bx, by), r)
                pygame.draw.circle(s, pb, (bx, by), r, 2)
                if gold:
                    pygame.draw.circle(s, GOLD, (bx, by), r + 4, 2)
                lab(f"#{pid}  {sz:.1f}x", bx - 24, by + 14, (170, 180, 205))
        pygame.draw.polygon(s, (60, 75, 110), [(sx + 60, sy - 26), (sx + 60, sy + 26), (self.ax0, sy + 4), (self.ax0, sy - 4)])
        pygame.draw.line(s, (75, 90, 130), (self.ax0, sy), (self.ax1, sy), 5)
        apxs = [self.ax0 + a * (self.ax1 - self.ax0) for a in self.aps]
        for ax in apxs:
            pygame.draw.line(s, (255, 240, 120), (max(self.ax0, ax - 26), sy), (ax, sy), 5)
        for x, w in self.sheaths:
            pygame.draw.rect(s, (205, 190, 120), (x, sy - 12, w, 24), border_radius=10)
            pygame.draw.rect(s, (235, 220, 160), (x, sy - 12, w, 24), 1, border_radius=10)
        for nx in self.nodes:
            lit = any(abs(nx - ax) < 18 for ax in apxs)
            pygame.draw.circle(s, (255, 240, 120) if lit else (90, 105, 150), (nx, sy), 10 if lit else 6)
        pygame.draw.circle(s, (28, 34, 58), (sx, sy), 68)
        pygame.draw.circle(s, vcolor(v, base), (sx, sy), 70, 6)
        openc = v > -50 or fl > 0.2
        for k in range(24):
            a = k * math.tau / 24
            pygame.draw.line(s, (230, 220, 120) if openc else (90, 95, 120),
                             (sx + math.cos(a) * 64, sy + math.sin(a) * 64), (sx + math.cos(a) * 78, sy + math.sin(a) * 78), 3)
        g = int((90 + 120 * min(1.0, fl)) * (1 - 0.5 * fat))
        for mx, my in self.mito:
            r = (int(mx) - 10, int(my) - 5, 20, 10)
            pygame.draw.ellipse(s, (g, 70 + g // 3, 60), r)
            pygame.draw.ellipse(s, (255, 200, 150), r, 1)
        pygame.draw.circle(s, (62, 52, 112), (sx - 4, sy + 2), 28)
        pygame.draw.circle(s, (95, 80, 160), (sx - 4, sy + 2), 28, 2)
        pygame.draw.circle(s, (130, 110, 200), (sx - 9, sy - 2), 8)
        for tm in self.terms:
            tx, ty = int(tm["x"]), int(tm["y"])
            pid = tm["pid"]
            sz = float(net.size[pid, i]) if pid is not None else 1.0
            pygame.draw.line(s, (75, 90, 130), (self.ax1, sy), (tx, ty), 3)
            r = 12 + int(4 * tm["fl"]) + int(2 * (sz - 1))
            pygame.draw.circle(s, lerp3((35, 45, 75), base, 0.3 + 0.7 * tm["fl"]), (tx, ty), r)
            pygame.draw.circle(s, base, (tx, ty), r, 2)
            if pid is not None and (pid, i) in memset:
                pygame.draw.circle(s, GOLD, (tx, ty), r + 4, 2)
                anygold = True
            for dx, dy in ((-4, -3), (3, -4), (0, 4)):
                pygame.draw.circle(s, (180, 200, 255), (tx + dx, ty + dy), 2)
            if pid is not None:
                lab(f"#{pid}  {sz:.1f}x", tx - 24, ty + r + 4, (170, 180, 205))
        for p in self.parts:
            k = p[5]
            col = (255, 225, 70) if k == "na" else (90, 230, 130) if k == "k" else (EXC_C if k == "ve" else INH_C)
            pygame.draw.circle(s, col, (int(p[0]), int(p[1])), 3)
        lab("Dendrites (inputs)", 20, 70)
        lab("Axon hillock", sx + 68, sy - 52)
        lab("Myelin sheath", self.ax0 + 70, sy - 34)
        lab("Node of Ranvier", self.ax0 - 6, sy + 24)
        lab("Axon terminals", 740, 578)
        lab("Soma", sx - 16, sy + 86)
        lab("purple: nucleus   orange: mitochondria (ATP)", 20, H - 70)
        s.blit(font.render("yellow: Na+ rushing in", True, (255, 225, 70)), (20, H - 50))
        s.blit(font.render("green: K+ flowing out", True, (90, 230, 130)), (20, H - 32))
        s.blit(font.render("dots right of terminals: neurotransmitter", True, base), (400, H - 32))
        if anygold:
            lab("gold ring: pathway is part of a stored memory (spines/terminals grow with strength)", 20, H - 90, GOLD)
        if fat > 0.4:
            lab("ATP low: this neuron is fatigued", 20, H - 108, (255, 120, 100))
        s.blit(big.render(f"INSIDE NEURON #{i}  -  {'excitatory (glutamate)' if exc else 'inhibitory (GABA)'}", True, (230, 235, 250)), (20, 14))
        extra = " (showing 12)" if len(self.pre) > 12 else ""
        lab(f"{len(self.pre)} inputs{extra}  |  {len(self.post)} outputs  |  Vm = {v:.0f} mV   click any part for info", 20, 44, vcolor(v, base))


def strength(net, links):
    return max(0.0, min(1.0, float(np.mean([net.size[l] - 1 for l in links])) / 3)) if links else 0.0


def pick_link(net, psx, psy, mx, my):
    ax, ay, bx, by = psx[net.lq], psy[net.lq], psx[net.lp], psy[net.lp]
    dx, dy = bx - ax, by - ay
    t = np.clip(((mx - ax) * dx + (my - ay) * dy) / (dx * dx + dy * dy + 1e-9), 0, 1)
    d = np.hypot(mx - (ax + t * dx), my - (ay + t * dy))
    k = int(d.argmin())
    return k, float(d[k])


def neuron_card(net, j, sim):
    kind = "excitatory" if net.exc[j] else "inhibitory"
    region = "hippocampus-like region" if net.hip[j] else "neocortex-like region"
    return dict(title=f"Neuron #{j} ({kind})", color=EXC_C if net.exc[j] else INH_C, action=None,
                text=f"A neuron sums its inputs and, past a threshold, fires a spike that travels down its axon to the cells it connects to. {kind.capitalize()} neurons make their targets {'more' if net.exc[j] else 'less'} likely to fire. "
                     f"This one sits in the {region}, receives {int(net.mask[j].sum())} inputs, sends {len(net.out[j])} outputs, and is at {net.v[j]:.0f} mV. Double-click to look inside.")


def link_card(net, k, sim):
    post, pre = int(net.lp[k]), int(net.lq[k])
    sz = net.size[post, pre]
    kind = "excitatory" if net.exc[pre] else "inhibitory"
    mem = " Gold or green means it belongs to a stored memory." if (post, pre) in sim.memset else ""
    return dict(title=f"Pathway #{pre} -> #{post} ({kind})", color=EXC_C if net.exc[pre] else INH_C, action=None,
                text=f"A pathway is a synapse: the contact where neuron #{pre} releases neurotransmitter onto #{post}. Strength: {sz:.1f}x baseline. "
                     f"When two neurons fire together repeatedly the pathway grows thicker and transmits more strongly; unused ones slowly shrink.{mem}")


def inside_card(kind, pid, net, i):
    title, text = INFO[kind]
    action = None
    if kind in ("bouton", "terminal"):
        ps = f"#{pid}" if pid is not None else "another neuron"
        sz = float(net.size[i, pid] if kind == "bouton" else net.size[pid, i]) if pid is not None else 1.0
        title, text = title.format(pid=ps), text.format(pid=ps, sz=sz)
        if pid is not None:
            action = (f"Go to neuron #{pid}", pid)
    return dict(title=title, text=text, action=action, color=(150, 175, 220))


def draw_card(screen, card, font, mid):
    w = 360
    x, y = PANEL_X - w - 16, 12
    lines = wrap(card["text"], font, w - 28)
    h = 44 + 17 * len(lines) + (40 if card["action"] else 8)
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    surf.fill((18, 22, 38, 240))
    screen.blit(surf, (x, y))
    pygame.draw.rect(screen, card["color"], (x, y, w, h), 2, border_radius=8)
    screen.blit(mid.render(card["title"], True, card["color"]), (x + 14, y + 10))
    screen.blit(font.render("x", True, (200, 205, 225)), (x + w - 22, y + 10))
    for k, ln in enumerate(lines):
        screen.blit(font.render(ln, True, (205, 212, 230)), (x + 14, y + 38 + 17 * k))
    act = None
    if card["action"]:
        act = pygame.Rect(x + 14, y + h - 36, w - 28, 28)
        pygame.draw.rect(screen, (40, 60, 100), act, border_radius=6)
        pygame.draw.rect(screen, card["color"], act, 1, border_radius=6)
        t = font.render(card["action"][0], True, (235, 240, 255))
        screen.blit(t, t.get_rect(center=act.center))
    return dict(card=pygame.Rect(x, y, w, h), close=pygame.Rect(x + w - 30, y + 4, 26, 24), action=act)


def make_buttons(sim):
    bs, x, y = [], 16, H - 46
    row = [("learn", "Learn", 90), ("sleep", "Sleep", 90), ("nosleep", "No sleep", 100)]
    if sim.state != "awake":
        row.append(("wake", "Wake", 80))
    for key, txt, w in row:
        bs.append((key, txt, pygame.Rect(x, y, w, 34)))
        x += w + 10
    if sim.state == "sleep":
        bs.append(("synaptic", "Synaptic consolidation", pygame.Rect(16, H - 90, 200, 34)))
        bs.append(("systems", "Systems consolidation", pygame.Rect(226, H - 90, 200, 34)))
    return bs


def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Neurosystems Explorer")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas,menlo,dejavusansmono", 14)
    mid = pygame.font.SysFont("consolas,menlo,dejavusansmono", 16, bold=True)
    big = pygame.font.SysFont("consolas,menlo,dejavusansmono", 20, bold=True)
    ins_surf = pygame.Surface((PANEL_X, H))

    sim = Sim()
    net = sim.net
    drive, gain, speed = 3.0, 1.0, 1
    plastic = True
    paused = spin = False
    yaw, pitch, zoom, panx, pany = HOME
    sel = 0
    inside, tin, enter_from = None, 1.0, (CX, CY)
    down, dragging, last_t, last_j, last_part = None, False, 0.0, -1, None
    card, rects = None, {}
    pulses = []
    raster, rate, vtrace = deque(maxlen=HIST), deque(maxlen=HIST), deque(maxlen=HIST)
    psx, psy, pk, pz = project(net.pos, yaw, pitch, zoom, panx, pany)

    def select(j):
        nonlocal sel
        if j != sel:
            sel = j
            vtrace.clear()

    def go_inside(j, anim):
        nonlocal inside, tin, enter_from, card
        select(j)
        inside, card = Inside(net, j), None
        pulses.clear()
        if anim:
            tin, enter_from = 0.0, (float(psx[j]), float(psy[j]))

    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return
            elif e.type == pygame.KEYDOWN:
                name = pygame.key.name(e.key)
                if e.key == pygame.K_ESCAPE:
                    if card:
                        card = None
                    elif inside:
                        inside = None
                    else:
                        return
                elif e.key in (pygame.K_b, pygame.K_BACKSPACE):
                    inside = None
                elif name in TYPES:
                    net.type_key = name
                    net.apply_type()
                elif e.key == pygame.K_SPACE:
                    paused = not paused
                elif e.key == pygame.K_MINUS:
                    drive = max(0, drive - 0.5)
                elif e.key == pygame.K_EQUALS:
                    drive = min(10, drive + 0.5)
                elif e.key == pygame.K_COMMA:
                    gain = max(0, gain - 0.1)
                elif e.key == pygame.K_PERIOD:
                    gain = min(3, gain + 0.1)
                elif e.key == pygame.K_t:
                    plastic = not plastic
                elif e.key == pygame.K_l:
                    net.dead[:] = False
                elif e.key == pygame.K_h:
                    yaw, pitch, zoom, panx, pany = HOME
                elif e.key == pygame.K_o:
                    spin = not spin
                elif e.key == pygame.K_LEFTBRACKET:
                    speed = max(1, speed - 1)
                elif e.key == pygame.K_RIGHTBRACKET:
                    speed = min(5, speed + 1)
                elif e.key == pygame.K_n:
                    net.build()
                    sim.reset()
                    inside, card = None, None
                    pulses.clear(); raster.clear(); rate.clear(); vtrace.clear()
                    sel = 0
            elif e.type == pygame.MOUSEWHEEL and not inside:
                zoom = max(0.3, min(6.0, zoom * 1.1 ** e.y))
            elif e.type == pygame.MOUSEBUTTONDOWN:
                if e.pos[0] >= PANEL_X:
                    continue
                if e.button == 1:
                    if card and rects:
                        if rects["close"].collidepoint(e.pos):
                            card = None
                            continue
                        if rects["action"] and rects["action"].collidepoint(e.pos):
                            go_inside(card["action"][1], False)
                            continue
                        if rects["card"].collidepoint(e.pos):
                            continue
                    if not inside:
                        hit = next((k for k, _, r in make_buttons(sim) if r.collidepoint(e.pos)), None)
                        if hit:
                            card = None
                            if hit == "learn":
                                sim.learn()
                            elif hit in ("sleep", "nosleep"):
                                sim.start(hit)
                            elif hit == "wake":
                                sim.wake()
                            else:
                                sim.sub = hit
                            continue
                    down, dragging = e.pos, False
                elif e.button == 3:
                    if inside:
                        inside = None
                    else:
                        net.dead[np.hypot(psx - e.pos[0], psy - e.pos[1]) < 55] = True
            elif e.type == pygame.MOUSEMOTION and down and not inside:
                if not dragging and math.hypot(e.pos[0] - down[0], e.pos[1] - down[1]) > 6:
                    dragging = True
                if dragging:
                    yaw += e.rel[0] * 0.008
                    pitch = max(-1.4, min(1.4, pitch + e.rel[1] * 0.008))
            elif e.type == pygame.MOUSEBUTTONUP and e.button == 1 and down:
                if not dragging:
                    mx, my = e.pos
                    now = time.time()
                    if inside:
                        if tin >= 1:
                            part = inside.part_at(mx, my)
                            if part:
                                kind, pid = part
                                if kind in ("bouton", "terminal") and pid is not None and part == last_part and now - last_t < 0.4:
                                    go_inside(pid, False)
                                else:
                                    card = inside_card(kind, pid, net, inside.i)
                                    if kind in ("soma", "nucleus", "membrane", "channel"):
                                        net.stim[sel] = 6
                            else:
                                card = None
                                net.stim[sel] = 6
                            last_t, last_part = now, part
                    else:
                        dn = np.hypot(psx - mx, psy - my)
                        j = int(dn.argmin())
                        if dn[j] < max(10, 9 * pk[j]) + 8:
                            if j == last_j and now - last_t < 0.4:
                                go_inside(j, True)
                            else:
                                select(j)
                                net.stim[dn < 55] = 6
                                card = neuron_card(net, j, sim)
                            last_j = j
                        else:
                            k, dl = pick_link(net, psx, psy, mx, my)
                            card = link_card(net, k, sim) if dl < 7 else None
                            if dl >= 7:
                                net.stim[dn < 55] = 6
                            last_j = -1
                        last_t = now
                down, dragging = None, False

        if not inside:
            keys = pygame.key.get_pressed()
            st = 9 / zoom
            panx = max(-700, min(700, panx + (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * st))
            pany = max(-700, min(700, pany + (keys[pygame.K_DOWN] - keys[pygame.K_UP]) * st))
            yaw += (keys[pygame.K_d] - keys[pygame.K_a]) * 0.03 + (0.004 if spin else 0)
            pitch = max(-1.4, min(1.4, pitch + (keys[pygame.K_e] - keys[pygame.K_q]) * 0.02))
            zoom = max(0.3, min(6.0, zoom * 1.025 ** (keys[pygame.K_w] - keys[pygame.K_s])))

        if not paused:
            for _ in range(speed * sim.speedmul):
                fired = sim.tick(drive, gain, plastic)
                idx = np.nonzero(fired)[0]
                raster.append(idx)
                rate.append(len(idx))
                vtrace.append(30.0 if fired[sel] else net.v[sel])
                if inside:
                    if fired[inside.i]:
                        inside.fire()
                else:
                    for i in idx:
                        for j in net.out[i]:
                            if len(pulses) < 2000:
                                pulses.append([i, j, 0.0])
            if inside:
                inside.step(net)

        fat = sim.fatigue
        screen.fill((8, 10, 30) if sim.state == "sleep" and not sim.up else BG)
        if inside:
            inside.draw(ins_surf, net, font, big, fat, sim.memset)
            if tin < 1:
                ease = 1 - (1 - tin) ** 3
                sc = 0.12 + 0.88 * ease
                w, h = max(2, int(PANEL_X * sc)), max(2, int(H * sc))
                cxp = enter_from[0] + (PANEL_X / 2 - enter_from[0]) * ease
                cyp = enter_from[1] + (H / 2 - enter_from[1]) * ease
                screen.blit(pygame.transform.smoothscale(ins_surf, (w, h)), (cxp - w / 2, cyp - h / 2))
                tin += 0.045
            else:
                screen.blit(ins_surf, (0, 0))
        else:
            psx, psy, pk, pz = project(net.pos, yaw, pitch, zoom, panx, pany)
            if fat > 0.25:  # struggling neurons jitter
                psx = psx + np.random.randn(net.n) * 1.6 * fat
                psy = psy + np.random.randn(net.n) * 1.6 * fat
            fog = np.clip(1.15 - (pz + 250) / 700, 0.35, 1.0)
            X, Y = psx.tolist(), psy.tolist()
            sz = net.size[net.lp, net.lq]
            favg = (fog[net.lq] + fog[net.lp]) / 2
            ismem = np.zeros(len(sz), bool)
            ismem[sim.memidx] = True
            bright = np.where(ismem, np.clip(0.45 * favg * (1 + 0.4 * (sz - 1)), 0, 1),
                              np.clip(0.32 * favg * (1 + 0.5 * (sz - 1)), 0, 0.85))
            base_c = np.where(ismem[:, None], np.array(GOLD, float), net.lcol)
            cols = (np.array(BG) + (base_c - np.array(BG)) * bright[:, None]).astype(int).tolist()
            wd = np.clip(1 + ((sz - 1) * 1.2).astype(int), 1, 5).tolist()
            for c, a, b, w_ in zip(cols, net.lq.tolist(), net.lp.tolist(), wd):
                pygame.draw.line(screen, c, (X[a], Y[a]), (X[b], Y[b]), w_)
            pulses = [p for p in pulses if p[2] < 1.0]
            for p in pulses:
                a, b, t = p[0], p[1], p[2]
                col = EXC_C if net.exc[a] else INH_C
                pygame.draw.circle(screen, col, (X[a] + (X[b] - X[a]) * t, Y[a] + (Y[b] - Y[a]) * t), 2)
                if not paused:
                    p[2] += 0.09
            for i in np.argsort(-pz).tolist():
                base = EXC_C if net.exc[i] else INH_C
                f = float(fog[i])
                fl = float(net.flash[i])
                r = max(2, int((5 + 4 * fl) * pk[i]))
                if net.dead[i]:
                    col = (int(55 * f), int(55 * f), int(60 * f))
                else:
                    col = vcolor(net.v[i], base, f)
                    if fat > 0:
                        col = lerp3(col, (210, 80, 60), 0.35 * fat)
                    if net.lapse[i] > 0:
                        col = tuple(int(c * 0.4) for c in col)
                    if fl > 0.15:
                        glow = pygame.Surface((80, 80), pygame.SRCALPHA)
                        pygame.draw.circle(glow, (*base, int(110 * fl)), (40, 40), int(min(38, 18 * pk[i])))
                        screen.blit(glow, (X[i] - 40, Y[i] - 40))
                pygame.draw.circle(screen, col, (X[i], Y[i]), r)
                if net.hip[i]:
                    pygame.draw.circle(screen, PURPLE, (X[i], Y[i]), r + 3, 1)
                if i in sim.ring:
                    pygame.draw.circle(screen, sim.ring[i], (X[i], Y[i]), r + 6, 2)
                if i == sel:
                    pygame.draw.circle(screen, (255, 255, 255), (X[i], Y[i]), r + 9, 1)
            if sim.state == "learn":
                for L, n_ in zip("ABC", sim.cur["h"]):
                    screen.blit(mid.render(L, True, GOLD), (X[n_] + 10, Y[n_] - 22))
            lx, ly, _, _ = project(np.array([net.pos[net.hip].mean(axis=0) if net.hip.any() else CENTER,
                                             [600.0, 70.0, 0.0]]), yaw, pitch, zoom, panx, pany)
            screen.blit(font.render("Hippocampus (fast, temporary)", True, PURPLE), (lx[0] - 100, ly[0] + 40))
            screen.blit(font.render("Neocortex (slow, permanent)", True, (110, 150, 170)), (lx[1] - 90, ly[1]))
            title, tcol, desc = sim.banner()
            screen.blit(big.render(title, True, tcol), (16, 12))
            for k, ln in enumerate(wrap(desc, font, 470)):
                screen.blit(font.render(ln, True, (170, 180, 205)), (16, 40 + 16 * k))
            yb = 40 + 16 * len(wrap(desc, font, 470)) + 6
            if sim.note:
                screen.blit(font.render(sim.note, True, (255, 140, 110)), (16, yb))
                yb += 16
            if sim.state == "sleep":
                screen.blit(font.render(f"slow wave: {'UP (active, replaying)' if sim.up else 'DOWN (silent)'}", True, (140, 150, 230)), (16, yb))
                yb += 16
            screen.blit(font.render("click a neuron, pathway or label for info  |  double-click a neuron: go inside", True, (95, 105, 135)), (16, yb))
            mpos = pygame.mouse.get_pos()
            for key, txt, rect in make_buttons(sim):
                active = key == sim.state or key == sim.sub
                col = BTN_COL[key]
                bgc = lerp3((22, 26, 42), col, 0.55 if active else (0.25 if rect.collidepoint(mpos) else 0.1))
                pygame.draw.rect(screen, bgc, rect, border_radius=8)
                pygame.draw.rect(screen, col, rect, 2, border_radius=8)
                tt = font.render(txt, True, (240, 243, 250))
                screen.blit(tt, tt.get_rect(center=rect.center))

        rects = draw_card(screen, card, font, mid) if card else {}

        # ---- side panel ----
        pygame.draw.rect(screen, (16, 19, 30), (PANEL_X, 0, W - PANEL_X, H))
        pygame.draw.line(screen, (40, 46, 70), (PANEL_X, 0), (PANEL_X, H))
        px, pw = PANEL_X + 20, W - PANEL_X - 40

        def label(txt, y, f=font, c=(190, 200, 220)):
            screen.blit(f.render(txt, True, c), (px, y))

        label("NEUROSYSTEMS", 14, big, (230, 235, 250))
        label(f"E type : {TYPES[net.type_key][0]}", 46)
        label(f"noise  : {drive:.1f}   gain: {gain:.1f}", 64)
        label(f"plastic: {'ON' if plastic else 'off'}   speed: {speed}x{' (auto x4)' if sim.speedmul > 1 else ''}", 82)
        hz = sum(rate) / max(1, len(rate)) / net.n * 1000
        label(f"rate   : {hz:.1f} Hz/neuron   lesions: {int(net.dead.sum())}", 100)

        label("Spike raster (last 300 ms)", 124, c=(130, 140, 170))
        ry, rh = 142, 120
        pygame.draw.rect(screen, (10, 12, 20), (px, ry, pw, rh))
        pygame.draw.line(screen, (55, 65, 100), (px, ry + int(sel * rh / net.n)), (px + pw, ry + int(sel * rh / net.n)))
        for t, idx in enumerate(raster):
            x = int(px + t * pw / HIST)
            for i in idx:
                c = EXC_C if net.exc[i] else INH_C
                yy = ry + int(i * rh / net.n)
                screen.set_at((x, yy), c)
                screen.set_at((x + 1, yy), c)

        label("Population activity", 270, c=(130, 140, 170))
        ay, ah = 288, 60
        pygame.draw.rect(screen, (10, 12, 20), (px, ay, pw, ah))
        if len(rate) > 1:
            m = max(10, max(rate))
            pts = [(px + t * pw / HIST, ay + ah - r / m * (ah - 4) - 2) for t, r in enumerate(rate)]
            pygame.draw.lines(screen, (120, 230, 170), False, pts, 1)

        kind = "excitatory" if net.exc[sel] else "inhibitory"
        label(f"Neuron #{sel} membrane potential ({kind})", 356, c=(130, 140, 170))
        vy, vh = 374, 70
        pygame.draw.rect(screen, (10, 12, 20), (px, vy, pw, vh))
        if len(vtrace) > 1:
            pts = [(px + t * pw / HIST, vy + vh - (v + 80) / 115 * (vh - 4) - 2) for t, v in enumerate(vtrace)]
            pygame.draw.lines(screen, EXC_C if net.exc[sel] else INH_C, False, pts, 1)

        label("Memories: pathway strength", 454, c=(130, 140, 170))
        screen.blit(font.render("hippocampus", True, PURPLE), (px + 34, 472))
        screen.blit(font.render("neocortex", True, (110, 150, 170)), (px + 172, 472))
        for k, m in enumerate(sim.mems):
            yy = 492 + k * 20
            label(m["name"], yy - 2)
            for bx, ln, c in ((px + 34, sim.links(m["h"]), GOLD), (px + 172, sim.links(m["k"]) if m["k"] else [], GREEN)):
                pygame.draw.rect(screen, (30, 36, 56), (bx, yy, 110, 10))
                pygame.draw.rect(screen, c, (bx, yy, int(110 * strength(net, ln)), 10))
        label("Fatigue (adenosine)", 578, c=(130, 140, 170))
        pygame.draw.rect(screen, (30, 36, 56), (px, 598, pw, 10))
        pygame.draw.rect(screen, lerp3((110, 220, 150), (255, 90, 70), fat), (px, 598, int(pw * fat), 10))

        hint = (["Arrows move  A/D turn  Q/E tilt  W/S zoom", "Drag orbit  H home  O spin  N new net",
                 "Click info  DblClick neuron: inside", "RMB lesion  L unlesion"] if not inside else
                ["Click any part for an explanation", "DblClick input/terminal: jump there",
                 "ESC / B / RMB: back to network"])
        hint.append("-/= noise  ,/. gain  T plasticity  1-4 type")
        for k, h_ in enumerate(hint):
            label(h_, 626 + k * 17, c=(110, 120, 150))

        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()
    pygame.quit()
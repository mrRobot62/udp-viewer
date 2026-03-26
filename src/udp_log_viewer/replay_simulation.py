from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass
from typing import Deque, List


def drain_replay_batch(lines: Deque[str], lines_per_tick: int) -> List[str]:
    batch: List[str] = []
    for _ in range(lines_per_tick):
        if not lines:
            break
        batch.append(lines.popleft())
    return batch


def build_temperature_replay_sample() -> List[str]:
    return [
        "[CSV_TEMP];14047;2633;228;14220;2666;221;0;0;1",
    ]


def build_text_replay_sample() -> List[str]:
    return [
        "[MAIN/INFO] ======================================================",
        "[MAIN/INFO] === ESP32-S3 + ST7701 480x480 + LVGL 9.4.x + Touch ===",
        "[MAIN/INFO] ======================================================",
        "[WIFI] Connected. IP: 192.168.0.103",
        "[UDP] selftest: sending 3 packets...",
        "[HOST/INFO] STATUS received, mask=0x0000 (    0x0000), adc=[203,0,0,0] tempRaw=203",
        "[OVEN/INFO] [T11] mode=0 door=0 lock=0 ntc=20.30 core=23.15 ui=23.15 ctrl=23.15 tgt=40.00 lo=37.00 hi=43.00 heaterIntent=0 heatRemMs=0 restRemMs=0",
        "[OVEN/INFO] [T11] mode=0 door=0 lock=0 ntc=20.80 core=23.20 ui=23.20 ctrl=23.20 tgt=40.00 lo=37.00 hi=43.00 heaterIntent=1 heatRemMs=2000 restRemMs=0",
        "[HEATER/DBG] pwm=4000Hz duty=50%",
        "[HOST/INFO] STATUS received, mask=0x1010 (    0x1010), adc=[205,0,0,0] tempRaw=205",
        "[UI/INFO] Listener: ON — 0.0.0.0:10514",
        "[UI/ERROR] UDP listener error: [Errno 9] Bad file descriptor",
        "[OVEN/WARN] Door opened — entering WAIT",
        "[OVEN/INFO] [T11] mode=1 door=1 lock=1 ntc=21.00 core=23.25 ui=23.25 ctrl=23.25 tgt=40.00 lo=37.00 hi=43.00 heaterIntent=0 heatRemMs=0 restRemMs=3000",
        "[MAIN/INFO] Sample done.",
    ]


@dataclass
class TextSimulationState:
    seq: int = 0
    ntc: float = 22.0
    core: float = 23.0
    target: float = 40.0
    heater: int = 0
    mask: int = 0x0000


def next_text_simulation_line(state: TextSimulationState) -> str:
    state.seq += 1
    if state.seq % 13 == 0:
        state.heater = 1 - state.heater
    if state.heater:
        state.ntc += 0.15 + random.random() * 0.05
        state.core += 0.05 + random.random() * 0.03
    else:
        state.ntc -= 0.03 + random.random() * 0.02
        state.core -= 0.01 + random.random() * 0.01
    state.ntc = max(18.0, min(80.0, state.ntc))
    state.core = max(18.0, min(70.0, state.core))
    if state.seq % 40 == 0:
        state.mask ^= 0x0010
    if state.seq % 97 == 0:
        state.mask ^= 0x0040
    roll = random.random()
    if roll < 0.45:
        adc0 = int(state.ntc * 10)
        return f"[HOST/INFO] STATUS received, mask=0x{state.mask:04x} (    0x{state.mask:04x}), adc=[{adc0},0,0,0] tempRaw={adc0}"
    if roll < 0.70:
        heater_intent = 1 if state.heater and state.core < (state.target - 0.3) else 0
        heat_rem = 800 if state.heater else 0
        rest_rem = 0 if state.heater else 1200
        low = state.target - 3.0
        high = state.target + 3.0
        return (
            f"[OVEN/INFO] [T11] mode=0 door=0 lock=0 "
            f"ntc={state.ntc:0.2f} core={state.core:0.2f} ui={state.core:0.2f} ctrl={state.core:0.2f} "
            f"tgt={state.target:0.2f} lo={low:0.2f} hi={high:0.2f} "
            f"heaterIntent={heater_intent} heatRemMs={heat_rem} restRemMs={rest_rem}"
        )
    if roll < 0.80:
        return f"[HEATER/INFO] {'ON' if state.heater else 'OFF'} pwm=4000Hz duty=50%"
    if roll < 0.90:
        return "[UI/DEBUG] screen_main tick"
    if roll < 0.97:
        return "[HOST/DEBUG] RX burst: 128 bytes"
    return "[HOST/ERROR] UART timeout while polling STATUS"


def next_logic_simulation_line(state: list[int]) -> str:
    for index in range(len(state)):
        if random.random() < 0.2:
            state[index] ^= 1
    values = ";".join(str(value) for value in state)
    return f"[CSV_LOGIC];{values}"

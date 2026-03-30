from __future__ import annotations
"""
Replay- und Simulationshelfer fuer den UDP-Viewer.

Die Datei hat zwei Aufgaben:

1. kleine Replay-Beispieldatensaetze fuer Demo-/Manuelltests bereitstellen
2. synthetische Live-Simulationen fuer Text-, Temperatur- und Logic-Daten erzeugen

Die Temperatur-PLOT-Simulation ist absichtlich kein physikalisch exaktes Modell.
Sie ist ein heuristisches Ofenmodell, das fuer UI- und Plot-Tests plausibles
Verhalten liefern soll:

- Chamber reagiert traeger und naehert sich der Zieltemperatur langsam
- HotSpot reagiert schneller, weil der Sensor naeher an der Heizquelle sitzt
- Door-Open-Ereignisse erzeugen kurzzeitige Temperaturverluste
- bei 150 °C HotSpot erfolgt ein harter Heater-Cutoff

Wichtig:
- `CSV_CLIENT_PLOT` und `CSV_HOST_PLOT` werden immer aus demselben
  Simulationszustand erzeugt
- beide Formate repraesentieren also denselben thermischen Zustand in
  unterschiedlicher Feldstruktur
"""

import random
from collections import deque
from dataclasses import dataclass
from typing import Deque, List


# ---------------------------------------------------------------------------
# Temperature-PLOT simulation tuning
# ---------------------------------------------------------------------------
# These constants define the qualitative physical behavior of the simple oven
# model. The intended direction is:
#
#   heater -> hotspot -> chamber
#
# So the HotSpot sensor reacts first and more aggressively. Chamber follows
# later because the drying chamber has more thermal inertia.

# Ambient temperature to which the whole system relaxes with heater OFF.
SIM_AMBIENT_TEMPERATURE = 22.0

# Hard HotSpot safety cutoff. Hitting this forces heater OFF immediately.
SIM_HOTSPOT_CUTOFF_TEMPERATURE = 150.0

# Chamber band around target that counts as "reached target".
SIM_TARGET_BAND = 1.5

# Probability per tick that a new door-open event starts after initial warm-up.
SIM_DOOR_OPEN_TRIGGER_PROBABILITY = 0.035

# Duration range of a simulated door-open event.
SIM_DOOR_OPEN_TICKS_MIN = 6
SIM_DOOR_OPEN_TICKS_MAX = 14

# Cooldown after a door-open event before heater may switch on again.
SIM_DOOR_OPEN_REST_TICKS = 6

# Cooldown after a normal heater-off cycle.
SIM_NORMAL_REST_TICKS_MIN = 4
SIM_NORMAL_REST_TICKS_MAX = 8

# Cooldown after hitting the HotSpot safety cutoff.
SIM_CUTOFF_REST_TICKS = 12

# Length of one heating pulse when heater switches on.
# With a 250 ms timer interval this corresponds to roughly 6..12 seconds.
SIM_HEATER_PULSE_TICKS_MIN = 24
SIM_HEATER_PULSE_TICKS_MAX = 48

# Chamber must drop this far below target before heating may restart.
SIM_HEATER_RESTART_DELTA = 1.5

# HotSpot must stay this far below cutoff before a new heating pulse is allowed.
SIM_CUTOFF_RESTART_MARGIN = 4.0

# Predictive estimate of how much of the current HotSpot-Chamber delta will
# still reach Chamber after heater-off. Larger values delay heater-off and let
# Chamber approach target more aggressively.
SIM_PREDICTIVE_CHAMBER_GAIN_FROM_HOTSPOT = 0.78

# Direct HotSpot rise while heater is ON. This is the primary energy source.
SIM_HOTSPOT_HEAT_BASE = 0.72

# Additional HotSpot rise when Chamber is still far below target.
SIM_HOTSPOT_HEAT_TARGET_FACTOR = 0.018
SIM_HOTSPOT_HEAT_TARGET_CAP = 0.55

# Random spread on active HotSpot heating.
SIM_HOTSPOT_HEAT_RANDOM_MIN = -0.03
SIM_HOTSPOT_HEAT_RANDOM_MAX = 0.08

# Chamber follows a hotter HotSpot through thermal coupling.
SIM_CHAMBER_FOLLOW_HEATING = 0.032

# Small direct Chamber rise from distributed system heating.
SIM_CHAMBER_HEAT_BASE = 0.020

# Random spread on Chamber heating.
SIM_CHAMBER_HEAT_RANDOM_MIN = -0.008
SIM_CHAMBER_HEAT_RANDOM_MAX = 0.020

# Door-open cooling: Chamber drops strongly to ambient, HotSpot also drops but
# is additionally pulled toward Chamber because the local hotspot dissipates.
SIM_CHAMBER_DOOR_COOLING = 0.10
SIM_HOTSPOT_TO_CHAMBER_DOOR_COUPLING = 0.18
SIM_HOTSPOT_TO_AMBIENT_DOOR_COOLING = 0.06

# Heater-off behavior: Chamber remains sluggish and may still gain some heat
# from a hotter HotSpot. HotSpot cools faster toward Chamber and ambient.
SIM_CHAMBER_AMBIENT_COOLING = 0.008
SIM_CHAMBER_FROM_HOTSPOT_COUPLING = 0.026
SIM_HOTSPOT_TO_CHAMBER_COOLING = 0.11
SIM_HOTSPOT_TO_AMBIENT_COOLING = 0.020

# Soft damping if Chamber overshoots target.
SIM_CHAMBER_OVERSHOOT_DAMPING = 0.035
SIM_CHAMBER_OVERSHOOT_DAMPING_CAP = 0.14

# Small random jitter so the curves do not look perfectly synthetic.
SIM_DOOR_CHAMBER_RANDOM_MIN = -0.08
SIM_DOOR_CHAMBER_RANDOM_MAX = 0.03
SIM_DOOR_HOTSPOT_RANDOM_MIN = -0.10
SIM_DOOR_HOTSPOT_RANDOM_MAX = 0.03
SIM_IDLE_CHAMBER_RANDOM_MIN = -0.03
SIM_IDLE_CHAMBER_RANDOM_MAX = 0.02
SIM_IDLE_HOTSPOT_RANDOM_MIN = -0.08
SIM_IDLE_HOTSPOT_RANDOM_MAX = 0.01

# Hard thermal clamps of the simplified model.
SIM_CHAMBER_MIN_TEMPERATURE = 18.0
SIM_CHAMBER_MAX_TEMPERATURE = 90.0
SIM_HOTSPOT_MIN_OFFSET_TO_CHAMBER = -2.0


def drain_replay_batch(lines: Deque[str], lines_per_tick: int) -> List[str]:
    """Liefert maximal `lines_per_tick` Replay-Zeilen aus einer Queue."""
    batch: List[str] = []
    for _ in range(lines_per_tick):
        if not lines:
            break
        batch.append(lines.popleft())
    return batch


def build_client_temperature_replay_sample() -> List[str]:
    """Kleines Einzelbeispiel im Client-PLOT-Format fuer Replay/Smoke-Tests."""
    return [
        "[CSV_CLIENT_PLOT];228;2508;228;221;2431;221;0;0;0",
    ]

def build_host_temperature_replay_sample() -> List[str]:
    """Kleines Einzelbeispiel im Host-PLOT-Format fuer Replay/Smoke-Tests."""
    return [
        "[CSV_HOST_PLOT];221;228;600;570,650;0",
    ]


def build_temperature_replay_sample() -> List[str]:
    """Kombiniert Client- und Host-PLOT-Beispiel zu einem zusammengehoerigen Replay."""
    return build_client_temperature_replay_sample() + build_host_temperature_replay_sample()

def build_text_replay_sample() -> List[str]:
    """Statisches Textlog-Replay fuer Demo- und Manual-Tests."""
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
    """
    Minimaler Zustand fuer die Textlog-Simulation.

    Die Werte werden nicht fuer echte Regelung verwendet, sondern nur, um
    in den synthetischen Logzeilen zeitlich konsistente Zahlen zu erzeugen.
    """
    seq: int = 0
    ntc: float = 22.0
    core: float = 23.0
    target: float = 40.0
    heater: int = 0
    mask: int = 0x0000


@dataclass
class TemperaturePlotSimulationState:
    """
    Laufzeit-Zustand der Temperatur-PLOT-Simulation.

    Feldbedeutung:
    - `chamber`: Temperatur des Gar-/Trocknungsraums
    - `hotspot`: lokaler Sensor nahe der Heizspirale
    - `target`: Solltemperatur
    - `heater_on`: aktueller Heizzustand
    - `door_open`: simulierte geoeffnete Tuer
    - `state`: kompakter Statuswert fuer CSV-Ausgabe
    - `heater_ticks_remaining`: Restlaufzeit des aktuellen Heizimpulses
    - `rest_ticks_remaining`: Sperrzeit bis zum naechsten Einschalten
    - `door_ticks_remaining`: Restdauer des aktuellen Door-Open-Ereignisses
    """
    seq: int = 0
    chamber: float = 21.9
    hotspot: float = 21.5
    target: float = 60.0
    heater_on: bool = False
    door_open: bool = False
    state: int = 0
    heater_ticks_remaining: int = 0
    rest_ticks_remaining: int = 0
    door_ticks_remaining: int = 0


def next_text_simulation_line(state: TextSimulationState) -> str:
    """
    Erzeugt genau eine synthetische Textlog-Zeile.

    Die Funktion mischt absichtlich verschiedene Log-Arten, damit Filter,
    Highlighting und die allgemeine Logansicht mit etwas Varianz getestet
    werden koennen.
    """
    state.seq += 1
    if state.seq % 13 == 0:
        state.heater = 1 - state.heater
    # Heizung an:
    # - `ntc` steigt etwas deutlicher
    # - `core` steigt moderater, damit die generierten Zahlen nicht zu hektisch wirken
    if state.heater:
        state.ntc += 0.25 + random.random() * 0.10
        state.core += 0.05 + random.random() * 0.03
    else:
        # Heizung aus:
        # - `ntc` faellt sichtbar ab
        # - `core` faellt langsamer, damit ein leichter Traegheitseindruck bleibt
        state.ntc -= 0.1 + random.random() * 0.02
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


def create_temperature_plot_simulation_state() -> TemperaturePlotSimulationState:
    """Erzeugt den Startzustand der Temperatur-PLOT-Simulation."""
    return TemperaturePlotSimulationState()


def next_temperature_plot_simulation_lines(state: TemperaturePlotSimulationState) -> list[str]:
    """
    Fortschreiben des thermischen Simulationszustands um genau einen Tick.

    Pro Aufruf werden zwei CSV-Zeilen erzeugt:
    - `CSV_CLIENT_PLOT`
    - `CSV_HOST_PLOT`

    Beide Zeilen repraesentieren denselben thermischen Zustand. Die Funktion ist
    damit die zentrale Stelle fuer:
    - Heizlogik
    - Door-Open-Verhalten
    - Chamber/HotSpot-Dynamik
    - Zieltemperatur-Annaeherung
    - HotSpot-Cutoff
    """
    state.seq += 1
    # ------------------------------------------------------------------
    # 1) Door-Open-Logik
    # ------------------------------------------------------------------
    # Ein Door-Open-Ereignis kann entweder noch laufen oder neu starten.
    # Sobald die Tuer offen ist, wird spaeter der Heater sofort deaktiviert.
    if state.door_ticks_remaining > 0:
        state.door_ticks_remaining -= 1
        state.door_open = True
    elif state.seq > 20 and random.random() < SIM_DOOR_OPEN_TRIGGER_PROBABILITY:
        state.door_ticks_remaining = random.randint(SIM_DOOR_OPEN_TICKS_MIN, SIM_DOOR_OPEN_TICKS_MAX)
        state.door_open = True
    else:
        state.door_open = False

    # ------------------------------------------------------------------
    # 2) Heater-Zustandsmaschine
    # ------------------------------------------------------------------
    # Reihenfolge ist wichtig:
    # - offene Tuer erzwingt OFF
    # - HotSpot-Cutoff erzwingt OFF
    # - ein aktiver Heizimpuls laeuft kontrolliert aus
    # - Restzeit blockiert Wiedereinschalten
    # - erst danach darf ein neuer Heizimpuls starten
    if state.door_open:
        state.heater_on = False
        state.heater_ticks_remaining = 0
        state.rest_ticks_remaining = max(state.rest_ticks_remaining, SIM_DOOR_OPEN_REST_TICKS)
    elif state.hotspot >= SIM_HOTSPOT_CUTOFF_TEMPERATURE:
        state.heater_on = False
        state.heater_ticks_remaining = 0
        state.rest_ticks_remaining = max(state.rest_ticks_remaining, SIM_CUTOFF_REST_TICKS)
    elif state.heater_on:
        state.heater_ticks_remaining = max(0, state.heater_ticks_remaining - 1)
        predictive_chamber_peak = state.chamber + max(0.0, state.hotspot - state.chamber) * SIM_PREDICTIVE_CHAMBER_GAIN_FROM_HOTSPOT
        if state.heater_ticks_remaining == 0 and (
            predictive_chamber_peak >= state.target - SIM_TARGET_BAND
            or state.hotspot >= min(SIM_HOTSPOT_CUTOFF_TEMPERATURE, state.target + 16.0)
        ):
            state.heater_on = False
            state.rest_ticks_remaining = random.randint(SIM_NORMAL_REST_TICKS_MIN, SIM_NORMAL_REST_TICKS_MAX)
    elif state.rest_ticks_remaining > 0:
        state.rest_ticks_remaining -= 1
    elif (
        state.chamber < state.target - SIM_HEATER_RESTART_DELTA
        and state.hotspot < SIM_HOTSPOT_CUTOFF_TEMPERATURE - SIM_CUTOFF_RESTART_MARGIN
    ):
        state.heater_on = True
        state.heater_ticks_remaining = random.randint(SIM_HEATER_PULSE_TICKS_MIN, SIM_HEATER_PULSE_TICKS_MAX)

    # ------------------------------------------------------------------
    # 3) Thermische Dynamik
    # ------------------------------------------------------------------
    # Es gibt drei Betriebsfaelle:
    # - Door-Open: Raum verliert schnell Energie
    # - Heater-On: HotSpot steigt direkt, Chamber folgt verzoegert
    # - Heater-Off: Chamber bleibt traege und profitiert kurz von Restwaerme
    if state.door_open:
        state.chamber += (
            (SIM_AMBIENT_TEMPERATURE - state.chamber) * SIM_CHAMBER_DOOR_COOLING
            + random.uniform(SIM_DOOR_CHAMBER_RANDOM_MIN, SIM_DOOR_CHAMBER_RANDOM_MAX)
        )
        state.hotspot += (
            (state.chamber - state.hotspot) * SIM_HOTSPOT_TO_CHAMBER_DOOR_COUPLING
            + (SIM_AMBIENT_TEMPERATURE - state.hotspot) * SIM_HOTSPOT_TO_AMBIENT_DOOR_COOLING
            + random.uniform(SIM_DOOR_HOTSPOT_RANDOM_MIN, SIM_DOOR_HOTSPOT_RANDOM_MAX)
        )
    elif state.heater_on:
        # Physikalische Kausalitaet:
        # - zuerst steigt der HotSpot durch die Heizspirale
        # - Chamber folgt nur ueber thermische Kopplung und reagiert traeger
        # - je groesser die Entfernung zum Sollwert, desto staerker darf
        #   der HotSpot in der Startphase noch ansteigen
        target_gap = max(0.0, state.target - state.chamber)
        hotspot_gain = (
            SIM_HOTSPOT_HEAT_BASE
            + min(target_gap * SIM_HOTSPOT_HEAT_TARGET_FACTOR, SIM_HOTSPOT_HEAT_TARGET_CAP)
            + random.uniform(SIM_HOTSPOT_HEAT_RANDOM_MIN, SIM_HOTSPOT_HEAT_RANDOM_MAX)
        )
        state.hotspot += hotspot_gain
        state.chamber += (
            max(0.0, state.hotspot - state.chamber) * SIM_CHAMBER_FOLLOW_HEATING
            + SIM_CHAMBER_HEAT_BASE
            + random.uniform(SIM_CHAMBER_HEAT_RANDOM_MIN, SIM_CHAMBER_HEAT_RANDOM_MAX)
        )
    else:
        # Heater OFF:
        # - HotSpot verliert seinen Vorsprung schrittweise
        # - Chamber profitiert noch kurz von gespeicherter HotSpot-Energie
        # - beide bewegen sich langfristig Richtung Umgebung
        state.chamber += (
            (SIM_AMBIENT_TEMPERATURE - state.chamber) * SIM_CHAMBER_AMBIENT_COOLING
            + max(0.0, state.hotspot - state.chamber) * SIM_CHAMBER_FROM_HOTSPOT_COUPLING
            + random.uniform(SIM_IDLE_CHAMBER_RANDOM_MIN, SIM_IDLE_CHAMBER_RANDOM_MAX)
        )
        state.hotspot += (
            (state.chamber - state.hotspot) * SIM_HOTSPOT_TO_CHAMBER_COOLING
            + (SIM_AMBIENT_TEMPERATURE - state.hotspot) * SIM_HOTSPOT_TO_AMBIENT_COOLING
            + random.uniform(SIM_IDLE_HOTSPOT_RANDOM_MIN, SIM_IDLE_HOTSPOT_RANDOM_MAX)
        )

    # Oberhalb des Sollwertes wird Chamber leicht zurueckgenommen, damit die
    # Zielkurve erkennbar angesteuert wird und nicht unkontrolliert davonlaeuft.
    if state.chamber > state.target:
        state.chamber -= min(
            (state.chamber - state.target) * SIM_CHAMBER_OVERSHOOT_DAMPING,
            SIM_CHAMBER_OVERSHOOT_DAMPING_CAP,
        )

    # Harte Klammern fuer den Simulationsraum.
    state.chamber = max(SIM_CHAMBER_MIN_TEMPERATURE, min(SIM_CHAMBER_MAX_TEMPERATURE, state.chamber))
    state.hotspot = max(
        state.chamber + SIM_HOTSPOT_MIN_OFFSET_TO_CHAMBER,
        min(SIM_HOTSPOT_CUTOFF_TEMPERATURE, state.hotspot),
    )

    # Der Cutoff wird nach der Dynamik nochmals geprueft, damit auch ein
    # innerhalb des Ticks errechnetes Ueberschreiten sofort in OFF endet.
    if state.hotspot >= SIM_HOTSPOT_CUTOFF_TEMPERATURE:
        state.heater_on = False
        state.heater_ticks_remaining = 0
        state.rest_ticks_remaining = max(state.rest_ticks_remaining, SIM_CUTOFF_REST_TICKS)

    # Kompakter Statuswert fuer CSV-Ausgabe und Plot.
    if state.door_open:
        state.state = 3
    elif state.heater_on:
        state.state = 1
    elif abs(state.chamber - state.target) <= 2.5:
        state.state = 2
    else:
        state.state = 0

    # ------------------------------------------------------------------
    # 4) CSV-Abbildung
    # ------------------------------------------------------------------
    # Der interne Zustand wird zum Schluss in die beiden Ausgabeformate
    # transformiert. Client und Host unterscheiden sich nur in der
    # Feldstruktur, nicht in den zugrundeliegenden Temperaturwerten.
    hot_tenths = int(round(state.hotspot * 10))
    chamber_tenths = int(round(state.chamber * 10))
    hot_raw = hot_tenths
    chamber_raw = chamber_tenths
    hot_mv = hot_raw * 11
    chamber_mv = chamber_raw * 11
    heater = int(state.heater_on)
    door = int(state.door_open)
    target_tenths = int(round(state.target * 10))
    temp_min_tenths = int(round((state.target - 3.0) * 10))
    temp_max_tenths = int(round((state.target + 5.0) * 10))

    client_line = (
        f"[CSV_CLIENT_PLOT];{hot_raw};{hot_mv};{hot_tenths};"
        f"{chamber_raw};{chamber_mv};{chamber_tenths};{heater};{door};{state.state}"
    )
    host_line = (
        f"[CSV_HOST_PLOT];{chamber_tenths};{hot_tenths};{target_tenths};"
        f"{temp_min_tenths},{temp_max_tenths};{state.state}"
    )
    return [client_line, host_line]


def next_client_logic_simulation_line(state: list[int]) -> str:
    """Einfache Toggle-Simulation fuer Client-Logic-Kanaele."""
    for index in range(len(state)):
        if random.random() < 0.2:
            state[index] ^= 1
    values = ";".join(str(value) for value in state)
    return f"[CSV_CLIENT_LOGIC];{values}"

def next_host_logic_simulation_line(state: list[int]) -> str:
    """Einfache Toggle-Simulation fuer Host-Logic-Kanaele."""
    for index in range(len(state)):
        if random.random() < 0.2:
            state[index] ^= 1
    values = ";".join(str(value) for value in state)
    return f"[CSV_HOST_LOGIC];{values}"

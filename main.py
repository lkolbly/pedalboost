import ctypes
from ctypes import wintypes
import time
from enum import Enum
import msvcrt

"""
Joystick stuff, from
https://stackoverflow.com/questions/60309652/how-to-get-usb-controller-gamepad-to-work-with-python
"""

winmmdll = ctypes.WinDLL('winmm.dll')

# [joyGetNumDevs](https://docs.microsoft.com/en-us/windows/win32/api/joystickapi/nf-joystickapi-joygetnumdevs)
"""
UINT joyGetNumDevs();
"""
joyGetNumDevs_proto = ctypes.WINFUNCTYPE(ctypes.c_uint)
joyGetNumDevs_func  = joyGetNumDevs_proto(("joyGetNumDevs", winmmdll))

# [joyGetDevCaps](https://docs.microsoft.com/en-us/windows/win32/api/joystickapi/nf-joystickapi-joygetdevcaps)
"""
MMRESULT joyGetDevCaps(UINT uJoyID, LPJOYCAPS pjc, UINT cbjc);

32 bit: joyGetDevCapsA
64 bit: joyGetDevCapsW

sizeof(JOYCAPS): 728
"""
joyGetDevCaps_proto = ctypes.WINFUNCTYPE(ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p, ctypes.c_uint)
joyGetDevCaps_param = (1, "uJoyID", 0), (1, "pjc", None), (1, "cbjc", 0)
joyGetDevCaps_func  = joyGetDevCaps_proto(("joyGetDevCapsW", winmmdll), joyGetDevCaps_param)

# [joyGetPosEx](https://docs.microsoft.com/en-us/windows/win32/api/joystickapi/nf-joystickapi-joygetposex)
"""
MMRESULT joyGetPosEx(UINT uJoyID, LPJOYINFOEX pji);
sizeof(JOYINFOEX): 52
"""
joyGetPosEx_proto = ctypes.WINFUNCTYPE(ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p)
joyGetPosEx_param = (1, "uJoyID", 0), (1, "pji", None)
joyGetPosEx_func  = joyGetPosEx_proto(("joyGetPosEx", winmmdll), joyGetPosEx_param)

# joystickapi - joyGetNumDevs
def joyGetNumDevs():
    try:
        num = joyGetNumDevs_func()
    except:
        num = 0
    return num

# joystickapi - joyGetDevCaps
def joyGetDevCaps(uJoyID):
    try:
        buffer = (ctypes.c_ubyte * JOYCAPS.SIZE_W)()
        p1 = ctypes.c_uint(uJoyID)
        p2 = ctypes.cast(buffer, ctypes.c_void_p)
        p3 = ctypes.c_uint(JOYCAPS.SIZE_W)
        ret_val = joyGetDevCaps_func(p1, p2, p3)
        ret = (False, None) if ret_val != JOYERR_NOERROR else (True, JOYCAPS(buffer))   
    except:
        ret = False, None
    return ret 

# joystickapi - joyGetPosEx
def joyGetPosEx(uJoyID):
    try:
        buffer = (ctypes.c_uint32 * (JOYINFOEX.SIZE // 4))()
        buffer[0] = JOYINFOEX.SIZE
        buffer[1] = JOY_RETURNALL
        p1 = ctypes.c_uint(uJoyID)
        p2 = ctypes.cast(buffer, ctypes.c_void_p)
        ret_val = joyGetPosEx_func(p1, p2)
        ret = (False, None) if ret_val != JOYERR_NOERROR else (True, JOYINFOEX(buffer))   
    except:
        ret = False, None
    return ret 

JOYERR_NOERROR = 0
JOY_RETURNX = 0x00000001
JOY_RETURNY = 0x00000002
JOY_RETURNZ = 0x00000004
JOY_RETURNR = 0x00000008
JOY_RETURNU = 0x00000010
JOY_RETURNV = 0x00000020
JOY_RETURNPOV = 0x00000040
JOY_RETURNBUTTONS = 0x00000080
JOY_RETURNRAWDATA = 0x00000100
JOY_RETURNPOVCTS = 0x00000200
JOY_RETURNCENTERED = 0x00000400
JOY_USEDEADZONE = 0x00000800
JOY_RETURNALL = (JOY_RETURNX | JOY_RETURNY | JOY_RETURNZ | \
                 JOY_RETURNR | JOY_RETURNU | JOY_RETURNV | \
                 JOY_RETURNPOV | JOY_RETURNBUTTONS)

# joystickapi - JOYCAPS
class JOYCAPS:
    SIZE_W = 728
    OFFSET_V = 4 + 32*2
    def __init__(self, buffer):
        ushort_array = (ctypes.c_uint16 * 2).from_buffer(buffer)
        self.wMid, self.wPid = ushort_array  

        wchar_array = (ctypes.c_wchar * 32).from_buffer(buffer, 4)
        self.szPname = ctypes.cast(wchar_array, ctypes.c_wchar_p).value
        
        uint_array = (ctypes.c_uint32 * 19).from_buffer(buffer, JOYCAPS.OFFSET_V) 
        self.wXmin, self.wXmax, self.wYmin, self.wYmax, self.wZmin, self.wZmax, \
        self.wNumButtons, self.wPeriodMin, self.wPeriodMax, \
        self.wRmin, self.wRmax, self.wUmin, self.wUmax, self.wVmin, self.wVmax, \
        self.wCaps, self.wMaxAxes, self.wNumAxes, self.wMaxButtons = uint_array

# joystickapi - JOYINFOEX
class JOYINFOEX:
  SIZE = 52
  def __init__(self, buffer):
      uint_array = (ctypes.c_uint32 * (JOYINFOEX.SIZE // 4)).from_buffer(buffer) 
      self.dwSize, self.dwFlags, \
      self.dwXpos, self.dwYpos, self.dwZpos, self.dwRpos, self.dwUpos, self.dwVpos, \
      self.dwButtons, self.dwButtonNumber, self.dwPOV, self.dwReserved1, self.dwReserved2 = uint_array

"""
Keyboard stuff from
https://stackoverflow.com/questions/13564851/how-to-generate-keyboard-events
"""

user32 = ctypes.WinDLL('user32', use_last_error=True)

INPUT_MOUSE    = 0
INPUT_KEYBOARD = 1
INPUT_HARDWARE = 2

KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP       = 0x0002
KEYEVENTF_UNICODE     = 0x0004
KEYEVENTF_SCANCODE    = 0x0008

MAPVK_VK_TO_VSC = 0

# msdn.microsoft.com/en-us/library/dd375731
VK_TAB  = 0x09
VK_MENU = 0x12
VK_SPACE = 0x20
VK_SHIFT = 0x10
VK_ZERO = 0x30
VK_ONE = 0x31 # Power to engines
VK_TWO = 0x32 # Power to lasers
VK_THREE = 0x33 # Power to shields
VK_FOUR = 0x34 # Balance power
VK_SEVEN = 0x37 # Focus shields front
VK_EIGHT = 0x38 # Focus shields back
VK_NINE = 0x39 # Balance shields
VK_G = 0x47 # Target my attacker
VK_J = 0x4A # Drift (while boosting)

# C struct definitions

wintypes.ULONG_PTR = wintypes.WPARAM

class MOUSEINPUT(ctypes.Structure):
    _fields_ = (("dx",          wintypes.LONG),
                ("dy",          wintypes.LONG),
                ("mouseData",   wintypes.DWORD),
                ("dwFlags",     wintypes.DWORD),
                ("time",        wintypes.DWORD),
                ("dwExtraInfo", wintypes.ULONG_PTR))

class KEYBDINPUT(ctypes.Structure):
    _fields_ = (("wVk",         wintypes.WORD),
                ("wScan",       wintypes.WORD),
                ("dwFlags",     wintypes.DWORD),
                ("time",        wintypes.DWORD),
                ("dwExtraInfo", wintypes.ULONG_PTR))

    def __init__(self, *args, **kwds):
        super(KEYBDINPUT, self).__init__(*args, **kwds)
        # some programs use the scan code even if KEYEVENTF_SCANCODE
        # isn't set in dwFflags, so attempt to map the correct code.
        if not self.dwFlags & KEYEVENTF_UNICODE:
            self.wScan = user32.MapVirtualKeyExW(self.wVk,
                                                 MAPVK_VK_TO_VSC, 0)

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = (("uMsg",    wintypes.DWORD),
                ("wParamL", wintypes.WORD),
                ("wParamH", wintypes.WORD))

class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = (("ki", KEYBDINPUT),
                    ("mi", MOUSEINPUT),
                    ("hi", HARDWAREINPUT))
    _anonymous_ = ("_input",)
    _fields_ = (("type",   wintypes.DWORD),
                ("_input", _INPUT))

LPINPUT = ctypes.POINTER(INPUT)

def _check_count(result, func, args):
    if result == 0:
        raise ctypes.WinError(ctypes.get_last_error())
    return args

user32.SendInput.errcheck = _check_count
user32.SendInput.argtypes = (wintypes.UINT, # nInputs
                             LPINPUT,       # pInputs
                             ctypes.c_int)  # cbSize

# Functions

def PressKey(hexKeyCode):
    x = INPUT(type=INPUT_KEYBOARD,
              ki=KEYBDINPUT(wVk=hexKeyCode))
    user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))

def ReleaseKey(hexKeyCode):
    x = INPUT(type=INPUT_KEYBOARD,
              ki=KEYBDINPUT(wVk=hexKeyCode,
                            dwFlags=KEYEVENTF_KEYUP))
    user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))

def AltTab():
    """Press Alt+Tab and hold Alt key for 2 seconds
    in order to see the overlay.
    """
    for i in range(5):
        print(f"{5-i}")
        time.sleep(1)
    PressKey(VK_SPACE)
    time.sleep(0.1)
    ReleaseKey(VK_SPACE)
    time.sleep(2)
    PressKey(VK_SHIFT)
    time.sleep(2)
    ReleaseKey(VK_SHIFT)

    #PressKey(VK_MENU)   # Alt
    #PressKey(VK_TAB)    # Tab
    #ReleaseKey(VK_TAB)  # Tab~
    #time.sleep(2)
    #ReleaseKey(VK_MENU) # Alt~

class State(Enum):
    IDLE = 1
    BOOST = 2
    DRIFT = 3

class AxisStateTracker:
    """
    Tracks the current state of axes for the quadrant
    Raw values are from 2^16 to 0. This is cleaned up into 0.0 to 1.0
    """

    def __init__(self, state_ranges):
        """
        state_ranges is a list of (state, min, max) pairs
        """
        self.state = state_ranges[0][0]
        self.state_ranges = state_ranges

    def update(self, raw):
        """
        Returns the current state based on the value, and whether it changed
        """
        value = (65536 - raw) / 65536
        #print(value, self.state)
        new_state = None
        for (state, minimum, maximum) in self.state_ranges:
            #print(minimum, value, maximum)
            if minimum < value and maximum > value:
                new_state = state
                break
        if new_state == None:
            return (self.state, False)
        if self.state == None:
            #print(new_state, self.state)
            self.state = new_state
            return (self.state, False)
        elif self.state != new_state:
            #print(new_state, self.state)
            self.state = new_state
            return (self.state, True)
        else:
            return (self.state, False)

def TapKey(code, duration=0.02):
    PressKey(code)
    time.sleep(duration)
    ReleaseKey(code)
    time.sleep(duration)

def set_power_with_shields(levels):
    KEYS = {
        "engine": VK_ONE,
        "laser": VK_TWO,
        "shield": VK_THREE,
    }
    if levels[0][0] == levels[1][0] and levels[1][0] == levels[2][0]:
        # Case 1
        print("Evenly distributed")
        TapKey(VK_FOUR)
    elif levels[0][0] > levels[1][0] and levels[1][0] == levels[2][0]:
        # Case 2
        print(f"Maximum to {levels[0][1]}, distribute rest")
        TapKey(VK_FOUR)
        TapKey(KEYS[levels[0][1]])
        TapKey(KEYS[levels[0][1]])
    elif levels[0][0] > levels[1][0] and levels[1][0] > levels[2][0]:
        # Case 3
        print(f"Maximum to {levels[0][1]}, remaining to {levels[1][1]}")
        TapKey(VK_FOUR)
        TapKey(KEYS[levels[0][1]])
        TapKey(KEYS[levels[1][1]])
        TapKey(KEYS[levels[0][1]])
        TapKey(KEYS[levels[1][1]])
        TapKey(KEYS[levels[0][1]])
    elif levels[0][0] == levels[1][0] and levels[1][0] > levels[2][0]:
        # Case 4
        print(f"3/4ths to {levels[0][1]} and {levels[1][1]}")
        TapKey(VK_FOUR)
        TapKey(KEYS[levels[0][1]])
        TapKey(KEYS[levels[1][1]])
        TapKey(KEYS[levels[0][1]])
        TapKey(KEYS[levels[1][1]])
    else:
        print("Unknown case!")
        TapKey(VK_FOUR)

def set_power_without_shields(levels):
    KEYS = {
        "engine": VK_ONE,
        "laser": VK_TWO,
        "shield": VK_THREE,
    }
    levels = list(filter(lambda level: level[1] != "shield", levels))
    if levels[0][0] == levels[1][0]:
        # Case 1
        print("Evenly distributed")
        TapKey(VK_FOUR)
    elif levels[0][0] > levels[1][0]:
        # Case 2
        print(f"Maximum to {levels[0][1]}, distribute rest")
        TapKey(VK_FOUR)
        TapKey(KEYS[levels[0][1]])
        TapKey(KEYS[levels[0][1]])
        TapKey(KEYS[levels[0][1]], duration=0.03)
    else:
        print("Unknown case!")
        TapKey(VK_FOUR)

if __name__ == "__main__":
    #AltTab()
    num = joyGetNumDevs()
    print(num)
    ret, caps, startinfo = False, None, None
    pedals_id = None
    quadrant_id = None
    for id in range(num):
        ret, caps = joyGetDevCaps(id)
        if ret:
            print(f"gamepad detected: {caps.szPname} nbuttons={caps.wNumButtons} naxes={caps.wNumAxes}")
            if caps.wNumButtons == 0 and caps.wNumAxes == 3:
                # This is the rudder pedals
                ret, startinfo = joyGetPosEx(id)
                pedals_id = id
                #break
            elif caps.wNumButtons == 12 and caps.wNumAxes == 6:
                _ = joyGetPosEx(id)
                quadrant_id = id

    """for i in range(5):
        print(f"{5-i}")
        time.sleep(1)
    TapKey(VK_FOUR)
    #time.sleep(0.02)
    TapKey(VK_ONE)

    time.sleep(5)
    TapKey(VK_FOUR)
    #time.sleep(0.02)
    TapKey(VK_TWO)42"""

    axis_states = [
        ("low", 0, 0.25),
        ("middle", 0.35, 0.65),
        ("high", 0.75, 1.0),
    ]
    shield_tracker = AxisStateTracker(axis_states)

    engine_pwr_tracker = AxisStateTracker(axis_states)
    laser_pwr_tracker = AxisStateTracker(axis_states)
    shield_pwr_tracker = AxisStateTracker(axis_states)
    shields_enabled = False
    power_change_needed = False

    last_buttons = None
    last_state = State.IDLE
    state = State.IDLE
    tm_since_boost = time.time()
    while True:
        if msvcrt.kbhit() and msvcrt.getch() == chr(27).encode(): # detect ESC
            break

        """
        Update the pedals (boost/drift)
        """
        ret, info = joyGetPosEx(pedals_id)
        if ret:
            axisXY = [info.dwXpos - startinfo.dwXpos, info.dwYpos - startinfo.dwYpos]
            #print(f"Axes: {info.dwXpos}")
            if state == State.IDLE:
                if info.dwXpos > 65535 * 0.9:
                    state = State.BOOST
                    PressKey(VK_SPACE)
                    time.sleep(0.03)
                    ReleaseKey(VK_SPACE)
            elif state == State.BOOST:
                if info.dwXpos < 65535 * 0.7:
                    state = State.DRIFT
                    PressKey(VK_J)
                    tm_since_boost = time.time()
            elif state == State.DRIFT:
                if info.dwXpos > 65535 * 0.9:
                    # Go back to boosting
                    state = State.BOOST
                    ReleaseKey(VK_J)
                    time.sleep(0.05)
                    PressKey(VK_SPACE)
                    time.sleep(0.03)
                    ReleaseKey(VK_SPACE)
                elif info.dwXpos < 65535 * 0.2:
                    # Done drifting
                    state = State.IDLE
                    ReleaseKey(VK_J)
                    print(f"Time drifting: {time.time() - tm_since_boost}")
            if state != last_state:
                print(f"{state}")
                last_state = state

        """
        Update the quadrant (power management)
        """
        ret, info = joyGetPosEx(quadrant_id)
        if ret:
            # From left to right, the axes are X, Y, Z, V, U, R. Each is lowest at max extent
            #print(f"{info.dwXpos} {info.dwYpos} {info.dwZpos} {info.dwRpos} {info.dwUpos} {info.dwVpos}")
            buttons = [(1 << i) & info.dwButtons != 0 for i in range(32)]
            if last_buttons is None:
                last_buttons = buttons

            for (idx,(b, b_last)) in enumerate(zip(buttons, last_buttons)):
                if b and not b_last:
                    print(f"Button {idx}")

            if buttons[11] and not last_buttons[11]:
                # Disable shields
                shields_enabled = False
                power_change_needed = True
            elif buttons[10] and not last_buttons[10]:
                # Enable shields
                shields_enabled = True
                power_change_needed = True

            if buttons[1] and not last_buttons[1]:
                # Target attacker
                TapKey(VK_G)
                pass

            if buttons[3] and not last_buttons[3]:
                # Convert power to lasers
                PressKey(VK_SHIFT)
                TapKey(VK_TWO)
                ReleaseKey(VK_SHIFT)
                pass

            if buttons[2] and not last_buttons[2]:
                # Convert power to engines
                PressKey(VK_SHIFT)
                TapKey(VK_ONE)
                ReleaseKey(VK_SHIFT)
                pass

            shield_state, did_change = shield_tracker.update(info.dwVpos)
            if did_change:
                print(shield_state)
                if shield_state == "low":
                    TapKey(VK_EIGHT)
                elif shield_state == "middle":
                    TapKey(VK_NINE)
                elif shield_state == "high":
                    TapKey(VK_SEVEN)

            engine_state, engine_did_change = engine_pwr_tracker.update(info.dwXpos)
            laser_state, laser_did_change = laser_pwr_tracker.update(info.dwYpos)
            shield_state, shield_did_change = shield_pwr_tracker.update(info.dwZpos)
            if engine_did_change or laser_did_change or shield_did_change or power_change_needed:
                power_change_needed = False
                print(engine_state, laser_state, shield_state)

                # Broadly speaking, there are a couple of different possible power states:
                # - All distributed
                # - One maxed out, remaining power distributed evenly
                # - One maxed out, remaining power in only one subsystem
                # - Two at 3/4s power, remaining one empty.
                # Note that there are other representable powers that we're not allowing.
                # The game supports any distribution of 12 pips across 3 stacks of at most 8.
                #
                # 1. If the quadrant is all equal, we distribute power evenly.
                # 2. If one lever is ahead of the other two (which are both equal), max one out
                #    and distribute the others.
                # 3. If one lever is ahead of another which is ahead of another, max one out
                #    and put the remaining power in the middle lever.
                # 4. If two levers are equal and ahead of the third, put both at 3/4 power.
                STATE_VALUES = {
                    "high": 2,
                    "middle": 1,
                    "low": 0,
                }
                engine_state = STATE_VALUES[engine_state]
                laser_state = STATE_VALUES[laser_state]
                shield_state = STATE_VALUES[shield_state]

                levels = [(engine_state, "engine"), (laser_state, "laser"), (shield_state, "shield")]
                levels.sort(reverse=True)

                print(levels)

                if shields_enabled:
                    set_power_with_shields(levels)
                else:
                    set_power_without_shields(levels)

            last_buttons = buttons

from miditok import Event


def writeToFile(path, content):
    if type(content) is not str:
        content = str(content)
    with open(path, "w") as f:
        f.write(content)


# Function to read from text from txt file:
def readFromFile(path):
    with open(path, "r") as f:
        return f.read()


def chain(input, funcs, *params):
    res = input
    for func in funcs:
        try:
            res = func(res, *params)
        except TypeError:
            res = func(res)
    return res


def to_beat_str(value, beat_res=8):
    values = [
        int(int(value * beat_res) / beat_res),
        int(int(value * beat_res) % beat_res),
        beat_res,
    ]
    return ".".join(map(str, values))


def to_base10(beat_str):
    integer, decimal, base = split_dots(beat_str)
    return integer + decimal / base


def split_dots(value):
    return list(map(int, value.split(".")))


class TextToEvent:
    def getlist(self, type, value):
        event_type = str(type).lower()
        try:
            return getattr(self, event_type, "")(value)
        except Exception as e:
            print("Error: Unknown event", type, value)
            raise e

    def time_shift(self, value):
        return [Event("Time-Shift", value)]

    def note_on(self, value):
        return [Event("Note-On", value), Event("Velocity", 100)]

    def note_off(self, value):
        return [Event("Note-Off", value)]

    def velocity(self, value):
        return []

    def chord(self, value):
        return []

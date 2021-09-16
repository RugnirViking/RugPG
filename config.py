import os


def check_for_config(filename) -> bool:
    return os.path.exists(filename)


class Config:
    OPTION_KEYS = ["MasterVolume",
                   "MusicVolume",
                   "GameVolume",
                   "AllowDebug",
                   ]

    DEFAULT_VALUES = [0.5,
                      1,
                      1,
                      False,
                      ]
    VAL_TYPES = [float,
                 float,
                 float,
                 bool,
                 ]

    def __init__(self):
        filename = "config.ini"
        self.values = {}
        if check_for_config(filename):
            if self.load_config(filename):
                pass
            else:
                # error with config. rename broken config file and create a new one from default
                self.rename_config(filename)
                self.set_to_defaults()
                self.create_config_file(filename)
        else:
            # no config file, create fresh one from defaults
            self.set_to_defaults()
            self.create_config_file(filename)

    def __str__(self):
        """Return a list of the options with their values"""
        val = "# Option | Value"

        for key in self.values:
            val = val + f"\n{key}: {str(self.values[key])}"

        return val

    def create_config_file(self, filename: str):
        f = open(filename, "a")
        f.write("# Winterfjell Deeps Config File. lines beginning with '#' are comments")
        x = 0

        for key in self.values:
            f.write(f"\n{key}: {str(self.values[key])}")
            x = x + 1

        f.close()

    def load_config(self, filename):
        file1 = open(filename, 'r')
        count = 0
        valid = True

        while True:

            # Get next line from file
            line = file1.readline()

            # if line is empty
            # end of file is reached
            if not line:
                break

            x = line.split(":")
            if line.startswith("#"):
                # ignore comments
                continue

            if len(x) < 2:
                # at least one value
                continue
            self.values[x[0]] = self.VAL_TYPES[count](x[1])
            count += 1

        file1.close()
        if len(self.values) == len(self.OPTION_KEYS):
            return True
        return False

    def set_to_defaults(self):
        x = 0
        self.values = {}
        for key in self.OPTION_KEYS:
            self.values[key] = self.DEFAULT_VALUES[x]
            x += 1

    def rename_config(self, filename: str):
        new_name = filename + "_old"
        os.rename(filename, new_name)

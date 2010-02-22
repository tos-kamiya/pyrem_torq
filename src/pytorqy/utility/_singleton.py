# reference http://en.wikipedia.org/wiki/Singleton_pattern#Python

class Singleton(type):
    def __init__(self, name, bases, dict):
        super(Singleton, self).__init__(name, bases, dict)
        self.instance = None
    def __call__(self, *args, **kw):
        if self.instance is None:
            self.instance = super(Singleton, self).__call__(*args, **kw)
        return self.instance

class SingletonWoInitArgs(type):
    def __init__(self, name, bases, dict):
        super(SingletonWoInitArgs, self).__init__(name, bases, dict)
        self.instance = None
    def __call__(self):
        if self.instance is None:
            self.instance = super(SingletonWoInitArgs, self).__call__()
        return self.instance

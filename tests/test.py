#  MIT License
#  Copyright (C) Michael Tao-Yi Lee (taoyil AT UCI EDU)
# A descriptor class
class PositiveAttr(object):
    def __init__(self, name):
        self.name = name
        self.parent = None

    def __get__(self, instance, cls):
        print("get called", instance, cls)
        return instance.__dict__[self.name]

    def __set__(self, instance, value):
        print("set called", instance, value)
        if value < 0 or value == 0:
            raise ValueError("Value of {} should be positive.".format(self.name))
        else:
            instance.__dict__[self.name] = value


class Employee:
    age = PositiveAttr('age')

    def __init__(self):
        self.age = 10
        self.age_descriptor.parent = 25

    def __getattribute__(self, key):
        if key == 'age_descriptor':
            return self.__class__.__dict__[key.replace("_descriptor", "")]
        v = object.__getattribute__(self, key)
        if hasattr(v, '__get__'):
            return v.__get__(None, self)
        return v


if __name__ == '__main__':
    tom = Employee()
    tom.age = 20
    print(tom.age)
    print(tom.age_descriptor)
    print(tom.age_descriptor.parent)
    tom.age_descriptor.parent = 10
    print(tom.age_descriptor.parent)
    print(tom.__dict__)

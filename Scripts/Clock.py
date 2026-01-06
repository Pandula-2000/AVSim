import datetime


class Time:
    _resolution = 1
    t = 1  # minutes (1 to 1440)
    DAY = 1
    sigma_random = 0

    # NOTE: Time starts at 1 and ends at 1440 minutes for a day.
    @staticmethod
    def init():
        Time.t = 1
        Time.sigma_random = (1 / 4) * (5 * Time._resolution + 15)

    @staticmethod
    def set_t(t):
        Time.t = t

    @classmethod
    def increment_time_unit(cls):
        if cls.get_time() < 1440:
            cls.t += cls._resolution
        else:
            cls.DAY += 1
            cls.t = 1

    @classmethod
    def increment_day(cls, d_count=1):
        cls.DAY += d_count


    @staticmethod
    def get_time():
        return Time.t

    @staticmethod
    def get_time_resolution():
        return Time._resolution

    @staticmethod
    def get_DAY():
        return Time.DAY

    @staticmethod
    def get_dayType():
        day = Time.DAY % 7
        if day == 0:
            return 7
        return day

    @staticmethod
    def get_sigmaRandom():
        return Time.sigma_random

    @staticmethod
    def minutes_to_time(minutes):
        hours = minutes // 60
        mins = minutes % 60
        time_str = f"{hours:02}:{mins:02}"
        return time_str

    @staticmethod
    def machineTime_to_humanTime(t):
        H, M = 0, 0
        H = int(t / 60)
        M = t % 60
        return f"{H}:{str(M).zfill(2)}"


if __name__ == "__main__":
    Time.init()
    # Time.set_t(1440)
    # print(Time.get_time())
    # Time.increment_time_unit()
    print(Time.get_DAY())
    # print(Time.get_time())
    # print(Time.machineTime_to_humanTime(370))
    Time.increment_day(17)
    print(Time.get_DAY())

"""Static BRUN TIME$ formatting model, not a captured runtime observation."""

def text_time(cx, dx):
    assert type(cx) is int and type(dx) is int and 0 <= cx < 65536 and 0 <= dx < 65536
    hour, minute, second, hundredth = cx >> 8, cx & 255, dx >> 8, dx & 255
    assert hour < 24 and minute < 60 and second < 60 and hundredth < 100
    if hundredth >= 50:
        second += 1
        if second == 60:
            second = 0
            minute += 1
            if minute == 60:
                minute = 0
                hour += 1  # Original routine has no 24-hour wrap here.
    return f'{hour:02}:{minute:02}:{second:02}'

if __name__ == '__main__':
    assert text_time(0, (59 << 8) | 49) == '00:00:59'
    assert text_time(0, (59 << 8) | 50) == '00:01:00'
    assert text_time((23 << 8) | 59, (59 << 8) | 49) == '23:59:59'
    assert text_time((23 << 8) | 59, (59 << 8) | 50) == '24:00:00'
    print('4 static rounding/carry examples passed; no target launched')

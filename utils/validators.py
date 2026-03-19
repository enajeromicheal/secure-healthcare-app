def validate_age(age):
    try:
        age = int(age)
        return 0 < age < 120
    except:
        return False


def validate_sex(value):
    return value in ["M", "F"]


def validate_blood_pressure(value):
    try:
        bp = int(value)
        return 50 < bp < 250
    except:
        return False
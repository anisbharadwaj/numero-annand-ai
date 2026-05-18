def validate_request(data):
    blocked_words = ["hack", "attack", "malware"]

    for word in blocked_words:
        if word in str(data).lower():
            return False

    return True

# Example rule: credential stuffing detection
def credential_stuffing(events_df, threshold=100, window_minutes=10):
    # events_df columns: timestamp, ip, user_id, event_type
    # detect IPs with > threshold failed auths in window
    events_df['ts'] = pd.to_datetime(events_df['timestamp'])
    # sliding window logic omitted for brevity
    # return list of suspicious IPs with counts
    return suspicious_ips

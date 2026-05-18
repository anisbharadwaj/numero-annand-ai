import pandas as pd
import numpy as np

def disparate_impact(df, group_col, outcome_col, privileged_value):
    # P(A=1|privileged) / P(A=1|unprivileged)
    priv = df[df[group_col]==privileged_value]
    unpriv = df[df[group_col]!=privileged_value]
    p_priv = priv[outcome_col].mean()
    p_unpriv = unpriv[outcome_col].mean()
    if p_priv == 0: return None
    return p_unpriv / p_priv

def confusion_by_group(df, group_col, y_true, y_pred):
    groups = {}
    for g, sub in df.groupby(group_col):
        tp = ((sub[y_true]==1) & (sub[y_pred]==1)).sum()
        tn = ((sub[y_true]==0) & (sub[y_pred]==0)).sum()
        fp = ((sub[y_true]==0) & (sub[y_pred]==1)).sum()
        fn = ((sub[y_true]==1) & (sub[y_pred]==0)).sum()
        groups[g] = {"TP":tp,"TN":tn,"FP":fp,"FN":fn}
    return groups

def equalized_odds(df, group_col, y_true, y_pred):
    groups = confusion_by_group(df, group_col, y_true, y_pred)
    # compute FPR and FNR per group
    metrics = {}
    for g, c in groups.items():
        fpr = c["FP"] / (c["FP"] + c["TN"]) if (c["FP"]+c["TN"])>0 else None
        fnr = c["FN"] / (c["FN"] + c["TP"]) if (c["FN"]+c["TP"])>0 else None
        metrics[g] = {"FPR": fpr, "FNR": fnr}
    return metrics

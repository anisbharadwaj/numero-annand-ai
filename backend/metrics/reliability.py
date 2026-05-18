from sklearn.calibration import calibration_curve
from sklearn.metrics import accuracy_score

def accuracy(y_true, y_pred):
    return accuracy_score(y_true, y_pred)

def calibration_curve_stats(y_true, y_prob, n_bins=10):
    prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=n_bins)
    return {"prob_true": prob_true.tolist(), "prob_pred": prob_pred.tolist()}

def hallucination_rate(generated_texts, references):
    # simple heuristic: count outputs with no overlap with references or with low BLEU
    from nltk.translate.bleu_score import sentence_bleu
    rates = []
    for gen, ref in zip(generated_texts, references):
        score = sentence_bleu([ref.split()], gen.split())
        rates.append(score)
    # hallucination if BLEU < 0.1
    return sum(1 for s in rates if s < 0.1) / len(rates)

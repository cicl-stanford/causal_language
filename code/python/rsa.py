import numpy as np
import pandas as pd
import json


def load_aspects(unoise, num_samples=1000):

    with open(f"aspects_paper/aspects_noise_{unoise}_samples_{num_samples}.json", "r") as f:
        aspects_json = json.load(f)

    aspects = np.array([asp["rep"] for asp in aspects_json[0]])[:30, :]
    
    return aspects

def conjunction(a, b):
    return a * b

def disjunction(a, b):
    return a + b - (a * b)

def softmax(x, beta, axis):
    expo = np.exp(beta * x)
    summands = np.sum(expo, axis=axis)
    if axis == 1:
        return expo / summands[:, np.newaxis]
    else:
        return expo / summands[np.newaxis, :]

def meaning(utterance, aspects, nap=None, softener=None):

    w, h, s, m, u = (0, 1, 2, 3, 4)

    whe = aspects[:, w]
    how = aspects[:, h]
    suf = aspects[:, s]
    mov = aspects[:, m]
    uni = aspects[:, u]

    if utterance == "caused":
        semval = conjunction(disjunction(whe, suf), how)

        if not softener is None:
            soft_mov = disjunction(mov, softener)
            soft_uni = disjunction(uni, softener)

            semval = conjunction(semval, soft_mov)
            semval = conjunction(semval, soft_uni)
    
    elif utterance == "enabled":
        semval = disjunction(whe, suf)
    
    elif utterance == "affected":
        semval = disjunction(disjunction(whe, how), suf)

    elif utterance == "made_no_diff":

        not_whe = 1 - whe
        not_how = 1 - how
        not_suf = 1 - suf

        if not nap is None:
            not_how = disjunction(not_how, nap)

        semval = conjunction(conjunction(not_whe, not_how), not_suf)

    else:
        raise ValueError("Invalid utterance value")
    
    return semval
    
def l0(aspects, nap=None, softener=None, vocab=["caused", "enabled", "affected", "made_no_diff"]):
    semvals = np.array([meaning(utt, aspects, nap, softener) for utt in vocab]).T
    return semvals/semvals.sum(axis=0)[np.newaxis, :]

def s1(aspects, so, nap=None, softener=None):
    lit_list = l0(aspects, nap, softener)
    # return lit_list/lit_list.sum(axis=1)[:, np.newaxis]
    return softmax(lit_list, so, 1)

def l1(aspects, so, nap=None, softener=None):
    speaker_probs = s1(aspects, so, nap, softener)
    return speaker_probs/speaker_probs.sum(axis=0)[np.newaxis, :]

def s2(aspects, so, nap=None, softener=None):
    listener_probs = l1(aspects, so, nap, softener)
    # return listener_probs/listener_probs.sum(axis=1)[:, np.newaxis]
    return softmax(listener_probs, so, 1)

def semantics(aspects, beta, nap=None, softener=None, vocab=["caused", "enabled", "affected", "made_no_diff"]):
    semvals = np.array([meaning(utt, aspects, nap, softener) for utt in vocab]).T
    return softmax(semvals, beta, 1)
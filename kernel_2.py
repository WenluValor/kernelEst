import math
import pandas as pd
import numpy as np
from scipy import integrate
from scipy.optimize import minimize_scalar
from scipy import stats
from cmath import exp

def opt_bandwith(index: int, p_value, fold=5):
    # index = 0, 1, 2, dimension
    minimum = minimize_scalar(func, bounds=(0, 100), method='bounded', args=(index, p_value, fold))
    return minimum.x

def func(bd, index: int, p_value, fold):
    vec_t = np.array([0, 0, 0, 0])
    for i in range(p_value + 1):
        file_name = str(i) + 'vec_t.csv'
        tmp_t = np.array(pd.read_csv(file_name, index_col=0))
        vec_t = np.vstack((vec_t, tmp_t))
    vec_t = np.delete(vec_t, 0, axis=0)

    t = vec_t[:, index]
    n = t.shape[0]
    ans = 0
    for k in range(fold):
        ind_set = range(k, n, fold)
        new_data = t[ind_set]
        old_data = np.delete(t, ind_set)
        ans += est_K(old_data, new_data, bd)
    ans /= fold
    return -ans

def est_K(old_data, new_data, bd):
    ans = 1
    for x in new_data:
        ans *= K(old_data, x, bd)
    return ans

def K(data, x, bd):
    ans = 0
    for dt in data:
        delta = abs(x - dt) / bd
        ans += (1 + delta + delta**2 / 3) * math.exp(-delta)
    ans /= (data.shape[0] * bd)
    return ans

def single_K(t, tau):
    # t in [-1, 1]
    delta = abs(t) / tau
    return (1 + delta + delta**2 / 3) * math.exp(-delta)

def int_f(t, w, tau):
    return single_K(t, tau) * exp(2 * math.pi * w * t * -1j).real

def p(w, low, up, tau: np.array):
    # low = -1
    # up = 1
    ans = 1
    for leng in tau:
        scale, err = integrate.quad(single_K, low, up, args=(leng))
        v, err = integrate.quad(int_f, low, up, args=(w, leng))
        ans *= v / scale
    return ans

def const_f(w, low, up, tau):
    norm = stats.norm(loc=0, scale=1)
    return p(w, low, up, tau) / norm.pdf(w)

def search_const(low, up, tau):
    res = minimize_scalar(const_f, args=(low, up, tau))
    const = res.fun
    return const

def sample_p(size: int, low, up, tau):
    count = 0
    norm = stats.norm(loc=0, scale=1)
    const = search_const(low, up, tau)
    ans = np.zeros([size])
    while (count < size):
        x = np.random.normal(loc=0, scale=1)
        u = np.random.uniform(0, 1)
        score = p(x, low, up, tau) / (const * norm.pdf(x))
        if (u <= score):
            ans[count] = x
            count += 1
    return  ans

def generate_wb(d: int, s: int, low, high, p_value):
    # d = 3
    # w, b: d*s
    w = np.zeros([d, s])
    b = np.zeros([d, s])
    tau = np.zeros([d])
    for i in range(d):
        tau[i] = opt_bandwith(i, p_value)

    for i in range (d):
        w[i] = sample_p(s, low, high, tau)
        b[i] = np.random.uniform(0, 2 * math.pi, size=s)

    DF = pd.DataFrame(w)
    DF.to_csv('w_js.csv')
    DF = pd.DataFrame(b)
    DF.to_csv('b_js.csv')

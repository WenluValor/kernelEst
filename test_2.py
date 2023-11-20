import math
import itertools
import numpy as np
import pandas as pd
import data_2 as dt_2
import random
import time
import torch

def set_global(c_value: np.array, s_value: int, n_value: int, p_value: int):
    global d, n, Y0, Z, s, p
    d = c_value.shape[0] - 1 # d = 3
    n = n_value
    s = s_value
    p = p_value

    Y0 = np.array(pd.read_csv('Y0.csv', index_col=0))[:, 0]
    Y0 = torch.tensor(Y0)

    Z = np.array(pd.read_csv('Z.csv', index_col=0))
    Z = torch.tensor(Z)

    global w_js, b_js
    w_js = np.array(pd.read_csv('w_js.csv', index_col=0))
    w_js = torch.tensor(w_js)

    b_js = np.array(pd.read_csv('b_js.csv', index_col=0))
    b_js = torch.tensor(b_js)

    return

def hat_fn_loss(X_test, Y_test, vec_c):
    Y_pred = hat_fn(X_test, vec_c)
    sum_main = torch.square(Y_test - Y_pred)
    loss_main = torch.mean(sum_main)
    return loss_main


def hat_fn(X_test, vec_c):
    mat_PSI = get_pdPSI(vec_t=X_test)
    return torch.matmul(mat_PSI.double(), vec_c.double())


def get_pdPSI(vec_t=1):
    if isinstance(vec_t, int):
        vec_t = np.array(pd.read_csv(str(0) + 'vec_t.csv', index_col=0))
        # vec_t *= 100
        vec_t = torch.tensor(vec_t)

    PSI = pdPSI(vec_t[0]).reshape(1, -1)
    for i in range(1, vec_t.shape[0]):
        tmp = pdPSI(vec_t[i]).reshape(1, -1)
        PSI = torch.cat((PSI, tmp), 0)
    return PSI


def pdPSI(t):
    # t = (t1, t2, t4) is not existing data
    PSI = psi_d(t)
    for i in range(p):
        PSI = torch.cat((PSI, first_diff_psi_d(t, i)), 0)
    return PSI

def first_diff_psi_d(t, part_ind: int, is_two_order=False):
    # part_ind = 0, 1, ... p-1
    mat_cos = tilde_psi(t, 0)
    mat_first = tilde_psi(t, 1)
    if is_two_order:
        mat_first = tilde_psi(t, 2)
    mat_zero = torch.zeros([d, s])

    ind_set = []
    for i in range(t.shape[0]):
        j = i + 1
        B = list(itertools.combinations(np.arange(t.shape[0]), j))
        ind_set = ind_set + B

    ans = torch.tensor([])
    for i in range(len(ind_set)):
        if part_ind in ind_set[i]:
            ind_i = int(ind_set[i][0])
            if ind_set[i][0] == part_ind:
                tmp = mat_first[part_ind]
            else:
                tmp = mat_cos[ind_i]

            pos = ind_set[i].index(part_ind)
            for l in range(1, len(ind_set[i])):
                ind_i = int(ind_set[i][l])
                if l == pos:
                    tmp = torch.kron(tmp, mat_first[part_ind])
                else:
                    tmp = torch.kron(tmp, mat_cos[ind_i])
        else:
            ind_i = int(ind_set[i][0])
            tmp = mat_zero[ind_i]
            for l in range(1, len(ind_set[i])):
                ind_i = int(ind_set[i][l])
                tmp = torch.kron(tmp, mat_zero[ind_i])

        ans = torch.cat((ans, tmp), 0)
    return ans

def psi_d(t):
    # t = torch, size = 3
    mat_cos = tilde_psi(t, 0)

    ind_set = []
    for i in range(t.shape[0]):
        j = i + 1
        B = list(itertools.combinations(np.arange(t.shape[0]), j))
        ind_set = ind_set + B

    ans = torch.tensor([])
    for i in range(len(ind_set)):
        ind_i = int(ind_set[i][0])
        tmp = mat_cos[ind_i]
        for l in range(1, len(ind_set[i])):
            ind_i = int(ind_set[i][l])
            tmp = torch.kron(tmp, mat_cos[ind_i])

        ans = torch.cat((ans, tmp), 0)
    return ans

def tilde_psi(t, order):
    # t of shape (d, )
    # order = 0, 1, 2
    # each row is s-dim random feature
    new_t = torch.kron(t.reshape(-1, 1), torch.ones(s))
    ans = new_t * w_js + b_js
    if order == 0:
        return torch.cos(ans) * math.sqrt(2 / s)
    elif order == 1:
        return -torch.sin(ans) * w_js * math.sqrt(2 / s)
    elif order == 2:
        return -torch.cos(ans) * w_js * w_js * math.sqrt(2 / s)
    return

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    random.seed(15)
    np.random.seed(4)
    set_global(c_value=np.array([1, 0.8, 0.7, 0.6]), s_value=5, n_value=200, p_value=2)

    C = np.array(pd.read_csv('torch_C.csv', index_col=0))[:, 0]
    C = torch.from_numpy(C).float()

    size = 1000
    A = np.zeros([size])
    time = 200
    B = np.zeros(time)

    np.random.seed(7)
    c = np.array([1, 0.8, 0.7, 0.6])
    for j in range(time):
        t = np.random.uniform(0.5, 1.5, size=(size, d))
        test = np.insert(t, d - 1, 1, axis=1)
        # t *= 100
        Y_test = torch.zeros([size])

        for i in range(size):
            Y_test[i] = torch.tensor(dt_2.true_f(c, test[i]))

        t = torch.tensor(t)
        B[j] = hat_fn_loss(X_test=t, Y_test=Y_test, vec_c=C)
        print(B[j])
        print('--------' + str(j) + '---------')

    print(np.mean(B))
    print(np.std(B))
    print('-=-=-=-=-==-=-=-=')

    exit(0)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/

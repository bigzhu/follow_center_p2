#!/usr/bin/env python
# -*- coding: utf-8 -*-


def trade(oper, max, atr, last_reverse_max):
    '''
    计算购入点
    >>> trade('buy', 1296940, 9800)
    {'reverse': 1277.34, 'intervals': [1294.49, 1292.04, 1289.59, 1287.14, 1284.69, 1282.24, 1279.79, 1277.34, 1274.89, 1272.44, 1269.99, 1267.54, 1265.09]}
    '''
    two_atr = 2 * atr
    one_quarter = atr / 4
    if oper == 'buy':
        reverse = max - two_atr
        stop = last_reverse_max - one_quarter
    else:
        reverse = max + two_atr
        stop = last_reverse_max + one_quarter
    result = dict(reverse=reverse / 1000)
    intervals = []
    tmp = max
    while True:
        # for i in range(1, 14):
        if oper == 'buy':
            tmp = tmp - one_quarter
            if tmp <= stop:
                break
        else:
            tmp = tmp + one_quarter
            if tmp >= stop:
                break
        intervals.append(tmp / 1000)
    result['intervals'] = intervals
    result['stop'] = stop / 1000
    return result


if __name__ == '__main__':
    import doctest
    doctest.testmod(verbose=False, optionflags=doctest.ELLIPSIS)

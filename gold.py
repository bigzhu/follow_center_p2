#!/usr/bin/env python
# -*- coding: utf-8 -*-


def getBuyReverse(max, atr):
    '''
    获取买入的反转点
    最高点两倍 atr 肯定要反转
    '''
    reverse = max - atr * 2
    return reverse


def getBuyStop(four_reverse_max, unit, reverse):
    '''
    止损点
    突破近4天最低点一个单位, 则止损
    如果反转点更高, 那么用反转点止损
    '''
    stop = four_reverse_max - unit
    if reverse > stop:
        return reverse
    else:
        return stop


def getSellReverse(max, atr):
    '''
    获取卖出的反转点
    '''
    reverse = max + atr * 2
    return reverse


def getSellStop(four_reverse_max, unit, reverse):
    '''
    获取卖出的止损点
    '''
    stop = four_reverse_max + unit
    if reverse < stop:
        return reverse
    else:
        return stop


def getBuyStepAndLose(max, unit, stop, reverse, week_atr, out1):
    '''
    计算买入点和可能的损失
    '''
    intervals = []
    tmp = max
    amount = 1
    while True:
        data = {}
        tmp -= unit
        if tmp <= reverse:
            break
        # 购买量
        data['amount'] = (amount) / 10
        # 入场点
        data['in'] = tmp / 1000
        # 出场点
        data['out'] = (tmp + week_atr) / 1000
        # 可能损失
        # 超过止损的没必要计算可能损失了
        # 价格比一级出场点的也不要买了
        if tmp > stop and tmp < out1:
            data['lose'] = (abs(tmp - stop) * amount) / 100 + 4
        amount += 1
        intervals.append(data)
    return intervals


def getSellStepAndLose(max, unit, stop, reverse, week_atr, out1):
    '''
    计算卖出点和可能的损失
    >>> stop = getSellStop()
    >>> getSellStepAndLose(1312830, 14760/4,  )
    '''
    intervals = []
    tmp = max
    amount = 1
    while True:
        data = {}
        tmp += unit
        if tmp >= reverse:
            break
        # 购买量
        data['amount'] = (amount) / 10
        # 入场点
        data['in'] = tmp / 1000
        # 出场点
        data['out'] = (tmp - week_atr) / 1000
        # 可能损失
        # 超过止损的没必要计算可能损失了
        # 比一级出场点还高, 没必要卖在这个点
        if tmp < stop and tmp > out1:
            data['lose'] = (abs(tmp - stop) * amount) / 100 + 4
        amount += 1
        intervals.append(data)
    return intervals


def getBuyOuts(four_reverse_max, atr, week_atr, unit):
    out1 = four_reverse_max + atr + unit  # 最低点+atr+unit
    out2 = four_reverse_max + 2 * atr  # 最低点加两倍atr
    out3 = four_reverse_max + week_atr  # 最低点加周波动
    if out1 > out2:
        out1, out2 = out2, out1
    if out2 > out3:
        out2, out3 = out3, out2

    return out1, out2, out3


def getSellOuts(four_reverse_max, atr, week_atr, unit):
    out1 = four_reverse_max - atr - unit
    out2 = four_reverse_max - 2 * atr
    out3 = four_reverse_max - week_atr
    if out1 < out2:
        out1, out2 = out2, out1
    if out2 < out3:
        out2, out3 = out3, out2
    return out1, out2, out3


def trade(oper, max, atr, four_reverse_max, week_atr):
    '''
    计算购入点
    >>> trade('buy', 1296940, 9800)
    {'reverse': 1277.34, 'intervals': [1294.49, 1292.04, 1289.59, 1287.14, 1284.69, 1282.24, 1279.79, 1277.34, 1274.89, 1272.44, 1269.99, 1267.54, 1265.09]}
    '''
    unit = atr / 4
    if oper == 'buy':
        out1, out2, out3 = getBuyOuts(four_reverse_max, atr, week_atr, unit)

        reverse = getBuyReverse(max, atr)
        stop = getBuyStop(four_reverse_max, unit, reverse)
        intervals = getBuyStepAndLose(max, unit, stop, reverse, week_atr, out1)

    else:

        out1, out2, out3 = getSellOuts(four_reverse_max, atr, week_atr, unit)

        reverse = getSellReverse(max, atr)
        stop = getSellStop(four_reverse_max, unit, reverse)
        intervals = getSellStepAndLose(
            max, unit, stop, reverse, week_atr, out1)

    result = dict(reverse=reverse / 1000)
    result['intervals'] = intervals
    result['stop'] = stop / 1000
    result['reverse'] = reverse / 1000

    result['out1'] = out1 / 1000
    result['out2'] = out2 / 1000
    result['out3'] = out3 / 1000

    return result


if __name__ == '__main__':
    import doctest
    doctest.testmod(verbose=False, optionflags=doctest.ELLIPSIS)

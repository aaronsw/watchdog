#!/usr/bin/env python
# encoding: utf-8
"""
captchasolver.py

This module provides mathematic captcha solvers. 
Created by Pradeep Gowda on 2008-04-22.
Copyright (c) 2008 Watchdog.net. All rights reserved.
"""

import sys
import os
import operator 

def toint(num):
    '''
    >>> toint('Two')
    2
    '''
    nums = ['zero','one', 'two', 'three', 'four','five', 'six', 'seven', 'eight', 'nine', 'ten']
    try:
        return int(num)
    except:
        num = num.lower()
        try:
            return nums.index(num)
        except:
            pass

def toop(op):
    '''
    >>> toop('X')
    <built-in function mul>
    '''
    op= op.lower()
    if op == 'x' or op == '*':
        return operator.mul
    if op == '+': return operator.add
    if op == '-': return operator.sub
    if op == '/': return operator.div
        
def sumof(captcha):
    '''
    >>> sumof('What is the sum of 1 plus 1')
    2
    '''
    captcha = captcha.replace('?','')
    st = captcha.find('sum of') + len('sum of')+1
    vars = captcha[st:].split(' ')
    total = 0
    for i in vars:
        num = toint(i)
        if num: total += num
    return total

def mathprob(captcha):
    '''
    >>> mathprob("Please solve the following math problem : two x 1")
    2
    >>> mathprob("Please solve the following math problem : two + three")
    5
    >>> mathprob("Please solve the following math problem: three x one?")
    3
    ''' 
    captcha = captcha.rstrip('?')
    vars = captcha.split(':')[1].split(' ')
    vars = [v for v in vars if v]
    op = [v for v in vars if v in('+','-','/', 'X','x', '*')][0]
    vars.remove(op)
    vars = [toint(v) for v in vars]
    return reduce(toop(op), vars)
    

def beginning(captcha):
    '''
    >>> beginning("01 : What number appears at the beginning of this question?")
    '01'
    '''
    return captcha.split(':')[0].strip()
    
def largest(captcha):
    '''
    >>> largest("Which of the numbers is largest: 1,3,7,19,2 ?")
    19
    '''
    foo = captcha.split(':')[1]
    foo.replace('?', '')
    foo = foo.split(',')
    nums = []
    for i in foo:
        try:
            nums.append(int(i))
        except:
            pass
    return max(nums)
    
def nextnum(captcha):
    '''
    >>> nextnum('Please provide the next number in this sequence: 2, 3, 4, 5:')
    6
    '''
    seq = captcha.split(':')[1]
    nums = [int(i.strip()) for i in seq.split(',') if i]
    diff = nums[1] - nums[0]
    next = nums[-1]+ diff
    return next
    

def minus(captcha):
    '''
    >>> minus ("what is 1 minus 1?")
    0
    >>> solve("what is ten minus one?")
    9
    '''
    captcha = captcha.rstrip('?')
    pos = captcha.find('what is')
    vars = captcha[pos+len('what is'):].split(' ')
    vars = [toint(v) for v in vars if toint(v)]
    return reduce(operator.sub, vars)

def solve(captcha):
    '''
    >>> solve("what is 4 minus 1?")
    3
    >>> solve("what is 1 minus 3?")
    -2
    >>> largest("Which of the numbers is largest: 1,3,7,19,2 ?")
    19
    >>> sumof('What is the sum of 21 plus 23')
    44
    >>> solve("What is ten minus one?")
    9
    >>> solve("Please solve the following math problem: three x one?    ")
    3
    '''
    captcha = captcha.strip().lower()
    result = None

    for s,f in [('sum of', sumof), ('math problem', mathprob),\
                    ('largest', largest), ('beginning', beginning), \
                    ('next number', nextnum), ('minus', minus)]:
        if captcha.find(s) > -1:  result =  f(captcha)
    return result

def _test():
    import doctest
    doctest.testmod()

if __name__ == '__main__':
    _test()

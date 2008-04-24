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
    nums = ['zero','one', 'two', 'three', 'four','five', 'six', 'seven', 'eight', 'nine']
    try:
        return int(num)
    except:
        num = num.lower()
        return nums.index(num)

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
    
def solve(captcha):
    '''
    >>> What is 2 minus one?
    1
    '''
    pass
    
def sumof(captcha):
    '''
    >>> sumof('What is the sum of 1 plus 1')
    2
    '''
    captcha = captcha.lower()
    st = captcha.find('sum of') + len('sum of')+1
    vars = captcha[st:].split(' ')
    #print "Vars: ", vars
    total = 0
    for i in vars:
        try:
            t = int(i)
            total += t
        except:
            pass
    return total

def mathprob(captcha):
    '''
    >>> mathprob("Please solve the following math problem : two x 1")
    2
    >>> mathprob("Please solve the following math problem : two + three")
    5
    '''    
    captcha = captcha.lower()
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
    Which of the numbers is largest: 1,3,7,19,2 ?
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
    captcha = captcha.lower()
    seq = captcha.split(':')[1]
    nums = [int(i.strip()) for i in seq.split(',') if i]
    diff = nums[1] - nums[0]
    next = nums[-1]+ diff
    return next
    
def solve(captcha):
    """docstring for solve
    >>> solve("What is the sum of 1 plus 1")
    2
    """
    if captcha.find('sum of ') > -1:
        return sumof(captcha)
    if captcha.find('math problem') > -1:
        return mathprob(captcha)

def _test():
    import doctest
    doctest.testmod()

if __name__ == '__main__':
    _test()
    #solve("What is the sum of 1 plus 1")

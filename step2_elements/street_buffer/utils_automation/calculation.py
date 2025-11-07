#!/usr/bin/env python
# coding: utf-8

# In[1]:


import numpy as np
import pandas as pd

def equations_top(T, p_0_top, p_10_top):
    if p_10_top < 0:
        return np.tan(np.radians(T)) / np.tan(np.radians(10 - T)) - (p_0_top / abs(p_10_top))
    else:
        return np.tan(np.radians(T)) / np.tan(np.radians(T - 10)) - (p_0_top / p_10_top)

def equations_bottom(T, p_0_bottom, p_10_bottom):
    if p_10_bottom < 0:
        return np.tan(np.radians(T)) / np.tan(np.radians(10 - T)) - (p_0_bottom / abs(p_10_bottom))
    else:
        return np.tan(np.radians(T)) / np.tan(np.radians(T - 10)) - (p_0_bottom / p_10_bottom)


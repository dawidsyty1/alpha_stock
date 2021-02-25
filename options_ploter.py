import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import csv
import glob
import os
import pandas as pd
import matplotlib.pyplot as plt


def combine_volumen(ticker):
    path = f'options/{ticker}/call'
    for filename in glob.glob(os.path.join(path, '*.csv')):
        print('call', filename)

    path = f'options/{ticker}/put'
    for filename in glob.glob(os.path.join(path, '*.csv')):
        print('put', filename)

combine_volumen('DBA')

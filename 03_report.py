import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from monitor import Monitor
import pandas as pd

mymon=Monitor(only_app_features=True)
df=mymon.get_dataframe(samples=None)

numeric_df = df.select_dtypes(include='number')

# Compute mean and variance
summary = pd.DataFrame({
    'mean': numeric_df.mean(),
    'variance': numeric_df.var()
})

print(summary)
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from monitor import Monitor
import pandas as pd
from pprint import pprint
from ai_module import AI
ai=AI()
#ai.train()
#a=ai.infer(single_step=False,plot_target='iperf_tcp_ul_sent_bps',horizon_step=5)
#pprint(a)

#a=ai.infer(single_step=False,plot_target='iperf_tcp_dl_received_bps',horizon_step=5)
#pprint(a)

a=ai.infer(single_step=False,plot_target='udpping_rtt_ns',horizon_step=5)
#pprint(a)

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Assuming 'metrics' is the dict returned from ai.infer(single_step=False)
metrics = a  # replace with your actual variable

# -------------------------
# 1. Horizon Accuracy Plot
# -------------------------
plt.figure(figsize=(12,6))
for target, vals in metrics.items():
    accuracy_horizon = 100 - np.array(vals['mape_per_horizon'])
    plt.plot(range(len(accuracy_horizon)), accuracy_horizon, marker='o', label=target)

plt.xlabel('Horizon Step', fontsize=14)
plt.ylabel('Accuracy (%)', fontsize=14)
plt.title('Prediction Accuracy per Horizon Step', fontsize=16)
plt.grid(True, linestyle='--', alpha=0.5)
plt.legend(fontsize=12)
plt.tight_layout()
plt.show()

# -------------------------
# 3. Summary Table
# -------------------------
rows = []
for target, vals in metrics.items():
    mae_mean = np.mean(vals['mae_per_horizon'])
    mse_mean = np.mean(vals['mse_per_horizon'])
    rmse_mean = np.mean(vals['rmse_per_horizon'])
    rmse_imp_mean = np.mean(vals['rmse_improvement_pct'])
    mape_mean = np.mean(vals['mape_per_horizon'])
    avg_err = vals['avg_error']
    std_err = vals['std_error']

    accuracy = 100 - mape_mean  # new metric

    rows.append({
        'Target': target,
        'MAE': mae_mean,
        'MSE': mse_mean,
        'RMSE': rmse_mean,
        'RMSE Improvement (%)': rmse_imp_mean,
        'MAPE (%)': mape_mean,
        'Accuracy (%)': accuracy,
        'Avg Error': avg_err,
        'Std Error': std_err
    })

df_summary = pd.DataFrame(rows)
print(df_summary)

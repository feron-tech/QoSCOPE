# ai.py (merged with model.py)
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
from torch.utils.data import DataLoader, TensorDataset
import gparams
from monitor import Monitor
import os
from pprint import pprint
import joblib
import matplotlib.pyplot as plt

# Map activations manually to avoid getattr issues
ACTIVATIONS = {
    "relu": nn.ReLU(),
    "tanh": nn.Tanh(),
    "sigmoid": nn.Sigmoid(),
    "leakyrelu": nn.LeakyReLU()
}

# Map optimizers
OPTIMIZERS = {
    "adam": optim.Adam,
    "sgd": optim.SGD,
    "rmsprop": optim.RMSprop
}

class LSTMModel(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim, num_layers, activation):
        super(LSTMModel, self).__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True)
        self.activation = ACTIVATIONS.get(activation.lower(), nn.ReLU())
        self.fc = nn.Linear(hidden_dim, output_dim)

    def forward(self, x):
        out, _ = self.lstm(x)
        out = out[:, -1, :]  # last timestep
        out = self.fc(out)  # no activation here
        return out

class AI:
    def __init__(self):
        self.base_config = gparams._AI

    def _merge_config(self, user_config: dict):
        """Merge user config with defaults from gparams._AI."""
        final_config = self.base_config.copy()
        for k, v in (user_config or {}).items():
            if k == "features":
                continue  # features always fixed
            final_config[k] = v
        return final_config

    def _prepare_data(self, df: pd.DataFrame, config, save_scalers=True):
        features = config["features"]
        targets = config["targets"]
        horizon = config["horizon"]
        timesteps = config["timesteps"]

        X = df[features].values
        y = df[targets].values

        # scaling
        if config["scaler"] == "standard":
            self.scaler_X = StandardScaler()
            self.scaler_y = StandardScaler()
        elif config["scaler"] == "robust":
            self.scaler_X = RobustScaler()
            self.scaler_y = RobustScaler()
        else:
            self.scaler_X = MinMaxScaler()
            self.scaler_y = MinMaxScaler()

        X_scaled = self.scaler_X.fit_transform(X)
        y_scaled = self.scaler_y.fit_transform(y)

        # Optionally save scalers
        if save_scalers:
            os.makedirs(gparams._MODEL_DIR, exist_ok=True)
            joblib.dump(self.scaler_X, os.path.join(gparams._MODEL_DIR, "scaler_X.save"))
            joblib.dump(self.scaler_y, os.path.join(gparams._MODEL_DIR, "scaler_y.save"))

        # build sequences
        X_seq, y_seq = [], []
        for i in range(len(X_scaled) - timesteps - horizon):
            X_seq.append(X_scaled[i:i+timesteps])
            y_seq.append(y_scaled[i+timesteps:i+timesteps+horizon])

        X_seq = np.array(X_seq)
        y_seq = np.array(y_seq)

        return TensorDataset(torch.tensor(X_seq, dtype=torch.float32), torch.tensor(y_seq, dtype=torch.float32))


    def train(self, user_config: dict = None):
        config = self._merge_config(user_config)

        # get data at runtime from Monitor
        to_test = config.get("remove_app_features", False)
        samples = config.get("train_samples", None)
        monitor = Monitor(remove_app_features=to_test)

        print(f"Entered train function with samples={samples}")
        df_train = monitor.get_dataframe(samples=samples)
        print(f"Got monitoring data raw with shape: {df_train.shape}")

        df_train = df_train.replace([np.inf, -np.inf], np.nan)
        df_train = df_train.fillna(0)
        print(f"Removed nans: {df_train.shape}")

        # --- Basic stats ---
        total_rows = len(df_train)
        rows_with_missing = df_train.isnull().any(axis=1).sum()
        perc_missing_rows = (rows_with_missing / total_rows) * 100 if total_rows > 0 else 0

        print(f"Total rows (experiments) = {total_rows}")
        print(f"Total rows with missing values = {rows_with_missing}")
        print(f"Percentage of missing rows = {perc_missing_rows:.2f}%")

        # --- Column-level missing percentage ---
        missing_report = (df_train.isnull().mean() * 100).round(2)
        missing_report = missing_report[missing_report > 0]  # drop 0%

        if not missing_report.empty:
            print("\nMissing value percentages by column:")
            for col, perc in missing_report.items():
                print(f"{col}: {perc}%")

        # Remove target columns from features to avoid leakage
        features = [f for f in config["features"] if f not in config["targets"]]
        config["features"] = features

        dataset = self._prepare_data(df_train, config)
        print(f"Completed data preparation with dataset size={len(dataset)}")

        loader = DataLoader(dataset, batch_size=config["batch_size"], shuffle=True)

        input_dim = len(config["features"])
        output_dim = len(config["targets"]) * config["horizon"]

        model = LSTMModel(
            input_dim=input_dim,
            hidden_dim=config["hidden_units"],
            output_dim=output_dim,
            num_layers=config["num_lstm_layers"],
            activation=config["activation"]
        )

        # device handling
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model.to(device)

        # loss
        loss_map = {
            "mse": nn.MSELoss,
            "mae": nn.L1Loss,
        }

        loss_name = config.get("loss", "mse").lower()
        criterion = loss_map.get(loss_name, nn.MSELoss)()

        # optimizer
        optimizer_cls = OPTIMIZERS.get(config["optimizer"].lower(), optim.Adam)
        optimizer = optimizer_cls(model.parameters(), lr=0.001)

        for epoch in range(config["epochs"]):
            for X_batch, y_batch in loader:
                X_batch, y_batch = X_batch.to(device), y_batch.to(device)

                optimizer.zero_grad()
                outputs = model(X_batch)
                loss = criterion(outputs, y_batch.view(y_batch.size(0), -1))
                loss.backward()

                # Clip exploding gradients
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)

                optimizer.step()
            print(f"Epoch {epoch + 1}/{config['epochs']}, Loss: {loss.item():.4f}")

        savename=os.path.join(gparams._MODEL_DIR,"lstm.pt")
        torch.save(model.state_dict(), savename)
        print("Model saved to:"+str(savename))
        return model

    def evaluate_predictions(self, predictions: dict, ground_truth: pd.DataFrame):
        """
        Evaluate predictions against ground truth with metrics and naive baseline.

        predictions: dict of shape {target: [seqs x horizon]}
        ground_truth: pd.DataFrame with columns for each target
        """
        targets = list(predictions.keys())
        horizon = self.base_config['horizon']

        metrics = {}

        for target in targets:
            pred_values = predictions[target]  # shape: (num_sequences, horizon)
            gt_values = ground_truth[target].values

            num_sequences = len(pred_values)

            # Ensure ground truth has enough rows
            required_rows = num_sequences + horizon - 1
            if len(gt_values) < required_rows:
                raise ValueError(f"Not enough ground truth rows for target '{target}' to match predictions.")

            # Build ground truth array: (num_sequences, horizon)
            gt_array = np.array([gt_values[i:i + horizon] for i in range(num_sequences)], dtype=np.float32)

            # Convert predictions to array
            pred_array = np.array(pred_values, dtype=np.float32)
            if pred_array.shape != gt_array.shape:
                raise ValueError(
                    f"Shape mismatch for target {target}: gt_array {gt_array.shape}, pred_array {pred_array.shape}")

            # Naive baseline: rolling mean over previous horizon
            naive_array = np.zeros_like(gt_array)
            naive_array[0, :] = gt_array[0, :]  # first row same as GT
            for i in range(1, num_sequences):
                naive_array[i, :] = gt_array[i - 1, :]  # naive: previous horizon

            # Metrics per horizon
            mse_per_horizon = np.mean((pred_array - gt_array) ** 2, axis=0)
            rmse_per_horizon = np.sqrt(mse_per_horizon)
            mae_per_horizon = np.mean(np.abs(pred_array - gt_array), axis=0)
            mape_per_horizon = np.mean(np.abs((pred_array - gt_array) / np.maximum(gt_array, 1e-8)), axis=0) * 100

            # Metrics for naive baseline
            rmse_naive = np.sqrt(np.mean((naive_array - gt_array) ** 2, axis=0))
            rmse_improvement = (rmse_naive - rmse_per_horizon) / (rmse_naive + 1e-8) * 100  # % improvement

            metrics[target] = {
                "rmse_per_horizon": rmse_per_horizon.tolist(),
                "mse_per_horizon": mse_per_horizon.tolist(),
                "mae_per_horizon": mae_per_horizon.tolist(),
                "mape_per_horizon": mape_per_horizon.tolist(),
                "rmse_avg": float(np.mean(rmse_per_horizon)),
                "rmse_improvement_pct": rmse_improvement.tolist(),
                "avg_error": float(np.mean(pred_array - gt_array)),
                "std_error": float(np.std(pred_array - gt_array))
            }

        return metrics


    def infer(self, samples=None, model_path=None, single_step=False, plot_target=None, horizon_step=0):

        horizon = self.base_config['horizon']
        to_test = self.base_config.get("remove_app_features", False)
        samples = samples or self.base_config.get("infer_samples", None)
        monitor = Monitor(remove_app_features=to_test)

        print(f"Entered infer function with samples={samples}")
        df = monitor.get_dataframe(samples=samples)
        df = df.replace([np.inf, -np.inf], np.nan).fillna(0)
        print(f"Got monitoring data cleaned with shape: {df.shape}")

        features = [f for f in self.base_config['features'] if f not in self.base_config['targets']]
        timesteps = self.base_config['timesteps']

        if len(df) < timesteps:
            raise ValueError(f"Not enough data for inference: require at least {timesteps} rows, got {len(df)}")

        model_path = model_path or os.path.join(gparams._MODEL_DIR, "lstm.pt")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at {model_path}")

        # Load trained scalers
        scaler_X_path = os.path.join(gparams._MODEL_DIR, "scaler_X.save")
        scaler_y_path = os.path.join(gparams._MODEL_DIR, "scaler_y.save")
        if not os.path.exists(scaler_X_path) or not os.path.exists(scaler_y_path):
            raise FileNotFoundError("Scalers not found. Train the model first.")
        self.scaler_X = joblib.load(scaler_X_path)
        self.scaler_y = joblib.load(scaler_y_path)

        # Scale features using training scaler
        X = df[features].values
        X_scaled = self.scaler_X.transform(X)

        # Build sequences
        X_seq = [X_scaled[i:i + timesteps] for i in range(len(X_scaled) - timesteps + 1)]
        X_seq_tensor = torch.tensor(
            [X_seq[-1]], dtype=torch.float32
        ).to(torch.device("cuda" if torch.cuda.is_available() else "cpu")) if single_step else torch.tensor(X_seq,
                                                                                                            dtype=torch.float32).to(
            torch.device("cuda" if torch.cuda.is_available() else "cpu"))

        # Load model
        input_dim = len(features)
        output_dim = len(self.base_config['targets']) * horizon
        model = LSTMModel(
            input_dim=input_dim,
            hidden_dim=self.base_config['hidden_units'],
            output_dim=output_dim,
            num_layers=self.base_config['num_lstm_layers'],
            activation=self.base_config['activation']
        )
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model.to(device)
        model.load_state_dict(torch.load(model_path, map_location=device))
        model.eval()
        print(f"Model loaded from {model_path}")

        # Run model
        with torch.no_grad():
            outputs = model(X_seq_tensor)

        if single_step:
            # reshape and inverse-transform
            outputs_np = outputs.cpu().numpy().reshape(horizon, len(self.base_config['targets']))
            outputs_np = self.scaler_y.inverse_transform(outputs_np)

            # Convert raw results into user-friendly string
            result_str = "Predictions:\n"
            for i, target in enumerate(self.base_config['targets']):
                values = outputs_np[:, i].tolist()

                # Map target to friendly name + convert units
                if "ul" in target:
                    name = "Throughput Uplink (Mbps)"
                    values = [v / 1e6 for v in values]  # bps -> Mbps
                elif "dl" in target:
                    name = "Throughput Downlink (Mbps)"
                    values = [v / 1e6 for v in values]  # bps -> Mbps
                elif "rtt" in target:
                    name = "RTT (ms)"
                    values = [v / 1e6 for v in values]  # ns -> ms
                else:
                    name = target

                values_str = ", ".join([f"{v:.2f}" for v in values])
                result_str += f"{name} = [{values_str}]\n\n"

            print(f"Single-step inference completed:\n{result_str}")
            return result_str

        else:
            # Multi-step / rolling prediction
            outputs_np = outputs.cpu().numpy().reshape(-1, horizon, len(self.base_config['targets']))
            outputs_np = self.scaler_y.inverse_transform(outputs_np.reshape(-1, len(self.base_config['targets']))).reshape(
                outputs_np.shape)
            result = {target: outputs_np[:, :, i].tolist() for i, target in enumerate(self.base_config['targets'])}

            # Prepare ground truth for evaluation
            gt_df = df[self.base_config['targets']].copy()
            metrics = self.evaluate_predictions(result, gt_df)

            # -------------------
            # PLOTTING: optional
            # -------------------
            if plot_target is not None:
                if plot_target not in self.base_config['targets']:
                    raise ValueError(f"plot_target must be in model targets: {self.base_config['targets']}")

                if not (0 <= horizon_step < self.base_config['horizon']):
                    raise ValueError(f"horizon_step must be between 0 and {self.base_config['horizon'] - 1}")

                pred_vals = np.array(result[plot_target])[:, horizon_step]
                gt_vals = gt_df[plot_target].values[
                          self.base_config['timesteps'] + horizon_step - 1:
                          self.base_config['timesteps'] + horizon_step - 1 + len(pred_vals)
                          ]

                plt.figure(figsize=(12, 6))
                plt.plot(gt_vals, label='Ground Truth', linewidth=2)
                plt.plot(pred_vals, label='Predictions', linewidth=2)
                plt.xlabel('Sequence Index', fontsize=14, fontweight='bold')
                plt.ylabel(plot_target, fontsize=14, fontweight='bold')
                plt.title(f'{plot_target} Predictions vs Ground Truth (Horizon step {horizon_step})', fontsize=16,
                          fontweight='bold')
                plt.legend(fontsize=12)
                plt.grid(True, linestyle='--', alpha=0.5)
                plt.tight_layout()
                plt.show()

            print(f"Rolling inference completed with metrics for targets: {list(result.keys())}")
            return metrics


ai=AI()
ai.train()
a=ai.infer(single_step=False,plot_target='iperf_tcp_dl_received_bps',horizon_step=1)
pprint(a)
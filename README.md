# Data Mining and Machine Learning for Online Prediction of Vessel Arrival Time Residuals.

Bachelor Thesis - Leiden University
Author - Maria Teodora Tudora

## Overview
The thesis studies the effect that integrating real-time meteorological features and dynamic port congestion indices has on vessel arrival time prediction accuracy. Standard AIS-reported ETAs are often manually entered and fail to account for real-time environmental and operational factors. This thesis presents an online predictive pipeline that integrates real-time Automatic Identification System (AIS) telemetry with meteorological factors and Dynamic Congestion Indices (DCIs).

## Repository Structure
•⁠  ⁠*/data*: Contains the ⁠ FINAL_COMPLETED_DATASET.csv.
•⁠  ⁠*/scripts*: 
    - ⁠ weather_miner.py ⁠: Meteorological data collection.
    - ⁠ raw_vessel_data.py ⁠: Live ingestion of real-time AIS telemetry.
    - ⁠ build_final_dataset.py ⁠: Data cleaning and multi-modal fusion.
    - ⁠ train_comparison_models.py ⁠: Machine learning training.
    - ⁠ port_type_analysis.py ⁠: Evaluation of results separated by port geography (Tidal vs. Coastal).
•⁠  ⁠*/output*: Final performance tables and feature importance weights.

## Installation & Setup
1.⁠ ⁠Clone the repository.
2.⁠ ⁠Install dependencies:
   ```bash
   pip install -r requirements.txt

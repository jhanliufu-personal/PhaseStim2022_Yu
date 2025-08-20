# CLC: Real-time Phase Detection and Phase-specific Stimulation
 This system estimates and tracks the oscillatory phase of an underlying signal in real time. It then issues stimulation commands when the estimated phase reaches a predefined target phase. This is called phase-specific stimulation, an important tool in experimental neuroscience and clinical applications. This setup currently supports three training-free phase estimation algorithms. We have a [python package](https://github.com/JhanLiufu/PhaseStimAnalysis2022_Yu/tree/master?tab=readme-ov-file) for analyzing its performance using various metrics. We analyzed algorithm performance and input signal features, identified key parameters and formed optimization strategies. We report our findings in the [CLC](https://www.biorxiv.org/content/10.1101/2024.08.24.609522v1.full.pdf) paper (under review at Journal of Neural Engineering). Visit its [project page](https://jhanliufu.github.io/projects/closed_loop_control.html) on Jhan's website to see the neuroscience motivation.

## Quickstart

### Installation Options

**Option 1: Using pip and requirements.txt**
```bash
git clone git@github.com:jhanliufu-personal/PhaseStim2022_Yu.git
cd PhaseStim2022_Yu
pip install -r requirements.txt
pip install .
```

**Option 2: Using conda environment**
```bash
git clone git@github.com:jhanliufu-personal/PhaseStim2022_Yu.git
cd PhaseStim2022_Yu
conda env create -f environment.yml
conda activate phasestim2022
pip install .
```

### Running the System
Launch the real-time phase detection and stimulation system:
```bash
python ControlCode.py --params config/[your-config-file].json
```

## Codebase Structure
- **[trodes_connection.py](trodes_connection.py)** contains functions to interface with the [Trodes](https://spikegadgets.com/) system. We stream local field potential (LFP) signal from Trodes and issue stimulation command to Trodes.
- **[phase_estimators.py](phase_estimators.py)** implements multiple phase estimation methods:
  - **ECHTEstimator**: endpoint-corrected Hilbert transform (ecHT), originally proposed by [Schreglmann et.al](https://www.nature.com/articles/s41467-020-20581-7)
  - **HTEstimator**: standard Hilbert transform method
  - **PMEstimator**: phase mapping method for real-time phase tracking
- **[detector.py](detector.py)** defines the **Detector** object with modular phase estimation support. A detector iteratively streams LFP from Trodes, estimates the current phase using the selected method (ecHT, HT, or PM), and issues stimulation commands when the estimated phase reaches the target phase.
- **[ControlCode.py](ControlCode.py)** establishes connection with Trodes and starts the detectors. Leveraging [multiprocessing](https://docs.python.org/3/library/multiprocessing.html) in python, the system can run an arbitrary number of detectors, each having their own parameters and output to separate Trodes digital outputs. The detector parameters are specified in JSON configuration files in [config](config).

## System Configuration
Create a ```json``` file in ```config/``` to specify the parameters for phase detection and stimulation. These parameters define your 
experiment and directly influence phase detection performance. 

| Parameter | Description |
|-----------|-------------|
| ```target_lowcut```, ```target_highcut``` | Define your frequency band of interest. Common neural oscillations are $\theta$ band (6-9 Hz), $\alpha$ band (8-12 Hz), $\gamma$ band (15-22 Hz) etc. |
| ```filter_type``` | Typed of filter used to filter the raw signal. Currently support Butterworth (```butter```), Chebyshev Type I (```cheby1```) and Elliptic (```ellip```) filter. We recommend ```butter``` |

# PhaseStim2022_Yu
Real-time phase detection and phase-specific stimulation system. We have a [python package](https://github.com/JhanLiufu/PhaseStimAnalysis2022_Yu/tree/master?tab=readme-ov-file) for analyzing stimulation outcome. For more introduction of the project, see its [project page](https://jhanliufu.github.io/projects/closed_loop_control.html) on Jhan's website.

## Quickstart

### Installation Options

**Option 1: Using pip and requirements.txt**
```bash
git clone [repository-url]
cd PhaseStim2022_Yu
pip install -r requirements.txt
pip install .
```

**Option 2: Using conda environment**
```bash
git clone [repository-url]
cd PhaseStim2022_Yu
conda env create -f environment.yml
conda activate phasestim2022
pip install .
```

**Option 3: Direct pip install**
```bash
git clone [repository-url]
cd PhaseStim2022_Yu
pip install .
```

### Running the System
Launch the real-time phase detection and stimulation system:
```bash
python ControlCode.py --params config/[your-config-file].json
```

## Files 
- **[trodes_connection.py](trodes_connection.py)** contains functions to interface with the [Trodes](https://spikegadgets.com/) system. We stream local field potential (LFP) signal from Trodes and issue stimulation command to Trodes.
- **[phase_estimators.py](phase_estimators.py)** implements multiple phase estimation methods:
  - **ECHTEstimator**: endpoint-corrected Hilbert transform (ecHT), originally proposed by [Schreglmann et.al](https://www.nature.com/articles/s41467-020-20581-7)
  - **HTEstimator**: standard Hilbert transform method
  - **PMEstimator**: phase mapping method for real-time phase tracking
- **[detector.py](detector.py)** defines the **Detector** object with modular phase estimation support. A detector iteratively streams LFP from Trodes, estimates the current phase using the selected method (ecHT, HT, or PM), and issues stimulation commands when the estimated phase reaches the target phase.
- **[ControlCode.py](ControlCode.py)** establishes connection with Trodes and starts the detectors. Leveraging [multiprocessing](https://docs.python.org/3/library/multiprocessing.html) in python, the system can run an arbitrary number of detectors, each having their own parameters and output to separate Trodes digital outputs. The detector parameters are specified in JSON configuration files in [config](config).

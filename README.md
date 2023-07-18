# pyo_oracle
## Python interface for the Bio-ORACLE ERDDAP server

### Quick start

```python
import pyo_oracle

# List available layers in the Bio-ORACLE server
pyo_oracle.list_layers()

# Define constraints and download a layer
constraints = {
    "time>=": "2000-01-01T00:00:00Z",
    "time<=": "2010-01-01T12:00:00Z",
    "time_step": 100,
    "latitude>=": 0,
    "latitude<=": 10,
    "latitude_step": 100,
    "longitude>=": 0,
    "longitude<=": 10,
    "longitude_step": 1
}
pyo_oracle.download_layers("thetao_baseline_2000_2019_depthsurf", constraints=constraints)

# See local data
pyo_oracle.list_local_data()
```

### Installation

```bash
# With conda
conda create -n pyo_oracle conda-forge::pyo-oracle

# or with pip
pip install pyo-oracle
```

Please open an issue if you experience any problems. More documentation coming soon!

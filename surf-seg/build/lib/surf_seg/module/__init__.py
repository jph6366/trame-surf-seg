from pathlib import Path

# Compute local path to serve
serve_path = str(Path(__file__).with_name("serve").resolve())

# Serve directory for JS/CSS files
serve = {"__surf_seg": serve_path}

# List of JS files to load (usually from the serve path above)
scripts = ["__surf_seg/surf_seg.umd.js"]

# List of CSS files to load (usually from the serve path above)
# styles = ["__surf_seg/style.css"]

# List of Vue plugins to install/load
vue_use = ["surf_seg"]

# Uncomment to add entries to the shared state
# state = {}


# Optional if you want to execute custom initialization at module load
def setup(app, **kwargs):
    """Method called at initialization with possibly some custom keyword arguments"""
    pass

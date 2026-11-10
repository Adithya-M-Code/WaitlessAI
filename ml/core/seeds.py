"""
Seed management utility ensuring reproducibility across stochastic algorithms (Rule R4).
"""

import os
import random
import numpy as np

SEEDS = [42, 123, 999]

def set_seeds(seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass


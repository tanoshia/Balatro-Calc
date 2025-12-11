"""Machine Learning modules for card and modifier recognition"""

from .card_classifier import CardClassifier
from .modifier_classifier import ModifierClassifier
from .data_generator import BalatroCardDataset, RealDatasetFromScreenshots
from .trainer import Trainer

__all__ = ['CardClassifier', 'ModifierClassifier', 'BalatroCardDataset', 'RealDatasetFromScreenshots', 'Trainer']
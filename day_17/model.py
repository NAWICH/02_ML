import torch
import torch.nn as nn

SUBJECTS = ['Gk', 'Math', 'Nepali', 'English', 'Science']
EMBEDDINGS = 384
class QoestionClassifire(nn.Module):
    def __init__(self,
                 input_size: int = EMBEDDINGS,
                 hidden1: int = 256,
                 hidden2: int = 128,
                 input_classes: int = len(SUBJECTS),
                 drop_out_rate: float = 0.3):
        super.__init__()
        
        self.classifier = nn.Sequential(
            #Layer 1
            nn.Linear(input_size, hidden1),
            nn.BatchNorm1d(hidden1),
            nn.ReLU(),
            nn.Dropout(drop_out_rate),

            #Layer 2
            nn.Linear(hidden1, hidden2),
            nn.BatchNorm1d(hidden2),
            nn.ReLU(),
            nn.Dropout(drop_out_rate),

            #output Layer()
            nn.Linear(hidden2, input_classes),
        )
    
    def forword(self, x: torch.tensor) -> torch.tensor:
        return self.classifier(x)
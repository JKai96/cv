import torch
from torch import nn
from torch.utils.data import DataLoader
from torchvision import datasets
from torchvision.transforms import ToTensor, Lambda, Compose
import matplotlib.pyplot as plt
import numpy as np
import random
import cv2 as cv
import time
datasetFileName = "../master_dataset.npz"


with np.load(datasetFileName, allow_pickle=True) as data:
    dataImages = data['images']
    dataLabels = data['labels'].astype('int64')
    dataLabelNames = data['labelnames']

desiredShape = (200, 200, 3)

N = len(dataImages)
shape = (N, desiredShape[0], desiredShape[1], desiredShape[2])

y = np.empty(shape, dtype='uint8')

for i in range(N):
    y[i] = cv.resize(dataImages[i], [200,200], interpolation=cv.INTER_NEAREST)

dataImages = y

dataImages = dataImages / 255.0

dataset = torch.tensor(dataImages)

all_data = []
for i in range(len(dataset)):
    all_data.append([dataset[i],dataLabels[i]])

random.shuffle(all_data)

train_split = int(len(all_data)*0.75)
test_spilt = len(all_data)-train_split
training_data, test_data = torch.utils.data.random_split(all_data,[train_split,test_spilt])

classes = {0: 'afiq', 1: 'azureen', 2: 'gavin', 3: 'goke',  4: 'inamul', 5: 'jincheng', 6: 'mahmuda', 7: 'numan', 8: 'saseendran'}

batch_size = 30

# Create data loaders.
train_dataloader = DataLoader(training_data, batch_size=batch_size)
test_dataloader = DataLoader(test_data, batch_size=batch_size)

# for X, y in test_dataloader:
#     print("Shape of X [N, C, H, W]: ", X.shape)
#     print("Shape of y: ", y.shape, y.dtype)
#     break

# Get cpu or gpu device for training.
device = "cuda" if torch.cuda.is_available() else "cpu"

#print(f"Using {device} device")

input_size = 3*200*200
output_size = 9
# Define model
class NeuralNetwork(nn.Module):
    def __init__(self):
        super(NeuralNetwork, self).__init__()
        self.flatten = nn.Flatten()
        self.linear_relu_stack = nn.Sequential(
            nn.Linear(input_size, 512),
            nn.ReLU(),
            nn.Linear(512, 512),
            nn.ReLU(),
            nn.Linear(512, 512),
            nn.ReLU(),
            nn.Linear(512, output_size)
        )

    def forward(self, x):
        x = self.flatten(x)
        logits = self.linear_relu_stack(x)
        return logits


model = NeuralNetwork().to(device)

loss_fn = nn.CrossEntropyLoss()
optimizer = torch.optim.SGD(model.parameters(), lr=1e-3)

def train(dataloader, model, loss_fn, optimizer):
    size = len(dataloader.dataset)
    model.train()
    for batch, (X, y) in enumerate(dataloader):
        X, y = X.to(device), y.to(device)

        # Compute prediction error
        pred = model(X.float())
        loss = loss_fn(pred, y)

        # Backpropagation
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        if batch % 100 == 0:
            loss, current = loss.item(), batch * len(X)
            print(f"loss: {loss:>7f}  [{current:>5d}/{size:>5d}]")

    return loss, current 

def test(dataloader, model, loss_fn):
    size = len(dataloader.dataset)
    num_batches = len(dataloader)
    model.eval()
    test_loss, correct = 0, 0
    with torch.no_grad():
        for X, y in dataloader:
            X, y = X.to(device), y.to(device)
            pred = model(X.float())
            test_loss += loss_fn(pred, y).item()
            correct += (pred.argmax(1) == y).type(torch.float).sum().item()
    test_loss /= num_batches
    correct /= size
    print(f"Test Error: \n Accuracy: {(100*correct):>0.1f}%, Avg loss: {test_loss:>8f} \n")

    return test_loss, correct

# epoch 10 max iter 5 save file with acc value
maxIterations = 5
testAccList = []
thresholdAcc = 0.9
lastTestAcc = 0.0

testLoss = 0.0
testAcc = 0.0
epoch = 30

if __name__ == "__main__":
    pt_start_time = time.time()
    for iter in range(maxIterations):

        print(f'simulation {iter + 1}', end='... ')

        for t in range(epoch):
            
            loss, current = train(train_dataloader, model, loss_fn, optimizer)
            test_loss, test_acc = test(test_dataloader, model, loss_fn)
            
            # save model if greater than threshold-accuracy 0.95
            if test_acc > thresholdAcc:
                # SavedModel format
                savedFile = f'trch/cv_image_torch_{(test_acc*100):.0f}.pth'
                torch.save(model.state_dict(), savedFile)
                print("Export Path = "+savedFile)

                thresholdAcc = test_acc
                
        print('Simulation Complete.')
    

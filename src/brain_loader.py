import aiml
import os

DATA_DIR = "data/aiml_set"

def loadBrain(kernel):
	aiml_files = os.listdir(DATA_DIR)
	for f in aiml_files:
		kernel.learn(f)
	return kernel

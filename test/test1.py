import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from data_record_creator import data_record_creator

path_to_models = "models"
data_record_creator = data_record_creator.DataRecordCreator()
data_record_creator.create(path_to_models)

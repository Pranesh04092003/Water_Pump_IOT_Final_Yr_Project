from graphviz import Digraph

# Create a directed graph
dot = Digraph(format='png')

# Define nodes
dot.node('S', 'IoT Sensors\n(Vibration, Current, Flow, Temp)')
dot.node('E', 'ESP32\n(MQTT Protocol)')
dot.node('M', 'MongoDB\n(Real-time Storage)')
dot.node('P', 'Preprocessing\n(Data Cleaning, Feature Extraction)')
dot.node('ML', 'Machine Learning Models\n(XGBoost, LSTM, Random Forest)')
dot.node('D', 'Dashboard & Alerts\n(Flask Web App)')

# Define edges to show the data flow
dot.edge('S', 'E', label='Real-time Data Transmission')
dot.edge('E', 'M', label='Store via MQTT')
dot.edge('M', 'P', label='Retrieve for Processing')
dot.edge('P', 'ML', label='Train & Predict')
dot.edge('ML', 'D', label='Send Predictions & Alerts')

# Render and save the diagram
dot.render('system_architecture')

# Display the diagram
from IPython.display import Image
Image(filename='system_architecture.png')

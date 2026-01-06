# Emulator Version 1.0
This is the first version of Agent Based Model (AI4HumanMotion)


## Installation
requirements.txt for python 3.10.8
```bash
pip install -r requirements.txt
```

## Usage
```bash
python main.py
```

## Events

### Vaccination
Agents can be vaccinated by the following methods:\
- Profession_location: Vaccination based on profession for agents in a given location.
- All: Vaccination for all agents in the simulation.

### PCR
Agents can be tested by the following methods:\
- Random: Daily testing for agents with symptoms.
 
### Quarantine
Once an agent is tested positive, the agent is quarantined until they get treated.
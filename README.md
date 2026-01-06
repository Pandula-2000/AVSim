# AVSim: Realistic Simulation Framework for Airborne and Vector-Borne Disease Dynamics

[![arXiv](https://img.shields.io/badge/arXiv-2502.06212-b31b1b.svg)](https://arxiv.org/abs/2502.06212)
[![Status](https://img.shields.io/badge/Status-Under_Review-yellow)](https://ieeexplore.ieee.org/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> **Note:** This paper is currently under review at *IEEE Transactions on Systems, Man, and Cybernetics: Systems*.

## 📖 Overview
**AVSim** is a novel Agent-Based Modeling (ABM) framework designed to simulate the spread of **airborne** (e.g., COVID-19) and **vector-borne** (e.g., Dengue) diseases under realistic conditions. 

Unlike traditional models that rely on synthetic mobility assumptions (which often fail to capture complex social dynamics), AVSim drives agent behavior using **real-world GPS traces**. By integrating rigorous data processing—specifically **DBSCAN** for location identification and **Spectral Clustering** for behavioral pattern recognition—AVSim generates high-fidelity, occupation-specific human mobility trajectories.

### Key Features
* **Real-World Mobility:** Agent movement is derived from GPS data collected from volunteers across 13 profession classes in Kandy, Sri Lanka.
* **Dual Disease Modeling:**
    * **Airborne:** Proximity-based transmission (1m radius) with factors for age, hygiene, and vaccination.
    * **Vector-Borne:** Network-patch methodology modeling vector density, mosquito lifecycles, and environmental factors (temperature/rainfall).
* **Granular Behavior:** Unsupervised clustering uncovers latent behavioral subgroups (e.g., day-shift vs. night-shift doctors).
* **Hierarchical Environment:** A tree-based geographical model (District $\to$ City $\to$ Functional Zone) combined with a functional public transport system (Inter/Intra-city buses).

## 🏗️ System Architecture
The simulation is built on four primary components:
1.  **Environment:** Modeled using real-world map polygons (Kandy, Pallekele, Gampola).
2.  **Agents:** Individuals with specific occupations, age profiles, and daily timetables generated via probability matrices.
3.  **Transport Network:** Simulates long-range mobility via private and public transit.
4.  **Vector Patches:** Represents localized vector (mosquito) densities and their SEIR progression.

## 🚀 Installation

### Prerequisites
* Python 3.8+
* Recommended: Virtual Environment (venv or conda)

### Setup
```bash
# Clone the repository
git clone [https://github.com/your-username/AVSim.git](https://github.com/your-username/AVSim.git)
cd AVSim

# Create a virtual environment (Optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

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

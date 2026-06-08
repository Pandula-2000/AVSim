import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import ast
import yaml
import subprocess
import sys
import time
import re
import folium
from streamlit_folium import st_folium

# --- Streamlit Page Config ---
st.set_page_config(page_title="AVSim Output Dashboard", layout="wide", initial_sidebar_state="expanded")

# IMPORTANT: Every Plotly chart natively supports downloading the visual as a PNG via the camera icon 
# in the modebar. We are explicitly enabling it in the config dictionaries below. 
# We are also providing st.download_button() for the raw CSV data per the user's request.

@st.cache_data
def load_data(sim_dir):
    data = {}
    
    pandemic_dir = os.path.join(sim_dir, "Pandemic")
    mobility_dir = os.path.join(sim_dir, "Mobility")
    
    # 1. Epidemic Curve
    try:
        state_counts_path = os.path.join(pandemic_dir, "State_counts_for_each_day.txt")
        with open(state_counts_path, 'r') as f:
            lines = f.readlines()
        
        days_data = []
        current_day = None
        current_counts = {}
        for line in lines:
            line = line.strip()
            if line.startswith("Day"):
                if current_day is not None:
                    days_data.append(current_counts)
                current_day = int(line.replace("Day ", "").replace(":", ""))
                current_counts = {"Day": current_day}
            elif line.startswith("State"):
                parts = line.split(":")
                state_idx = int(parts[0].replace("State ", "").strip())
                count = int(parts[1].strip())
                current_counts[f"State_{state_idx}"] = count
        if current_day is not None:
            days_data.append(current_counts)
        
        data['state_counts'] = pd.DataFrame(days_data)
    except Exception as e:
        data['state_counts'] = None

    # 2. Infected by class
    try:
        data['infected_by_class'] = pd.read_excel(os.path.join(pandemic_dir, "Infected_by_Class.xlsx"))
    except:
        data['infected_by_class'] = None
        
    # 3. Agent contacts
    try:
        data['contacts'] = pd.read_excel(os.path.join(pandemic_dir, "Agent_contacts.xlsx"))
    except:
        data['contacts'] = None

    try:
        data['env_df'] = pd.read_excel(os.path.join(sim_dir, "../../Data/NodeEnv.xlsx"), header=None)
    except:
        data['env_df'] = None

    # Lazy loaded paths
    data['time_tables_path'] = os.path.join(mobility_dir, "Agent_time_tables.txt")
    data['agent_states_path'] = os.path.join(pandemic_dir, "Agent_States_over_days.txt")
    
    return data

def parse_timetable(line):
    try:
        agent_id_part, data_part = line.split(" >> ", 1)
        agent_id = agent_id_part.replace("Agent ", "").strip()
        data_tuple = ast.literal_eval(data_part.strip())
        return agent_id, data_tuple[0], data_tuple[1]
    except Exception:
        return None, None, None

def get_agent_schedules_all_days(file_path, target_agent):
    if not os.path.exists(file_path): return {}
    schedules = {}
    current_day = 1
    with open(file_path, 'r') as f:
        for line in f:
            if line.startswith("====="):
                m = re.search(r'day (\d+)', line.lower())
                if m:
                    current_day = int(m.group(1))
            elif line.startswith(f"Agent {target_agent} >>"):
                agent_id, locs, times = parse_timetable(line)
                if locs and times:
                    schedules[current_day] = (locs, times)
    return schedules

def get_agent_state(file_path, target_agent):
    if not os.path.exists(file_path): return None
    with open(file_path, 'r') as f:
        for line in f:
            if line.startswith(f"{target_agent}:"):
                try:
                    data_part = line.split(":", 1)[1].strip()
                    return ast.literal_eval(data_part)
                except:
                    pass
    return None

def parse_polygon(poly_str):
    try:
        poly_str = str(poly_str)
        # Handle WKT POLYGON ((lon lat, lon lat)) format
        pairs = re.findall(r'(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)', poly_str)
        if pairs:
            # folium uses (lat, lon) while WKT is (lon, lat)
            return [(float(lat), float(lon)) for lon, lat in pairs]
    except:
        pass
    return []

def get_centroid(points):
    if not points: return None
    avg_lat = sum(p[0] for p in points) / len(points)
    avg_lon = sum(p[1] for p in points) / len(points)
    return (avg_lat, avg_lon)

def main():
    st.title("🦠 AVSim Output Dashboard")
    
    st.sidebar.header("Data Selection")
    results_base = "../Results"
    
    if not os.path.exists(results_base):
        st.error(f"Cannot find Results directory at {os.path.abspath(results_base)}. Run this script from the Scripts folder.")
        return
        
    sim_dirs = [d for d in os.listdir(results_base) if os.path.isdir(os.path.join(results_base, d))]
    sim_dirs.sort(reverse=True)
    
    if not sim_dirs:
        st.warning("No simulation directories found.")
        return
        
    selected_sim = st.sidebar.selectbox("Select Simulation Run", sim_dirs)
    
    if selected_sim:
        with st.spinner("Loading Output Data..."):
            data = load_data(os.path.join(results_base, selected_sim))
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Disease Progression", "🤝 Contact Analysis", "👤 Individual Agent View", "⚙️ Simulation Runner", "🗺️ Environment Map"])
        
        # TAB 1: EPIDEMIOLOGY
        with tab1:
            st.header("Epidemiology Analytics")
            if data['state_counts'] is not None:
                df_sc = data['state_counts'].copy()
                df_sc['Susceptible'] = df_sc['State_1']
                df_sc['Exposed'] = df_sc['State_2']
                df_sc['Infected'] = df_sc[['State_3', 'State_4', 'State_5', 'State_6', 'State_7']].sum(axis=1)
                df_sc['Recovered'] = df_sc['State_8']
                df_sc['Dead'] = df_sc['State_9']
                
                plot_df = df_sc[['Day', 'Susceptible', 'Exposed', 'Infected', 'Recovered', 'Dead']].melt(
                    id_vars='Day', var_name='State', value_name='Count')
                
                fig1 = px.line(plot_df, x='Day', y='Count', color='State', 
                               title="Epidemic Curve (SEIR)", 
                               color_discrete_map={"Susceptible": "#1f77b4", "Exposed": "#ff7f0e", "Infected": "#d62728", "Recovered": "#2ca02c", "Dead": "#000000"})
                fig1.update_layout(hovermode="x unified")
                st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': True, 'toImageButtonOptions': {'filename': 'epidemic_curve.png'}})
                
                with st.expander("⬇️ Download SEIR Data"):
                    st.download_button("Download CSV", df_sc.to_csv(index=False), "seir_data.csv", "text/csv")
            
            st.markdown("---")
            if data['infected_by_class'] is not None:
                df_ib = data['infected_by_class'].copy()
                if 'Unnamed: 0' in df_ib.columns:
                    df_ib = df_ib.drop(columns=['Unnamed: 0'])
                    
                ib_melt = df_ib.melt(id_vars='Day', var_name='Profession', value_name='Infections')
                fig2 = px.bar(ib_melt, x='Day', y='Infections', color='Profession', title="Infections by Class/Profession over Time")
                st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': True, 'toImageButtonOptions': {'filename': 'infections_by_class.png'}})
                
                with st.expander("⬇️ Download Demographics Data"):
                    st.download_button("Download CSV", df_ib.to_csv(index=False), "infected_by_class.csv", "text/csv")

        # TAB 2: CONTACTS
        with tab2:
            st.header("Contact Tracing Analytics")
            if data['contacts'] is not None and not data['contacts'].empty:
                df_c = data['contacts'].copy()
                col1, col2 = st.columns(2)
                
                with col1:
                    if 'Time' in df_c.columns:
                        df_c['Hour'] = (df_c['Time'] // 60) % 24
                        fig3 = px.histogram(df_c, x='Hour', nbins=24, title="Contact Volume by Hour of Day", color_discrete_sequence=['#835AF1'])
                        st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar': True})
                
                with col2:
                    if 'Location' in df_c.columns:
                        # Use a Ring chart (Donut) as requested
                        loc_counts = df_c['Location'].value_counts().reset_index()
                        loc_counts.columns = ['Location', 'Contacts']
                        top_locs = loc_counts.head(10)
                        
                        fig4 = px.pie(top_locs, values='Contacts', names='Location', title="Top 10 Hotspot Locations", hole=0.45)
                        fig4.update_traces(textinfo='percent+label', textposition='inside')
                        st.plotly_chart(fig4, use_container_width=True, config={'displayModeBar': True})
                
                with st.expander("⬇️ Download Raw Contacts Data"):
                    st.download_button("Download CSV", df_c.to_csv(index=False), "agent_contacts.csv", "text/csv")

                st.markdown("---")
                st.subheader("Contact Hotspots Map")
                if data.get('env_df') is not None and not data['env_df'].empty:
                    m2 = folium.Map(location=[0, 0], zoom_start=2)
                    loc_coords = {}
                    valid_points = []
                    for _, row in data['env_df'].iterrows():
                        if len(row) > 2:
                            centroid = get_centroid(parse_polygon(row[2]))
                            if centroid:
                                loc_coords[str(row[0])] = centroid
                    
                    loc_counts = df_c['Location'].value_counts().to_dict()
                    for loc, count in loc_counts.items():
                        if loc in loc_coords:
                            centroid = loc_coords[loc]
                            valid_points.append(centroid)
                            folium.CircleMarker(
                                location=centroid,
                                radius=min(max(count, 5), 30),
                                popup=f"{loc}: {count} contacts",
                                color="red",
                                fill=True,
                                fill_color="red"
                            ).add_to(m2)
                    if valid_points:
                        m2.fit_bounds(valid_points)
                    st_folium(m2, width=800, height=400, returned_objects=[])
                else:
                    st.info("Environment data needed to plot map.")

            else:
                st.info("No contact data available in this run. (Agent_contacts.xlsx is empty or missing)")

        # TAB 3: INDIVIDUAL VIEW
        with tab3:
            st.header("Individual Agent Timeline")
            
            target_agent = st.text_input("Search for an Agent ID", value="Student_1", placeholder="e.g. Student_42")
            
            if target_agent:
                # Retrieve State Trajectory
                agent_states = get_agent_state(data['agent_states_path'], target_agent)
                if agent_states:
                    st.subheader(f"Disease Trajectory: {target_agent}")
                    df_traj = pd.DataFrame({"Day": list(range(1, len(agent_states) + 1)), "State": agent_states})
                    
                    fig5 = px.scatter(df_traj, x='Day', y='State', title="Daily Disease State", color='State', 
                                      color_continuous_scale='Reds', size_max=15)
                    fig5.update_traces(marker=dict(size=12))
                    fig5.update_yaxes(tickvals=list(range(1, 10)))
                    st.plotly_chart(fig5, use_container_width=True, config={'displayModeBar': True})
                
                # Retrieve Gantt Schedule
                agent_schedules = get_agent_schedules_all_days(data['time_tables_path'], target_agent)
                locs = []
                if agent_schedules:
                    available_days = sorted(list(agent_schedules.keys()))
                    selected_day = st.selectbox("Select Simulation Day for Timetable", available_days)
                    locs, times = agent_schedules[selected_day]
                    
                    st.subheader(f"Daily Mobility Schedule: {target_agent} (Day {selected_day})")
                    
                    df_gantt = pd.DataFrame({
                        'Location': locs,
                        'Start': [t[0]/60.0 for t in times],
                        'Duration': [t[1]/60.0 for t in times]
                    })
                    df_gantt['Task'] = "Schedule"
                    
                    fig_gantt = go.Figure()
                    for loc in df_gantt['Location'].unique():
                        df_sub = df_gantt[df_gantt['Location'] == loc]
                        fig_gantt.add_trace(go.Bar(
                            base=df_sub['Start'],
                            x=df_sub['Duration'],
                            y=df_sub['Task'],
                            orientation='h',
                            name=loc,
                            text=loc,
                            textposition='inside'
                        ))
                        
                    fig_gantt.update_layout(
                        barmode='overlay', 
                        xaxis_title="Hour of Day", 
                        xaxis=dict(range=[0, 24], tick0=0, dtick=1),
                        height=250,
                        showlegend=True
                    )
                    st.plotly_chart(fig_gantt, use_container_width=True, config={'displayModeBar': True})
                    
                    st.markdown("---")
                    st.subheader(f"Trajectory Map: {target_agent} (Day {selected_day})")
                    if data.get('env_df') is not None and not data['env_df'].empty:
                        m3 = folium.Map(location=[0, 0], zoom_start=2)
                        loc_coords = {}
                        for _, row in data['env_df'].iterrows():
                            if len(row) > 2:
                                centroid = get_centroid(parse_polygon(row[2]))
                                if centroid:
                                    loc_coords[str(row[0])] = centroid
                        
                        trajectory_points = []
                        for loc in locs:
                            if loc in loc_coords:
                                trajectory_points.append(loc_coords[loc])
                        
                        if trajectory_points:
                            folium.PolyLine(trajectory_points, color="blue", weight=2.5, opacity=1).add_to(m3)
                            for i, loc in enumerate(locs):
                                if loc in loc_coords:
                                    folium.Marker(loc_coords[loc], popup=f"{i+1}. {loc}").add_to(m3)
                            m3.fit_bounds(trajectory_points)
                            st_folium(m3, width=800, height=400, returned_objects=[])
                        else:
                            st.info("No valid locations mapped.")
                    else:
                        st.info("Environment data needed to plot map.")
                
                if not agent_states and not locs:
                    st.warning(f"Could not find timetable or state data for {target_agent}")

        # TAB 4: SIMULATION RUNNER
        with tab4:
            st.header("Simulation Runner")
            st.markdown("Edit `config.yaml` parameters and run a simulation script directly from this dashboard.")
            
            config_path = "config.yaml"
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f) or {}
                
                with st.form("config_form"):
                    st.subheader("Configuration")
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        sim_name = st.text_input("Simulation Name", value=config.get('simulation_name', 'TEST'))
                        sim_days = st.number_input("Simulation Days", value=config.get('simulation_days', 2), min_value=1)
                        infect_pct = st.number_input("Percentage of Agents to Infect", value=float(config.get('percentage_of_agents_to_infect', 0.0001)), format="%.5f")
                        bus_risk = st.slider("Bus Max Risk", 0.0, 1.0, float(config.get('bus_max_risk', 0.3)))
                        loc_risk = st.slider("Location Max Risk", 0.0, 1.0, float(config.get('location_max_risk', 0.5)))
                        rad_inf = st.number_input("Radius of Infection", value=config.get('radius_of_infection', 1))
                        
                    with col_b:
                        infect_random = st.checkbox("Infect Random", value=config.get('infect_random', True))
                        run_vacc = st.checkbox("Run Vaccine", value=config.get('run_vaccine', False))
                        quar_agents = st.checkbox("Quarantine Agents", value=config.get('quarantine_agents', True))
                        quar_pcr = st.checkbox("Quarantine by PCR", value=config.get('quarantine_by_pcr', False))
                        quar_class = st.checkbox("Quarantine by Class", value=config.get('quarantine_by_class', False))
                        step_freq = st.number_input("Step Disease Frequency", value=config.get('step_disease_frequency', 5))
                        detect_thresh = st.number_input("Pandemic Detection Threshold", value=float(config.get('pandemic_detection_threshold', 0.1)), format="%.2f")
                        
                        script_options = ["main.py", "main_randomU.py"]
                        selected_script = st.selectbox("Simulation Script to Run", script_options)
                        
                    submit_button = st.form_submit_button("💾 Save Config & 🚀 Launch Simulation")
                    
                if submit_button:
                    # Update config
                    config['simulation_name'] = sim_name
                    config['simulation_days'] = sim_days
                    config['percentage_of_agents_to_infect'] = infect_pct
                    config['bus_max_risk'] = bus_risk
                    config['location_max_risk'] = loc_risk
                    config['radius_of_infection'] = rad_inf
                    config['infect_random'] = infect_random
                    config['run_vaccine'] = run_vacc
                    config['quarantine_agents'] = quar_agents
                    config['quarantine_by_pcr'] = quar_pcr
                    config['quarantine_by_class'] = quar_class
                    config['step_disease_frequency'] = step_freq
                    config['pandemic_detection_threshold'] = detect_thresh
                    
                    with open(config_path, 'w') as f:
                        yaml.dump(config, f)
                    
                    st.success(f"Config saved! Launching `{selected_script}`...")
                    
                    log_area = st.empty()
                    
                    # Run subprocess with real-time output
                    env = os.environ.copy()
                    env["PYTHONUNBUFFERED"] = "1"
                    
                    process = subprocess.Popen([sys.executable, selected_script], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True, env=env)
                    
                    output_lines = []
                    current_line = ""
                    last_update_time = time.time()
                    
                    temp_log_path = os.path.join(results_base, f"{sim_name}_temp_terminal.log")
                    with open(temp_log_path, "w") as log_f:
                        while True:
                            char = process.stdout.read(1)
                            if not char:
                                break
                            if char == '\r':
                                if len(output_lines) == 0:
                                    output_lines.append(current_line)
                                else:
                                    output_lines[-1] = current_line
                                current_line = ""
                            elif char == '\n':
                                if len(output_lines) == 0:
                                    output_lines.append(current_line)
                                else:
                                    output_lines[-1] = current_line
                                
                                log_f.write(output_lines[-1] + '\n')
                                log_f.flush()
                                
                                output_lines.append("")
                                current_line = ""
                                
                                # Throttle UI updates to 5Hz to prevent Streamlit from freezing
                                if time.time() - last_update_time > 0.2:
                                    log_area.code('\n'.join(output_lines[-30:]), language="bash")
                                    last_update_time = time.time()
                            else:
                                current_line += char

                    process.wait()
                    log_area.code('\n'.join(output_lines[-30:]), language="bash")
                    
                    # Move the temp log file into the newly created simulation folder
                    try:
                        import glob
                        import shutil
                        search_pattern = os.path.join(results_base, f"{sim_name}_*")
                        matching_dirs = [d for d in glob.glob(search_pattern) if os.path.isdir(d)]
                        if matching_dirs:
                            newest_dir = max(matching_dirs, key=os.path.getmtime)
                            final_log_path = os.path.join(newest_dir, "terminal_output.log")
                            shutil.move(temp_log_path, final_log_path)
                        elif os.path.exists(temp_log_path):
                            # Fallback if no dir matched
                            shutil.move(temp_log_path, os.path.join(results_base, f"{sim_name}_terminal_output.log"))
                    except Exception:
                        pass
                    
                    if process.returncode == 0:
                        st.success("Simulation Completed Successfully! Please refresh the page to see the new outputs.")
                        st.balloons()
                    else:
                        st.error("Simulation Failed.")
            else:
                st.error("config.yaml not found in current directory.")

        # TAB 5: ENVIRONMENT MAP
        with tab5:
            st.header("Environment Map")
            if data.get('env_df') is not None and not data['env_df'].empty:
                default_colors = {
                    "ResidentialZone": "#1f77b4", 
                    "MedicalZone": "#d62728", 
                    "EducationZone": "#2ca02c", 
                    "CommercialFinancialZone": "#ff7f0e", 
                    "AdministrativeZone": "#9467bd", 
                    "AgriculturalZone": "#8c564b", 
                    "IndustrialManufactureZone": "#7f7f7f", 
                    "Home": "#17becf" 
                }
                
                with st.expander("🎨 Customize Zone Colors"):
                    cols = st.columns(4)
                    ZONE_COLORS = {}
                    for i, (zone, default_color) in enumerate(default_colors.items()):
                        with cols[i % 4]:
                            ZONE_COLORS[zone] = st.color_picker(zone, value=default_color)
                
                legend_html = "<b>Zone Legend:</b><br>"
                for zone, color in ZONE_COLORS.items():
                    legend_html += f"<span style='color:{color}; font-size:18px;'>■</span> {zone}&nbsp;&nbsp;&nbsp; "
                st.markdown(legend_html, unsafe_allow_html=True)
                st.markdown("---")

                m_env = folium.Map(location=[0, 0], zoom_start=2)
                all_points = []
                for _, row in data['env_df'].iterrows():
                    if len(row) > 2:
                        loc_name = str(row[0])
                        base_zone = loc_name.split('_')[0]
                        poly_color = ZONE_COLORS.get(base_zone, "gray")
                        poly = parse_polygon(row[2])
                        if poly:
                            folium.Polygon(
                                locations=poly, 
                                color=poly_color, 
                                fill=True, 
                                fill_color=poly_color, 
                                fill_opacity=0.6, 
                                popup=loc_name
                            ).add_to(m_env)
                            all_points.extend(poly)
                if all_points:
                    m_env.fit_bounds(all_points)
                st_folium(m_env, width=1000, height=600, returned_objects=[])
            else:
                st.info("Environment data is not available.")

if __name__ == "__main__":
    main()

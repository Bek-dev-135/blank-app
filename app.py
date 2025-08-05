import streamlit as st
import pandas as pd
import folium
from folium import plugins
import streamlit.components.v1 as components
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import json
import time
import os
import psycopg2
from sqlalchemy import create_engine, text
import io
from typing import Dict, List, Optional

# Page configuration
st.set_page_config(
    page_title="BC Employment Data Explorer with Map",
    page_icon="🗺️",
    layout="wide"
)

# Title and description
st.title("🗺️ BC Employment Data Explorer")
st.markdown("""
Explore employment equity employer data across British Columbia constituencies with interactive mapping.
Filter by location, constituency, or search for specific organizations.
""")

@st.cache_data
def load_employer_data():
    """Load employer data from Excel file."""
    try:
        df = pd.read_excel('attached_assets/employer list_1754425983093.xlsx')
        # Clean column names
        df.columns = ['constituency', 'organization_name', 'municipality_name', 'postal_code', 'email']
        
        # Clean data
        df = df.dropna(subset=['organization_name'])  # Remove rows without organization names
        df['municipality_name'] = df['municipality_name'].fillna('Unknown')
        df['postal_code'] = df['postal_code'].fillna('')
        df['email'] = df['email'].fillna('')
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()

def get_db_connection():
    """Get database connection using environment variables."""
    return create_engine(os.environ["DATABASE_URL"])

def save_locations_to_db(locations_data: List[Dict]):
    """Save geocoded locations to database for caching."""
    if not locations_data:
        return
    
    engine = get_db_connection()
    
    # Create locations table if it doesn't exist
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS location_cache (
                id SERIAL PRIMARY KEY,
                location_name VARCHAR(255) UNIQUE,
                latitude DECIMAL(10, 8),
                longitude DECIMAL(11, 8),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.commit()
    
    # Insert locations
    df = pd.DataFrame(locations_data)
    df.to_sql('location_cache_temp', engine, if_exists='replace', index=False)
    
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO location_cache (location_name, latitude, longitude)
            SELECT location_name, latitude, longitude
            FROM location_cache_temp
            ON CONFLICT (location_name) DO UPDATE SET
                latitude = EXCLUDED.latitude,
                longitude = EXCLUDED.longitude
        """))
        conn.execute(text("DROP TABLE location_cache_temp"))
        conn.commit()

def get_cached_locations():
    """Get cached locations from database."""
    try:
        engine = get_db_connection()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT location_name, latitude, longitude FROM location_cache"))
            return {row[0]: (float(row[1]), float(row[2])) for row in result.fetchall()}
    except:
        return {}

@st.cache_data
def geocode_locations(municipalities):
    """Geocode municipality locations with caching."""
    
    # Get cached locations first
    cached_locations = get_cached_locations()
    locations = {}
    locations_to_save = []
    
    geolocator = Nominatim(user_agent="bc_employment_explorer")
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_locations = len(municipalities)
    
    for i, municipality in enumerate(municipalities):
        if municipality in cached_locations:
            locations[municipality] = cached_locations[municipality]
            status_text.text(f"Loading cached location for {municipality}...")
        else:
            status_text.text(f"Geocoding {municipality}... ({i+1}/{total_locations})")
            
            try:
                # Try with province for better accuracy
                location = geolocator.geocode(f"{municipality}, British Columbia, Canada", timeout=10)
                
                if location:
                    coord = (location.latitude, location.longitude)
                    locations[municipality] = coord
                    locations_to_save.append({
                        'location_name': municipality,
                        'latitude': location.latitude,
                        'longitude': location.longitude
                    })
                else:
                    # Fallback to just municipality name
                    location = geolocator.geocode(f"{municipality}, BC", timeout=10)
                    if location:
                        coord = (location.latitude, location.longitude)
                        locations[municipality] = coord
                        locations_to_save.append({
                            'location_name': municipality,
                            'latitude': location.latitude,
                            'longitude': location.longitude
                        })
                
                # Rate limiting
                time.sleep(0.5)
                
            except GeocoderTimedOut:
                st.warning(f"Geocoding timeout for {municipality}")
            except Exception as e:
                st.warning(f"Error geocoding {municipality}: {str(e)}")
        
        progress_bar.progress((i + 1) / total_locations)
    
    # Save new locations to database
    if locations_to_save:
        save_locations_to_db(locations_to_save)
    
    progress_bar.empty()
    status_text.empty()
    
    return locations

def create_map(df, municipality_locations):
    """Create Folium map with employer locations."""
    
    # Center map on BC
    bc_center = [53.7267, -127.6476]
    m = folium.Map(location=bc_center, zoom_start=6, tiles='OpenStreetMap')
    
    # Group employers by municipality
    municipality_groups = df.groupby('municipality_name')
    
    # Color palette for constituencies
    constituency_colors = [
        'red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred',
        'beige', 'darkblue', 'darkgreen', 'cadetblue', 'darkpurple', 'white',
        'pink', 'lightblue', 'lightgreen', 'gray', 'black', 'lightgray'
    ]
    
    constituencies = df['constituency'].unique()
    color_map = {constituency: constituency_colors[i % len(constituency_colors)] 
                for i, constituency in enumerate(constituencies)}
    
    # Add markers for each municipality
    for municipality, group in municipality_groups:
        if municipality in municipality_locations:
            lat, lon = municipality_locations[municipality]
            
            # Create popup content
            popup_content = f"""
            <b>{municipality}</b><br>
            <b>Total Employers:</b> {len(group)}<br><br>
            """
            
            # Group by constituency within municipality
            for constituency, const_group in group.groupby('constituency'):
                popup_content += f"<b>{constituency}:</b> {len(const_group)} employers<br>"
                for _, employer in const_group.head(5).iterrows():  # Show up to 5 employers
                    popup_content += f"• {employer['organization_name']}<br>"
                if len(const_group) > 5:
                    popup_content += f"• ... and {len(const_group) - 5} more<br>"
                popup_content += "<br>"
            
            # Use most common constituency color for municipality
            most_common_constituency = group['constituency'].mode().iloc[0]
            marker_color = color_map[most_common_constituency]
            
            folium.CircleMarker(
                location=[lat, lon],
                radius=min(len(group) * 2, 20),  # Size based on number of employers
                popup=folium.Popup(popup_content, max_width=300),
                color=marker_color,
                fillColor=marker_color,
                fillOpacity=0.7,
                weight=2
            ).add_to(m)
    
    # Add legend for constituencies
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 200px; height: auto; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px">
    <b>Constituencies</b><br>
    '''
    
    for constituency, color in color_map.items():
        count = len(df[df['constituency'] == constituency])
        legend_html += f'<i class="fa fa-circle" style="color:{color}"></i> {constituency} ({count})<br>'
    
    legend_html += '</div>'
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m

def create_csv_download(data: pd.DataFrame) -> bytes:
    """Create CSV download from filtered data."""
    csv_buffer = io.StringIO()
    data.to_csv(csv_buffer, index=False)
    return csv_buffer.getvalue().encode('utf-8')

def main():
    # Load data
    df = load_employer_data()
    
    if df.empty:
        st.error("No data loaded. Please check the Excel file.")
        return
    
    st.sidebar.subheader("📊 Data Overview")
    st.sidebar.write(f"**Total Employers:** {len(df):,}")
    st.sidebar.write(f"**Constituencies:** {df['constituency'].nunique()}")
    st.sidebar.write(f"**Municipalities:** {df['municipality_name'].nunique()}")
    
    # Filters
    st.sidebar.subheader("🔍 Filters")
    
    # Constituency filter
    constituencies = ['All'] + sorted(df['constituency'].unique().tolist())
    selected_constituency = st.sidebar.selectbox("Select Constituency", constituencies)
    
    # Municipality filter
    if selected_constituency != 'All':
        municipality_options = ['All'] + sorted(df[df['constituency'] == selected_constituency]['municipality_name'].unique().tolist())
    else:
        municipality_options = ['All'] + sorted(df['municipality_name'].unique().tolist())
    
    selected_municipality = st.sidebar.selectbox("Select Municipality", municipality_options)
    
    # Search filter
    search_term = st.sidebar.text_input("Search Organizations", placeholder="Enter organization name...")
    
    # Apply filters
    filtered_df = df.copy()
    
    if selected_constituency != 'All':
        filtered_df = filtered_df[filtered_df['constituency'] == selected_constituency]
    
    if selected_municipality != 'All':
        filtered_df = filtered_df[filtered_df['municipality_name'] == selected_municipality]
    
    if search_term:
        filtered_df = filtered_df[filtered_df['organization_name'].str.contains(search_term, case=False, na=False)]
    
    # Display filtered data info
    st.sidebar.markdown("---")
    st.sidebar.write(f"**Filtered Results:** {len(filtered_df):,} employers")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🗺️ Interactive Map")
        
        if st.button("🌍 Generate Map with Locations", type="primary"):
            with st.spinner("Geocoding municipalities and creating map..."):
                # Get unique municipalities for geocoding
                unique_municipalities = filtered_df['municipality_name'].unique()
                municipality_locations = geocode_locations(unique_municipalities)
                
                # Create and display map
                if municipality_locations:
                    map_obj = create_map(filtered_df, municipality_locations)
                    map_html = map_obj._repr_html_()
                    components.html(map_html, height=500)
                    
                    st.success(f"Map generated with {len(municipality_locations)} geocoded locations!")
                else:
                    st.error("No locations could be geocoded.")
    
    with col2:
        st.subheader("📋 Filtered Data")
        
        if not filtered_df.empty:
            # Display summary
            constituency_counts = filtered_df['constituency'].value_counts()
            st.write("**By Constituency:**")
            for constituency, count in constituency_counts.head(10).items():
                st.write(f"• {constituency}: {count}")
            
            if len(constituency_counts) > 10:
                st.write(f"• ... and {len(constituency_counts) - 10} more")
            
            # Download button
            csv_data = create_csv_download(filtered_df)
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=f"bc_employers_{selected_constituency.lower().replace(' ', '_') if selected_constituency != 'All' else 'all'}.csv",
                mime="text/csv"
            )
        else:
            st.info("No employers match the current filters.")
    
    # Data table
    st.subheader("📊 Employer Data")
    
    if not filtered_df.empty:
        # Display options
        show_all = st.checkbox("Show all records", value=False)
        
        if show_all:
            display_df = filtered_df
        else:
            display_df = filtered_df.head(100)
            if len(filtered_df) > 100:
                st.info(f"Showing first 100 of {len(filtered_df)} records. Check 'Show all records' to see more.")
        
        # Rename columns for display
        display_df = display_df.copy()
        display_df.columns = ['Constituency', 'Organization Name', 'Municipality', 'Postal Code', 'Email']
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No data to display with current filters.")

if __name__ == "__main__":
    main()

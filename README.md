
### How to run it on your own machine

1. Install the requirements

   ```
   $ pip install -r requirements.txt
   ```

2. Run the app

   ```
   $ streamlit run streamlit_app.py
   ```
# Overview

This is a BC Employment Data Explorer built with Streamlit, Folium mapping, and PostgreSQL. The application provides an interactive web interface for exploring employment equity employer data across British Columbia constituencies with precise location-based filtering using Leaflet maps. Users can filter by constituency, municipality, or search for specific organizations, and visualize the data on dual-mode interactive maps: overview mode shows municipality clusters, while detailed mode displays individual employer pins geocoded by postal codes. The tool features PostgreSQL caching for geocoded locations, Excel data import, and CSV export functionality.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Framework**: Streamlit for web interface
- **Layout**: Wide layout configuration for better data presentation
- **User Interface**: Simple form-based interaction with configuration options and download capabilities

## Data Processing Architecture
- **Excel Data Import**: Direct loading of employer data from Excel files using pandas and openpyxl
- **PostgreSQL Database**: Location caching system for geocoded municipality coordinates
- **Geolocation Services**: Integration with Nominatim/OpenStreetMap for geocoding municipality locations
- **Data Filtering**: Real-time filtering by constituency, municipality, and organization name search
- **Data Export**: CSV generation using pandas DataFrame with filtered results

## Core Components
- **Interactive Mapping**: Folium-based mapping with Leaflet integration for location visualization
- **Geolocation Caching**: PostgreSQL-based caching system for municipality coordinates with SQLAlchemy integration
- **Data Filtering System**: Multi-level filtering by constituency, municipality, and organization search
- **Excel Data Processing**: 
  - Direct Excel file loading using pandas and openpyxl
  - Data cleaning and validation with null value handling
  - Dynamic constituency and municipality option generation
  - Real-time data filtering and display
- **Map Visualization**: 
  - Interactive markers sized by employer count per municipality
  - Color-coded by constituency with legend
  - Popup information showing employer details and counts
  - Responsive design with zoom controls
- **Location Services**: Nominatim geocoding with rate limiting and error handling
- **Export Functionality**: Filtered CSV download with customized naming

## Design Patterns
- **Caching Strategy**: Location geocoding results cached in PostgreSQL to avoid repeated API calls
- **Component-Based Architecture**: Separate functions for data loading, mapping, filtering, and export
- **Progressive Enhancement**: Base functionality with optional interactive mapping features

# External Dependencies

## Python Libraries
- **streamlit**: Web application framework for the user interface
- **pandas**: Data manipulation and CSV export functionality
- **folium**: Interactive mapping library using Leaflet.js for web-based maps
- **geopy**: Geocoding library with Nominatim integration for location services
- **openpyxl**: Excel file reading and writing capabilities
- **psycopg2-binary**: PostgreSQL database adapter for Python
- **sqlalchemy**: SQL toolkit and Object-Relational Mapping for database operations
- **io**: In-memory file operations for CSV processing
- **typing**: Type hints for better code documentation

## External Data Source
- **Excel Data File**: Primary data source containing BC employer information with constituencies, organizations, municipalities, postal codes, and emails
- **Nominatim/OpenStreetMap**: Geocoding service for converting municipality names to coordinates

## Infrastructure Requirements
- **Python Runtime**: Compatible with standard Python 3.x environments
- **PostgreSQL Database**: Local database instance for caching employer data
- **Web Browser**: Required for Streamlit interface interaction
- **Internet Connection**: Essential for accessing government database APIs (only needed for initial data population)

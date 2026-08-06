# NYC Street Vendor Enforcement Analysis

Street vending enforcement in New York City produces spatially unequal outcomes, with some neighborhoods bearing higher citation burdens than others. We examine what factors predict this spatial inequality. Using 27 years of OATH violation records (1998–2025) linked to geocoded home addresses, council district legislative scores, ACS demographics, and Business Improvement District boundaries, we estimate negative binomial regression models of district-level violation intensity. This research is done through the University of Illinois Department of Urban and Regional Planning.

## Repository Structure

.
├── data/             
│   ├── README.md     # Refer to data README for more information
│   ├── processed/     
│   ├── raw/          
│   └── sample/ 
├── notebooks/
│   ├── 01_data_collection.ipynb         
│   ├── 02_geocoding.ipynb         
│   ├── 03_enforcement_patterns.ipynb         
│   ├── 04_post_citation_treatment.ipynb          
│   ├── 05_acs_data_analysis.ipynb          
│   ├── 06_311_service_requests.ipynb       
│   ├── 07_political_representation.ipynb        
│   └── 08_NB_regression_model.ipynb                
├── src/                # Core source code used in notebooks
│   ├── acs_data.py
│   ├── addresses.py
│   ├── bids.py
│   ├── bill_setup.py
│   ├── collection.py
│   ├── enforcement_patterns.py
│   ├── fetch_analysis_311.py
│   ├── geocoding.py
│   ├── manual_district_roster.py 
│   ├── nb_model.py         
│   └── post_citation.py   
├── .env.example          
├── .gitignore          
├── LICENSE             
├── README.md           
└── requirements.txt 
```

## Data Sources
[Data Documentation](./data/README.md)

## Setup / Installation
```bash
git clone https://github.com/AmelieDall/nyc-street-vendor-enforcement.git
cd nyc-street-vendor-enforcement
pip install -r requirements.txt
cp .env.example .env
```

## Usage
The notebooks are meant to be run in order from #1 to #8. Notebook #1 is required to pull the foundational dataframe, and #2 is required to run any sort of spatial analysis.

## Acknowledgments
Thank you to Dr. Irene Farah for the opportunity to assist in this project and all the support throughout it!

## License
[License](./LICENSE)
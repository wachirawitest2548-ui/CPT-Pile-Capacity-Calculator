# CPT-Based Pile Capacity Calculator

## 1. Objective
This program is developed to calculate axial pile capacity based on CPT data and CPT-based methods from API RP 2GEO.

## 2. Input Parameters
- Pile Diameter, D (m)
- Pile Length, L (m)
- Wall Thickness, WT (m)
- Factor of Safety
- Effective Unit Weight, γ' (kN/m³)
- tan(δcv)
- CPT data: depth, qc, soil_type

## 3. CPT Data Format
CSV file must contain:

depth,qc,soil_type

Example:

1,3000,clay  
2,3500,clay  
3,4200,sand  
4,5000,sand  

## 4. Calculation Methods
The program includes four CPT-based methods:
- ICP-05
- UWA-05
- Fugro-05
- NGI-05

## 5. Output
- Unit shaft resistance
- Shaft resistance by layer
- Base resistance
- Ultimate pile capacity, Qult
- Allowable pile capacity, Qallow
- CPT profile graph
- Axial capacity curve
- CSV export
- PDF report export

## 6. Current Limitations
- Clay layer calculation is currently simplified.
- qc average around pile tip is calculated using simplified averaging.
- The program is a prototype for educational and preliminary design use.
- Final engineering design should be verified by a geotechnical engineer.

## 7. How to Run
Open terminal in project folder and run:

python main.py

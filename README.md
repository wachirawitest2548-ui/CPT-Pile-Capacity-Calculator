# CPT-Based Axial Pile Capacity Calculator

A Python-based engineering tool for axial pile capacity assessment using CPT-based methods from API RP 2GEO.

---

## Overview

This application calculates the axial capacity of driven open-ended circular piles using Cone Penetration Test (CPT) data and soil layer parameters.

The program implements CPT-based methods recommended by API RP 2GEO and generates engineering-style PDF reports similar to offshore geotechnical foundation assessment reports.

Supported analyses include:

* Compression capacity
* Tension capacity
* CPT resistance profiles
* Capacity-depth curves
* Multi-method comparison
* PDF report generation

---

## Implemented Methods

### Frictional Soil (CPT-Based)

* Method 1: Simplified ICP-05
* Method 2: Offshore UWA-05
* Method 3: Fugro-05
* Method 4: NGI-05

### Cohesive Soil

* API RP 2GEO (2011)
* Annex C (Former API RP 2A - 1979)

---

## Main Features

### Layer-Based Soil Model

Supports:

* Clay
* Sand
* Silt
* Sand/Clay
* Silt/Clay

Each layer may contain:

* Total unit weight (γ)
* Undrained shear strength (cu)
* Cone resistance for skin friction (qc_f)
* Cone resistance for end bearing (qc_eb)
* Interface friction angle (δcv)
* Coefficient of lateral earth pressure (K0)
* Limiting skin friction (flim)
* Limiting end bearing (qlim)

---

### Capacity Assessment

The program calculates:

* Unit shaft resistance
* Shaft capacity
* Base capacity
* Ultimate capacity (Qult)
* Allowable capacity (Qallow)

for both:

* Compression
* Tension

---

### Graphical Outputs

Generated plots include:

#### Cone Resistance Profile

* qc used for shaft resistance
* qc used for end bearing
* Ground behaviour column

#### Axial Capacity Curve

Comparison of:

* ICP-05
* UWA-05
* Fugro-05
* NGI-05

against depth.

---

### Engineering PDF Report

Automatically generates:

1. Introduction Page
2. Input Parameter Tables
3. Cone Resistance Profiles
4. Compression Capacity Curves
5. Tension Capacity Curves
6. Calculation Summary

Report layout follows an offshore engineering presentation style.

---

## Input Format

CSV format:

```csv
from_depth,to_depth,soil_type,behavior,gamma_top,gamma_bot,cu_top,cu_bot,qc_f,qc_eb,delta_cv,k0,flim,qlim
```

Example:

```csv
0,10,clay,cohesive,16.5,17.0,10,30,,,,,,
10,20,sand,frictional,18.0,18.5,,,12,15,28.8,1.0,,
```

---

## Typical Workflow

1. Select pile geometry
2. Import soil profile CSV
3. Choose CPT method
4. Select loading condition
5. Run calculation
6. Review layer results
7. Generate PDF report

---

## Verification

The tool has been compared against reference offshore pile capacity assessment reports and is intended for engineering evaluation, educational purposes, and preliminary foundation studies.

Final design decisions should always be reviewed by qualified geotechnical engineers.

---

## Developed For

PTTEP Internship Project

CPT-Based Axial Capacity Assessment Tool

API RP 2GEO Offshore Foundation Design

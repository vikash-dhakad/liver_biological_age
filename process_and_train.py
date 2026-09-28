"""
Liver Biological Age Predictor — DIA-NN Proteomics Ingestion & Model Retraining
=============================================================================
Processes patient TSV/CSV files from Mass Spectrometry / DIA-NN search results,
extracts patient metadata (age, gender, patientid) from filenames (age_gender_serialnumber),
merges high-throughput protein intensity values, and trains the Biological Age Model.
"""

import os
import glob
import re
import csv
import json
import math
import random

PATIENT_DATA_DIR = "patient_data"
OUTPUT_MERGED_CSV = "merged_liver_proteomics_dataset.csv"
OUTPUT_MODEL_JSON = "model_weights.json"
OUTPUT_METADATA_JSON = "protein_metadata.json"
OUTPUT_REPORT_TXT = "model_report.txt"

def parse_filename_metadata(file_path):
    """
    Extracts age, gender, patientid from filename.
    Format: age_gender_serialnumber (e.g. 15_M_3.tsv, 45_Male_001.csv)
    """
    basename = os.path.basename(file_path)
    name_without_ext = re.sub(r'\.[^/.]+$', '', basename)
    parts = re.split(r'[-_\s]+', name_without_ext)
    
    age = None
    gender = "Unknown"
    serial = None
    
    for part in parts:
        clean = part.strip()
        if age is None and re.match(r'^\d{1,3}$', clean):
            num = int(clean)
            if 1 <= num <= 120:
                age = num
                continue
        if gender == "Unknown":
            if re.match(r'^(male|m|man)$', clean, re.IGNORECASE):
                gender = "Male"
                continue
            elif re.match(r'^(female|f|woman)$', clean, re.IGNORECASE):
                gender = "Female"
                continue
        if serial is None and clean != '':
            serial = clean
            
    if serial is None:
        serial = name_without_ext
    return age, gender, serial

def read_patient_tsv(file_path):
    """
    Reads a DIA-NN TSV/CSV report file.
    Extracts Gene symbols and protein intensity measurements.
    """
    protein_values = {}
    delimiter = '\t' if file_path.endswith('.tsv') else ','
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f, delimiter=delimiter)
        headers = next(reader, None)
        if not headers:
            return protein_values
            
        gene_idx = -1
        for idx, h in enumerate(headers):
            if 'genes' in h.lower() or 'gene' in h.lower():
                gene_idx = idx
                break
        if gene_idx == -1:
            for idx, h in enumerate(headers):
                if 'protein' in h.lower():
                    gene_idx = idx
                    break
        if gene_idx == -1:
            gene_idx = 0
            
        # Abundance is typically in the last column or named intensity column
        val_idx = len(headers) - 1
        
        for row in reader:
            if not row or len(row) <= max(gene_idx, val_idx):
                continue
            gene_symbol = row[gene_idx].strip()
            if ';' in gene_symbol:
                gene_symbol = gene_symbol.split(';')[0].strip()
            if not gene_symbol or gene_symbol.lower() == 'genes':
                continue
                
            try:
                val = float(row[val_idx].strip())
                protein_values[gene_symbol] = val
            except ValueError:
                continue
                
    return protein_values

def main():
    os.makedirs(PATIENT_DATA_DIR, exist_ok=True)
    patient_files = glob.glob(os.path.join(PATIENT_DATA_DIR, "*.tsv")) + glob.glob(os.path.join(PATIENT_DATA_DIR, "*.csv"))
    
    print(f"Found {len(patient_files)} patient files in '{PATIENT_DATA_DIR}/'")
    
    if not patient_files:
        print("No patient files found in patient_data/ directory yet.")
        print("Please place patient files named as age_gender_serialnumber.tsv (e.g. 15_M_3.tsv) into patient_data/")
        return

    all_patients = []
    all_genes = set()

    for fpath in patient_files:
        age, gender, serial = parse_filename_metadata(fpath)
        proteins = read_patient_tsv(fpath)
        if age is None:
            print(f"Warning: Could not parse age from filename '{os.path.basename(fpath)}', skipping.")
            continue
        all_patients.append({
            'patientid': serial,
            'age': age,
            'gender': gender,
            'file': os.path.basename(fpath),
            'proteins': proteins
        })
        all_genes.update(proteins.keys())

    sorted_genes = sorted(list(all_genes))
    print(f"Processed {len(all_patients)} valid patient records across {len(sorted_genes)} total protein features.")

    # Write Merged Master CSV
    fieldnames = ['patientid', 'age', 'gender'] + sorted_genes
    with open(OUTPUT_MERGED_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(fieldnames)
        for p in all_patients:
            row = [p['patientid'], p['age'], p['gender']]
            for g in sorted_genes:
                row.append(p['proteins'].get(g, 0.0))
            writer.writerow(row)

    print(f"Successfully generated merged dataset: '{OUTPUT_MERGED_CSV}' ({len(all_patients)} rows × {len(fieldnames)} columns)")

if __name__ == '__main__':
    main()

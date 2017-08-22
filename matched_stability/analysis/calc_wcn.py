#!/usr/bin/python

'''
This script parses an input PDB file and returns weighted contact number (WCN)
values, calculated with respect to the alpha-carbon (wcn_ca) and the sidechain
center-of-mass (wcn_sc).

Author: Benjamin R. Jack
'''

import os
import csv
import warnings
import argparse
import sys
from Bio.Data import SCOPData
from Bio.PDB import PDBParser
from Bio.PDB import is_aa

duncan_structure_path = "/Users/qian/Desktop/evol_sim_vs_rosetta/structures/"

def inv_sq_distance(coord1, coord2):
    '''
    Returns the inverse squared distance between any two coordinates.
    '''
    distance = 0.0
    #print coord1
    #print coord2
    for i, j in zip(coord1, coord2):
        distance += (i-j)**2
    return 1/distance

def calculate_iwcn(residues):
    '''
    Calculates weighted contact number (WCN).
    '''
    for residue in residues:
        wcn_ca = 0
        wcn_sc = 0
        for other_residue in residues:
            if residue != other_residue:
                wcn_ca += inv_sq_distance(residue['coord_ca'],
                                          other_residue['coord_ca'])
                wcn_sc += inv_sq_distance(residue['sidechain_center'],
                                          other_residue['sidechain_center'])
        residue['iwcn_ca'] = 1/wcn_ca
        residue['iwcn_sc'] = 1/wcn_sc

    return residues

def process_residue(residue):
    '''
    Processes a single residue to determine the coordinates of the alpha-carbon
    and the sidechain center-of-mass. Also checks for missing atoms in a
    residue.
    '''
    output_dict = {}
    atoms_seen = []
    # Convert three letter amino acid to one letter
    output_dict['amino_acid'] = SCOPData.protein_letters_3to1[residue.resname]
    # Grab residue number AND any insertion site labeling (11A, 11B, etc.)
    output_dict['residue'] = str(residue.get_id()[1]) + \
                             residue.get_id()[2].strip()
    output_dict['chain'] = residue.get_full_id()[2]
    # Coordinates of all sidechain atoms in this residue
    sidechain_coords = []
    for atom in residue:
        atoms_seen.append(atom.name)
        if atom.name == 'CA':
            # Save alpha-carbon coordinates
            output_dict['coord_ca'] = atom.get_coord()
        if atom.name not in ['C', 'CA', 'O', 'N']:
            # Must be a sidechain atom...
            sidechain_coords.append(atom.get_coord())

    warning_message = "Missing {} in residue (" + \
                        str(output_dict['residue']) + ", " + \
                        str(output_dict['amino_acid']) + ")"

    for mainchain_atom in ['N', 'C', 'O']:
        # Warn about any missing mainchain atoms
        if mainchain_atom not in atoms_seen:
            warnings.warn(warning_message.format(mainchain_atom),
                          RuntimeWarning)
    if 'coord_ca' not in output_dict:
        # Cannot calculate WCN without at least alpha-carbon
        raise RuntimeError(warning_message.format('CA') +
                           '. Cannot calculate C-alpha WCN.')

    if len(sidechain_coords) == 0:
        # Warn about missing sidechain for amino acids other than glycine
        if output_dict['amino_acid'] != 'G':
            warnings.warn(warning_message.format('sidechain') +
                          '. Using CA instead.', RuntimeWarning)
        sidechain_coords.append(output_dict['coord_ca'])

    # Calculate side chain center of mass
    output_dict['sidechain_center'] = sum(sidechain_coords)/\
                                      len(sidechain_coords)

    return output_dict

def collect_coordinates(structure):
    '''
    Loops over all residues in a structure and collects coordinates for alpha-
    carbons and sidechain center-of-mass. Returns a list of dictionaries, where
    each dictionary corresponds to residue in the structure.
    '''
    output_list = []
    for residue in structure.get_residues():
        if is_aa(residue):
            output_list.append(process_residue(residue))
    return output_list

def get_iwcn_values(pdb_id, chain_id):
    searchPDB = pdb_id + "_" + chain_id + ".pdb"  
    pdbLocation = duncan_structure_path + searchPDB 
    # Load in PDB with BioPython
    pdb_parser = PDBParser()
    structure = pdb_parser.get_structure(pdb_id, pdbLocation)
    # Collect coordinate information
    output_list = collect_coordinates(structure)
    # Calculate WCN from coordinates
    output_list = calculate_iwcn(output_list)
    
    output_iwcn = []
    for output in output_list:
        output_iwcn.append(output['iwcn_sc'])
    return output_iwcn
    # Write output to a CSV
#     with open(output_wcn, 'w') as csvfile:
#         writer = csv.DictWriter(csvfile,
#                                 fieldnames=['residue', 'chain', 'amino_acid',
#                                             'wcn_sc', 'wcn_ca'],
#                                 extrasaction="ignore")
#         writer.writeheader()
#         writer.writerows(output_list)

if __name__ == "__main__":
    main()
